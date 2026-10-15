#!/usr/bin/env python3
"""Validação sem interface gráfica (útil para laboratório e instalação)."""
from __future__ import annotations
import argparse
from pathlib import Path
from pl_viewer.readers import scan_source


def main():
    p = argparse.ArgumentParser(description="Audita arquivos PL sem exigir PySide6")
    p.add_argument('origem', type=Path, help="Pasta ou ZIP")
    p.add_argument('--recursivo', action='store_true')
    args = p.parse_args()
    r = scan_source(args.origem, recursive=args.recursivo)
    print(f'Aquisições: {len(r.spectra)}')
    print(f'Arquivos examinados: {r.total_examined}')
    print(f'Duplicatas binário/DAT verificadas: {r.paired_duplicates}')
    print(f'Arquivos ignorados: {r.ignored}; erros: {len(r.errors)}')
    print('Amostras detectadas:', ', '.join(sorted({s.sample for s in r.spectra})))
    for s in r.spectra:
        print(f'  {s.sample:>8} | fenda(nome)={s.slit_filename_um}µm | lock-in={s.lockin_range_mv}mV '
              f'| pontos={len(s.signal)} | pico={s.wavelength_nm[s.signal.argmax()]:.1f}nm | avisos={len(s.warnings)}')
    if r.errors:
        print('\nERROS:')
        for msg in r.errors:
            print(' -', msg)
    return 0 if r.spectra and not r.errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
