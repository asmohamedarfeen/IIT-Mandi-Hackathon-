from backend.cardio.schemas.patient_schema import PatientInputSchema
from backend.cardio.service.explanation_service import build_feature_lineage
from backend.cardio.service.prediction_service import prediction_service_instance


def test_recorded_and_derived_lineage_uses_assessed_inputs():
    inputs = {"St Depression": 1, "LDL": 160, "HDL": 40}
    recorded = build_feature_lineage("St Depression", inputs, 1.0)
    assert recorded.feature_kind == "recorded"
    assert recorded.source_measurements[0].model_dump() == {"input_key": "St Depression", "recorded_value": 1}
    ratio = build_feature_lineage("Castelli_Risk_Index_II", inputs, 4.0)
    assert ratio.feature_kind == "derived"
    assert [(s.input_key, s.recorded_value) for s in ratio.source_measurements] == [("LDL", 160), ("HDL", 40)]
    assert ratio.model_input_value == 4.0
    assert ratio.derivation
    inputs["LDL"] = 80
    assert ratio.source_measurements[0].recorded_value == 160


def test_lineage_preserves_fitted_composite_definitions():
    inputs = PatientInputSchema().model_dump(by_alias=True)
    ecg = build_feature_lineage("ECG_Abnormality_Score", inputs, 0)
    assert [s.input_key for s in ecg.source_measurements] == ["St Elevation", "St Depression", "Tinversion", "Q Wave"]
    metabolic = build_feature_lineage("Metabolic_Risk_Score", inputs, 0)
    assert [s.input_key for s in metabolic.source_measurements] == ["DM", "HTN", "TG", "FBS"]
    unknown = build_feature_lineage("unrecognized_ratio", inputs, 7)
    assert unknown.feature_kind == "unmapped"
    assert unknown.source_measurements == []
    assert unknown.derivation is None


def test_every_saved_feature_has_known_non_leaking_measurement_lineage():
    inputs = PatientInputSchema().model_dump(by_alias=True)
    for feature in prediction_service_instance.bundle["feature_names"]:
        lineage = build_feature_lineage(feature, inputs, 0)
        assert lineage.feature_kind != "unmapped", feature
        assert lineage.source_measurements, feature
        for source in lineage.source_measurements:
            assert source.input_key in inputs
            assert source.input_key not in {"patient_id", "Cath", "CAD", "LAD", "LCX", "RCA"}


def test_returned_lineage_matches_exact_model_vector_without_changing_shap_or_scores():
    service = prediction_service_instance
    patient = PatientInputSchema(Age=67, **{"St Depression": 1})
    vector, _ = service._prepare_patient_feature_vector(patient)
    prediction = service.predict(patient)
    for target, impacts in prediction.shap_explanations.items():
        original_shap = service.tree_explainers[target].shap_values(vector)[0]
        for impact in impacts:
            idx = service.bundle["feature_names"].index(impact.feature)
            assert impact.model_input_value == float(vector[0, idx])
            assert impact.contribution == round(float(original_shap[idx]), 4)
            for source in impact.source_measurements:
                assert source.recorded_value == prediction.evidence.clinical_inputs[source.input_key]
        expected = round(float(service.bundle["calibrated_models"][target].predict_proba(vector)[0, 1]), 4)
        risk = prediction.overall_cad if target == "CAD" else prediction.vessels[target]
        assert risk.probability == expected
        assert len(impacts) <= 8
        assert all(abs(impact.contribution) >= .001 for impact in impacts)
