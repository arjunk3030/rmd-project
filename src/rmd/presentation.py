"""Frozen demos by default; explicit isolated redesigns when requested."""
import argparse
import json
from .config import ROOT,OUTPUT_DIR
from .freeze import verify

VIEWS=[('single_face_3d.html','1 · Same face','Packaging experiment: known rod/pin collision.'),
       ('direct_3d.html','2 · Split faces','Chosen mechanism; nominal 3 mm package passes.'),
       ('direct_2d.html','3 · Planar six-bar','Rigid links, joint names and target motion.'),
       ('bat_3d.html','4 · Bat appearance','Cosmetic body and colors; same solved wing motion.')]


def write_index():
    cards=''.join(f'<article><h2>{title}</h2><p>{note}</p><a href="{url}">Open animation →</a></article>' for url,title,note in VIEWS)
    (OUTPUT_DIR/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Bat mechanism demo</title><style>body{font:16px/1.6 system-ui;background:#101722;color:#e4eaf2;max-width:1100px;margin:40px auto;padding:0 24px}h1{font-size:32px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}article{padding:24px;background:#1a2636;border:1px solid #33475f;border-radius:14px}h2{font-size:20px}a{color:#8fc4ff}small{color:#b5c1d0}</style><h1>Bat mechanism demo</h1><p>One frozen Stephenson six-bar design · four views · no resynthesis</p><main>'''+cards+'''</main><p><a href="diagnostics/index.html">Motion, transmission and sensitivity plots</a> · <a href="diagnostics/numbers.md">Where each number comes from</a> · <a href="../README.md">Run instructions</a> · <a href="videos/">MP4 exports (after video command)</a></p><small>The original checks describe 3 mm stock. Planned 6.35 mm plywood and actual actuator capacity remain unverified. The same-face experiment deliberately retains its known interference.</small></html>''')


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
