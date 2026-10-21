"""Frozen demos by default; explicit isolated redesigns when requested."""
import argparse
import json
from .config import ROOT,OUTPUT_DIR
from .freeze import verify

def write_index():
    template=ROOT/'src/rmd/templates/index.html'
    (OUTPUT_DIR/'index.html').write_text(template.read_text())


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',nargs='?',default='demo',choices=['demo','validate','diagnostics','video','all','direct','render','init-redesign','redesign'])
    parser.add_argument('name',nargs='?',help='Experiment name for init-redesign/redesign')
    parser.add_argument('--no-video',action='store_true',help='Compatibility flag; demo never encodes videos unless requested.')
    parser.add_argument('--view',default='all',choices=['all','direct','single_face','bat','2d'],help='Video selection')
    args=parser.parse_args(argv)
    verify()
    if args.command in ('init-redesign','redesign'):
        if not args.name:parser.error('This command requires an experiment name.')
        from .redesign import initialize,run
        try:
            (initialize if args.command=='init-redesign' else run)(args.name)
        finally:verify()
        return
    if args.name:parser.error('Only redesign commands accept an experiment name.')
    if args.command in ('demo','all','direct','render'):
        from .designs import build
        from .single_face import build as single_face
        result=build('direct',video=False,allow_fit=False)
        if not result['nominal_prototype_passes']:raise ValueError('Original direct package failed validation.')
        single_face()
    elif args.command=='validate':
        from .designs import build
        from .single_face import build as single_face
        result=build('direct',validate_only=True,allow_fit=False)
        experiment=single_face()
        if not result['nominal_prototype_passes']:raise ValueError('Original direct package failed validation.')
        print('Same-face experiment:',experiment['status'],'(known interference, not a fabrication PASS)')
    if args.command not in ('video',):
        from .diagnostics import generate
        generate()
        write_index()
    if args.command=='video':
        from .demo_video import export
        export(args.view)
    verify()
    print('Frozen dimensions and physical inputs unchanged.')
