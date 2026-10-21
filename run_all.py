"""Portable project entry point; no installation or working-directory tricks."""
from pathlib import Path
import os
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'outputs'/'.matplotlib'))
from rmd.cli import main

if __name__=='__main__': main()
