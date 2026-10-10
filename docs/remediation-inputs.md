# Confirmed inputs and form remediation

Addresses **I03 and I14** and scenarios S16–S19, S08, S32. Input metadata is separate from model predictors. No model retraining or clinical-validation claim is made.

## Delivered

- Explicit demonstration versus reviewed-case modes. Existing clients remain in demonstration mode unless they opt into reviewed mode.
- Each raw measurement records supplied/defaulted/calculated/unknown provenance, its reviewed confirmation, normalized value, and whether it is modeled.
- Reviewed submissions require every modeled original measurement to be explicitly supplied and confirmed. Unknown/defaulted measurements cannot silently become absent or normal. BMI may be calculated from verified height/weight; a separately recorded BMI requires confirmation. Exertional chest pain remains visible as informational and excluded from predictors.
- The form displays provenance, confirmation progress, units, supported ranges, and field errors linked through `aria-describedby` and `aria-invalid`. Native validation opens collapsed groups containing invalid controls.
- Each group has an explicit attestation: the user verified measurements against the case record. Attestation converts presented values into confirmed supplied inputs; it is the user's statement, not automated evidence of measurement.
- Changing a measurement invalidates its confirmation. Editing weight/height recomputes BMI and invalidates its prior recorded provenance. Unconfirmed reviewed cases block automatic reassessment.
- Training sample cases are labeled as examples, not held-out validation. Saved snapshots remain distinct from edited form values.

## Verification

Tests were added and observed failing before implementation. Five backend provenance tests cover defaults versus supplied inputs, reviewed completeness and confirmation, unknown/default source rejection, metadata key validation, and recorded BMI confirmation. Frontend tests cover default provenance, edit invalidation, BMI derivation and accessible reviewed-form/error rendering. Existing input-contract and normalization tests continue passing.

At the final agent checkpoint, the full frontend suite passed 71 tests, the full backend suite passed 138 tests, and the production build passed (existing large-chunk warning and scientific-library warnings). An earlier concurrent backend run observed two deployed-explanation tests failing before that separate implementation was completed; both pass in this checkpoint. The root integration run supersedes these counts if additional work lands.

## Remaining boundaries

No automatic unit conversion is inferred; units remain explicit. No acquisition timestamp, authenticated assessor identity, source-document verification, longitudinal measurement alignment, clinically validated missing-input imputation, or distribution-shift detection is claimed. Reviewed mode is an input-completeness and attestation workflow, not authorization for clinical use. Demo mode can still model synthetic defaults, with assumptions preserved for interpretation. Source categories and confirmation are client declarations; institutional audit identity belongs in a future authenticated clinical workflow.
