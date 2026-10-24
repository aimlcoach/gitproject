import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path

from deploy import deploy


ROOT = Path(__file__).resolve().parent.parent
VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+")


def run(*command: str) -> subprocess.CompletedProcess[str]:
    print(f"+ {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        if error.stdout:
            print(error.stdout, end="")
        if error.stderr:
            print(error.stderr, end="", file=sys.stderr)
        raise
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result


def current_branch() -> str:
    return run("git", "branch", "--show-current").stdout.strip()


def require_branch(stage: str, branch: str) -> None:
    allowed = {
        "dev": branch == "dev" or branch.startswith("feature/"),
        "qa": branch == "qa",
        "release": branch == "qa",
        "prod": branch == "main",
    }
    expected = {
        "dev": "dev or feature/*",
        "qa": "qa",
        "release": "qa",
        "prod": "main",
    }
    if not allowed[stage]:
        raise SystemExit(
            f"{stage} pipeline must run on {expected[stage]} "
            f"(currently on {branch or 'detached HEAD'})."
        )


def require_clean_worktree() -> None:
    status = run("git", "status", "--porcelain").stdout
    if status:
        raise SystemExit("Commit or stash all changes before creating a release or deploying prod.")


def read_version() -> str:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not VERSION_PATTERN.fullmatch(version):
        raise SystemExit(f"VERSION must contain a semantic version like 0.1.0; found {version!r}.")
    return version


def quality_checks() -> None:
    run(sys.executable, "-m", "ruff", "check", ".")
    run(sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v")


def require_approval(stage: str, approved: bool) -> None:
    if not approved:
        raise SystemExit(
            f"{stage.upper()} deployment blocked: review the quality checks, then rerun with --approve."
        )


def create_release_candidate(version: str) -> None:
    tag = f"v{version}"
    existing_tag = subprocess.run(
        ("git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"),
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if existing_tag.returncode == 0:
        raise SystemExit(f"Tag {tag} already exists; update VERSION before creating another release.")

    archive = ROOT / "dist" / f"hello-{version}-rc.zip"
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as release:
        release.write(ROOT / "hi.py", "hi.py")
        release.write(ROOT / "VERSION", "VERSION")

    run("git", "tag", "-a", tag, "-m", f"Release {version}")
    print(f"Release candidate created: {archive}")
    print(f"Annotated release tag created: {tag}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Git environment pipeline.")
    parser.add_argument("stage", choices=("dev", "qa", "release", "prod"))
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Confirm the manual QA or production approval gate.",
    )
    args = parser.parse_args()

    branch = current_branch()
    require_branch(args.stage, branch)
    if args.stage in {"release", "prod"}:
        require_clean_worktree()

    quality_checks()
    version = read_version()

    if args.stage == "dev":
        commit = run("git", "rev-parse", "HEAD").stdout.strip()
        deploy("dev", version, commit)
    elif args.stage == "qa":
        require_approval("QA", args.approve)
        commit = run("git", "rev-parse", "HEAD").stdout.strip()
        deploy("qa", version, commit)
    elif args.stage == "release":
        create_release_candidate(version)
    else:
        require_approval("Production", args.approve)
        tag = f"v{version}"
        run("git", "merge-base", "--is-ancestor", tag, "HEAD")
        commit = run("git", "rev-parse", "HEAD").stdout.strip()
        deploy("prod", version, commit)


if __name__ == "__main__":
    main()
