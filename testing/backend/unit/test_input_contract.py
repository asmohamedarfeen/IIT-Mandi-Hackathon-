"""Regressions for the shared dataset/API feature contract."""
import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError
from backend.cardio.constants import RAW_BINARY_TEXT_FEATURES
from backend.cardio.schemas.patient_schema import PatientInputSchema
from backend.cardio.service.feature_service import ClinicalFeatureEngineer, clean_and_encode_dataset
from backend.cardio.service.prediction_service import prediction_service_instance as service


def test_numeric_and_text_categories_have_identical_vectors():
    text = {name: "Y" for name in RAW_BINARY_TEXT_FEATURES}
    numeric = {name: 1.0 for name in RAW_BINARY_TEXT_FEATURES}
    text.update(Sex="Male", BBB="RBBB", VHD="Moderate")
    numeric.update(Sex=1.0, BBB=2.0, VHD=2.0)
    a, _ = service._prepare_patient_feature_vector(PatientInputSchema(**text))
    b, _ = service._prepare_patient_feature_vector(PatientInputSchema(**numeric))
    np.testing.assert_array_equal(a, b)


def test_missing_bmi_is_computed_and_retained_in_aligned_vector():
    vector, frame = service._prepare_patient_feature_vector(PatientInputSchema(Weight=90, Length=175))
    assert frame.iloc[0]["BMI"] == pytest.approx(90 / 1.75 ** 2)
    assert np.isfinite(vector).all()
    assert list(frame.columns) == service.bundle["feature_names"]


def test_ecg_composite_preserves_saved_training_definition():
    raw = pd.DataFrame([{ "LVH": "Y", "Poor R Progression": "Y", "St Elevation": 0,
        "St Depression": 0, "Tinversion": 0, "Q Wave": 0 }])
    engineered = ClinicalFeatureEngineer().transform(clean_and_encode_dataset(raw))
    assert engineered.iloc[0]["ECG_Abnormality_Score"] == 0
    assert engineered.iloc[0]["LVH"] == 1
    assert engineered.iloc[0]["Poor R Progression"] == 1
    assert engineered.iloc[0]["Ischemic_ECG"] == 0


def test_sample_patients_round_trip_without_losing_features():
    for sample in service.get_sample_patients():
        vector, frame = service._prepare_patient_feature_vector(PatientInputSchema(**sample["features"]))
        np.testing.assert_allclose(vector[0], [sample["features"][name] for name in frame.columns], rtol=1e-6)


@pytest.mark.parametrize("field,value", [("Sex", "unknown"), ("BBB", 3), ("VHD", 4),
    ("LVH", 0.5), ("DM", 2), ("Function Class", -1), ("Region RWMA", 5), ("BMI", float("nan"))])
def test_invalid_categories_and_nonfinite_bmi_are_rejected(field, value):
    with pytest.raises(ValidationError):
        PatientInputSchema(**{field: value})


def test_saved_reference_background_matches_current_feature_definitions():
    from backend.cardio.service.feature_service import prepare_training_data
    features, _, _ = prepare_training_data("extention of Z-Alizadeh sani dataset.xlsx")
    background = service.bundle["reference_background"]
    actual = features[service.bundle["feature_names"]].iloc[:len(background)].to_numpy(dtype=np.float32)
    np.testing.assert_allclose(actual, background, rtol=1e-6, atol=1e-6)


def test_missing_bmi_is_computed_per_row_without_replacing_supplied_bmi():
    raw = pd.DataFrame([{"Weight": 90, "Length": 175, "BMI": None},
                        {"Weight": 70, "Length": 170, "BMI": 31}])
    result = clean_and_encode_dataset(raw)
    assert result.iloc[0]["BMI"] == pytest.approx(90 / 1.75 ** 2)
    assert result.iloc[1]["BMI"] == 31
