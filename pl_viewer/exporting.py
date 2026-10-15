"""Exportações de dados independentes da interface Qt."""
from __future__ import annotations
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable
from .models import Spectrum


def export_curves_csv(path: str | Path, spectra: Iterable[Spectrum]):
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['id', 'amostra', 'fenda_nome_um', 'fundo_escala_lockin_mv',
                    'temperatura_informada_operador_k', 'comprimento_onda_nm',
                    'sinal_bruto_unidade_nao_verificada', 'sinal_bruto_V'])
        for s in spectra:
            for x, y in zip(s.wavelength_nm, s.signal):
                w.writerow([s.uid, s.sample, s.slit_filename_um, s.lockin_range_mv,
                            s.temperature_operator_k, format(float(x), '.17g'),
                            format(float(y), '.17g'), format(float(y), '.17g')])


def export_metadata_json(path: str | Path, spectra: Iterable[Spectrum], source: str | None):
    output = {'origem': source, 'exportado_em': datetime.now().isoformat(),
              'aviso': 'Valores adquiridos em V. A exibição em mV multiplica por 1000, sem alterar o sinal. Divergências de metadados preservadas.',
              'aquisicoes': [s.summary for s in spectra]}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def export_scaled_curves_csv(path: str | Path, spectra: Iterable[Spectrum],
                             scale_factors: dict[str, float] | None = None):
    """Explicit new CSV with original and multiplied signals, never in-place editing."""
    from .plotting import scaled_signal, validate_factor
    scales = scale_factors or {}
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['id', 'amostra', 'comprimento_onda_nm',
                    'sinal_bruto_unidade_nao_verificada', 'fator_adimensional',
                    'sinal_multiplicado_unidade_nao_verificada', 'sinal_bruto_V', 'sinal_multiplicado_V'])
        for sp in spectra:
            factor = validate_factor(scales.get(sp.uid, 1.0))
            yy = scaled_signal(sp, factor)
            for wavelength, raw, scaled in zip(sp.wavelength_nm, sp.signal, yy):
                w.writerow([sp.uid, sp.sample, format(float(wavelength), '.17g'),
                            format(float(raw), '.17g'), format(factor, '.17g'),
                            format(float(scaled), '.17g'), format(float(raw), '.17g'),
                            format(float(scaled), '.17g')])
