"""Leitores defensivos de DTLG e tabelas .dat, com rastreabilidade.

Importante: formato DTLG derivado empiricamente; não é especificação oficial.
"""
from __future__ import annotations
import io
import json
import math
import re
import zipfile
from pathlib import Path
from typing import Callable
import numpy as np

from decodificar_dtlg import decodificar
from .models import Spectrum, ScanReport

MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_SPECTRUM_POINTS = 1_000_000


class InvalidSpectrum(ValueError):
    pass


class _MemoryPath:
    def __init__(self, data: bytes):
        self.data = data

    def read_bytes(self) -> bytes:
        return self.data


def decode_binary(data: bytes) -> tuple[np.ndarray, np.ndarray, dict]:
    if not data.startswith(b"DTLG"):
        raise InvalidSpectrum("Assinatura DTLG ausente")
    try:
        rows, fields, _, _ = decodificar(_MemoryPath(data))
    except (ValueError, UnicodeError, OverflowError, OSError) as exc:
        raise InvalidSpectrum(str(exc)) from exc
    xy = np.asarray(rows, dtype=float)
    if len(xy) > MAX_SPECTRUM_POINTS:
        raise InvalidSpectrum("Curva excede o limite de pontos")
    return xy[:, 0] / 10.0, xy[:, 1], {f["campo"]: f["valor"] for f in fields}


def _to_float(token: str) -> float:
    token = token.strip().replace("\u2212", "-").replace("\u00a0", "")
    if "," in token and "." not in token:
        token = token.replace(",", ".")
    return float(token)


def _tokens(line: str) -> list[str]:
    line = line.strip()
    if ";" in line:
        return [c.strip() for c in line.split(";")]
    if "\t" in line:
        return [c.strip() for c in line.split("\t")]
    pieces = line.split()
    if len(pieces) >= 2:
        return pieces
    if "," in line:
        return [c.strip() for c in line.split(",")]
    return pieces


def _decode_text(data: bytes) -> str:
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise InvalidSpectrum("Codificação não reconhecida")


def decode_dat(data: bytes, unit: str = "auto") -> tuple[np.ndarray, np.ndarray, str, list[str]]:
    """Retorna x[nm], y[original], origem da unidade e avisos.

    A inferência automática Å/nm por escala é heurística e é explicitamente
    registrada. O operador pode forçar a unidade em Configurações da interface.
    """
    if unit not in ("auto", "angstrom", "nm"):
        raise ValueError("Unidade DAT inválida")
    text = _decode_text(data)
    rows: list[tuple[float, float]] = []
    header: list[str] = []
    extra_columns = False
    for line_number, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith(("#", "//")):
            if not rows and s: header.append(s)
            continue
        cells = _tokens(s)
        try:
            if len(cells) < 2:
                raise ValueError("Menos de duas colunas")
            x, y = _to_float(cells[0]), _to_float(cells[1])
        except ValueError:
            if not rows and len(header) < 50:
                header.append(s)
                continue
            raise InvalidSpectrum(f"Linha {line_number}: registro inválido após o início dos dados")
        if not (math.isfinite(x) and math.isfinite(y)):
            raise InvalidSpectrum(f"Linha {line_number}: valor não finito")
        rows.append((x, y))
        extra_columns = extra_columns or len(cells) > 2
        if len(rows) > MAX_SPECTRUM_POINTS:
            raise InvalidSpectrum("Arquivo contém pontos demais")
    if len(rows) < 2:
        raise InvalidSpectrum("Menos de dois pontos válidos no DAT")
    xy = np.asarray(rows, dtype=float)
    x = xy[:, 0]
    if not np.all(np.diff(x) > 0):
        raise InvalidSpectrum("Comprimentos de onda não são estritamente crescentes")
    header_text = " ".join(header).lower()
    warnings = []
    if unit == "auto":
        if "ångstr" in header_text or "angstrom" in header_text or re.search(r"\b(?:lambda|wavelength|comprimento)[ _-]*\(?[åa]\)?\b", header_text):
            unit = "angstrom"; origin = "Cabeçalho DAT: Å"
        elif re.search(r"\b(?:lambda|wavelength|comprimento)[ _-]*\(?nm\)?\b", header_text):
            unit = "nm"; origin = "Cabeçalho DAT: nm"
        elif 3000 < np.median(x) <= 200000:
            unit = "angstrom"; origin = "Inferida pela escala: Å"
            warnings.append("Unidade do DAT inferida como Å pelos valores do eixo X; confirme nas medidas futuras.")
        elif 100 <= np.median(x) <= 3000:
            unit = "nm"; origin = "Inferida pela escala: nm"
            warnings.append("Unidade do DAT inferida como nm pelos valores do eixo X; confirme nas medidas futuras.")
        else:
            raise InvalidSpectrum("Unidade espectral ambígua no DAT; selecione Å ou nm na interface")
    else:
        origin = f"Definida pelo operador: {unit}"
    if extra_columns:
        warnings.append("Mais de duas colunas no DAT: foram usadas apenas as duas primeiras.")
    nm = x / 10 if unit == "angstrom" else x
    if np.min(nm) <= 0:
        raise InvalidSpectrum("Comprimento de onda não positivo")
    return nm, xy[:, 1], origin, warnings


def parse_filename(name: str) -> dict:
    """Extrai condições sem confundir data, hora e sensibilidade com amostra."""
    stem = Path(name).name
    stem = re.sub(r"\.(?:dat|dtlg|bin|csv)$", "", stem, flags=re.I).strip()
    prefix = re.search(r"^(\d{8})[\s_]+(\d{4})[\s_-]+(.+)$", stem)
    segment = prefix.group(3) if prefix else stem
    # O identificador entre parênteses é conservado separadamente: 4557(1659)
    # significa amostra principal 4557 e código adicional 1659, sem presumir
    # relação física entre ambos.
    sample_match = (re.match(r"\s*(ITA|\d{3,8})(?:\(([^()]+)\))?(?=[\s_-]|$)", segment, re.I)
                    or re.match(r"\s*([A-Za-z][A-Za-z0-9_-]*)(?:\(([^()]+)\))?(?=\s|$)", segment, re.I))
    slit = re.search(r"(?<![A-Za-z0-9])(\d+(?:[.,]\d+)?)\s*(?:um|µm|μm)(?![A-Za-z0-9])", segment, re.I)
    mv = re.search(r"(?<![A-Za-z0-9])(\d+(?:[.,]\d+)?)\s*mV(?![A-Za-z0-9])", segment, re.I)
    temp = re.search(r"(?<![A-Za-z0-9])(\d+(?:[.,]\d+)?)\s*K(?![A-Za-z0-9])", segment, re.I)
    return {
        "sample": (sample_match.group(1).upper() if sample_match else "Não identificada"),
        "sample_code": (sample_match.group(2).strip() if sample_match and sample_match.group(2) else None),
        "slit_um": _to_float(slit.group(1)) if slit else None,
        "lockin_mv": _to_float(mv.group(1)) if mv else None,
        "temperature_k": _to_float(temp.group(1)) if temp else None,
        "date_label": (prefix.group(1) + " " + prefix.group(2)) if prefix else "",
        "stem": stem,
    }


def _make_spectrum(uid: str, filename: str, data: bytes, unit: str) -> Spectrum:
    name = Path(filename).name
    attr = parse_filename(name)
    raw = {}
    warnings: list[str] = []
    if data.startswith(b"DTLG"):
        x, y, raw = decode_binary(data)
        primary = "DTLG"
        x_origin = "DTLG: Å (decodificador validado para formato inicial)"
    elif name.lower().endswith((".dat", ".csv", ".txt")):
        x, y, x_origin, warnings = decode_dat(data, unit)
        primary = "DAT"
    else:
        raise InvalidSpectrum("Formato não reconhecido")
    if raw:
        # O cabeçalho pode continuar contendo o nome antigo após renomeação.
        # Nunca usar esse campo para substituir o arquivo lido do sistema.
        original_filename = str(raw.get("Nome do arquivo", "")).strip()
        if original_filename and parse_filename(original_filename)["stem"].casefold() != attr["stem"].casefold():
            warnings.append("Nome atual do arquivo diverge do nome interno DTLG; prevalece o nome atual.")
        raw_sample = str(raw.get("Amostra", "")).strip()
        if raw_sample:
            if attr["sample"] != "Não identificada":
                if attr["sample"] != raw_sample.upper():
                    warnings.append(f"Amostra divergente: nome {attr['sample']}; cabeçalho {raw_sample}. Prevalece o nome.")
            else:
                # Só há fallback se o nome não fornecer uma identificação.
                attr["sample"] = raw_sample.upper()
                warnings.append("Amostra ausente no nome: identificação obtida do cabeçalho (fallback).")
        raw_t = raw.get("Temperatura")
        if raw_t is not None and attr["temperature_k"] is not None and abs(float(raw_t) - attr["temperature_k"]) > 0.5:
            warnings.append(f"Temperatura divergente: nome {attr['temperature_k']:g} K; cabeçalho {raw_t:g} K. Valor real requer operador.")
        for key in ("Fenda de entrada (mm)", "Fenda de saida (mm)"):
            slit_header = raw.get(key)
            if slit_header is not None and attr["slit_um"] is not None and abs(float(slit_header) * 1000 - attr["slit_um"]) > .5:
                warnings.append(f"Fendas divergentes: nome {attr['slit_um']:g} µm; cabeçalho {key}={float(slit_header)*1000:g} µm.")
    # Aviso conservador: platô com >=3 valores consecutivos exatamente iguais no topo.
    max_signal = float(np.max(y))
    if np.isfinite(max_signal) and max_signal > 0:
        plateaus = (y == max_signal)
        consecutive = 0
        for is_top in plateaus:
            consecutive = consecutive + 1 if is_top else 0
            if consecutive >= 3:
                warnings.append("Possível saturação: ao menos três pontos consecutivos no valor máximo.")
                break
    return Spectrum(uid=uid, name=attr["stem"], wavelength_nm=x, signal=y,
                    sample=attr["sample"], sample_code_filename=attr["sample_code"],
                    slit_filename_um=attr["slit_um"],
                    lockin_range_mv=attr["lockin_mv"], temperature_filename_k=attr["temperature_k"],
                    metadata_original=raw, source_files=[filename], primary_format=primary,
                    date_label=attr["date_label"], warnings=warnings, wavelength_origin=x_origin)


def _files(source: Path, recursive: bool):
    if source.is_file() and source.suffix.lower() == ".zip":
        with zipfile.ZipFile(source) as z:
            for info in z.infolist():
                if info.is_dir(): continue
                if info.file_size > MAX_FILE_BYTES:
                    yield info.filename, None, "Arquivo grande demais para leitura segura"
                else:
                    try:
                        yield info.filename, z.read(info), None
                    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                        yield info.filename, None, str(exc)
    elif source.is_dir():
        iterator = source.rglob("*") if recursive else source.iterdir()
        for p in sorted(iterator):
            if not p.is_file(): continue
            if p.stat().st_size > MAX_FILE_BYTES:
                yield str(p.relative_to(source)), None, "Arquivo grande demais para leitura segura"
            else:
                try:
                    yield str(p.relative_to(source)), p.read_bytes(), None
                except OSError as exc:
                    yield str(p.relative_to(source)), None, str(exc)
    else:
        raise FileNotFoundError(f"Pasta ou ZIP não encontrado: {source}")


def scan_source(source: str | Path, recursive: bool = False, dat_unit: str = "auto",
                cancelled: Callable[[], bool] | None = None) -> ScanReport:
    source = Path(source)
    result = ScanReport()
    buckets: dict[str, list[Spectrum]] = {}
    for filename, data, error in _files(source, recursive):
        if cancelled and cancelled():
            raise InterruptedError("Leitura cancelada")
        result.total_examined += 1
        if error:
            result.errors.append(f"{filename}: {error}")
            continue
        ext = Path(filename).suffix.lower()
        if not (ext in (".dat", ".csv", ".txt") or (data is not None and data[:4] == b"DTLG")):
            result.ignored += 1
            continue
        try:
            sp = _make_spectrum(filename, filename, data, dat_unit)
        except (InvalidSpectrum, ValueError, IndexError) as exc:
            result.errors.append(f"{filename}: {exc}")
            continue
        stem_key = re.sub(r"\.(?:dat|dtlg|bin|csv|txt)$", "", filename, flags=re.I).casefold()
        buckets.setdefault(stem_key, []).append(sp)
    for group in buckets.values():
        binaries = [s for s in group if s.primary_format == "DTLG"]
        texts = [s for s in group if s.primary_format != "DTLG"]
        for b in binaries:
            # Não presumir igualdade só porque os nomes coincidem.
            for t in list(texts):
                if (b.wavelength_nm.shape == t.wavelength_nm.shape
                    and np.allclose(b.wavelength_nm, t.wavelength_nm, rtol=0, atol=1e-9)
                    and np.allclose(b.signal, t.signal, rtol=2e-6, atol=1e-9)):
                    b.source_files.extend(t.source_files)
                    b.duplicates_verified = True
                    b.warnings = list(dict.fromkeys(b.warnings + [w for w in t.warnings if "inferida" not in w.lower()]))
                    texts.remove(t)
                    result.paired_duplicates += 1
                    break
        if binaries and texts:
            for sp in binaries + texts:
                sp.warnings.append("Arquivos de mesmo nome-base não equivalentes: mantidos separadamente.")
        result.spectra.extend(binaries + texts)
    result.spectra.sort(key=lambda s: (s.sample.lower(), s.slit_filename_um or -1,
                                       s.lockin_range_mv or -1, s.uid.casefold()))
    return result
