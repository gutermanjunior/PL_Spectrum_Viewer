"""v1.4.1: preview/export geometry isolation, export fidelity, UI regression."""
from __future__ import annotations

import ast
from pathlib import Path
import xml.etree.ElementTree as ET

import fitz
import numpy as np
import pytest
from matplotlib.figure import Figure

from pl_viewer.plotting import (
    PlotSettings, VerticalAnnotation, HorizontalAnnotation,
    render_plot, create_export_figure, export_vector,
)
from pl_viewer.readers import scan_source

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'exemplos' / '20261009 PL 4573-4574-4575-4576-4577.zip'


def sample():
    return next(x for x in scan_source(DATA).spectra
                if x.sample == '4574' and x.slit_filename_um == 300)


@pytest.mark.parametrize('preview_size', [(3.5, 5.0), (5.2, 3.65), (9.0, 3.0)])
def test_live_preview_retains_its_actual_resized_dimensions(preview_size):
    """Simulate QWidget resizing: replot must not overwrite the canvas geometry."""
    s = PlotSettings(figure_width_in=20, figure_height_in=14)
    fig = Figure(figsize=(5.2, 3.65), dpi=100)
    for w, h in (preview_size, (2.8, 3.1), preview_size):
        fig.set_size_inches(w, h, forward=False)  # what Qt does on resize
        axes = render_plot(fig, [sample()], s, resize_figure=False)
        assert tuple(fig.get_size_inches()) == pytest.approx((w, h))
        assert len(axes[0].lines) == 1


def test_export_is_independent_from_responsive_preview(tmp_path):
    s = PlotSettings(figure_width_in=14.2, figure_height_in=6.3,
                     y_unit='mV', x_unit='angstrom')
    sp = sample()
    anns = [VerticalAnnotation(824.5, 'Posição espectral'),
            HorizontalAnnotation(0.03, 'Referência')]
    live = Figure(figsize=(4.1, 3.1), dpi=110)
    live_axes = render_plot(live, [sp], s, anns, resize_figure=False,
                            scale_factors={sp.uid: 2})
    size_before = live.get_size_inches().copy()
    export_fig = create_export_figure([sp], s, anns, scale_factors={sp.uid: 2})
    assert tuple(export_fig.get_size_inches()) == pytest.approx((14.2, 6.3))
    assert tuple(live.get_size_inches()) == pytest.approx(tuple(size_before))
    assert export_fig is not live
    np.testing.assert_allclose(export_fig.axes[0].lines[0].get_ydata(),
                               live_axes[0].lines[0].get_ydata())
    pdf = tmp_path / 'figura.pdf'
    svg = tmp_path / 'figura.svg'
    export_vector(export_fig, pdf)
    export_vector(export_fig, svg)
    with fitz.open(pdf) as doc:
        page = doc[0]
        assert page.rect.width == pytest.approx(14.2 * 72, abs=.5)
        assert page.rect.height == pytest.approx(6.3 * 72, abs=.5)
        assert len(page.get_drawings()) > 3
        assert not page.get_images(full=True)  # curves/annotations remain vector
        assert '8245' in page.get_text()  # angstrom wavelength reference
    root = ET.parse(svg).getroot()
    text_nodes = root.findall('.//{http://www.w3.org/2000/svg}text')
    assert text_nodes
    assert tuple(live.get_size_inches()) == pytest.approx(tuple(size_before))


def test_default_plot_call_keeps_publication_size_for_existing_scripts():
    s = PlotSettings(figure_width_in=16, figure_height_in=7.2)
    fig = Figure(figsize=(4, 3))
    render_plot(fig, [sample()], s)  # prior API remains unchanged
    assert tuple(fig.get_size_inches()) == pytest.approx((16, 7.2))


def test_gui_routes_preview_and_export_through_separate_figures():
    """Structural regression when PySide6 is not installed in CI."""
    source = (ROOT / 'pl_viewer' / 'gui.py').read_text()
    assert 'resize_figure=False' in source
    assert 'create_export_figure(' in source
    assert 'export_vector(export_figure,' in source
    assert 'export_vector(self.figure,' not in source
    assert 'self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding' in source
    assert 'class ResponsiveFigureCanvas(FigureCanvasQTAgg):' in source
    assert 'export_bar = QGridLayout()' in source
    ast.parse(source)
