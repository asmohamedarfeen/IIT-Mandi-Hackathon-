# Local deployment and verification

Run from the repository root. Python 3.11 and Node 24+ are required for local setup.
`bash deploy/scripts/start.sh` installs locked dependencies, migrates the database,
and starts loopback-only services. Existing occupied ports cause it to stop safely;
use `BACKEND_PORT=18000 FRONTEND_PORT=15173 bash deploy/scripts/start.sh` to choose others.

With a running Docker daemon and Compose v2:

```sh
docker compose -f deploy/docker/docker-compose.yml up --build --wait
curl --fail http://127.0.0.1:8080/api/v1/health
python3 deploy/scripts/smoke_docker.py
```

Open http://127.0.0.1:8080. The backend runs Alembic before serving and readiness
returns 503 when models are unavailable. Compose persists assessments in its own
named volume. The smoke command creates a separate random project, random loopback
ports and fresh volume, checks the frontend proxy, synthetic assessment/PDF,
private-file exclusion and restart, then removes only that disposable project.
Normal `docker compose ... down` retains your database volume; never add `--volumes`
to that command unless deletion is intended.

The backend image contains serving weights, aggregate benchmarks and reference
anatomy. It excludes local databases, workbook, release archives and private OOF
evidence. Quality Lab cohort evidence is intentionally absent; the separate
`docker-compose.quality.yml` override mounts protected evidence explicitly.

Browser checks use an isolated temporary SQLite database and ports 18080/15173:

```sh
cd frontend
npm ci
npx playwright install chromium
npm run test:e2e
```

Use `E2E_PYTHON=python` with an already activated Python 3.11 environment; otherwise
the runner uses the repository `.venv`. It refuses to reuse an existing server.
The current Chromium checks cover assessment, vessel selection, stale edits,
reassessment, saved PDF, unavailable-model retry, keyboard vessel selection with
WebGL disabled, and simulated context-loss recovery. Browser traces remain private.
CI runs backend tests, frontend tests/build and these browser checks on a clean
checkout; a separate job runs the Docker smoke command.

These defaults are for a local educational demo with synthetic/de-identified data.
Allowed CORS origins are explicit and API responses prohibit storage in caches.
API/nginx access logs are disabled in Docker; application errors log exception type
only. Nginx operational error logs may include request paths and require protected
storage. The local startup script also disables uvicorn access logs; when starting
uvicorn directly, include `--no-access-log` to preserve that default.

An optional `API_TOKEN` environment secret requires `Authorization: Bearer ...` for
API routes, including history and reports; readiness and CORS preflight remain
public. Set it in the backend environment or shell before Compose; never put it in
`VITE_*`, the JavaScript bundle, a committed file or a query string. The browser UI
does not manage credentials; using this guard with the UI requires an authenticated
gateway or a future identity flow. It is a shared deployment guard, **not** user
identity or record-level authorization. TLS, user identity/ACLs, rate limits,
retention/deletion and protected backups remain prerequisites for shared real-data
use. Loopback binding and CORS do not provide those controls.

Verification on 10 October 2026: Compose configuration parsed, isolated Chromium
checks passed (4/4), and security tests passed (5/5). Docker CLI was installed but the
daemon was unavailable, so the clean image build/start and nginx runtime remain
unverified locally. The smoke script and CI job provide the executable check;
their existence is not a passing run.
