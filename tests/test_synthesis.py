"""Numerical regression tests; run python3 -m unittest discover -s tests -v."""
from pathlib import Path
import sys
import json
import os
os.environ.setdefault("MPLCONFIGDIR",str(Path(__file__).resolve().parents[1]/"outputs/.matplotlib"))
import unittest
from unittest.mock import patch
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from rmd.fourbar import freudenstein, forward_fourbar, grashof_crank_rocker
from rmd.config import ESTIMATED_SAMPLES, ROOT
from rmd import targets, model
from rmd.design_io import load_design
from rmd.validation import screen
from rmd.clearance import segment_distance
from rmd.legacy_geared_synthesis import _residuals_band, N_OPT

class SynthesisTests(unittest.TestCase):
    def test_compact_full_drive_preserves_motion_and_has_no_sampled_clashes(self):
        from rmd.compact_drive import settings,geometry,audit,gear_specs,layout
        from rmd.assembly import gear_outline
        cfg=settings();d,b1,b2,_=load_design()
        th=np.linspace(0,2*np.pi,361)
        sim=model.simulate(d,th,b1,b2);geom=geometry(d,sim,cfg)
        half,o,rho=layout(cfg)
        for side,m,dx in [('R',1,0),('L',-1,cfg['left_axial_offset_mm'])]:
            p=geom['parts'];crank=p[side+'/crank1'];rod=p[side+'/coupler1'];rocker=p[side+'/rocker1']
            np.testing.assert_allclose(np.linalg.norm(crank['q']-crank['p'],axis=1),d['a1'],atol=1e-9)
            np.testing.assert_allclose(np.linalg.norm(rod['q']-rod['p'],axis=1),d['b1'],atol=1e-9)
            np.testing.assert_allclose(np.linalg.norm(rocker['q']-rocker['p'],axis=1),d['c1'],atol=1e-9)
            angles=np.unwrap(np.arctan2(rocker['q'][:,2],m*rocker['q'][:,1]-half))-d['kappa1']-rho
            np.testing.assert_allclose(angles,sim['alpha'],atol=1e-9)
            shaft=p[side+'/motor_shaft']
            self.assertAlmostEqual(shaft['p'][0,1],m*15)
            self.assertAlmostEqual(shaft['p'][0,2],o[1])
        for label in ('inner_spar','outer_spar','rod2','elbow_horn'):
            r=geom['parts']['R/'+label];l=geom['parts']['L/'+label]
            for key in ('p','q'):
                np.testing.assert_allclose(r[key][:,1],-l[key][:,1],atol=1e-9)
                np.testing.assert_allclose(r[key][:,2],l[key][:,2],atol=1e-9)
        self.assertEqual(len(gear_specs(0,cfg)),6)
        self.assertTrue(np.isfinite(gear_outline(0,gear=cfg['gear'])).all())
        report=audit(d,b1,b2,cfg)
        self.assertEqual(report['status'],'PASS',report['conflicts'])
        self.assertFalse(report['build_ready'])
        # Axial separation is necessary, not merely decorative.
        bad=dict(cfg,left_axial_offset_mm=0,audit_samples=180)
        self.assertEqual(audit(d,b1,b2,bad)['status'],'FAIL')



    def test_freudenstein_recovers_known_geometry(self):
        lengths={'a':20.,'b':70.,'c':35.,'d':60.}
        pairs=[]
        for phi in (.4,1.7,3.6):
            _,psi=forward_fourbar((0,0),(60,0),20,70,35,phi)
            pairs.append((phi,psi))
        recovered=freudenstein(pairs,60)
        for key,value in lengths.items():self.assertAlmostEqual(recovered[key],value,places=8)

    def test_change_point_not_accepted_as_healthy_crank_rocker(self):
        self.assertFalse(grashof_crank_rocker(10,20,30,40))
        self.assertFalse(grashof_crank_rocker(-1,20,30,40))

    def test_periodic_targets_hit_samples_without_unrequested_hyperextension(self):
        for t,a,f in ESTIMATED_SAMPLES:
            self.assertAlmostEqual(np.degrees(targets.alpha_target(2*np.pi*t)),a,places=9)
            self.assertAlmostEqual(np.degrees(targets.F_target(2*np.pi*t)),f,places=9)
        values=[np.degrees(targets.F_target(t)) for t in np.linspace(0,2*np.pi,3601)]
        self.assertGreaterEqual(min(values),0)
        self.assertLessEqual(max(values),50+1e-10)
        self.assertAlmostEqual(targets.F_target(-.01),targets.F_target(2*np.pi-.01),places=12)

    def test_fresh_dense_result_recomputed_not_saved_flags(self):
        d,b1,b2,_=load_design()
        for n in (1440,7200):
            result=screen(d,b1,b2,n=n)
            self.assertTrue(result['passes'],result['failed_checks'])
            self.assertLess(result['max_link_length_error_mm'],1e-8)
            self.assertLess(result['cycle_closure_error_mm'],1e-8)
        sim=model.simulate(d,np.linspace(0,2*np.pi,3601),b1,b2)
        np.testing.assert_allclose(sim['P2'],d['a2']*np.column_stack([np.cos(model.DRIVE_SIGN*sim['thetas']+d['delta']),np.sin(model.DRIVE_SIGN*sim['thetas']+d['delta'])]),atol=1e-10)


    def test_stale_results_rejected(self):
        with patch('rmd.design_io.input_digest',return_value='changed'):
            with self.assertRaisesRegex(ValueError,'Shared inputs do not match'):load_design()

    def test_invalid_geometry_residual_has_consistent_size(self):
        from rmd.legacy_geared_synthesis import KEYS
        d,b1,b2,_=load_design();d['b1']=10000
        residual=_residuals_band([d[k] for k in KEYS],b1,b2)
        self.assertEqual(len(residual),4*N_OPT+2)
        self.assertFalse(screen(d,b1,b2)['passes'])

    def test_segment_distance_crossing_parallel_and_skew(self):
        p=np.array([[0.,0,0]]);q=np.array([[1.,0,0]])
        self.assertAlmostEqual(float(segment_distance(p,q,np.array([[.5,-1,0]]),np.array([[.5,1,0]]))[0]),0)
        self.assertAlmostEqual(float(segment_distance(p,q,np.array([[0,2,0]]),np.array([[1,2,0]]))[0]),2)
        self.assertAlmostEqual(float(segment_distance(p,q,np.array([[.5,-1,3]]),np.array([[.5,1,3]]))[0]),3)



    def test_compact_horn_and_one_way_bending(self):
        d,b1,b2,_=load_design();report=screen(d,b1,b2,n=7200)
        self.assertLessEqual(d['c2'],38)
        self.assertGreaterEqual(report['min_F_deg'],0)



    def test_pitched_tapered_panels_and_rectangular_alternative(self):
        from rmd.panels import panel_geometry
        from rmd.config import FIXED
        d,b,c,_=load_design();sim=model.simulate(d,np.linspace(0,2*np.pi,73),b,c)
        pitched,ribs=panel_geometry(sim);flat,_=panel_geometry(sim,pitch_deg=0)
        rectangle,_=panel_geometry(sim,style='rectangular')
        self.assertEqual(len(ribs),10)
        for name,quad in pitched.items():
            root=np.linalg.norm(quad[3]-quad[0],axis=1)
            tip=np.linalg.norm(quad[2]-quad[1],axis=1)
            if 'outer' in name:self.assertTrue(np.all(root>tip))
            a,b1,c1,d1=rectangle[name]
            np.testing.assert_allclose(np.linalg.norm(d1-a,axis=1),np.linalg.norm(c1-b1,axis=1),atol=1e-8)
            self.assertFalse(np.allclose(quad[2][:,2],flat[name][2][:,2]))
        report=screen(d,b,c,n=7200)
        self.assertGreaterEqual(report['max_F_deg'],45)

    def test_direct_closure_common_axis_and_freshness(self):
        from rmd.designs import get_direct
        from rmd.direct_drive import Problem,geometry,gears,settings
        v,ba,be,_=get_direct(allow_fit=False)
        p=Problem(7200);sim=p.state(v,ba,be)['simulation']
        self.assertTrue(sim['ok'])
        np.testing.assert_allclose(np.linalg.norm(sim['Q2']-sim['P2'],axis=1),v[9],atol=1e-8)
        np.testing.assert_allclose(np.linalg.norm(sim['Q2']-sim['E'],axis=1),v[7],atol=1e-8)
        geom=geometry(v,ba,be,np.array([0.,1.,3.]))
        for side in ('R','L'):
            a=geom['parts'][side+'/crank1']['p'];b=geom['parts'][side+'/crank2_direct']['p']
            np.testing.assert_allclose(a[:,1:],b[:,1:],atol=1e-9)
            self.assertTrue(np.all(abs(a[:,0]-b[:,0])>0))
            self.assertLess(float(abs(a[0,0]-b[0,0])),45) # short shafts, motor outside body
            self.assertNotIn(side+'/control_lever2',geom['parts'])
        self.assertGreaterEqual(sim['mu1'].min(),40)
        self.assertGreaterEqual(sim['mu2'].min(),40)
        np.testing.assert_allclose(np.linalg.norm(sim['E'],axis=1),100,atol=1e-8)
        np.testing.assert_allclose(np.linalg.norm(sim['TIP']-sim['E'],axis=1),150,atol=1e-8)
        self.assertEqual(len(gears(0,settings())),2)
        with patch('rmd.designs.direct_digest',return_value=('changed',{})):
            with self.assertRaisesRegex(ValueError,'Saved direct fit does not match'):get_direct(allow_fit=False)

    def test_both_complete_designs_recompute_checks(self):
        from rmd.designs import build
        for kind in ('compact','direct'):
            with self.subTest(kind=kind):
                r=build(kind,validate_only=True,allow_fit=False)
                self.assertTrue(r['nominal_prototype_passes'],r)
                self.assertFalse(r['build_ready'])
                self.assertEqual(r['clearance']['conflict_count'],0)
                self.assertGreaterEqual(r['kinematics']['mu1_min_deg'],40)
                self.assertGreaterEqual(r['kinematics']['mu2_min_deg'],40)
                if kind=='direct':
                    body=r['hardware']['body_envelope']
                    self.assertLessEqual(body['width_mm'],76)
                    self.assertLessEqual(body['height_mm'],80)
                    self.assertLessEqual(body['depth_mm'],80)
                    self.assertEqual(r['clearance']['belt_count'],1)

    def test_body_cover_is_audited_not_only_cosmetic(self):
        from rmd import direct_drive as direct,compact_drive as compact
        from rmd.designs import get_direct
        v,ba,be,_=get_direct(allow_fit=False)
        cfg=direct.settings();cfg['audit_samples']=90
        cfg['body_cover']=dict(cfg['body_cover'],plane_x_mm=cfg['front_crank_plane_x_mm'])
        d,b1,b2,_=load_design()
        with patch.object(direct,'settings',return_value=cfg):
            r=compact.audit(d,b1,b2,cfg,geometry_fn=lambda d,s,c:direct.geometry(v,ba,be,s['thetas']),gear_specs_fn=direct.gears)
        self.assertEqual(r['status'],'FAIL')
        self.assertTrue(any(any('body_cover/' in n for n in x['parts']) for x in r['conflicts']))

if __name__=='__main__':unittest.main()
