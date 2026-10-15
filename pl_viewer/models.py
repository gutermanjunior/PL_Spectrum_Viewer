"""Modelos de aquisição; mantém valores instrumentais e interpretações separados."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import numpy as np


@dataclass
class Spectrum:
    uid: str
    name: str
    wavelength_nm: np.ndarray
    signal: np.ndarray
    sample: str = "Não identificada"
    sample_code_filename: str | None = None  # Código auxiliar entre parênteses, não é amostra principal
    slit_filename_um: float | None = None
    lockin_range_mv: float | None = None
    temperature_filename_k: float | None = None
    temperature_operator_k: float | None = None
    metadata_original: dict[str, Any] = field(default_factory=dict)
    source_files: list[str] = field(default_factory=list)
    primary_format: str = ""
    date_label: str = ""
    warnings: list[str] = field(default_factory=list)
    duplicates_verified: bool = False
    wavelength_origin: str = ""

    @property
    def sample_display(self) -> str:
        return (f"{self.sample}({self.sample_code_filename})"
                if self.sample_code_filename else self.sample)

    @property
    def temperature_indicated(self) -> str:
        """Value displayed in the acquisition list, exclusively from filename."""
        return (f"{self.temperature_filename_k:g} K (nome)"
                if self.temperature_filename_k is not None else "—")

    @property
    def temperature_effective(self) -> str:
        if self.temperature_operator_k is not None:
            return f"{self.temperature_operator_k:g} K (operador)"
        if self.temperature_filename_k is not None:
            return f"{self.temperature_filename_k:g} K (nome; não confirmado)"
        return "Não informada"

    @property
    def header_slits_um(self) -> tuple[float | None, float | None]:
        def v(key):
            try:
                return float(self.metadata_original[key]) * 1000
            except (KeyError, TypeError, ValueError):
                return None
        return v("Fenda de entrada (mm)"), v("Fenda de saida (mm)")

    @property
    def summary(self) -> dict[str, Any]:
        return {
            "id": self.uid,
            "nome": self.name,
            "amostra": self.sample,
            "amostra_codigo_auxiliar_nome": self.sample_code_filename,
            "criterio_identificacao": "Nome do arquivo prevalece; metadados instrumentais para conferência",
            "data_hora_nome": self.date_label or None,
            "fenda_nome_um": self.slit_filename_um,
            "fendas_entrada_saida_nome_um": [self.slit_filename_um, self.slit_filename_um]
                if self.slit_filename_um is not None else None,
            "fenda_cabecalho_entrada_um": self.header_slits_um[0],
            "fenda_cabecalho_saida_um": self.header_slits_um[1],
            "fundo_escala_lockin_mv": self.lockin_range_mv,
            "fundo_escala_origem": "nome do arquivo" if self.lockin_range_mv is not None else "não informado",
            "temperatura_nome_k": self.temperature_filename_k,
            "temperatura_informada_operador_k": self.temperature_operator_k,
            "temperatura_cabecalho_k": self.metadata_original.get("Temperatura"),
            "temperatura_exibida": self.temperature_effective,
            "origem_unidade_espectral": self.wavelength_origin,
            "formato_primario": self.primary_format,
            "arquivos": self.source_files,
            "equivalencia_binario_dat_confirmada": self.duplicates_verified,
            "pontos": int(self.signal.size),
            "faixa_nm": [float(self.wavelength_nm[0]), float(self.wavelength_nm[-1])],
            "unidade_sinal_armazenado": "V",
            "sinal_maximo_armazenado_V": float(np.max(self.signal)),
            "sinal_maximo_armazenado": float(np.max(self.signal)),
            "avisos": list(dict.fromkeys(self.warnings)),
            "metadados_binarios_originais": self.metadata_original,
        }


@dataclass
class ScanReport:
    spectra: list[Spectrum] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    ignored: int = 0
    total_examined: int = 0
    paired_duplicates: int = 0
