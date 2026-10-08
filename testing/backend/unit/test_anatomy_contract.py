"""Full-source anatomy selection, geometry validity and deterministic transport."""
import json
from pathlib import Path
import zipfile
import numpy as np
from scripts.process_3d_heart import process_3d_assets, structure_for_filename, parse_obj_data

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / 'BP51939_FMA3_2_1_inference_partof_FMA7088_Heart.zip'


def test_complete_registered_source_geometry_is_deterministic(tmp_path):
    source = ROOT / 'artifacts/heart_model_anatomy.json'
    payload = process_3d_assets(ARCHIVE, tmp_path / 'heart.json')
    assert (tmp_path / 'heart.json').read_bytes() == source.read_bytes()
    assert source.read_bytes() == (ROOT / 'frontend/public/heart_model_anatomy.json').read_bytes()
    files = payload['metadata']['source_files']
    with zipfile.ZipFile(ARCHIVE) as archive:
        selected = {name for name in archive.namelist() if structure_for_filename(name)}
    assert set(name for names in files.values() for name in names) == selected
    # Each group uses the same source-space center, scale and orientation.
    with zipfile.ZipFile(ARCHIVE) as archive:
        for name, group_files in files.items():
            source_vertices, _ = parse_obj_data(archive.read(group_files[0]).decode('utf-8'))
            v = (np.asarray(source_vertices[0]) - payload['metadata']['center']) * payload['metadata']['scale']
            np.testing.assert_allclose(payload['structures'][name]['positions'][:3],
                                       v[[0, 2, 1]] * [1, 1, -1], atol=0.00000051)
    assert sum(map(len, files.values())) == 62
    assert len(files['myocardium']) == 38
    assert any('Marginal branch of right coronary artery' in name for name in files['rca'])
    assert not any('right coronary artery' in name for name in files['lcx'])
    assert not any('papillary' in name or 'Trabecula' in name for name in files['myocardium'])
    for group in payload['structures'].values():
        positions, indices = np.asarray(group['positions']), np.asarray(group['indices'])
        assert positions.size == group['vertex_count'] * 3
        assert indices.size == group['face_count'] * 3
        assert np.isfinite(positions).all()
        assert indices.min() >= 0 and indices.max() < group['vertex_count']


def test_obj_negative_indices_and_invalid_geometry():
    vertices, faces = parse_obj_data('v 0 0 0\nv 1 0 0\nv 0 1 0\nf -3 -2 -1', 5)
    assert faces == [[5, 6, 7]]
    import pytest
    with pytest.raises(ValueError):
        parse_obj_data('v 0 0 0\nf 1 2 3')
