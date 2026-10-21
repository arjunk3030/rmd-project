"""Explicit opt-in redesigns, isolated from the submitted demo."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from .config import ROOT


def workspace(name):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',name):
        raise ValueError('Use a simple experiment name: letters, numbers, underscores or hyphens.')
    path=ROOT/'experiments'/name
    if path.is_symlink():raise ValueError('Experiment must not be a symlink.')
    return path


def initialize(name):
    dest=workspace(name)
    dest.mkdir(parents=True,exist_ok=False)
    shutil.copytree(ROOT/'config',dest/'config')
    shutil.rmtree(dest/'config/presentation',ignore_errors=True)
    (dest/'config/presentation').mkdir()
    shutil.copy2(ROOT/'config/presentation/display.json',dest/'config/presentation/display.json')
    print(f'Editable inputs: {dest}/config\nThen run: python3 run_all.py redesign {name}')


def run(name):
    dest=workspace(name)
    if not (dest/'config/direct_drive.json').is_file():
        raise ValueError(f'Initialize first: python3 run_all.py init-redesign {name}')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run_dir=dest/'runs'/stamp
    shutil.copytree(dest/'config',run_dir/'config')
    out=run_dir/'outputs';out.mkdir();(out/'direct').mkdir()
    shutil.copy2(ROOT/'outputs/dimensions.json',out/'dimensions.json')
    env=dict(os.environ,RMD_CONFIG_DIR=str(run_dir/'config'),RMD_OUTPUT_DIR=str(out),
             PYTHONPATH=str(ROOT/'src'),MPLCONFIGDIR=str(run_dir/'.matplotlib'))
    print(f'Redesign run: {run_dir}\nOptimization log: {run_dir}/run.log',flush=True)
    with (run_dir/'run.log').open('w') as log:
        result=subprocess.run([sys.executable,'-m','rmd.redesign_worker'],env=env,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    print(f'Redesign exit code: {result.returncode}. See {run_dir}/run.log')
    if (out/'index.html').exists():print(f'Open {out}/index.html')
    if result.returncode:raise RuntimeError('Redesign did not pass all chosen-layout checks. Inspect its log and validation; the submitted demo is unchanged.')
