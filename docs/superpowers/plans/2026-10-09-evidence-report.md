# One-click evidence report

Implement a downloadable PDF for a completed, saved assessment. Save the complete response alongside the existing database record and retrieve it by its UUID, without rerunning inference or trusting client-submitted predictions. Add model artifact SHA-256, application version and supplied validation metrics to the inference snapshot. Include all assessed inputs, CAD/LAD/LCX/RCA scores, vessel territories/color source, signed factors and source measurements, validation context and limitations.

1. Test saved-snapshot retrieval, PDF content and unknown/legacy assessments, persistence failure and unchanged history/inference count.
2. Add nullable snapshot/UUID columns with an additive migration, response provenance, report service and GET download endpoint.
3. Add a one-click download button with loading/error/retry states; disable it for missing, stale, busy or unsaved results. Cancel superseded downloads and preserve assessment identity.
4. Verify full backend/frontend suites, production build, schema migration preservation, PDF extraction and visual rendering of every page.

Use ReportLab for generation, pypdf for test extraction, and Poppler for visual QA. Browser access previously denied; do not retry it without renewed authorization.

Implemented and verified: 44 backend tests, 48 frontend tests, production build,
PDF content extraction and visual inspection of all seven synthetic sample pages.
Migration checks cover fresh and legacy databases. Local migration preserved all
91 assessments; pre-migration backup is `db/cardiovision-before-evidence-report-20261009.db`.
Download tests cover retry, cancellation, stale/unsaved results, PDF validation and
object-URL cleanup. Backend tests prove report generation does not rerun inference
or add history, and cover missing snapshots and sanitized generation failures.
Live browser verification was not performed because browser access was denied.
Independent code review found no blocking issues. Its two minor suggestions were
applied: explicit ESR/WBC/platelet units and PDF assertions for signed contributions
and original measurement values. Backend tests and seven-page visual QA were rerun.
Preserve earlier user changes; leave changes uncommitted.
