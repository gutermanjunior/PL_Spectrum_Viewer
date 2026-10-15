"""Testes do processamento de dados, independentes de interface Qt."""
import io
from pathlib import Path
import sys
import zipfile
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pl_viewer.readers import decode_dat, decode_binary, parse_filename, scan_source, InvalidSpectrum

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / 'exemplos' / '20261009 PL 4573-4574-4575-4576-4577.zip'


def test_dataset_13_unique_13_duplicates_and_no_errors():
    result = scan_source(ZIP)
    assert len(result.spectra) == 13
    assert result.paired_duplicates == 13
    assert result.errors == []
    assert all(s.duplicates_verified for s in result.spectra)
    assert all(len(s.source_files) == 2 for s in result.spectra)
    assert {s.sample for s in result.spectra} == {'4573', '4574', '4575', '4576', '4577'}
    assert sum(len(s.signal) for s in result.spectra) == 7*301+6*401


def test_binary_dat_data_identical_pointwise():
    with zipfile.ZipFile(ZIP) as z:
        for n in z.namelist():
            if not n.endswith('.dat'):
                continue
            xb, yb, meta = decode_binary(z.read(n[:-4]))
            xd, yd, _, _ = decode_dat(z.read(n))
            np.testing.assert_array_equal(xb, xd)
            np.testing.assert_array_equal(yb, yd)
            assert meta['Temperatura'] == 300


def test_wavelength_conversion_and_original_signal():
    result = scan_source(ZIP)
    s = next(s for s in result.spectra if s.sample == '4573' and s.slit_filename_um == 50)
    assert s.wavelength_nm[0] == 750
    assert s.wavelength_nm[-1] == 900
    assert len(s.signal) == 301
    assert np.max(s.signal) == pytest.approx(.0726)


def test_preserves_header_filename_conflicts():
    result = scan_source(ZIP)
    sp = next(s for s in result.spectra if s.sample == '4573' and s.slit_filename_um == 50)
    assert sp.temperature_filename_k == 77
    assert sp.metadata_original['Temperatura'] == 300
    assert sp.header_slits_um == (400, 400)
    assert sp.slit_filename_um == 50
    assert sp.temperature_operator_k is None
    assert any('Temperatura divergente' in w for w in sp.warnings)
    assert any('Fendas divergentes' in w for w in sp.warnings)


def test_ita_is_future_compatible(tmp_path):
    (tmp_path / '20261103 1410 - ITA 150um 77K 500mV.dat').write_text('7500\t0.01\n7505\t0.02\n7510\t0.01\n', encoding='utf-8')
    r = scan_source(tmp_path)
    assert not r.errors
    assert len(r.spectra) == 1
    assert r.spectra[0].sample == 'ITA'
    assert r.spectra[0].slit_filename_um == 150
    assert r.spectra[0].wavelength_nm[1] == 750.5
    assert r.spectra[0].temperature_filename_k == 77


def test_different_folders_without_config_change(tmp_path):
    a, b = tmp_path / 'a', tmp_path / 'b'
    a.mkdir(); b.mkdir()
    (a / '20261009 1450 - 4574 300um 77K 200mV.dat').write_text('750 2\n751 4\n752 3\n')
    (b / '20261010 1450 - 8888 100um 77K 500mV.dat').write_text('750 1\n751 3\n752 2\n')
    assert scan_source(a).spectra[0].sample == '4574'
    assert scan_source(b).spectra[0].sample == '8888'


def test_duplicate_name_different_values_kept(tmp_path):
    with zipfile.ZipFile(ZIP) as archive:
        binary_name = next(n for n in archive.namelist() if not n.endswith('.dat'))
        (tmp_path / binary_name).write_bytes(archive.read(binary_name))
        (tmp_path / (binary_name+'.dat')).write_text('7500\t0.1\n7505\t0.2\n7510\t0.1\n')
    r = scan_source(tmp_path)
    assert len(r.spectra) == 2
    assert r.paired_duplicates == 0
    assert all(any('não equivalentes' in w for w in s.warnings) for s in r.spectra)


def test_semicolon_decimal_comma_text():
    x, y, origin, issues = decode_dat('750,0;0,005\n750,5;0,010\n751,0;0,008\n'.encode(), unit='nm')
    np.testing.assert_array_equal(x, [750, 750.5, 751])
    np.testing.assert_array_equal(y, [.005, .01, .008])
    assert origin.startswith('Definida')


def test_reject_non_monotonic_invalid_nonfinite_and_truncated():
    with pytest.raises(InvalidSpectrum):
        decode_dat(b'750 2\n749 3\n')
    with pytest.raises(InvalidSpectrum):
        decode_dat(b'750 2\n751 inf\n')
    with pytest.raises(InvalidSpectrum):
        decode_binary(b'DTLG')


def test_parsing_no_timestamp_confusion_and_ita():
    d = parse_filename('20261009 1435 - 4573 50um 77K 500mV.dat')
    assert d['sample'] == '4573'
    assert d['date_label'] == '20261009 1435'
    assert d['slit_um'] == 50
    assert d['lockin_mv'] == 500
    assert d['temperature_k'] == 77
    assert parse_filename('20261011 1033 - ITA 300um 77K 200mV.dat')['sample'] == 'ITA'


def test_all_cases_in_sample_zip_have_filename_header_slit_conflicts():
    r = scan_source(ZIP)
    assert all(any('Fendas divergentes' in w for w in s.warnings) for s in r.spectra)


def test_zip_corrupt_member_does_not_abort_other_files(tmp_path):
    zpath = tmp_path / 'data.zip'
    with zipfile.ZipFile(zpath, 'w') as z:
        z.writestr('ITA 150um 77K 500mV.dat', '750 2\n751 3\n')
        z.writestr('bad.dat', 'x y\ninvalid\n')
    report = scan_source(zpath)
    assert len(report.spectra) == 1
    assert len(report.errors) == 1


def test_saturation_warning_for_known_files():
    r = scan_source(ZIP)
    ids = {(s.sample, s.slit_filename_um, s.lockin_range_mv)
           for s in r.spectra if any('saturação' in issue for issue in s.warnings)}
    assert ('4575', 1000, 500) in ids
    assert ('4577', 300, 50) in ids


def test_csv_and_json_export_preserve_values_and_metadata(tmp_path):
    import csv
    import json
    from pl_viewer.exporting import export_curves_csv, export_metadata_json
    s = scan_source(ZIP).spectra[0]
    s.temperature_operator_k = 77
    csv_file, json_file = tmp_path/'curves.csv', tmp_path/'meta.json'
    export_curves_csv(csv_file, [s])
    export_metadata_json(json_file, [s], 'sample.zip')
    with csv_file.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(s.signal)
    assert float(rows[0]['comprimento_onda_nm']) == s.wavelength_nm[0]
    assert float(rows[0]['sinal_bruto_unidade_nao_verificada']) == s.signal[0]
    m = json.loads(json_file.read_text(encoding='utf-8'))['aquisicoes'][0]
    assert m['temperatura_informada_operador_k'] == 77
    assert m['temperatura_cabecalho_k'] == 300
    assert m['fenda_cabecalho_entrada_um'] == 400


def test_underscore_filename_support():
    info = parse_filename('20261101_0902_ITA_250um_77K_200mV.dat')
    assert info['sample'] == 'ITA'
    assert info['date_label'] == '20261101 0902'
    assert info['slit_um'] == 250
    assert info['lockin_mv'] == 200
