"""
Project detection for Piper - scans for tech stack signals.
"""

from pathlib import Path
import json

#maps the project types to their  configuration files
SIGNALS = {
    "node": ["package.json", "pnpm-lock.yaml", "yarn.lock"],
    "python": ["requirements.txt", "pyproject.toml", "tox.ini"],
    # ... etc
}

def scan(root="."):
    """Detect project type by looking for configuration files."""
    path = Path(root)
    found = {k: [] for k in SIGNALS}

    #check for each signal file
    for tech_type, files in SIGNALS.items():
        for file_name in files:
            if (path / file_name).exists():
                found[tech_type].append(file_name)

    #determine primary technology types
    detected_types = []
    for lang in ["node", "python", "rust", "go"]:
        if found[lang]:
            detected_types.append(lang)

    #pick framework (next.js has priority over vue)
    framework = "next" if found["next"] else "vue" if found["vue"] else None

    #pick deployment target
    deploy = ("vercel" if found["vercel"] else
              "netlify" if found["netlify"] else
              "heroku" if found["heroku"] else
              "railway" if found["railway"] else
              "docker" if found["docker"] else None)

    return {
        "types": detected_types,
        "framework": framework,
        "deploy": deploy,
        "signals": found
    }

def write_report(data, path=".pipeline/detection.json"):
    """Save detection results to JSON file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2))
    return path
