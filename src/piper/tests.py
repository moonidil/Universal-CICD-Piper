from pathlib import Path
import json


def detect_tests(cwd="."):
    """Detect test commands for different project types."""
    project_path = Path(cwd)
    commands = []

    #node.js projects
    if (project_path / "package.json").exists():
        package_json = json.loads((project_path / "package.json").read_text())

        #use npm test script if defined
        if "scripts" in package_json and "test" in package_json["scripts"]:
            commands.append({"run": "node", "cmd": "npm test"})
        #fall back to Jest or Vitest if available
        elif "devDependencies" in package_json:
            if "jest" in package_json["devDependencies"]:
                commands.append({"run": "node", "cmd": "npx jest"})
            elif "vitest" in package_json["devDependencies"]:
                commands.append({"run": "node", "cmd": "npx vitest"})

    #python projects
    python_test_files = list(project_path.glob("tests/test_*.py"))
    if ((project_path / "pyproject.toml").exists() or
        (project_path / "pytest.ini").exists() or
        python_test_files):
        commands.append({"run": "python", "cmd": "pytest -q --maxfail=1 --disable-warnings"})

    #rust projects
    if (project_path / "Cargo.toml").exists():
        commands.append({"run": "rust", "cmd": "cargo test --all --quiet"})

    #go projects
    if (project_path / "go.mod").exists():
        commands.append({"run": "go", "cmd": "go test ./..."})

    #fallback if no tests detected
    return commands or [{"run": "fallback", "cmd": "echo 'No tests detected'"}]
