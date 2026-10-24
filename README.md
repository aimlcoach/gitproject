# Git environment promotion demo

A small Python project for practicing Git-based promotion through `dev`, `qa`,
and `main`. Deployments are **local simulations**: the scripts copy the app
into `build/deployments/` and write a manifest. They do not contact cloud
services or deploy to real infrastructure.

## Set up

Install Python 3.11 or later, then install the linter:

```powershell
python -m pip install -r requirements-dev.txt
```

The repository starts with `main`, `dev`, and `qa` pointing at the same
scaffold commit. Run commands from the project root.

## 1. Develop and test a feature

Create a feature branch from `dev`, make a change to `hi.py` or its test, and
run the early pipeline. The `dev` pipeline accepts both `dev` and `feature/*`
branches; it runs Ruff and unit tests before simulating a dev deployment.

```powershell
git switch dev
git switch -c feature/friendlier-greeting
python scripts/pipeline.py dev
git add hi.py tests/test_hi.py
git commit -m "Add friendlier greeting"
git switch dev
git merge --no-ff feature/friendlier-greeting
python scripts/pipeline.py dev
```

## 2. Promote to QA

Merge the tested `dev` branch into `qa`. The quality checks run before the
explicit `--approve` gate allows the local QA deployment.

```powershell
git switch qa
git merge --no-ff dev
python scripts/pipeline.py qa --approve
```

Omit `--approve` to verify that the deployment is blocked after the checks.

## 3. Create a release candidate

On `qa`, update `VERSION` (for example, to `0.2.0`) and commit it. Release
creation requires a clean worktree, runs the checks, creates
`dist/hello-0.2.0-rc.zip`, and adds the annotated tag `v0.2.0`.

```powershell
# Edit VERSION to the next MAJOR.MINOR.PATCH version, then:
git add VERSION
git commit -m "Prepare release 0.2.0"
python scripts/pipeline.py release
```

## 4. Promote to production

Merge `qa` into `main`. The production pipeline checks that the release tag is
included in `main`, reruns quality checks, and requires explicit approval
before simulating deployment.

```powershell
git switch main
git merge --no-ff qa
python scripts/pipeline.py prod --approve
```

Deployment copies and manifests are written under `build/deployments/<env>/`.
The release archive is written under `dist/`; both directories are ignored by
Git.
