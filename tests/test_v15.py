"""v1.5 multiple independent panels + title/subtitle/footer layout toggles.

All these tests are headless, not a substitute for interactive PySide6 smoke testing.
"""
from copy import deepcopy
from pathlib import Path
import json
import xml.etree.ElementTree as ET

import fitz
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
import numpy as np
import pytest

from pl_viewer.readers import scan_source
from pl_viewer.plotting import PlotSettings, VerticalAnnotation, HorizontalAnnotation, render_plot, export_vector, save_session, load_session
from pl_viewer.multipanel import (Composition, PanelState, render_composition,
                                  create_composition_export_figure,
                                  composition_to_dict, composition_from_dict,
                                  augment_session_json, restore_composition_from_session)

DATA = Path(__file__).resolve().parents[1] / 'exemplos' / '20261009 PL 4573-4574-4575-4576-4577.zip'


def records():
    s = scan_source(DATA).spectra
    a = next(x for x in s if x.sample == '4574' and x.slit_filename_um == 300)
    b = next(x for x in s if x.sample == '4575' and x.slit_filename_um == 300)
    c = next(x for x in s if x.sample == '4576' and x.slit_filename_um == 300)
    return a, b, c


def composition():
    a, b, c = records()
    comp = Composition(layout='1x2')
    comp.panels[0] = PanelState([a.uid,b.uid], PlotSettings(
        title='Regime de baixa temperatura', x_unit='nm', y_unit='mV',
        subtitle='Amostras 4574 e 4575', footer='Nota experimental preservada.',
        show_title=True, show_subtitle=True, show_footer=True),
        [VerticalAnnotation(824.5,'Pico próximo'), HorizontalAnnotation(.03,'Guia horizontal')])
    comp.panels[1] = PanelState([c.uid], PlotSettings(
        title='Amostra 4576', show_title=False, show_subtitle=False,
        show_footer=False, x_unit='angstrom',y_unit='V',
        line_width=2.5, legend_fields=['sample']),
        [VerticalAnnotation(824.5,'λ referência')], legend=True)
    return comp


def test_figure_optional_text_and_reclaimed_area():
    a, *_ = records()
    default = PlotSettings(subtitle='Subtítulo experimental')
    ax0 = render_plot(Figure(),[a], default)[0]
    top0, bottom0 = ax0.figure.subplotpars.top, ax0.figure.subplotpars.bottom
    compact = PlotSettings(title='Preservado em JSON', subtitle='Ainda editável',
                           footer='Ainda editável',show_title=False,
                           show_subtitle=False,show_footer=False)
    fig = Figure(figsize=(7,4))
    ax = render_plot(fig,[a],compact,resize_figure=False)[0]
    assert tuple(fig.get_size_inches()) == pytest.approx((7,4))
    assert not fig.texts
    assert fig.subplotpars.top > top0
    assert fig.subplotpars.bottom < bottom0
    assert compact.title == 'Preservado em JSON'


@pytest.mark.parametrize('layout,count', [('1x1',1), ('1x2',2), ('2x1',2), ('2x2',4)])
def test_composition_shapes_and_non_resizing_preview(layout,count):
    a,b,c = records()
    comp=composition()
    comp.layout=layout
    fig=Figure(figsize=(5.2,3.65))
    original=np.asarray(a.signal).copy()
    axes=render_composition(fig,{x.uid:x for x in (a,b,c)},comp,
                            display_factors={c.uid:2},resize_figure=False)
    assert len(axes)==count
    assert tuple(fig.get_size_inches())==pytest.approx((5.2,3.65))
    np.testing.assert_array_equal(a.signal,original)
    if count > 1:
        assert axes[0].get_ylabel().endswith('(mV)')
        assert axes[1].get_ylabel().endswith('(V)')
        assert axes[0].get_xlabel().endswith('(nm)')
        assert axes[1].get_xlabel().endswith('(Å)')
        assert 'Pico próximo' in '\n'.join(t.get_text() for t in axes[0].texts)
        assert 'λ referência' in '\n'.join(t.get_text() for t in axes[1].texts)
        assert axes[1].get_title(loc='left') == ''
        assert axes[0].get_legend() is not None
        assert axes[1].get_legend() is not None


def test_composition_shared_axes_guard_and_persistence():
    comp=composition()
    comp.share_x=True
    with pytest.raises(ValueError,match='unidade'):
        comp.validate()
    comp.share_x=False
    comp.share_y=True
    with pytest.raises(ValueError,match='unidade'):
        comp.validate()
    comp.share_y=False
    data=composition_to_dict(comp)
    copy=composition_from_dict(data)
    assert composition_to_dict(copy)==data
    assert copy.panels[0].annotations[0].wavelength_nm==824.5
    assert copy.panels[1].settings.show_title is False


def test_independent_curve_colors_selection_order():
    a,b,c = records()
    comp=composition()
    comp.panels[0].uids=[b.uid,a.uid]
    fig=Figure(figsize=(10,5))
    axes=render_composition(fig,{s.uid:s for s in (a,b,c)},comp)
    assert axes[0].lines[0].get_color()=='#1f77b4'
    assert axes[0].lines[1].get_color()=='#ff7f0e'
    assert axes[1].lines[0].get_color()=='#1f77b4'


def test_composition_footer_and_title_visibility_affect_margins():
    comp=composition()
    fig=Figure()
    render_composition(fig, {x.uid:x for x in records()},comp)
    base_top=fig.subplotpars.top
    base_bottom=fig.subplotpars.bottom
    assert any('Nota experimental' in t.get_text() for t in fig.texts)
    for panel in comp.panels:
        panel.settings.show_title=False
        panel.settings.show_subtitle=False
    comp.panels[0].settings.show_footer=False
    fig2=Figure()
    render_composition(fig2, {x.uid:x for x in records()},comp)
    assert fig2.subplotpars.top>base_top
    assert fig2.subplotpars.bottom<base_bottom
    assert not fig2.texts


def test_export_combined_pdf_svg_and_old_session(tmp_path):
    a,b,c=records()
    comp=composition()
    by={s.uid:s for s in (a,b,c)}
    fig=create_composition_export_figure(by,comp,display_factors={c.uid:2})
    assert tuple(fig.get_size_inches())==pytest.approx((13.5,7.7))
    pdf=tmp_path/'composicao.pdf'
    svg=tmp_path/'composicao.svg'
    export_vector(fig,pdf)
    export_vector(fig,svg)
    doc=fitz.open(pdf)
    assert len(doc)==1
    page=doc[0]
    assert not page.get_images(full=True)
    assert len(page.get_drawings())>30
    assert '(a)' in page.get_text() and '4576' in page.get_text()
    root=ET.parse(svg).getroot()
    assert any(node.tag.endswith('text') for node in root.iter())
    assert any(node.tag.endswith('path') for node in root.iter())
    raw=tmp_path/'legacy.json'
    save_session(raw,PlotSettings(),[],str(DATA),[a.uid],0,True,True)
    augment_session_json(raw,comp,True)
    obj,settings,annotations=load_session(raw)
    enabled, restored=restore_composition_from_session(obj)
    assert enabled
    assert restored.panels[0].uids==[a.uid,b.uid]
    assert restored.panels[1].settings.show_footer is False
    assert settings.x_unit=='nm'
    assert restore_composition_from_session({'schema':'pl-spectrum-viewer-plot-session/v1'}) is None


def test_normalized_panel_guides_not_confused_with_signal_v():
    a,b,c=records()
    comp=composition()
    comp.mode=2
    comp.panels[0].annotations.append(HorizontalAnnotation(.5,'Norm.',reference_scale='normalized'))
    fig=Figure()
    ax=render_composition(fig,{s.uid:s for s in (a,b,c)},comp)[0]
    txt=' '.join(t.get_text() for t in ax.texts)
    assert 'Norm.' in txt
    assert 'Guia horizontal' not in txt
    assert ax.get_ylabel()=='Sinal relativo (normalizado)'
