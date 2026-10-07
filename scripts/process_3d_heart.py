#!/usr/bin/env python3
"""
3D Anatomical Heart Asset Processor
Extracts BodyParts3D OBJ files from zip, groups LAD, LCX, RCA, and Myocardium,
normalizes coordinates to origin, and outputs an optimized Three.js BufferGeometry JSON asset.
"""

import os
import json
import zipfile
import numpy as np

def parse_obj_data(text: str, vertex_offset: int):
    vertices = []
    faces = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("v "):
            parts = line.split()
            vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
        elif line.startswith("f "):
            parts = line.split()[1:]
            idx = [int(p.split("/")[0]) - 1 + vertex_offset for p in parts]
            if len(idx) == 3:
                faces.append(idx)
            elif len(idx) == 4:
                faces.append([idx[0], idx[1], idx[2]])
                faces.append([idx[0], idx[2], idx[3]])
    return vertices, faces

def process_3d_assets(zip_path: str, output_json_path: str):
    print(f"Opening {zip_path}...")
    with zipfile.ZipFile(zip_path) as z:
        all_names = z.namelist()

        categories = {
            "lad": ["anterior interventricular", "diagonal branch"],
            "lcx": ["circumflex", "marginal artery"],
            "rca": ["right coronary", "conus branch"],
            "myocardium": ["ventricle", "atrium", "septum"]
        }

        raw_groups = {}
        all_global_coords = []

        for group_name, patterns in categories.items():
            files = [n for n in all_names if any(p in n.lower() for p in patterns)]
            group_verts = []
            group_faces = []
            curr_v_count = 0

            # For myocardium, take representative chamber walls to keep performance fast (<40k faces)
            if group_name == "myocardium" and len(files) > 20:
                files = files[::2]

            for fn in files:
                text = z.read(fn).decode("utf-8", errors="ignore")
                v, f = parse_obj_data(text, curr_v_count)
                curr_v_count += len(v)
                group_verts.extend(v)
                group_faces.extend(f)

            raw_groups[group_name] = {
                "vertices": np.array(group_verts, dtype=np.float32),
                "faces": np.array(group_faces, dtype=np.int32)
            }
            all_global_coords.append(raw_groups[group_name]["vertices"])

    # Compute global center and scale
    all_stacked = np.vstack(all_global_coords)
    min_bound = all_stacked.min(axis=0)
    max_bound = all_stacked.max(axis=0)
    center = (min_bound + max_bound) / 2.0
    scale = 3.5 / np.max(max_bound - min_bound)

    print(f"Bounding box: Min={min_bound}, Max={max_bound}, Center={center}, Scale={scale}")

    # Build Three.js buffer geometry compatible dictionaries
    heart_payload = {
        "metadata": {
            "version": "1.0",
            "source": "BodyParts3D FMA 3.2.1",
            "units": "normalized_cardiac",
            "scale": float(scale),
            "center": center.tolist()
        },
        "structures": {}
    }

    for group_name, data in raw_groups.items():
        # Center and scale vertices
        norm_verts = (data["vertices"] - center) * scale
        # Orient heart to face camera properly (swap/invert if needed for standard anatomical view)
        # In BodyParts3D: X is Left-Right, Y is Antero-Posterior, Z is Cranio-Caudal
        # In Three.js: X is Left-Right, Y is Up-Down, Z is Depth
        three_verts = np.zeros_like(norm_verts)
        three_verts[:, 0] = norm_verts[:, 0]
        three_verts[:, 1] = norm_verts[:, 2]  # Z (height) -> Three.js Y
        three_verts[:, 2] = -norm_verts[:, 1] # -Y (depth) -> Three.js Z

        # Flatten arrays for direct Float32Array and Uint32Array ingestion
        flat_positions = [round(float(coord), 4) for coord in three_verts.flatten()]
        flat_indices = [int(idx) for idx in data["faces"].flatten()]

        heart_payload["structures"][group_name] = {
            "positions": flat_positions,
            "indices": flat_indices,
            "vertex_count": len(three_verts),
            "face_count": len(data["faces"]),
        }
        print(f"Processed {group_name:10s}: {len(three_verts)} vertices, {len(data['faces'])} faces")

    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, "w") as f:
        json.dump(heart_payload, f)
    file_size_mb = os.path.getsize(output_json_path) / (1024 * 1024)
    print(f"Successfully generated {output_json_path} ({file_size_mb:.2f} MB)")

if __name__ == "__main__":
    zip_f = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "BP51939_FMA3_2_1_inference_partof_FMA7088_Heart.zip"))
    out_f = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "artifacts", "heart_model_anatomy.json"))
    process_3d_assets(zip_f, out_f)
