import test from 'node:test';
import assert from 'node:assert/strict';
import * as patientModule from '../src/utils/patient.ts';
import { DEFAULT_PATIENT, normalizePatient, updatePatient } from '../src/utils/patient.ts';

test('demo defaults stay unconfirmed and explicit inputs keep their provenance', () => {
  const demo = normalizePatient({ Age: 60 });
  assert.equal(demo.input_sources.BP, 'defaulted');
  assert.equal(demo.input_sources.Age, 'supplied');
  assert.deepEqual(demo.confirmed_measurements, []);
  assert.equal(demo.input_sources.BMI, 'calculated');
});

test('reviewed mode cannot submit untouched defaults and editing clears confirmation', () => {
  const demo = normalizePatient(DEFAULT_PATIENT);
  const reviewed = { ...demo, assessment_mode: 'reviewed', confirmed_measurements: ['Age'] };
  assert.ok(patientModule.reviewedIssues(reviewed).includes('BP'));
  const edited = updatePatient(reviewed, 'Age', 61);
  assert.ok(!edited.confirmed_measurements.includes('Age'));
  assert.equal(edited.input_sources.Age, 'supplied');
});

test('changing body measurements invalidates recorded BMI provenance and confirmation', () => {
  const patient = normalizePatient({ Weight: 81, Length: 180, BMI: 26 });
  patient.confirmed_measurements = ['Weight','BMI'];
  const next = updatePatient(patient, 'Weight', 90);
  assert.equal(next.BMI, 90 / 1.8 ** 2);
  assert.equal(next.input_sources.BMI, 'calculated');
  assert.ok(!next.confirmed_measurements.includes('BMI'));
});

test('explicit null measurements remain unknown on normalization', () => {
  const patient = normalizePatient({ Age: null, DM: null });
  assert.ok(Number.isNaN(patient.Age));
  assert.ok(Number.isNaN(patient.DM));
  assert.equal(patient.input_sources.Age, 'unknown');
  assert.equal(patient.input_sources.DM, 'unknown');
});
