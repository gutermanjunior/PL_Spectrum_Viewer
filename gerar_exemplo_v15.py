"""Reproduce the actual October 9 measurements in v1.5 as PDF/SVG/PNG.

No physical interpretation or signal calibration is introduced. Visual guide lines
are illustrative. Run from the project root: python gerar_exemplo_v15.py
"""
from pathlib import Path

from pl_viewer.readers import scan_source
from pl_viewer.multipanel import Composition, PanelState, create_composition_export_figure
from pl_viewer.plotting import PlotSettings, VerticalAnnotation, export_vector

ROOT=Path(__file__).resolve().parent
source=ROOT/'exemplos'/'20261009 PL 4573-4574-4575-4576-4577.zip'
out=ROOT/'exemplos'/'v1_5_multiplos_paineis'
out.mkdir(exist_ok=True)
spectra=scan_source(source).spectra

def get(sample, slit, lockin):
    return next(sp for sp in spectra if sp.sample==sample and sp.slit_filename_um==slit
                and sp.lockin_range_mv==lockin)

p1=[get(n,300,200) for n in ('4574','4575','4576')]
p2=[get(n,90,500) for n in ('4573','4577')]
by={sp.uid:sp for sp in spectra}

base=dict(x_unit='nm',y_unit='mV',x_min=770,x_max=845,
          figure_width_in=15.5,figure_height_in=7.1,
          font_title=13,font_subtitle=10,font_axes=11,font_ticks=9,
          font_legend=9,font_annotations=8,footer='',
          show_title=True,show_subtitle=False,show_footer=False,
          margin_left=.075,margin_right=.975,margin_top=.89,margin_bottom=.14,
          legend_fields=['sample','slit','lockin'])

comp=Composition(layout='1x2',hspace=.34,wspace=.28,share_x=True,share_y=False)
comp.panels[0]=PanelState(uids=[sp.uid for sp in p1],settings=PlotSettings(**(base|dict(
    title='Série de crescimento em baixa temperatura',
    y_max=172, y_min=0))),annotations=[VerticalAnnotation(824.5,'Referência visual',label_y=.69)],grid=True)
comp.panels[1]=PanelState(uids=[sp.uid for sp in p2],settings=PlotSettings(**(base|dict(
    title='Cinco poços × um poço',
    y_min=0,y_max=510))),annotations=[],grid=True)
# Different explicit y limits are fine with share_y=False.
fig=create_composition_export_figure(by,comp)
for fmt in ('pdf','svg','png'):
    export_vector(fig,out/f'PL_09out_2026_dois_paineis.{fmt}',title='PL 09out2026 — comparação em dois painéis')
fig.clear()

# The same records, with four independent subplot assignments, to demo 2x2.
comp2=Composition(layout='2x2',wspace=.24,hspace=.50,share_x=True,share_y=False)
for i,spec in enumerate((p1[:2],p1[2:],p2[:1],p2[1:])):
    small=base|dict(title=(('4574 e 4575','4576','4573','4577')[i]),
                    y_min=0,y_max=None,font_title=11,font_axes=10,font_ticks=8,
                    font_legend=8,figure_width_in=14.8,figure_height_in=10.5)
    comp2.panels[i]=PanelState(uids=[sp.uid for sp in spec],settings=PlotSettings(**small),
                               grid=True,legend=True)
fig2=create_composition_export_figure(by,comp2)
for fmt in ('pdf','svg','png'):
    export_vector(fig2,out/f'PL_09out_2026_quatro_paineis.{fmt}',title='PL 09out2026 — quatro painéis')
fig2.clear()
print('Exemplos criados em',out)
