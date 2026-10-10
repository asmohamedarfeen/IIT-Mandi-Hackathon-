import pytest
from pydantic import ValidationError
from backend.cardio.schemas.patient_schema import PatientInputSchema


def test_defaults_are_distinguished_from_supplied_measurements():
    patient = PatientInputSchema(Age=60)
    provenance = patient.input_provenance()
    assert provenance['assessment_mode'] == 'demo'
    assert provenance['measurements']['Age']['source'] == 'supplied'
    assert provenance['measurements']['BP']['source'] == 'defaulted'
    assert provenance['measurements']['BMI']['source'] == 'calculated'
    assert not provenance['measurements']['Age']['confirmed']


def test_reviewed_mode_rejects_defaults_and_requires_confirmation():
    with pytest.raises(ValidationError, match='Reviewed case requires'):
        PatientInputSchema(assessment_mode='reviewed', Age=60)
    payload = PatientInputSchema().model_dump(by_alias=True)
    payload.pop('BMI')
    payload['assessment_mode'] = 'reviewed'
    payload['confirmed_measurements'] = [key for key in payload if key not in {'patient_id', 'assessment_mode', 'confirmed_measurements', 'input_sources', 'Exertional CP'}]
    reviewed = PatientInputSchema(**payload)
    assert reviewed.input_provenance()['measurements']['BMI']['source'] == 'calculated'
    payload['confirmed_measurements'].remove('BP')
    with pytest.raises(ValidationError, match='BP'):
        PatientInputSchema(**payload)


def test_claimed_unknown_or_default_measurement_is_not_accepted_as_reviewed():
    payload = PatientInputSchema().model_dump(by_alias=True)
    payload.update(assessment_mode='reviewed', confirmed_measurements=[key for key in payload if key not in {'patient_id','assessment_mode','confirmed_measurements','input_sources'}], input_sources={'BP': 'defaulted'})
    with pytest.raises(ValidationError, match='BP'):
        PatientInputSchema(**payload)


def test_rejects_unknown_source_keys_and_confirmation_keys():
    with pytest.raises(ValidationError, match='Unknown measurement'):
        PatientInputSchema(confirmed_measurements=['CAD'])
    with pytest.raises(ValidationError, match='Unknown measurement'):
        PatientInputSchema(input_sources={'Cath': 'supplied'})


def test_reviewed_recorded_bmi_must_be_confirmed_but_computed_bmi_needs_no_extra_attestation():
    payload = PatientInputSchema().model_dump(by_alias=True)
    payload.update(assessment_mode='reviewed', input_sources={'BMI': 'supplied'})
    payload['confirmed_measurements'] = [key for key in payload if key not in {'patient_id','assessment_mode','confirmed_measurements','input_sources','BMI'}]
    with pytest.raises(ValidationError, match='BMI'):
        PatientInputSchema(**payload)
    payload['confirmed_measurements'].append('BMI')
    assert PatientInputSchema(**payload).input_provenance()['measurements']['BMI']['confirmed']
