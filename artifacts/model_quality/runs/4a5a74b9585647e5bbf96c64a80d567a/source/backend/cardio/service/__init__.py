from backend.cardio.service.feature_service import (
    ClinicalFeatureEngineer,
    clean_and_encode_dataset,
    prepare_training_data
)

def __getattr__(name):
    """Keep historical exports without loading production weights for ML utilities."""
    if name in {'PredictionService', 'prediction_service_instance'}:
        from backend.cardio.service import prediction_service
        value = getattr(prediction_service, name)
        globals()[name] = value
        return value
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')

__all__ = [
    "ClinicalFeatureEngineer",
    "clean_and_encode_dataset",
    "prepare_training_data",
    "PredictionService",
    "prediction_service_instance"
]
