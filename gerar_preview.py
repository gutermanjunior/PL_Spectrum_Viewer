#!/usr/bin/env python3
"""Prévia gráfica de validação, sem interface Qt (opcional)."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from pl_viewer.readers import scan_source

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'exemplos' / '20261009 PL 4573-4574-4575-4576-4577.zip'
TARGET = ROOT / 'exemplos' / 'preview_1000um_500mV.png'


def generate(source=SOURCE, target=TARGET):
    report = scan_source(source)
    subset = [s for s in report.spectra if s.slit_filename_um == 1000 and s.lockin_range_mv == 500]
    fig = Figure(figsize=(11, 6), dpi=155)
    ax = fig.add_subplot(111)
    for s in subset:
        ax.plot(s.wavelength_nm, s.signal, label=s.sample, linewidth=1.3)
    ax.set(title='PL: fendas declaradas 1000 µm / lock-in 500 mV',
           xlabel='Comprimento de onda (nm)', ylabel='Sinal armazenado (unidade não verificada)')
    ax.grid(alpha=.25)
    ax.legend(title='Amostra')
    fig.text(.5, .015, 'Gráfico estático de conferência — não substitui o aplicativo interativo.', ha='center', fontsize=9)
    fig.savefig(target, bbox_inches='tight')
    print(f'Gráfico de conferência: {target}')
    return target


if __name__ == '__main__':
    generate()
