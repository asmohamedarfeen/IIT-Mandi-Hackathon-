import test from "node:test";
import assert from "node:assert/strict";
import {
  DEFAULT_PATIENT,
  FIELD_GROUPS,
  normalizePatient,
  updatePatient,
  sampleVessels,
} from "../src/utils/patient.ts";

test("normalizes the actual categorical control labels and numeric API codes", () => {
  for (const { fields } of FIELD_GROUPS)
    for (const field of fields) {
      if (!field.options) continue;
      field.options.forEach((label, index) => {
        assert.equal(
          normalizePatient({ [field.key]: label })[field.key],
          index,
          `${field.key}: ${label}`,
        );
        assert.equal(
          normalizePatient({ [field.key]: index })[field.key],
          index,
        );
      });
    }
});

test("sample payload contains patient inputs only and preserves supplied BMI", () => {
  const patient = normalizePatient(
    {
      Age: 59,
      BMI: 29.043708989207214,
      Weight: 81,
      Length: 167,
      Sex: 1,
      Obesity: 1,
      VHD: 2,
      CAD: 1,
      Pulse_Pressure: 42,
    },
    "CASE-1",
  );
  assert.deepEqual(
    Object.keys(patient).sort(),
    Object.keys(DEFAULT_PATIENT).sort(),
  );
  assert.equal(patient.patient_id, "CASE-1");
  assert.equal(patient.BMI, 29.043708989207214);
  assert.equal(patient.Obesity, 1);
  assert.equal(patient.VHD, 2);
});

test("BMI recomputes with height/weight, while an empty field remains invalid", () => {
  const patient = normalizePatient({ Weight: 81, Length: 180, BMI: null });
  assert.equal(patient.BMI, 25);
  assert.equal(updatePatient(patient, "Length", 150).BMI, 36);
  assert.equal(updatePatient(patient, "Weight", 90).BMI, 90 / 1.8 ** 2);
  assert.equal(updatePatient(patient, "Age", 60).BMI, 25);
  assert.ok(Number.isNaN(updatePatient(patient, "Weight", NaN).BMI));
});

test("unknown categories stay invalid and known backend text remains compatible", () => {
  const patient = normalizePatient({
    Sex: " Fmale ",
    BBB: "RBBB",
    VHD: "Moderate",
    DM: "Y",
    Obesity: "N",
  });
  assert.equal(patient.Sex, 0);
  assert.equal(patient.BBB, 2);
  assert.equal(patient.VHD, 2);
  assert.equal(patient.DM, 1);
  assert.equal(patient.Obesity, 0);
  assert.ok(Number.isNaN(normalizePatient({ Sex: "Unknown" }).Sex));
});

test("recorded vessel labels represent the real three multivessel cases", () => {
  const caseWith = (LAD, LCX, RCA) => ({ ground_truth: { LAD, LCX, RCA } });
  assert.equal(
    sampleVessels(caseWith("Stenotic", "Stenotic", "Stenotic")),
    "LAD + LCX + RCA",
  );
  assert.equal(
    sampleVessels(caseWith("Stenotic", "Normal", "Stenotic")),
    "LAD + RCA",
  );
  assert.equal(
    sampleVessels(caseWith("Stenotic", "Stenotic", "Normal")),
    "LAD + LCX",
  );
});

test("category aliases never cross fields and numeric codes must be valid indexes", () => {
  for (const [key, value] of [
    ["BBB", "Male"], ["Sex", "Severe"], ["VHD", "RBBB"],
    ["DM", "Female"], ["Function Class", "Y"], ["Region RWMA", "Mild"],
    ["Sex", 3], ["BBB", -1], ["VHD", 1.5], ["DM", ""],
  ]) assert.ok(Number.isNaN(normalizePatient({ [key]: value })[key]), `${key}: ${value}`);
  assert.equal(normalizePatient({ BBB: "N", VHD: "N" }).BBB, 0);
  assert.equal(normalizePatient({ BBB: "N", VHD: "N" }).VHD, 0);
});
