"""V1.4: signal units, configurable scientific figure, independent legend fields."""
from __future__ import annotations

from dataclasses import asdict
import csv
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import fitz
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
import numpy as np
import pytest

from pl_viewer.readers import scan_source
from pl_viewer.plotting import (
    PlotSettings, VerticalAnnotation, HorizontalAnnotation, render_plot, export_vector,
    signal_display, signal_v_from_display, legend_label, save_session, load_session,
    find_spectrum_maximum,
)
from pl_viewer.exporting import export_curves_csv, export_scaled_curves_csv

DATA = Path(__file__).resolve().parents[1] / 'exemplos' / '20261009 PL 4573-4574-4575-4576-4577.zip'


def sample_records():
    return [x for x in scan_source(DATA).spectra if x.sample in ('4574', '4575', '4576')
            and x.slit_filename_um == 300 and x.lockin_range_mv == 200]


def test_signal_unit_conversion_is_lossless_for_readings():
    assert signal_display(.15835, 'mV') == pytest.approx(158.35)
    assert signal_v_from_display(158.35, 'mV') == pytest.approx(.15835)
    assert signal_display(.15835, 'V') == .15835
    for unit in ('not-signal', '', 'mv'):
        with pytest.raises(ValueError):
            signal_v_from_display(2, unit)


@pytest.mark.parametrize('unit, multiplier', [('V',1), ('mV',1000)])
def test_plot_y_units_convert_without_modifying_raw(unit, multiplier):
    sp = sample_records()[0]
    before = sp.signal.copy()
    axes = render_plot(Figure(), [sp], PlotSettings(y_unit=unit, x_unit='angstrom'))
    line = axes[0].lines[0]
    np.testing.assert_allclose(line.get_ydata(), sp.signal * multiplier)
    assert axes[0].get_ylabel() == f'Sinal do lock-in ({unit})'
    assert axes[0].get_xlabel() == 'Comprimento de onda (Å)'
    np.testing.assert_array_equal(sp.signal, before)


def test_horizontal_annotation_stays_on_the_same_physical_level():
    mark = HorizontalAnnotation(.032, 'Referência', label_x=.36)
    for unit, expected in [('V', .032), ('mV', 32.)]:
        axes = render_plot(Figure(), sample_records()[:1], PlotSettings(y_unit=unit), [mark])
        guide = axes[0].lines[-1]
        assert list(guide.get_ydata()) == pytest.approx([expected, expected])
        assert f'Y = {expected:g} {unit}' in axes[0].texts[-1].get_text()
    assert mark.signal_value == .032  # permanent canonical value


def test_normalized_annotations_never_mix_units():
    marks = [HorizontalAnnotation(.032,'V',reference_scale='signal_v'),
             HorizontalAnnotation(.5,'normalized',reference_scale='normalized')]
    for mode, text in [(0, 'V'), (2, 'normalized')]:
        ax = render_plot(Figure(),sample_records()[:1],PlotSettings(y_unit='mV'),marks,mode=mode)[0]
        labels = [t.get_text() for t in ax.texts]
        assert any(text in t for t in labels)
        assert len(labels) == 1
        if mode == 2:
            assert ax.get_ylabel() == 'Sinal relativo (normalizado)'
            assert 'mV' not in ax.get_ylabel()


def test_legend_custom_field_choices_and_absent_fields():
    sp = sample_records()[0]
    assert '300 µm' in legend_label(sp, ['slit'])
    assert '200 mV (escala)' in legend_label(sp, ['lockin'])
    assert '#'+sp.sample in legend_label(sp, ['sample'])
    assert sp.name in legend_label(sp, ['filename'])
    assert '×2.5' in legend_label(sp, ['factor'], 2.5)
    assert '×' not in legend_label(sp, ['factor'], 1)
    assert legend_label(sp, ['lockin', 'sample']).startswith('200 mV (escala)')
    ax=render_plot(Figure(),[sp],PlotSettings(legend_fields=['sample','temperature']))[0]
    assert '77 K (nome)' in ax.get_legend().get_texts()[0].get_text()
    assert '200 mV (escala)' not in ax.get_legend().get_texts()[0].get_text()


def test_figure_style_geometry_fonts_and_spacing():
    s=PlotSettings(figure_width_in=16,figure_height_in=6,font_family='DejaVu Serif',
                   font_title=24,font_axes=17,font_ticks=13,font_legend=15,
                   line_width=3.1,line_style='--',legend_columns=2,
                   grid_alpha=.4,margin_left=.18,margin_right=.94)
    fig=Figure()
    ax=render_plot(fig,sample_records(),s)[0]
    assert tuple(fig.get_size_inches()) == pytest.approx((16,6))
    assert ax.lines[0].get_linewidth()==pytest.approx(3.1)
    assert ax.lines[0].get_linestyle()=='--'
    assert ax.xaxis.label.get_fontsize()==17
    assert ax.xaxis.get_major_ticks()[0].label1.get_fontsize()==13
    assert ax.get_legend()._ncols==2
    assert fig.subplotpars.left==pytest.approx(.18)
    assert fig.subplotpars.right==pytest.approx(.94)


def test_peak_and_factor_are_in_volts_independent_of_y_display():
    sp=sample_records()[0]
    peak=find_spectrum_maximum(sp, 2)
    fig=Figure()
    ax=render_plot(fig,[sp],PlotSettings(y_unit='mV'),scale_factors={sp.uid:2},highlight_peak_uid=sp.uid)[0]
    assert 'mV' in next(t.get_text() for t in ax.texts if 'Máximo:' in t.get_text())
    assert max(ax.lines[0].get_ydata())==pytest.approx(peak.scaled_value*1000)
    assert peak.raw_value_at_peak == pytest.approx(sp.signal[peak.index])


def test_legend_empty_metadata_does_not_fake_defaults():
    from pl_viewer.models import Spectrum
    sp=Spectrum(uid='demo',name='arquivo',wavelength_nm=np.array([800.,805.]),signal=np.array([.03,.04]),sample='ITA')
    assert legend_label(sp,['slit','temperature','lockin'])=='arquivo'
    assert legend_label(sp,['sample'])=='ITA'


def test_settings_and_annotation_session_roundtrip(tmp_path):
    config=PlotSettings(x_unit='angstrom',y_unit='mV',font_family='STIXGeneral',
                        legend_fields=['sample','date','factor'],figure_width_in=16.2,
                        line_width=2.4,annotation_line_width=1.9)
    marks=[VerticalAnnotation(824.5,'linha vertical'),HorizontalAnnotation(.02,'referência V')]
    f=tmp_path/'edicao.json'
    save_session(f,config,marks,'dados.zip',['s2','s1'],0,True,True)
    saved, loaded, annotations=load_session(f)
    assert asdict(loaded)==asdict(config)
    assert [asdict(i) for i in annotations]==[asdict(i) for i in marks]
    assert saved['selected_spectrum_uids']==['s2','s1']
    assert saved['settings']['y_unit']=='mV'


def test_pre_v14_label_upgraded_without_overwriting_user_text(tmp_path):
    p=tmp_path/'old.json'
    payload={'schema':'pl-spectrum-viewer-plot-session/v1','settings':
             {'y_label':'Recorded lock-in signal (original units; uncalibrated)'},
             'selected_spectrum_uids':[], 'vertical_annotations':[]}
    p.write_text(json.dumps(payload),encoding='utf-8')
    _,settings,_=load_session(p)
    assert settings.y_label=='Sinal do lock-in'
    assert settings.y_unit=='V'
    payload['settings']['y_label']='Meu sinal experimental'
    p.write_text(json.dumps(payload),encoding='utf-8')
    _,settings,_=load_session(p)
    assert settings.y_label=='Meu sinal experimental'


def test_style_rejects_invalid_fields_and_axes():
    for attrs in ({'y_unit':'uV'}, {'font_title':999},{'legend_fields':['temperature','nada']},
                  {'margin_left':.4,'margin_right':.6}, {'figure_height_in':2.2},
                  {'legend_columns':0}):
        with pytest.raises(ValueError):
            PlotSettings(**attrs).validate()


def test_vector_export_uses_chosen_figure_ratio_and_readable_text(tmp_path):
    s=PlotSettings(x_unit='angstrom',y_unit='mV',figure_width_in=15.0,
                   figure_height_in=8.5,font_title=19,
                   legend_fields=['sample','slit','temperature','lockin','factor'])
    marks=[HorizontalAnnotation(.08,'Referência de sinal'),
           VerticalAnnotation(824.5,'Linha espectral')]
    fig=Figure()
    render_plot(fig,sample_records(),s,marks)
    pdf=tmp_path/'example.pdf'
    svg=tmp_path/'example.svg'
    export_vector(fig,pdf,title=s.title)
    export_vector(fig,svg,title=s.title)
    with fitz.open(pdf) as document:
        page=document[0]
        assert page.rect.width/page.rect.height == pytest.approx(15/8.5,rel=.005)
        text=page.get_text()
        assert 'Sinal do lock-in' in text
        assert 'Referência de sinal' in text
        assert 'mV' in text
        assert 'Å' in text or 'Comprimento de onda' in text
        assert not page.get_images()
    root=ET.parse(svg)
    ns={'svg':'http://www.w3.org/2000/svg'}
    assert root.findall('.//svg:text',ns)
    assert not root.findall('.//svg:image',ns)


def test_csv_preserves_volt_values_and_legacy_columns(tmp_path):
    sp=sample_records()[0]
    a=tmp_path/'bruto.csv';b=tmp_path/'ajustado.csv'
    export_curves_csv(a,[sp]);export_scaled_curves_csv(b,[sp],{sp.uid:2.0})
    with a.open(encoding='utf-8-sig') as f:
        r=next(csv.DictReader(f))
    with b.open(encoding='utf-8-sig') as f:
        q=next(csv.DictReader(f))
    assert float(r['sinal_bruto_V']) == pytest.approx(sp.signal[0])
    assert float(q['sinal_multiplicado_V']) == pytest.approx(sp.signal[0]*2)
    assert 'sinal_bruto_unidade_nao_verificada' in r
