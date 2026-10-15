"""Testes da v1.3.2: anotações em X/Y e nome de arquivo como fonte principal."""
from pathlib import Path
from xml.etree import ElementTree as ET
import json
import zipfile

import numpy as np
import pytest
from matplotlib.figure import Figure

from pl_viewer.readers import scan_source, parse_filename, _make_spectrum
from pl_viewer.plotting import (
    HorizontalAnnotation, VerticalAnnotation, PlotSettings, render_plot,
    save_session, load_session, export_vector,
)

ZIP = Path(__file__).resolve().parents[1] / 'exemplos' / '20261009 PL 4573-4574-4575-4576-4577.zip'


@pytest.mark.parametrize('name,expected', [
    ('20261008 1505 - ITA 60um 77K 500mV', ('ITA', None, 60, 77, 500)),
    ('20261008 1657 - 4557(1659) 290um 77K 500mV.dat', ('4557','1659',290,77,500)),
    ('20261008 1819 - 4555(1655) 77K 290um', ('4555','1655',290,77,None)),
    ('20261008 1828 - 4555 600um 77K 500mV', ('4555',None,600,77,500)),
    ('20261009 1435 - 4573 62um 77K 200mV', ('4573',None,62,77,200)),
    ('20261009 1538 - 4576 1000um 77K 500mV', ('4576',None,1000,77,500)),
])
def test_actual_filename_patterns(name, expected):
    parsed = parse_filename(name)
    assert tuple(parsed[k] for k in ('sample','sample_code','slit_um','temperature_k','lockin_mv')) == expected
    assert parsed['date_label'][:8] in ('20261008','20261009')


def test_renamed_binary_prevails_over_embedded_name(tmp_path):
    with zipfile.ZipFile(ZIP) as z:
        original = next(n for n in z.namelist() if n.startswith('20261009 1435 - 4573 50um') and not n.endswith('.dat'))
        new_name = '20261008 1657 - 4557(1659) 290um 77K 500mV'
        # Inside this renamed binary the DTLG header still has the *old* name.
        (tmp_path / new_name).write_bytes(z.read(original))
        renamed_dat = new_name + '.dat'
        (tmp_path / renamed_dat).write_bytes(z.read(original + '.dat'))
    result = scan_source(tmp_path)
    assert not result.errors
    assert result.paired_duplicates == 1
    assert len(result.spectra) == 1
    sp = result.spectra[0]
    assert sp.name == new_name and sp.sample == '4557' and sp.sample_display == '4557(1659)'
    assert sp.sample_code_filename == '1659'
    assert sp.slit_filename_um == 290 and sp.lockin_range_mv == 500
    assert sp.temperature_filename_k == 77
    assert sp.metadata_original['Fenda de entrada (mm)'] == 0.4
    assert sp.summary['data_hora_nome'] == '20261008 1657'
    assert sp.summary['amostra_codigo_auxiliar_nome'] == '1659'
    assert any('Nome atual do arquivo diverge' in w for w in sp.warnings)
    assert any('Fendas divergentes' in w for w in sp.warnings)


def test_different_metadata_sample_never_overrides_filename(monkeypatch):
    import pl_viewer.readers as readers
    original = readers.decode_binary
    def impostor(data):
        x,y,meta = original(data)
        meta['Amostra'] = '9999'
        return x,y,meta
    monkeypatch.setattr(readers, 'decode_binary', impostor)
    with zipfile.ZipFile(ZIP) as z:
        original_filename = next(n for n in z.namelist() if n.startswith('20261009 1435 - 4573 50um') and not n.endswith('.dat'))
        sp = _make_spectrum('dummy', original_filename, z.read(original_filename), 'auto')
    assert sp.sample == '4573'
    assert sp.metadata_original['Amostra'] == '9999'
    assert any('Amostra divergente' in w and 'Prevalece o nome' in w for w in sp.warnings)


def test_horizontal_line_geometry_and_label_shift():
    sp = scan_source(ZIP).spectra[0]
    fig = Figure(figsize=(13,7))
    horizontal = HorizontalAnnotation(0.032, 'referência Y', label_x=.72, label_dy_pt=25)
    vertical = VerticalAnnotation(824.5, 'referência λ', label_dx_pt=-20)
    for unit in ('nm', 'angstrom'):
        ax = render_plot(fig, [sp], PlotSettings(x_unit=unit), [vertical, horizontal])[0]
        ylines = [line for line in ax.lines if np.asarray(line.get_ydata()).size==2 and
                  np.allclose(np.asarray(line.get_ydata()), [.032, .032])]
        assert len(ylines) == 1
        ytexts = [t for t in ax.texts if 'referência Y' in t.get_text()]
        assert len(ytexts) == 1 and 'Y = 0.032' in ytexts[0].get_text()
        assert ytexts[0].get_position() == (.72, .032)
        y_actual = ytexts[0].get_transform().transform((.72,.032))[1]
        y_expected = ax.get_yaxis_transform().transform((.72,.032))[1] + 25/72*fig.dpi
        assert y_actual == pytest.approx(y_expected,abs=.001)


def test_horizontal_validation():
    for val in (float('nan'), float('inf')):
        with pytest.raises(ValueError): HorizontalAnnotation(val).validate()
    for bad in (float('nan'), 1, -1, 240.1, -240.1):
        if abs(bad) <= 1 and np.isfinite(bad):
            with pytest.raises(ValueError): HorizontalAnnotation(0.1, label_x=bad).validate()
        else:
            with pytest.raises(ValueError): HorizontalAnnotation(0.1, label_dy_pt=bad).validate()
    HorizontalAnnotation(-0.01, label_x=.06, label_dy_pt=-240).validate()


def test_mixed_roundtrip_legacy_and_vector(tmp_path):
    import fitz
    vertical = VerticalAnnotation(824.5, 'onda', label_dx_pt=-20)
    horizontal = HorizontalAnnotation(.0235, 'sinal', label_dy_pt=30)
    marks = [horizontal, vertical, HorizontalAnnotation(0.0, 'zero')]
    fig = Figure(figsize=(13,7))
    render_plot(fig, scan_source(ZIP).spectra[:2], PlotSettings(), marks)
    for suffix in ('.pdf','.svg'):
        path = tmp_path / ('mixed' + suffix)
        export_vector(fig, path)
        assert path.stat().st_size > 2000
        if suffix == '.pdf':
            with fitz.open(path) as doc:
                text = doc[0].get_text()
                assert not doc[0].get_images()
                assert 'sinal' in text and 'onda' in text and 'zero' in text
        else:
            tree = ET.parse(path)
            ns = {'svg':'http://www.w3.org/2000/svg'}
            assert tree.findall('.//svg:text',ns)
            assert '<image' not in path.read_text(encoding='utf-8')
    session = tmp_path / 'session.json'
    save_session(session, PlotSettings(), marks, 'source.zip', [], 0, True, True)
    data,settings,loaded=load_session(session)
    assert [type(a) for a in loaded] == [HorizontalAnnotation, VerticalAnnotation, HorizontalAnnotation]
    assert data['vertical_annotations'][0]['wavelength_nm']==824.5
    assert len(data['horizontal_annotations'])==2
    assert loaded[0].label_dy_pt==30
    # Old v1.3.1 profiles with only vertical_annotations must still load.
    old = tmp_path / 'old.json'
    data.pop('annotations'); data.pop('horizontal_annotations')
    old.write_text(json.dumps(data),encoding='utf-8')
    _,_,olds=load_session(old)
    assert len(olds)==1 and isinstance(olds[0],VerticalAnnotation)
