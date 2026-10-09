"""Protect fold isolation, strict outcome validation, and the saved feature contract."""

import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone

from backend.cardio.service import feature_service as features


def test_normalization_keeps_missing_values_for_training_fold_imputation():
    frame = pd.DataFrame({" Age ": [20, None, 80], "Sex": ["Male", None, "Female"]})
    normalized = features.normalize_dataset(frame, impute=False)
    assert normalized.Age.isna().tolist() == [False, True, False]
    assert normalized.Sex.isna().tolist() == [False, True, False]
    assert normalized.Sex.dropna().tolist() == [1, 0]
    assert " Age " in frame


def test_preprocessor_imputes_only_training_medians_and_clones():
    preprocessor = features.ClinicalPreprocessor(feature_names=["Age", "Sex", "Pulse_Pressure"])
    preprocessor.fit(pd.DataFrame({"Age": [20, 40], "Sex": ["Male", "Male"], "BP": [100, 140]}))
    output = preprocessor.transform(pd.DataFrame({"Age": [None, 1000], "Sex": [None, "Female"], "BP": [None, 200]}))
    assert output.columns.tolist() == ["Age", "Sex", "Pulse_Pressure"]
    assert output.iloc[0].tolist() == pytest.approx([30, 1, 42])
    assert output.iloc[1].tolist() == pytest.approx([1000, 0, 70])
    assert all(dtype == np.dtype("float32") for dtype in output.dtypes)
    assert preprocessor.get_feature_names_out().tolist() == output.columns.tolist()
    assert not hasattr(clone(preprocessor), "medians_")


@pytest.mark.parametrize("value", [None, "unreported", "", 1])
def test_targets_reject_unrecognized_or_missing_outcomes(value):
    frame = pd.DataFrame({"Cath": [value], "LAD": ["Normal"], "LCX": ["Normal"], "RCA": ["Normal"]})
    with pytest.raises(ValueError, match="Cath"):
        features.extract_targets(frame)


def test_targets_encode_supported_labels_and_preserve_row_index():
    frame = pd.DataFrame({"Cath": [" CAD ", "normal"], "LAD": ["Stenotic", "Normal"], "LCX": ["normal", "stenotic"], "RCA": ["Normal", "Normal"]}, index=[8, 3])
    targets = features.extract_targets(frame)
    assert targets["CAD"].tolist() == [1, 0]
    assert targets["LCX"].tolist() == [0, 1]
    assert targets["CAD"].index.tolist() == [8, 3]


def test_prepare_features_excludes_outcomes_and_enforces_contract():
    frame = pd.DataFrame({"Age": [30], "BP": [120], "Cath": ["CAD"], "LAD": ["Stenotic"], "Exertional CP": [0]})
    output = features.prepare_features(frame, feature_names=["Pulse_Pressure", "Age"])
    assert output.iloc[0].tolist() == pytest.approx([42, 30])
    assert "Cath" not in features.prepare_features(frame)
    with pytest.raises(ValueError, match="Missing"):
        features.prepare_features(frame, feature_names=["unknown"])
    with pytest.raises(ValueError, match="target|outcome"):
        features.prepare_features(frame, feature_names=["LAD"])
    with pytest.raises(ValueError, match="finite"):
        features.prepare_features(pd.DataFrame({"Age": [np.inf], "BP": [120]}))


def test_bounded_models_do_not_mutate_factories_or_write_catboost_files():
    from backend.model_quality.models import bounded_threads, get_candidate_models, get_voting_model
    candidates = get_candidate_models(include_additional=True)
    assert {"SVM", "DecisionTree"} <= candidates.keys()
    bounded = bounded_threads(get_voting_model())
    params = bounded.get_params(deep=True)
    assert params["n_jobs"] == 1
    assert params["catboost__thread_count"] == 1
    assert params["catboost__allow_writing_files"] is False
    assert params["xgboost__n_jobs"] == 1
    assert "thread_count" not in candidates["CatBoost"].get_params()


def test_shared_features_match_saved_production_background():
    import joblib
    bundle = joblib.load("artifacts/cardiovision_ensemble.joblib")
    frame = pd.read_excel("extention of Z-Alizadeh sani dataset.xlsx")
    output = features.prepare_features(frame, bundle["feature_names"])
    np.testing.assert_array_equal(output.iloc[:50].to_numpy(), bundle["reference_background"])


def test_legacy_metric_adapter_preserves_supplied_decision_labels():
    from scripts.train_pipeline import calculate_metrics
    metrics = calculate_metrics(np.array([0, 1]), np.array([0, 1]), np.array([.8, .9]))
    assert metrics["accuracy"] == 1
    assert set(metrics) == {"accuracy", "precision", "recall", "f1", "roc_auc", "specificity", "mcc"}
