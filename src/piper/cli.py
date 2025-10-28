import json
import subprocess
import sys
import click
import yaml
from .detect import scan, write_report
from .deps import install_for
from .tests import detect_tests
from .workflow import write_assembler
from .security import tools_for
from .deploy import default_target
from .report import pretty



@click.group()
def main():
    """Piper - Intelligent CI/CD pipeline generator."""
    pass


@main.command()
@click.option("--root", default=".", help="Project root directory to scan")
@click.option("--report", default=".pipeline/detection.json", help="Output path for detection report")
def scan_cmd(root, report):
    """Scan project and detect technology stack."""
    detection = scan(root)
    write_report(detection, report)
    pretty(detection)



@main.command()
@click.option("--in", "inpath", default=".pipeline/detection.json", help="Input detection report")
@click.option("--out", "outpath", default=".github/workflows/generated.yml", help="Output workflow file")
def generate(inpath, outpath):
    """Generate CI/CD workflow based on detection results."""
    #load detection results
    detection = json.loads(open(inpath).read())

    #determine pipeline components
    tools = tools_for(detection)
    tests = detect_tests(".")
    target = default_target(detection)

    #save generation plan
    plan = {"tools": tools, "tests": tests, "target": target}
    open(".pipeline/plan.json", "w").write(json.dumps(plan, indent=2))

    #build test steps
    test_steps = []
    for test in tests:
        test_steps.append({"name": f"Run tests ({test['run']})", "run": test["cmd"]})

    #build security scanning steps
    security_steps = []
    if "safety" in tools:
        security_steps.append({"name": "Safety", "run": "pipx run safety check -r requirements.txt || true"})
    if "bandit" in tools:
        security_steps.append({"name": "Bandit", "run": "pipx run bandit -q -r . || true"})
    if "npm-audit" in tools:
        security_steps.append({"name": "npm audit", "run": "npm audit --audit-level=high || true"})
    if "snyk" in tools:
        security_steps.append({"name": "Snyk", "run": "snyk test || true"})
    if "trivy" in tools:
        security_steps.append({"name": "Trivy FS", "run": "trivy fs --exit-code 0 --severity HIGH,CRITICAL ."})
    if "hadolint" in tools:
        security_steps.append({"name": "Hadolint", "run": "hadolint Dockerfile || true"})

    #build deployment steps
    deploy_steps = []
    if target == "vercel":
        deploy_steps.append({
            "name": "Vercel Deploy",
            "uses": "amondnet/vercel-action@v25",
            "with": {
                "vercel-org-id": "${{ secrets.VERCEL_ORG_ID }}",
                "vercel-project-id": "${{ secrets.VERCEL_PROJECT_ID }}",
                "vercel-token": "${{ secrets.VERCEL_TOKEN }}"
            }
        })
    elif target == "railway":
        deploy_steps.append({"name": "Railway Up", "run": "curl -fsSL https://railway.app/install.sh | sh && railway up"})
    elif target == "heroku":
        deploy_steps.append({"name": "Heroku", "run": "echo 'Heroku deployment would go here'"})
    elif target == "docker":
        deploy_steps.append({"name": "Docker Build", "run": "docker build -t app:ci ."})

    #build complete workflow
    generated_workflow = {
        "name": "Piper: Generated Pipeline",
        "on": {"workflow_call": {}},
        "jobs": {
            "setup": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"uses": "actions/checkout@v4"},
                    {"uses": "actions/setup-node@v4", "with": {"node-version": "lts/*"}},
                    {"uses": "actions/setup-python@v5", "with": {"python-version": "3.12"}},
                    {"name": "Install Python deps", "run": "python -m pip install -U pip setuptools wheel pytest"},
                    {"name": "Install Node deps", "run": "if [ -f package.json ]; then if [ -f pnpm-lock.yaml ]; then corepack enable && pnpm i --frozen-lockfile; elif [ -f yarn.lock ]; then yarn install --frozen-lockfile; else npm ci || npm i; fi; fi"}
                ]
            },
            "test": {
                "needs": "setup",
                "runs-on": "ubuntu-latest",
                "steps": [{"uses": "actions/checkout@v4"}] + test_steps
            },
            "security": {
                "needs": "test",
                "runs-on": "ubuntu-latest",
                "steps": [{"uses": "actions/checkout@v4"}] + security_steps
            },
            "deploy": {
                "needs": "security",
                "runs-on": "ubuntu-latest",
                "steps": [{"uses": "actions/checkout@v4"}] + deploy_steps
            }
        }
    }

    #writes generated workflow
    open(outpath, "w").write(yaml.safe_dump(generated_workflow, sort_keys=False))
    print(f"Generated workflow: {outpath}")


@main.command()
@click.option("--root", default=".", help="Project root directory")
def install(root):
    """Install dependencies for detected project type."""
    detection = scan(root)
    install_for(detection, root)
