"""One estimator registry shared by production training and quality experiments."""

from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, VotingClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier


def get_candidate_models(random_state=42, include_additional=False):
    models = {
        "LogisticRegression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=random_state),
        "RandomForest": RandomForestClassifier(n_estimators=180, max_depth=5, min_samples_leaf=2, class_weight="balanced", random_state=random_state),
        "ExtraTrees": ExtraTreesClassifier(n_estimators=180, max_depth=5, min_samples_leaf=2, class_weight="balanced", random_state=random_state),
        "XGBoost": XGBClassifier(n_estimators=140, max_depth=3, learning_rate=0.03, subsample=0.8, colsample_bytree=0.7, reg_alpha=0.5, reg_lambda=2.0, eval_metric="logloss", random_state=random_state),
        "LightGBM": LGBMClassifier(n_estimators=140, max_depth=3, num_leaves=14, learning_rate=0.03, subsample=0.8, colsample_bytree=0.7, reg_alpha=0.5, reg_lambda=2.0, random_state=random_state, verbose=-1),
        "CatBoost": CatBoostClassifier(iterations=200, depth=4, learning_rate=0.03, l2_leaf_reg=4.0, verbose=0, random_seed=random_state),
    }
    if include_additional:
        models.update({
            "SVM": SVC(probability=True, class_weight="balanced", random_state=random_state),
            "DecisionTree": DecisionTreeClassifier(max_depth=5, min_samples_leaf=2, class_weight="balanced", random_state=random_state),
        })
    return models


def get_voting_model(random_state=42):
    models = get_candidate_models(random_state)
    names = [("catboost", "CatBoost"), ("xgboost", "XGBoost"), ("lightgbm", "LightGBM"), ("rf", "RandomForest"), ("et", "ExtraTrees")]
    return VotingClassifier(estimators=[(short, models[name]) for short, name in names], voting="soft")


def bounded_threads(estimator):
    """Return an unfitted clone constrained to one thread and no CatBoost files."""
    bounded = clone(estimator)
    updates = {key: 1 for key in bounded.get_params(deep=True) if key.split("__")[-1] in {"n_jobs", "thread_count"}}

    def constrain_catboost(model, prefix=""):
        if isinstance(model, CatBoostClassifier):
            updates[prefix + "thread_count"] = 1
            updates[prefix + "allow_writing_files"] = False
        # get_params includes direct estimator children, including voting/pipeline steps.
        for name, value in model.get_params(deep=False).items():
            if hasattr(value, "get_params"):
                constrain_catboost(value, prefix + name + "__")
        for name, value in getattr(model, "estimators", []) or []:
            constrain_catboost(value, prefix + name + "__")
        for name, value in getattr(model, "steps", []) or []:
            constrain_catboost(value, prefix + name + "__")

    constrain_catboost(bounded)
    return bounded.set_params(**updates)
