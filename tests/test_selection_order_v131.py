"""v1.3.1 regression: colors follow checkbox click order, not file/table order."""
from __future__ import annotations
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pl_viewer.selection_order import SelectionOrder
from pl_viewer.plotting import (
    PLOT_COLOR_CYCLE, PlotSettings, render_plot, save_session, load_session
)
from pl_viewer.readers import scan_source

SOURCE = Path(__file__).resolve().parents[1] / 'exemplos' / '20261009 PL 4573-4574-4575-4576-4577.zip'


def _spectra():
    all_sp = scan_source(str(SOURCE), False, 'auto').spectra
    return [next(sp for sp in all_sp if sp.sample == number and sp.slit_filename_um == 300 and sp.lockin_range_mv == 200)
            for number in ('4574', '4575', '4576')]


def test_checkbox_order_and_remark_changes_color_position():
    a, b, c = _spectra()
    order = SelectionOrder()
    for sp in (c, a, b):
        order.set_checked(sp.uid, True)
    assert order.uids == [c.uid, a.uid, b.uid]
    order.set_checked(c.uid, True)  # repaint / unchanged checked state does not reorder
    assert order.uids == [c.uid, a.uid, b.uid]
    order.set_checked(a.uid, False)
    assert order.uids == [c.uid, b.uid]
    order.set_checked(a.uid, True)
    assert order.uids == [c.uid, b.uid, a.uid]
    assert [order.position(sp.uid) for sp in (c, b, a)] == [1, 2, 3]
    order.set_checked(c.uid, False)
    assert order.position(c.uid) is None


def test_bulk_mark_keeps_earlier_selection_and_order():
    a, b, c = _spectra()
    order = SelectionOrder([b.uid])
    for sp in (c, a, b):  # display-sorted current table order
        order.set_checked(sp.uid, True)
    assert order.uids == [b.uid, c.uid, a.uid]
    for sp in (c, a, b):
        order.set_checked(sp.uid, False)
    assert order.uids == []
    order.replace([a.uid, a.uid, c.uid])
    assert order.uids == [a.uid, c.uid]
    order.retain_only({c.uid})
    assert order.uids == [c.uid]


@pytest.mark.parametrize('mode', [0, 1, 2])
def test_first_checkbox_selection_is_first_color_in_every_plot_mode(mode):
    a, b, c = _spectra()
    selected = [c, a, b]  # neither file order nor table order
    before = {sp.uid: sp.signal.copy() for sp in selected}
    fig = Figure(figsize=(12, 7))
    axes = render_plot(fig, selected, PlotSettings(), mode=mode)
    lines = [axes[i].lines[0] for i in range(3)] if mode == 1 else axes[0].lines[:3]
    assert [ln.get_color() for ln in lines] == list(PLOT_COLOR_CYCLE[:3])
    labels = [ln.get_label() for ln in lines]
    assert '#4576' in labels[0] and '#4574' in labels[1] and '#4575' in labels[2]
    for sp in selected:
        np.testing.assert_array_equal(sp.signal, before[sp.uid])


def test_color_reassigned_after_uncheck_and_recheck():
    a, b, c = _spectra()
    order = SelectionOrder([c.uid, a.uid, b.uid])
    order.set_checked(c.uid, False)
    order.set_checked(c.uid, True)
    by_uid = {sp.uid: sp for sp in (a, b, c)}
    ordered = [by_uid[uid] for uid in order.uids]
    ax = render_plot(Figure(), ordered, PlotSettings())[0]
    assert '#4574' in ax.lines[0].get_label() and ax.lines[0].get_color() == PLOT_COLOR_CYCLE[0]
    assert '#4575' in ax.lines[1].get_label() and ax.lines[1].get_color() == PLOT_COLOR_CYCLE[1]
    assert '#4576' in ax.lines[2].get_label() and ax.lines[2].get_color() == PLOT_COLOR_CYCLE[2]


def test_json_persists_chronological_selection_and_old_version_loads(tmp_path):
    a, b, c = _spectra()
    ordered = [c.uid, a.uid, b.uid]
    path = tmp_path / 'edicao.json'
    save_session(path, PlotSettings(), [], 'dados.zip', ordered, 0, True, True,
                 scale_factors={c.uid: 2.0})
    data, _, _ = load_session(path)
    assert data['selected_spectrum_uids'] == ordered
    assert SelectionOrder(data['selected_spectrum_uids']).uids == ordered
    # Same schema as 1.3 and earlier, no new mandatory property.
    old = json.loads(path.read_text(encoding='utf-8'))
    old.pop('spectrum_display_factors', None)
    old.pop('highlight_peak_uid', None)
    path.write_text(json.dumps(old), encoding='utf-8')
    restored, _, _ = load_session(path)
    assert restored['selected_spectrum_uids'] == ordered


def test_session_rejects_duplicate_or_invalid_selection_ids(tmp_path):
    p = tmp_path / 'bad.json'
    save_session(p, PlotSettings(), [], None, ['a'], 0, True, True)
    obj = json.loads(p.read_text(encoding='utf-8'))
    for invalid in (['a', 'a'], 'a', ['a', 123]):
        obj['selected_spectrum_uids'] = invalid
        p.write_text(json.dumps(obj), encoding='utf-8')
        with pytest.raises(ValueError):
            load_session(p)
