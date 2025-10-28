from jinja2 import Template
from pathlib import Path




#GitHub Actions workflow template that uses this system
TEMPLATE = """name: IQ Pipeline
on:
 push:
   branches: [ main ]
 pull_request:
   branches: [ main ]
jobs:
 detect:
   runs-on: ubuntu-latest
   steps:
     - uses: actions/checkout@v4
     - name: Setup Python
       uses: actions/setup-python@v5
       with:
         python-version: '3.12'
     - name: Install CLI
       run: |
         python -m pip install -U pip
         python -m pip install "{{ package }}"
     - name: Scan
       run: pipeline scan --report .pipeline/detection.json
     - name: Generate Workflow
       run: pipeline generate --in .pipeline/detection.json --out .github/workflows/generated.yml
 pipeline:
   needs: detect
   uses: ./.github/workflows/generated.yml
"""




def write_assembler(package="pipelineiq", path=".github/workflows/pipelineiq.yml"):
   """
   Generate the main pipeline GitHub Actions workflow file.
   This workflow detects the project type and generates a custom pipeline.
   """
   #render the template with the package name
   content = Template(TEMPLATE).render(package=package)


   #ensure the directory exists
   workflow_path = Path(path)
   workflow_path.parent.mkdir(parents=True, exist_ok=True)


   #write the generated workflow file
   workflow_path.write_text(content)


   return str(workflow_path)
