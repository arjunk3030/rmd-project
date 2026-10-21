"""Guard the submitted geometry against accidental resynthesis during demos."""
import hashlib
import json
from .config import ROOT, CONFIG_DIR, OUTPUT_DIR


def verify():
    if CONFIG_DIR != ROOT/'config' or OUTPUT_DIR != ROOT/'outputs':
        raise ValueError('Frozen demo requires the project config and outputs directories; unset RMD_CONFIG_DIR and RMD_OUTPUT_DIR.')
    lock=json.loads((ROOT/'config/presentation/frozen_design.json').read_text())
    changed=[name for name,digest in lock['sha256'].items()
             if not (ROOT/name).exists() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest]
    if changed:
        raise ValueError('Frozen design changed; no outputs generated. Restore these files or explicitly start a new design: '+', '.join(changed))
    return lock
