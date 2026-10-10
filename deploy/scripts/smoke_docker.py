"""Build and verify an isolated disposable Docker deployment (no existing volumes)."""
import json
import os
from pathlib import Path
import subprocess
from urllib.request import Request, urlopen
from uuid import uuid4


def main():
    root = Path(__file__).resolve().parents[2]
    try:
        subprocess.run(["docker", "info"], check=True, stdout=subprocess.DEVNULL)
    except (FileNotFoundError, subprocess.CalledProcessError):
        raise SystemExit("Docker smoke requires an installed CLI and a running Docker daemon.")
    project = "cardiovision-smoke-" + uuid4().hex[:12]
    env = {**os.environ, "BACKEND_PORT": "0", "FRONTEND_PORT": "0", "API_TOKEN": ""}
    command = ["docker", "compose", "-p", project, "-f", str(root / "deploy/docker/docker-compose.yml")]

    def compose(*args, capture=False):
        return subprocess.run(command + list(args), cwd=root, env=env, check=True,
                              text=True, stdout=subprocess.PIPE if capture else None).stdout

    try:
        compose("up", "--build", "--detach", "--wait", "--wait-timeout", "180")
        address = compose("port", "frontend", "80", capture=True).strip()
        base = "http://" + address

        def get(path):
            return urlopen(base + path, timeout=120)

        assert get("/").status == 200
        assert json.load(get("/api/v1/health"))["models_ready"] is True
        assert json.load(get("/api/v1/history")) == []
        # Explicit synthetic demo inputs; this never imports a private cohort.
        request = Request(base + "/api/v1/predict", data=json.dumps({
            "patient_id": "SYNTHETIC-DOCKER-SMOKE", "assessment_mode": "demo",
        }).encode(), headers={"Content-Type": "application/json"})
        assessment = json.load(urlopen(request, timeout=120))
        assert assessment["evidence"]["report_available"] is True
        assessment_id = assessment["evidence"]["assessment_id"]
        assert get(f"/api/v1/assessments/{assessment_id}/report").read(5) == b"%PDF-"
        # Inspect the running image: serving artifacts only; migrations, no local DB.
        compose("exec", "-T", "backend", "python", "-c",
                "from pathlib import Path; "
                "assert {p.name for p in Path('/app/artifacts').iterdir()} == "
                "{'cardiovision_ensemble.joblib','heart_model_anatomy.json','benchmark_summary.json'}; "
                "assert not list(Path('/app/db').rglob('*.db')); "
                "assert not list(Path('/app').rglob('oof.json'))")
        # Existing-volume startup reruns migrations and retains the saved report.
        compose("restart", "backend")
        compose("up", "--detach", "--wait", "--wait-timeout", "180")
        assert get(f"/api/v1/assessments/{assessment_id}/report").read(5) == b"%PDF-"
        print("Docker smoke passed: clean migration, readiness/proxy, image privacy, saved PDF and restart.")
    finally:
        # The random project name prevents removing any user's deployment volumes.
        compose("down", "--volumes", "--remove-orphans")


if __name__ == "__main__":
    main()
