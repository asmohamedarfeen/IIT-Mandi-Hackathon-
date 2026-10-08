"""Explicit local smoke: stores six supplied-example assessments in the chosen API DB."""
import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.cardio.constants import RAW_BINARY_TEXT_FEATURES
from backend.cardio.schemas.patient_schema import PatientInputSchema


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    def request(path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        with urlopen(Request(base + path, data=data, headers={"Content-Type": "application/json"}), timeout=30) as response:
            assert response.status == 200
            return json.load(response)

    health = request("/health")
    assert health["models_ready"] and health["status"] == "healthy"
    samples = request("/sample-patients")
    assert len(samples) == 3
    anatomy = request("/3d-anatomy")
    supplied = json.loads((ROOT / "artifacts/heart_model_anatomy.json").read_text())
    assert anatomy == supplied
    assert (ROOT / "artifacts/heart_model_anatomy.json").read_bytes() == (ROOT / "frontend/public/heart_model_anatomy.json").read_bytes()
    assert request("/benchmarks")
    evidence = []
    for sample in samples:
        numeric = PatientInputSchema(**sample["features"]).model_dump(by_alias=True)
        numeric["patient_id"] = "VERIFY-" + sample["patient_id"]
        text = dict(numeric)
        for name in RAW_BINARY_TEXT_FEATURES:
            text[name] = ["N", "Y"][numeric[name]]
        for name, labels in {"Sex": ["Fmale", "Male"], "BBB": ["N", "LBBB", "RBBB"], "VHD": ["N", "Mild", "Moderate", "Severe"]}.items():
            text[name] = labels[numeric[name]]
        numeric_result, text_result = request("/predict", numeric), request("/predict", text)
        probabilities = {}
        shap_counts = {}
        for target in ["CAD", "LAD", "LCX", "RCA"]:
            a = numeric_result["overall_cad"] if target == "CAD" else numeric_result["vessels"][target]
            b = text_result["overall_cad"] if target == "CAD" else text_result["vessels"][target]
            assert math.isfinite(a["probability"]) and 0 <= a["probability"] <= 1
            assert a == b, (sample["patient_id"], target)
            explanations = numeric_result["shap_explanations"][target]
            assert explanations and explanations == text_result["shap_explanations"][target]
            assert all(math.isfinite(row["contribution"]) for row in explanations)
            probabilities[target] = a["probability_percent"]
            shap_counts[target] = len(explanations)
        evidence.append({"case": sample["patient_id"], "probability_percent": probabilities,
                         "shap_counts": shap_counts, "numeric_text_equal": True})
    history = request("/history?limit=100")
    for row in evidence:
        assert sum(item["patient_identifier"] == "VERIFY-" + row["case"] for item in history) >= 2
    result = {"verified_at": datetime.now(timezone.utc).isoformat(), "base_url": base,
              "models_ready": True, "asset_source_equal": True,
              "vertices": sum(row["vertex_count"] for row in anatomy["structures"].values()),
              "triangles": sum(row["face_count"] for row in anatomy["structures"].values()),
              "cases": evidence, "history_persistence": True}
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
