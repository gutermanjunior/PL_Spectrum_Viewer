"""Gera exemplos v1.4 determinísticos com os espectros incluídos no pacote.

Uso: python gerar_exemplo_v14.py
Fonte: ZIP real de 09/10/2026; nenhuma calibração, ajuste ou medida nova.
"""
from pathlib import Path
from matplotlib.figure import Figure
from pl_viewer.readers import scan_source
from pl_viewer.plotting import (PlotSettings, VerticalAnnotation, HorizontalAnnotation,
                                render_plot, export_vector, save_session)

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'exemplos'/'20261009 PL 4573-4574-4575-4576-4577.zip'
OUT=ROOT/'exemplos'/'v1_4_unidades_e_formatacao'
OUT.mkdir(parents=True,exist_ok=True)
all_records=scan_source(SOURCE).spectra
# Simula ordem de clique: 4576 → 4574 → 4575
records=[]
for sample in ('4576','4574','4575'):
    found=[s for s in all_records if s.sample==sample and s.slit_filename_um==300
           and s.lockin_range_mv==200]
    if len(found)!=1:
        raise RuntimeError(f'Aquisição {sample} ambígua/ausente: {len(found)}')
    records.append(found[0])
factors={records[0].uid:2.0}  # Somente fator visual
marks=[VerticalAnnotation(824.5,'Referência em λ', color='#687180',label_y=.57,label_dx_pt=-25),
       HorizontalAnnotation(.08,'Referência em sinal (0,08 V)',color='#d14343',
                            linestyle='--',label_x=.72,label_dy_pt=19)]
for xunit,yunit,tag in [('angstrom','mV','angstrom_mV'),('nm','V','nm_V')]:
    s=PlotSettings(
        title='9 de outubro de 2026  |  Séries de fotoluminescência',
        subtitle='Amostras #4574, #4575 e #4576 — 77 K indicados no nome dos arquivos',
        x_unit=xunit,y_unit=yunit,
        figure_width_in=15.5,figure_height_in=8.8,font_family='DejaVu Sans',
        font_title=19, font_subtitle=12,font_axes=15,font_ticks=12,
        font_legend=11,font_annotations=10,font_footer=10,
        line_width=2.5,annotation_line_width=1.4,
        margin_left=.105,margin_right=.97,margin_top=.85,margin_bottom=.16,
        legend_fields=['sample','slit','temperature','lockin','factor'],
        legend_location='upper right',legend_columns=1,
        footer='Exibição ilustrativa dos sinais adquiridos em V; nenhuma correção de linha de base.',
        grid_alpha=.2)
    fig=Figure()
    render_plot(fig,records,s,marks,scale_factors=factors,highlight_peak_uid=records[2].uid)
    prefix=OUT/f'PL_v14_{tag}'
    for suffix in ('png','pdf','svg'):
        export_vector(fig,prefix.with_suffix('.'+suffix),title=s.title)
    save_session(prefix.with_suffix('.json'),s,marks,str(SOURCE),
                 [r.uid for r in records],0,True,True,
                 scale_factors=factors,highlight_peak_uid=records[2].uid)
    print(prefix)
