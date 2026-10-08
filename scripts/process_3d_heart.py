#!/usr/bin/env python3
"""Preserve supplied BodyParts3D external heart surfaces in one registered frame."""
import hashlib
import json
from pathlib import Path
import zipfile
import numpy as np


def structure_for_filename(filename):
    """Select anatomy by supplied labels, never by file position or mesh size."""
    name = Path(filename).name.lower()
    if not name.endswith('.obj'):
        return None
    if 'right coronary artery' in name:
        return 'rca'
    if 'circumflex' in name or 'left marginal artery' in name:
        return 'lcx'
    if 'anterior interventricular' in name or 'diagonal branch of anterior descending' in name:
        return 'lad'
    if 'stem of left coronary artery' in name:
        return 'left_main'
    if ('wall' in name and any(chamber in name for chamber in ('ventricle', 'atrium', 'auricle'))
            or 'septum' in name):
        return 'myocardium'
    return None


def parse_obj_data(text, vertex_offset=0):
    vertices, faces = [], []
    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == 'v':
            vertices.append([float(value) for value in parts[1:4]])
        elif parts[0] == 'f':
            indices = [int(value.split('/')[0]) for value in parts[1:]]
            indices = [(index - 1 if index > 0 else len(vertices) + index) for index in indices]
            if len(indices) < 3 or any(index < 0 or index >= len(vertices) for index in indices):
                raise ValueError('Invalid OBJ face index')
            # Triangle fan also handles polygon faces without dropping supplied geometry.
            faces.extend([[indices[0] + vertex_offset, indices[i] + vertex_offset,
                           indices[i + 1] + vertex_offset] for i in range(1, len(indices) - 1)])
    if not vertices or not faces or not np.isfinite(vertices).all():
        raise ValueError('OBJ must contain finite vertices and faces')
    return vertices, faces


def process_3d_assets(zip_path, output_json_path):
    groups = {name: {'vertices': [], 'faces': [], 'source_files': []}
              for name in ('lad', 'lcx', 'rca', 'myocardium', 'left_main')}
    omitted = []
    with zipfile.ZipFile(zip_path) as archive:
        for filename in sorted(archive.namelist()):
            group_name = structure_for_filename(filename)
            if group_name is None:
                omitted.append(filename)
                continue
            group = groups[group_name]
            vertices, faces = parse_obj_data(archive.read(filename).decode('utf-8'), len(group['vertices']))
            group['vertices'].extend(vertices)
            group['faces'].extend(faces)
            group['source_files'].append(filename)

    all_vertices = np.vstack([group['vertices'] for group in groups.values()])
    center = (all_vertices.min(axis=0) + all_vertices.max(axis=0)) / 2
    scale = 3.5 / np.ptp(all_vertices, axis=0).max()
    payload = {'metadata': {
        'version': '2.0', 'source': 'BodyParts3D FMA 3.2.1', 'units': 'normalized_cardiac',
        'source_archive': Path(zip_path).name,
        'source_sha256': hashlib.sha256(Path(zip_path).read_bytes()).hexdigest(),
        'scale': float(scale), 'center': center.tolist(),
        'coordinate_transform': '[x,y,z] = scale * [source_x-center_x, source_z-center_z, -(source_y-center_y)]',
        'source_files': {name: group['source_files'] for name, group in groups.items()},
        'omitted_files': omitted,
        'selection': 'All coronary arterial branches, left coronary stem, chamber/auricle walls and septa. Internal valve, conduction, papillary/trabecular, fibrous support and venous structures omitted for external surface display.',
        'patient_specific': False,
    }, 'structures': {}}
    for name, group in groups.items():
        vertices = (np.asarray(group['vertices'], dtype=np.float64) - center) * scale
        vertices = vertices[:, [0, 2, 1]] * [1, 1, -1]
        faces = np.asarray(group['faces'], dtype=np.int64)
        if not np.isfinite(vertices).all() or faces.min() < 0 or faces.max() >= len(vertices):
            raise ValueError(f'Invalid geometry in {name}')
        payload['structures'][name] = {
            'positions': np.round(vertices, 6).flatten().tolist(), 'indices': faces.flatten().tolist(),
            'vertex_count': len(vertices), 'face_count': len(faces),
        }
        print(f'{name}: {len(group["source_files"])} files; {len(vertices)} vertices; {len(faces)} triangles')
    output = Path(output_json_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, separators=(',', ':'), allow_nan=False))
    return payload


if __name__ == '__main__':
    root = Path(__file__).resolve().parent.parent
    process_3d_assets(root / 'BP51939_FMA3_2_1_inference_partof_FMA7088_Heart.zip',
                      root / 'artifacts/heart_model_anatomy.json')
    # Both transports serve the exact same asset.
    (root / 'frontend/public/heart_model_anatomy.json').write_bytes(
        (root / 'artifacts/heart_model_anatomy.json').read_bytes())
