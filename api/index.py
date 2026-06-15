"""Diagnostic entry point — prints runtime paths for debugging."""
import sys
import os
import json
import site
from pathlib import Path


def handler(event, context):
    body = {
        "sys_path": sys.path,
        "site_packages": site.getsitepackages(),
        "user_site": site.getusersitepackages(),
        "cwd": os.getcwd(),
        "pythonpath": os.environ.get("PYTHONPATH", ""),
        "env": {k: v for k, v in sorted(os.environ.items())},
        "vendored_agents_exists": os.path.isfile(
            "/var/task/_vendor/agents/__init__.py"
        ),
        "vendored_agents_content": "",
    }
    vp = "/var/task/_vendor/agents/__init__.py"
    if os.path.isfile(vp):
        with open(vp) as f:
            body["vendored_agents_content"] = f.read()
    # Find real agents
    for sp in site.getsitepackages():
        ap = Path(sp) / "agents" / "__init__.py"
        if ap.exists():
            body["real_agents_path"] = str(ap)
            break
    else:
        body["real_agents_path"] = "NOT FOUND"
    return {
        "statusCode": 200,
        "body": json.dumps(body, indent=2),
    }
