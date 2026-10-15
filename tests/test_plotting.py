"""Headless regression tests for scientific plotting and editable annotation sessions."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pl_viewer.plotting import (
    PlotSettings, VerticalAnnotation, render_plot, export_vector,
    wavelength_display, wavelength_nm_from_display, save_session, load_session,
)
from pl_viewer.readers import scan_source

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / 'exemplos' / '20261009 PL 4573-4574-4575-4576-4577.zip'


def _three():
    spectra = scan_source(ZIP).spectra
    return [s for s in spectra if s.sample in ('4574', '4575', '4576')
            and s.slit_filename_um == 300 and s.lockin_range_mv == 200]


def test_nm_angstrom_annotations_keep_physical_position():
    mark = VerticalAnnotation(824.5, "Pico observado", label_y=.77)
    mark.validate()
    assert wavelength_display(mark.wavelength_nm, 'angstrom') == 8245.0
    assert wavelength_nm_from_display(8245, 'angstrom') == 824.5
    settings = PlotSettings(x_unit='angstrom', x_min=8000, x_max=8500)
    fig = Figure(figsize=(14, 8))
    axes = render_plot(fig, _three(), settings, [mark])
    assert len(axes) == 1
    assert list(axes[0].lines[3].get_xdata()) == [8245.0, 8245.0]
    assert axes[0].get_xlim() == pytest.approx((8000, 8500))
    assert any('8245 Å' in txt.get_text() for txt in axes[0].texts)
    # No mutation of original measurements.
    assert max(float(np.max(s.signal)) for s in _three()) == pytest.approx(.15835)


def test_modes_separate_and_normalized_and_raw_not_mutated():
    spectra = _three()
    before = [s.signal.copy() for s in spectra]
    fig = Figure(figsize=(13, 7))
    axes = render_plot(fig, spectra, PlotSettings(), mode=1)
    assert len(axes) == 3
    axes = render_plot(fig, spectra, PlotSettings(), mode=2)
    assert len(axes) == 1
    assert max(np.max(line.get_ydata()) for line in axes[0].lines) == pytest.approx(1.0)
    for s, y in zip(spectra, before):
        np.testing.assert_array_equal(s.signal, y)


def test_pdf_svg_truly_vector_with_visible_labels(tmp_path):
    import fitz
    spectra = _three()
    settings = PlotSettings(title='October 9, 2026  |  Low-temperature growth series',
                            footer='Sem atribuição física automática dos picos.',
                            x_min=760, x_max=930)
    fig = Figure(figsize=(12, 7))
    marks = [VerticalAnnotation(824.5, 'Máximo observado', label_y=.68),
             VerticalAnnotation(834., 'Referência visual', color='#d14343', linestyle='--', label_y=.39)]
    axes = render_plot(fig, spectra, settings, marks)
    assert len(axes[0].lines) == 5  # 3 spectra + 2 guides
    assert 'Máximo observado' in axes[0].texts[0].get_text()
    pdf, svg, png = (tmp_path / 'figure.pdf', tmp_path / 'figure.svg', tmp_path / 'figure.png')
    original_size = fig.get_size_inches().copy()
    for path in (pdf, svg, png):
        export_vector(fig, path, title=settings.title)
        assert path.stat().st_size > 1000
    np.testing.assert_allclose(fig.get_size_inches(), original_size)
    with fitz.open(pdf) as doc:
        page = doc[0]
        page_text = page.get_text()
        assert 'Máximo observado' in page_text
        assert 'Low-temperature growth series' in page_text
        assert len(page.get_drawings()) > 10
        assert not page.get_images()  # No rasterized plot or screenshot
    tree = ET.parse(svg)
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    assert tree.findall('.//svg:text', ns)
    assert not tree.findall('.//svg:image', ns)
    xml = svg.read_text(encoding='utf-8')
    assert '824.5 nm' in xml
    assert 'Máximo observado' in xml


def test_session_roundtrip(tmp_path):
    p = tmp_path / 'edicao.json'
    settings = PlotSettings(title='PL 77 K', x_unit='angstrom', x_min=7600, x_max=9500,
                            footer='Dado bruto; sem correção de baseline.')
    original = [VerticalAnnotation(785.3, 'Poço nominal', linestyle='--', label_y=.28),
                VerticalAnnotation(824.5, 'GaAs', label_y=.76)]
    save_session(p, settings, original, 'series.zip', ['u01','u02'], 0, True, True)
    data, loaded_settings, loaded_marks = load_session(p)
    assert data['data_source'] == 'series.zip'
    assert data['selected_spectrum_uids'] == ['u01','u02']
    assert asdict(loaded_settings) == asdict(settings)
    assert [asdict(a) for a in loaded_marks] == [asdict(a) for a in original]
    assert 'sinal' not in data  # no raw signal included in session


def test_bad_annotation_and_session_are_rejected(tmp_path):
    with pytest.raises(ValueError):
        VerticalAnnotation(-2).validate()
    with pytest.raises(ValueError):
        VerticalAnnotation(824.5, linestyle='??').validate()
    with pytest.raises(ValueError):
        PlotSettings(x_min=900, x_max=800).validate()
    p = tmp_path / 'bad.json'
    p.write_text(json.dumps({'schema': 'pl-spectrum-viewer-plot-session/v1',
                             'settings': asdict(PlotSettings()),
                             'vertical_annotations': [{'wavelength_nm': float('nan')}]}))
    with pytest.raises(ValueError):
        load_session(p)


def test_horizontal_label_offset_in_points_is_symmetric_and_does_not_move_lines():
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    values = [-55.0, 0.0, 55.0]
    fig = Figure(figsize=(14, 8), dpi=100)
    marks = [VerticalAnnotation(824.5, f"Rótulo {v}", show_value=False,
                                label_dx_pt=v, label_y=.5) for v in values]
    ax = render_plot(fig, _three(), PlotSettings(), marks)[0]
    FigureCanvasAgg(fig).draw()
    # 3 data lines + 3 visual guides; the guide stays at the wavelength.
    for guide in ax.lines[-3:]:
        assert list(guide.get_xdata()) == [824.5, 824.5]
    positions = [label.get_transform().transform(label.get_position())[0]
                 for label in ax.texts]
    expected_pixels = 55 / 72 * fig.dpi
    assert positions[0] < positions[1] < positions[2]
    assert positions[1] - positions[0] == pytest.approx(expected_pixels, abs=.001)
    assert positions[2] - positions[1] == pytest.approx(expected_pixels, abs=.001)


def test_horizontal_shift_identical_for_nm_and_angstrom_units():
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    fig = Figure(figsize=(14, 8), dpi=120)
    marks = [VerticalAnnotation(824.5, 'A', show_value=False, label_dx_pt=0),
             VerticalAnnotation(824.5, 'B', show_value=False, label_dx_pt=48)]
    distances = []
    for unit in ('nm', 'angstrom'):
        axes = render_plot(fig, _three(), PlotSettings(x_unit=unit), marks)
        FigureCanvasAgg(fig).draw()
        x0, x1 = [txt.get_transform().transform(txt.get_position())[0] for txt in axes[0].texts]
        distances.append(x1-x0)
    assert distances[0] == pytest.approx(48 / 72 * fig.dpi, abs=.001)
    assert distances[1] == pytest.approx(distances[0], abs=.001)


def test_horizontal_offset_roundtrip_and_v11_backcompat(tmp_path):
    p = tmp_path / 'new.json'
    settings = PlotSettings()
    marks = [VerticalAnnotation(824.5, 'esquerda', label_dx_pt=-45),
             VerticalAnnotation(834.0, 'direita', label_dx_pt=55)]
    save_session(p, settings, marks, 'source.zip', [], 0, True, True)
    _, _, loaded = load_session(p)
    assert [x.label_dx_pt for x in loaded] == [-45, 55]
    old = tmp_path / 'old.json'
    contents = json.loads(p.read_text(encoding='utf-8'))
    for mark in contents['vertical_annotations']:
        del mark['label_dx_pt']
    contents.pop('annotations', None)  # v1.1 did not contain the v1.3.2 combined representation
    contents.pop('horizontal_annotations', None)
    old.write_text(json.dumps(contents), encoding='utf-8')
    _, _, old_marks = load_session(old)
    assert [m.label_dx_pt for m in old_marks] == [0, 0]


def test_horizontal_offset_validation_and_vector_export(tmp_path):
    import fitz
    for bad in (float('nan'), float('inf'), -240.1, 240.1):
        with pytest.raises(ValueError):
            VerticalAnnotation(824.5, label_dx_pt=bad).validate()
    for okay in (-240, -5, 0, 5, 240):
        VerticalAnnotation(824.5, label_dx_pt=okay).validate()
    fig = Figure(figsize=(14, 8))
    marks = [VerticalAnnotation(824.5, 'rótulo esquerdo', label_dx_pt=-42),
             VerticalAnnotation(834, 'rótulo direito', label_dx_pt=51)]
    render_plot(fig, _three(), PlotSettings(), marks)
    pdf = tmp_path / 'shift.pdf'
    svg = tmp_path / 'shift.svg'
    for path in (pdf, svg):
        export_vector(fig, path)
    with fitz.open(pdf) as doc:
        page = doc[0]
        assert not page.get_images()
        text = page.get_text()
        assert 'rótulo esquerdo' in text
        assert 'rótulo direito' in text
    root = ET.parse(svg)
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    assert root.findall('.//svg:text', ns)
    assert 'rótulo esquerdo' in svg.read_text(encoding='utf-8')

# v1.3 — peak readout and independent non-destructive per-series display factors.
def test_peak_global_real_data_and_units_not_fitted():
    from pl_viewer.plotting import find_spectrum_maximum, format_wavelength
    spectra = _three()
    sp = spectra[0]
    peak = find_spectrum_maximum(sp)
    i = int(np.argmax(sp.signal))
    assert peak.index == i
    assert peak.wavelength_nm == pytest.approx(float(sp.wavelength_nm[i]))
    assert peak.scaled_value == pytest.approx(float(sp.signal[i]))
    assert peak.raw_value_at_peak == pytest.approx(peak.scaled_value)
    assert format_wavelength(peak.wavelength_nm, 'angstrom').endswith(' Å')
    assert format_wavelength(peak.wavelength_nm, 'nm').endswith(' nm')


def test_factors_per_series_peak_is_after_scaling_and_not_mutating():
    from pl_viewer.plotting import find_spectrum_maximum, scaled_signal
    spectra = _three()
    copies = [s.signal.copy() for s in spectra]
    scales = {spectra[0].uid: 2.5, spectra[1].uid: 0.35}
    fig = Figure(figsize=(12, 7))
    ax = render_plot(fig, spectra, PlotSettings(), scale_factors=scales)[0]
    np.testing.assert_allclose(ax.lines[0].get_ydata(), copies[0] * 2.5)
    np.testing.assert_allclose(ax.lines[1].get_ydata(), copies[1] * .35)
    np.testing.assert_array_equal(ax.lines[2].get_ydata(), copies[2])
    assert '×2.5' in ax.lines[0].get_label()
    assert '×0.35' in ax.lines[1].get_label()
    pk = find_spectrum_maximum(spectra[0], 2.5)
    assert pk.scaled_value == pytest.approx(2.5 * np.max(copies[0]))
    neg = find_spectrum_maximum(spectra[0], -3)
    assert neg.index == int(np.argmin(copies[0]))  # negatives reverse peak ordering
    assert neg.scaled_value == pytest.approx(-3 * np.min(copies[0]))
    zero = find_spectrum_maximum(spectra[0], 0)
    assert zero.scaled_value == 0
    assert zero.tied_points == len(spectra[0].signal)
    for original, sp in zip(copies, spectra):
        np.testing.assert_array_equal(sp.signal, original)
    for bad in (float('nan'), float('inf'), -1e7, 1e7):
        with pytest.raises(ValueError):
            scaled_signal(spectra[0], bad)


def test_peak_highlight_vector_pdf_svg_and_series_selection(tmp_path):
    import fitz
    spectra = _three()
    sp = spectra[1]
    fig = Figure(figsize=(12, 7))
    ax = render_plot(fig, spectra, PlotSettings(title='Picos experimentais'),
                     scale_factors={sp.uid: 1.5}, highlight_peak_uid=sp.uid)[0]
    assert any('Máximo:' in t.get_text() for t in ax.texts)
    assert len([t for t in ax.texts if 'Máximo:' in t.get_text()]) == 1
    assert any(line.get_marker() == 'o' for line in ax.lines)
    for extension in ('pdf', 'svg'):
        path = tmp_path / ('maximo.' + extension)
        export_vector(fig, path)
        assert path.stat().st_size > 1000
        if extension == 'pdf':
            with fitz.open(path) as doc:
                assert 'Máximo:' in doc[0].get_text()
                assert not doc[0].get_images()
        else:
            doc = path.read_text(encoding='utf-8')
            assert 'Máximo:' in doc and '<text' in doc and '<image' not in doc


def test_factor_roundtrip_v12_backward_compat_and_invalid_json(tmp_path):
    p = tmp_path / 'profile.json'
    save_session(p, PlotSettings(), [], 'dados.zip', ['A'], 0, True, True,
                 scale_factors={'A': 3.125, 'B': -1.5, 'C': 1}, highlight_peak_uid='A')
    data, _, _ = load_session(p)
    assert data['spectrum_display_factors'] == {'A': 3.125, 'B': -1.5}
    assert data['highlight_peak_uid'] == 'A'
    old = tmp_path / 'v12.json'
    raw = json.loads(p.read_text(encoding='utf-8'))
    del raw['spectrum_display_factors']
    del raw['highlight_peak_uid']
    old.write_text(json.dumps(raw), encoding='utf-8')
    olddata, _, _ = load_session(old)
    assert olddata.get('spectrum_display_factors', {}) == {}
    assert olddata.get('highlight_peak_uid') is None
    raw['spectrum_display_factors'] = {'A': float('nan')}
    old.write_text(json.dumps(raw), encoding='utf-8')
    with pytest.raises(ValueError):
        load_session(old)


def test_export_scaled_csv_is_explicit_raw_and_derived(tmp_path):
    import csv
    from pl_viewer.exporting import export_curves_csv, export_scaled_curves_csv
    sp = _three()[0]
    before = sp.signal.copy()
    path_raw = tmp_path / 'raw.csv'
    path_scaled = tmp_path / 'scaled.csv'
    export_curves_csv(path_raw, [sp])
    export_scaled_curves_csv(path_scaled, [sp], {sp.uid: 2.25})
    with path_raw.open(encoding='utf-8-sig', newline='') as f:
        raw_rows = list(csv.DictReader(f))
    with path_scaled.open(encoding='utf-8-sig', newline='') as f:
        scaled_rows = list(csv.DictReader(f))
    assert len(raw_rows) == len(scaled_rows) == len(sp.signal)
    for i in (0, len(sp.signal)//2, len(sp.signal)-1):
        assert float(raw_rows[i]['sinal_bruto_unidade_nao_verificada']) == pytest.approx(float(before[i]))
        assert float(scaled_rows[i]['sinal_bruto_unidade_nao_verificada']) == pytest.approx(float(before[i]))
        assert float(scaled_rows[i]['sinal_multiplicado_unidade_nao_verificada']) == pytest.approx(float(before[i])*2.25)
    np.testing.assert_array_equal(sp.signal, before)
