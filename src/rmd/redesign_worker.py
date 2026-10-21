"""Fresh-process pipeline so every module reads the experiment's input snapshot."""
import json
import platform
import numpy
import scipy
from .config import ROOT, CONFIG_DIR, OUTPUT_DIR, input_digest


def main():
    if ROOT/'config'==CONFIG_DIR or ROOT/'outputs'==OUTPUT_DIR:
        raise ValueError('Redesign worker requires isolated config/output directories.')
    metadata={'python':platform.python_version(),'numpy':numpy.__version__,'scipy':scipy.__version__,
              'status':'running','inputs':str(CONFIG_DIR)}
    record=OUTPUT_DIR.parent/'run.json'
    try:
        reference=json.loads((OUTPUT_DIR/'dimensions.json').read_text())
        if reference.get('input_digest')!=input_digest():
            print('Shared inputs changed: regenerating the historical reference required by the current backend.',flush=True)
            from .synthesize import main as reference_fit
            reference_fit()
        from .designs import build
        result=build('direct',refit=True,allow_fit=True,video=False)
        from .single_face import build as single_face
        alternate=single_face()
        links=''.join(f'<li><a href="{file}">{label}</a></li>' for file,label in [
            ('direct_3d.html','Split-face 3D'),('single_face_3d.html','Same-face 3D'),
            ('direct_2d.html','Planar six-bar'),('bat_3d.html','Bat appearance')])
        (OUTPUT_DIR/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Redesign results</title><h1>Experimental redesign</h1><p>New results, not the submitted design. Split-face status: '+result['status']+'; same-face clearance: '+alternate['status']+'. Read validation before using these dimensions.</p><ul>'+links+'</ul><a href="direct/validation.json">Full validation</a>')
        metadata.update(status=result['status'],same_face_status=alternate['status'])
        if not result['nominal_prototype_passes']:raise RuntimeError('New split-face candidate failed nominal validation.')
    except Exception as error:
        metadata.update(status='FAIL',error=str(error));raise
    finally:record.write_text(json.dumps(metadata,indent=2)+'\n')


if __name__=='__main__':main()
