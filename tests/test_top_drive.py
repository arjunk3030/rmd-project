"""Regression checks for the independently animated upper motor pinion."""
import json,re,unittest
from pathlib import Path
import numpy as np
from rmd.direct_drive import gears,settings

ROOT=Path(__file__).resolve().parents[1]


def data(name):
    text=(ROOT/'outputs'/name).read_text()
    match=re.search(r'const DATA=(.*),META=(.*),DIMS=(.*),AUDIT=(.*);\n',text)
    return [json.loads(group) for group in match.groups()]


class TopDriveTests(unittest.TestCase):
    def test_gear_phase_and_same_motion(self):
        split,meta,_,_=data('direct_3d.html');same,_,_,_=data('single_face_3d.html')
        self.assertEqual(meta['top_motor_drive']['pinion_teeth'],18)
        self.assertEqual(meta['top_motor_drive']['wing_gear_teeth'],34)
        self.assertEqual(len(split),len(same))
        phases=[]
        for left,right in zip(split,same):
            for key in ('theta_deg','alpha_deg','F_deg','mu1_deg','mu2_deg'):self.assertEqual(left[key],right[key])
            self.assertFalse(any(p['name'] in ('body_pulley','pedestal_pulley','belt_span_-1','belt_span_1') for p in left['parts']))
            actual={g['name']:g for g in left['gears']};baseline=gears(np.radians(left['theta_deg']),settings())
            self.assertEqual(len(actual),3)
            for g in baseline:self.assertAlmostEqual(actual[g['name']]['phase'],g['phase'],places=11)
            phases.append(actual['top_motor_pinion']['phase'])
        np.testing.assert_allclose(np.diff(np.unwrap(phases)),-(34/18)*np.radians(5),atol=1e-11)
        plate=next(x for x in meta['plates'] if abs(x['center'][0]-9.5)<.01)
        center=meta['top_motor_drive']['center_mm'];idx=next(i for i,h in enumerate(plate['holes']) if np.allclose(h[1:],center[1:]))
        self.assertEqual(plate['hole_radii'][idx],5)

    def test_limited_screen_reports(self):
        for name in ('split','same'):
            report=json.loads((ROOT/'outputs/top_motor'/name/'clearance.json').read_text())
            self.assertEqual(report['detected_drive_conflicts'],[])
            self.assertEqual(report['sampled_gear_vertex_penetrations'],0)
            self.assertGreater(report['rear_support_min_existing_hole_web_mm'],0)
            self.assertGreater(report['rear_support_min_edge_web_mm'],0)
            self.assertFalse(report['build_ready'])

if __name__=='__main__':unittest.main()
