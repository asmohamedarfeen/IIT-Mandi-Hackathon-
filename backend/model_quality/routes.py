"""Public aggregate evidence; private OOF rows never leave the service."""
import json
import os
from pathlib import Path
from enum import Enum
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from backend.core.config import settings
from backend.model_quality.exports import csv_export, pdf_export, selection
from backend.model_quality.service import ArtifactCorrupt, ArtifactMissing, QualityService

router = APIRouter(prefix='/model-quality', tags=['Model Quality'])


class Target(str, Enum):
    CAD = 'CAD'
    LAD = 'LAD'
    LCX = 'LCX'
    RCA = 'RCA'


class Section(str, Enum):
    results = 'results'
    metrics = 'metrics'
    confusion = 'confusion-matrices'
    calibration = 'calibration'
    roc = 'roc'
    pr = 'pr'
    shap = 'shap'
    stability = 'feature-stability'
    thresholds = 'thresholds'
    histogram = 'histogram'
    distribution = 'class-distribution'
    reproducibility = 'reproducibility'


class Format(str, Enum):
    pdf = 'pdf'
    csv = 'csv'
    json = 'json'


@lru_cache(maxsize=1)
def get_quality_service():
    root = Path(__file__).resolve().parents[2]
    dataset = os.environ.get('MODEL_QUALITY_DATASET_PATH', str(root / 'extention of Z-Alizadeh sani dataset.xlsx'))
    return QualityService(settings.MODEL_QUALITY_DIR, settings.MODEL_BUNDLE_PATH, dataset_path=dataset, source_root=root)


def snapshot(service, with_audit=False):
    try:
        return service.capture() if with_audit else service.overview()
    except ArtifactMissing:
        raise HTTPException(404, 'Model quality evidence is not available. Run the offline evaluation first.')
    except ArtifactCorrupt:
        raise HTTPException(503, 'Model quality evidence failed integrity or schema validation.')


def checked_model(summary, model):
    identifier = model or summary['selected_model']
    if identifier not in {m['id'] for m in summary['models']}:
        raise HTTPException(422, 'Unknown evaluation model.')
    return identifier


@router.get('/overview')
def overview(service=Depends(get_quality_service)):
    return snapshot(service)


@router.get('/models')
def models(service=Depends(get_quality_service)):
    data = snapshot(service)
    return {'run_id': data['run_id'], 'selected_model': data['selected_model'], 'models': data['models']}


@router.get('/reproducibility')
def reproducibility(service=Depends(get_quality_service)):
    data = snapshot(service)
    return {'run_id': data['run_id'], 'status': data['status'], 'provenance': data['provenance'], 'data_quality': data['data_quality'], 'limitations': data['limitations']}


def target_detail(target, service):
    data = snapshot(service)
    return {'run_id': data['run_id'], 'target': target, 'status': data['status'], **data['targets'][target]}


for name in ('CAD', 'LAD', 'LCX', 'RCA'):
    # The target is fixed by route, not a user-controlled hidden query.
    def factory(target):
        def read(service=Depends(get_quality_service)):
            return target_detail(target, service)
        return read
    router.add_api_route('/' + name.lower(), factory(name), methods=['GET'])


def diagnostic(kind, target, model, service):
    data = snapshot(service)
    identifier = checked_model(data, model)
    evidence = data['targets'][target]
    value = evidence[kind] if kind in ('class_distribution', 'shap_stability', 'feature_stability') else evidence['models'][identifier]['diagnostics'][kind]
    evidence_model = value['model'] if kind in ('shap_stability', 'feature_stability') else identifier
    return {'run_id': data['run_id'], 'target': target, 'model': evidence_model, kind: value}


for url, key in [('calibration', 'calibration'), ('roc', 'roc'), ('pr', 'pr'), ('shap', 'shap_stability'), ('feature-stability', 'feature_stability'), ('class-distribution', 'class_distribution'), ('thresholds', 'thresholds'), ('histogram', 'probability_histogram')]:
    def factory(kind):
        def read(target: Target = Target.CAD, model: str | None = None, service=Depends(get_quality_service)):
            return diagnostic(kind, target.value, model, service)
        return read
    router.add_api_route('/' + url, factory(key), methods=['GET'])


@router.get('/confusion-matrix')
def confusion_matrix(target: Target = Target.CAD, model: str | None = None, threshold: float = Query(.5, ge=0, le=1, allow_inf_nan=False), service=Depends(get_quality_service)):
    data, audit = snapshot(service, with_audit=True)
    identifier = checked_model(data, model)
    try:
        return service.confusion_from_snapshot(data, audit, target.value, identifier, threshold)
    except ArtifactMissing:
        raise HTTPException(404, 'Model quality evidence is not available.')
    except ArtifactCorrupt:
        raise HTTPException(503, 'Model quality evidence failed validation.')


@router.get('/report')
def report(format: Format = Format.pdf, section: Section = Section.results, target: Target | None = None, model: str | None = None, threshold: float = Query(.5, ge=0, le=1, allow_inf_nan=False), expected_run_id: str | None = Query(None, pattern=r'^[a-f0-9]{8,64}$'), service=Depends(get_quality_service)):
    data, audit = snapshot(service, with_audit=True)
    if expected_run_id is not None and expected_run_id != data['run_id']:
        raise HTTPException(409, 'Evaluation run changed. Refresh the quality evidence before downloading.')
    identifier = checked_model(data, model) if model else None
    if section == Section.confusion:
        target = target or Target.CAD
        identifier = checked_model(data, model)
    cm = service.confusion_from_snapshot(data, audit, target.value, identifier, threshold) if section == Section.confusion else None
    payload = selection(data, section.value, target.value if target else None, identifier, cm)
    payload['selection']['threshold'] = threshold if section == Section.confusion else None
    body = pdf_export(payload) if format == Format.pdf else csv_export(payload) if format == Format.csv else json.dumps(payload, allow_nan=False).encode()
    threshold_label = f'-threshold-{threshold}' if section == Section.confusion else ''
    filename = f"model-quality-{data['run_id']}-{section.value}{'-' + target.value if target else ''}{'-' + identifier if identifier else ''}{threshold_label}.{format.value}"
    media = {'pdf': 'application/pdf', 'csv': 'text/csv', 'json': 'application/json'}[format.value]
    return Response(body, media_type=media, headers={'Content-Disposition': f'attachment; filename="{filename}"'})
