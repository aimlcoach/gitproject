import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VALID_ENVIRONMENTS = {"dev", "qa", "prod"}


def deploy(environment: str, version: str, commit: str) -> Path:
    if environment not in VALID_ENVIRONMENTS:
        raise ValueError(f"Unsupported deployment environment: {environment}")

    destination = ROOT / "build" / "deployments" / environment / f"{version}-{commit[:7]}"
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "hi.py", destination / "hi.py")
    shutil.copy2(ROOT / "VERSION", destination / "VERSION")

    manifest = {
        "environment": environment,
        "version": version,
        "commit": commit,
        "deployed_at": datetime.now(timezone.utc).isoformat(),
    }
    (destination / "deployment.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Simulated {environment} deployment: {destination}")
    return destination
