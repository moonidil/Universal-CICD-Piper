import subprocess
import sys
from pathlib import Path


def run(cmd, cwd=None):
    """Run a shell command and raise error if it fails."""
    subprocess.run(cmd, cwd=cwd, check=True)


def install_for(detection, cwd="."):
    """
    Install dependencies based on detected project type.
    handles Python, Node.js, Rust, and Go projects.
    """
    types = detection.get("types", [])
    project_path = Path(cwd)

    #python projects
    if "python" in types:
        #always update pip first
        run([sys.executable, "-m", "pip", "install", "-U", "pip", "setuptools", "wheel"])

        #install from requirements.txt if it exists, otherwise just pytest
        if (project_path / "requirements.txt").exists():
            run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=cwd)
        else:
            run([sys.executable, "-m", "pip", "install", "pytest"], cwd=cwd)

    #node.js projects
    if "node" in types:
        #determine which package manager lock file exists
        lock_file = None
        for lock in ["pnpm-lock.yaml", "yarn.lock", "package-lock.json"]:
            if (project_path / lock).exists():
                lock_file = lock
                break

        #use appropriate package manager and command
        if lock_file and lock_file == "pnpm-lock.yaml":
            run(["pnpm", "install", "--frozen-lockfile"], cwd=cwd)
        elif lock_file and lock_file == "yarn.lock":
            run(["yarn", "install", "--frozen-lockfile"], cwd=cwd)
        else:
            #use npm with ci for lockfile, install without
            run(["npm", "ci" if lock_file else "install"], cwd=cwd)

    #rust projects
    if "rust" in types:
        run(["cargo", "update"], cwd=cwd)

    #go projects
    if "go" in types:
        run(["go", "mod", "download"], cwd=cwd)
