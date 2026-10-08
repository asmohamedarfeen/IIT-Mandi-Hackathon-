# CardioVision redesign verification

Verified 8 October 2026 on macOS, Python 3.11.14, Node 24.7.0, npm 11.5.1.
The tested checkout is `codex/cardiovision-redesign`. Services used
`127.0.0.1:8001` and `127.0.0.1:5174`; database
`sqlite:////tmp/cardiovision-redesign-task3.db`. Existing servers on other ports
were not stopped. This is functional research-tool verification, not clinical validation.

## Reproduce

From the repository root:

```sh
DATABASE_URL=sqlite:////tmp/cardiovision-verification.db \
  BACKEND_PORT=8001 FRONTEND_PORT=5174 ./deploy/scripts/start.sh
```

Wait for backend startup. If you opened the frontend before model loading finished,
use its service/case/evidence retry controls. In another terminal:

```sh
.venv/bin/python -m pytest testing/backend -q
npm --prefix frontend test
npm --prefix frontend run build
.venv/bin/python scripts/verify_api.py \
  --base-url http://127.0.0.1:8001/api/v1 \
  --output /tmp/cardiovision-verification.json
```

The live smoke script explicitly stores six assessments from the three supplied
training examples. Use an isolated database. It checks health/readiness, benchmarks,
asset transport equality, numeric/text input equivalence, all probabilities and
explanation targets, and persisted history. It uses the standard library and the
existing backend input schema; no browser test framework was installed.

## Recorded checks

- Backend: **34 passed**, **205 warnings**, 8.05 s. Coverage includes all 50×84 saved
  reference features, all three sample vectors, input validation, omitted BMI,
  persistence rollback, and deterministic complete-source anatomy regeneration.
- Frontend: **12 passed**, zero failures, 415 ms. Coverage includes every categorical
  control label, field-specific aliases and invalid numeric codes, raw input
  whitelisting/BMI, real case labels, complete anatomy construction and material
  updates/disposal, and optional/denied/fullscreen entry and exit APIs.
- The new cross-field regression first failed on `BBB: "Male"`; after the fix it
  passed along with out-of-range, fractional, empty and other cross-field inputs.
- Production build: TypeScript/Vite passed; 1,588 modules, 7.92 s. JS **785.31 kB**
  (**225.52 kB gzip**); CSS **26.59 kB**. The >500 kB chunk warning is retained.
- `bash -n deploy/scripts/start.sh` and `git diff --check`: passed.
- Startup: pinned backend install through the project's Python 3.11 `.venv`,
  `npm ci`, Alembic migrations, loopback bindings, matching API base and explicit
  ports worked in two launches. Occupied ports failed before installation/migration
  and preserved running services. Terminating the owning script cleaned up both
  actual server processes. Immediate restart exposed a TIME_WAIT false positive;
  socket reuse fixed it. Starting Vite from `frontend/` removed the observed
  Tailwind content warning. No global Python environment was modified.

### Live API results

The durable machine-readable record is [verification-api.json](verification-api.json).
All values below are percentages, rounded by the actual API. Each target has eight
finite surrogate SHAP contributions. Numeric and backend-label submissions return
identical probabilities and explanation rows; both persist in assessment history.

| Supplied case | CAD | LAD | LCX | RCA |
| --- | ---: | ---: | ---: | ---: |
| PATIENT-1016 | 95.8 | 86.6 | 76.0 | 83.2 |
| PATIENT-1001 | 89.5 | 69.2 | 23.0 | 50.9 |
| PATIENT-1002 | 97.1 | 93.8 | 77.2 | 34.2 |

API anatomy equals the artifact JSON, which equals the public asset byte for byte.
The registered five structures total **95,363 vertices / 171,186 triangles**, drawn
from all 62 selected source OBJ files. Backend deterministic-source tests also
check common coordinate transformation and source selection, including right
marginal branches. No arbitrary triangle subsampling or substitute heart is used.

### Browser checks

All browser interactions used CUA in the Codex in-app browser. No independent
Playwright process or browser automation dependency was added. Screenshot files
below are committed evidence, not scratch files or application assets.

- Desktop **1280×900**, **1600×1000**, and **1600×1200**: actual shaded tissue and
  registered coronary trees load in one canvas. At 1280 px the document width was
  1280 px, with no horizontal overflow. The final 1600×1200 hero captures all stage
  controls. Drag visibly rotates the heart to a different anatomical view; explicit
  zoom in/out, reset and LAD/LCX/RCA focus respond. Focus selection states switch
  correctly. Repeated pulse on/off toggles, tissue hide/show, and opacity 1→0.4→1
  retain one canvas. Pulse is labelled illustrative.
- Fullscreen enters and resizes the anatomy. `fullscreenchange` changes the control
  to **Exit fullscreen heart viewer**; clicking that observed control restores the
  page and **Expand heart viewer**. Unsupported APIs and synchronous/asynchronous
  denial return visible-status messages in the utility tests; the runtime browser
  supports fullscreen, so denied/unsupported browser policy was not forced.
- All three cases were selected and explicitly submitted through the desktop UI.
  Their four outputs match the API table. Loading alone never creates a result.
  CAD/LAD/LCX/RCA explanation tabs each display eight rows and distinct contributions.
- Editing PATIENT-1016 weight **81→82 kg** changes BMI **29.0→29.4**, marks all four
  results **Needs reassessment**, labels prior explanations, removes risk percentages
  from the viewer and returns the anatomy to neutral colors. Clearing required FBS,
  collapsing its laboratory group and submitting opens that group, focuses the empty
  field and shows native validation; no new assessment replaces the stale result.
- Mobile **390×844**: document width **390 px**, one canvas, zero desktop pin spacers.
  Real submission of PATIENT-1001 succeeds. Hiding tissue in risk mode visibly shows
  complete red LAD, green LCX, amber RCA trees with neutral untargeted left stem.
  The benchmark dialog is **352 px** wide; its table scrolls internally while the
  page remains within 390 px. All four benchmark tabs show seven candidate rows.
- Both dialogs expose labelled headings, initial close-button focus, Escape closure
  and return focus to their opening controls. Native Tab cycling visits modal controls,
  the browser/body boundary, then wraps to the close control; no background application
  control receives focus. All three guide and story vessel disclosures expand and
  expose their corresponding descriptions.
- Real backend unavailability: while the standalone frontend remained live, the owned
  backend was terminated. Submission showed a concise retry message, service unavailable
  and a disabled submit control. Existing same-input results remained visible. Restarting
  the backend, selecting **Recheck connection**, and resubmitting produced a successful
  assessment and removed the failure alert. Case and benchmark unavailable states during
  a separate backend startup recovered with **Retry cases** and **Retry evidence**.
  Local static anatomy stayed usable during the API outage.
- Focused browser error/warn log snapshots returned `[]`, including after recovery.
  This is not a claim that the deliberately unavailable API produced no failed requests:
  connection failure is directly evidenced by the UI and controlled backend shutdown.

## Durable screenshots

| Evidence | File |
| --- | --- |
| Full desktop hero and actual anatomy | [desktop-hero.jpg](screenshots/desktop-hero.jpg) |
| Desktop anatomy at 1280 px | [desktop-anatomy.jpg](screenshots/desktop-anatomy.jpg) |
| Fullscreen anatomy | [fullscreen-anatomy.jpg](screenshots/fullscreen-anatomy.jpg) |
| Different anatomical view after orbit | [orbit-anatomy.jpg](screenshots/orbit-anatomy.jpg) |
| Desktop real assessment | [desktop-assessment.jpg](screenshots/desktop-assessment.jpg) |
| Anatomy guide | [anatomy-guide.jpg](screenshots/anatomy-guide.jpg) |
| Mobile hero with actual heart | [mobile-hero.jpg](screenshots/mobile-hero.jpg) |
| Mobile real assessment | [mobile-assessment.jpg](screenshots/mobile-assessment.jpg) |
| Mobile colored coronary trees | [mobile-risk.jpg](screenshots/mobile-risk.jpg) |
| Mobile benchmark dialog | [mobile-evidence.jpg](screenshots/mobile-evidence.jpg) |
| Backend unavailable during benchmark load | [mobile-evidence-unavailable.jpg](screenshots/mobile-evidence-unavailable.jpg) |
| Backend unavailable during submission | [mobile-assessment-unavailable.jpg](screenshots/mobile-assessment-unavailable.jpg) |

## Limits and follow-up

- The available CUA browser capabilities expose viewport and visibility only. The live
  runtime reported `prefers-reduced-motion: false`; no supported media-emulation control
  was available. Code inspection confirms reduced motion disables pulse, GSAP desktop
  pin/entry/stacking and CSS transitions/sticky story positions. Runtime switching to
  reduced motion remains **unverified**; no synthetic preference override was used.
- Desktop/mobile viewport checks are not physical-device touch/pinch or Safari/Firefox
  coverage. WebGL context-loss/retry, prolonged GPU memory behavior and delayed-response
  races were not stress-tested here. Existing mesh identity/disposal tests do not prove
  those GPU/runtime behaviors.
- Docker daemon was unavailable in this environment; Docker build/start is **unverified**.
  Backend warning cleanup and deferred 3D/motion lazy loading remain follow-up work.
- All three supplied cases have recorded multivessel involvement and come from training
  data. Saved uncalibrated CV results are not external validation of the deployed
  calibrated ensemble. SHAP comes from separate XGBoost surrogates. Reference surface
  anatomy is not patient-specific; whole-vessel colors do not locate lesions or blood
  flow. Uniform pulse preserves registration and is not physiological motion. Model
  weights, API schemas and source geometry were preserved.

See [MODEL_AND_ANATOMY_AUDIT.md](MODEL_AND_ANATOMY_AUDIT.md) for provenance, licensing
and saved-feature limitations. Temporary viewport overrides were reset after testing.
