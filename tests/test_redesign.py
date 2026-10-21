"""Isolation checks without running an optimizer in unit tests."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from rmd import redesign


class RedesignTests(unittest.TestCase):
    def test_reject_path_traversal(self):
        for name in ('../config','/tmp/demo','a/b',''):
            with self.assertRaises(ValueError):redesign.workspace(name)

    def test_snapshot_and_failed_run_preserve_original(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(redesign,'ROOT',Path(tmp)):
            root=Path(tmp);(root/'config/presentation').mkdir(parents=True);(root/'outputs').mkdir()
            (root/'config/direct_drive.json').write_text('{"target":35}')
            (root/'config/presentation/display.json').write_text('{}')
            (root/'outputs/dimensions.json').write_text('{"original":true}')
            redesign.initialize('trial')
            edited=root/'experiments/trial/config/direct_drive.json';edited.write_text('{"target":34}')
            with patch.object(redesign.subprocess,'run') as process:
                process.return_value.returncode=1
                with self.assertRaises(RuntimeError):redesign.run('trial')
                env=process.call_args.kwargs['env']
                self.assertEqual(json.loads((Path(env['RMD_CONFIG_DIR'])/'direct_drive.json').read_text())['target'],34)
                self.assertNotEqual(Path(env['RMD_OUTPUT_DIR']),root/'outputs')
                self.assertEqual((root/'config/direct_drive.json').read_text(),'{"target":35}')
                self.assertEqual((root/'outputs/dimensions.json').read_text(),'{"original":true}')
                with self.assertRaises(FileExistsError):redesign.initialize('trial')
