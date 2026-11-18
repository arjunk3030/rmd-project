"""Self-contained 3D viewer, shared by the compact geared and direct designs."""
import json
from pathlib import Path

HTML=(Path(__file__).parent/'templates/viewer.html').read_text()


def write_viewer(frames,meta,dimensions,audit,path,*,generate_related=True):
    from .config import CONFIG_DIR
    from copy import deepcopy
    display=json.loads((CONFIG_DIR/'presentation/display.json').read_text())
    original_frames,original_meta,original_dimensions=deepcopy(frames),deepcopy(meta),deepcopy(dimensions)
    meta=dict(meta,cycle_seconds=display['cycle_seconds'])
    if path.name in ('direct_3d.html','single_face_3d.html'):
        from .top_drive import apply
        frames,meta,dimensions=apply(frames,meta,dimensions)
    if meta.get('design_id')=='direct' and not meta.get('bat_preview'):
        meta['other_viewer']='direct_3d.html' if meta.get('integrated_crank') else 'single_face_3d.html'
    html=HTML.replace("/* MOCKUP_GEOMETRY */", (Path(__file__).parent/"templates/mockup_geometry.js").read_text() if meta.get("mockup") else "")
    if meta.get('mockup'):
        start=html.index('<h2>How to read it</h2>');end=html.index('<h2>Dimensions / limits</h2>',start)
        settings=meta.get('mockup_settings',{})
        wing='separate strips · rigid connections required' if settings.get('separate_strips') else 'rigid inner-wing frame &amp; outer spar' if settings.get('frame_wing') else 'inner-wing triangle &amp; outer spar'
        note=('<div>Concept only: rigid connectors, bearings and strip clearances are not designed or validated. Strip offsets are illustrative.</div>' if settings.get('separate_strips') else '<div>Frame members are rigidly connected; they are not separate pivots. Clearance and strength are unverified.</div>' if settings.get('frame_wing') else '')
        collision='' if meta.get('split_mockup') else '<div style="color:#ff4f58">'+('Red · bridge intersects blue elbow coupler and D screw' if meta.get('mockup_bridge') else 'Red · A–B coupler (intersects gray D screw)')+'</div>'
        html=html[:start]+'<h2>Legend</h2><div style="color:#ffe23b">Yellow · '+wing+'</div><div style="color:#438bff">Blue · printed linkage</div>'+collision+note+html[end:]

    for key,value in [('DATA',frames),('META',meta),('DIMS',dimensions),('AUDIT',audit)]:
        html=html.replace('__'+key+'__',json.dumps(value,allow_nan=False))
    path.write_text(html)
    print('Wrote',path)

    if path.name == 'direct_3d.html' and generate_related:
        from .linkage2d import write_linkage_viewer
        write_linkage_viewer(frames,path.with_name('direct_2d.html'))
        from .bat_preview import appearance
        themed = dict(original_meta, bat_preview=True, scale_reference=False, costume=appearance(),
                      name='Bat costume — appearance preview', other_viewer='direct_3d.html',
                      description='Same solved wing motion, with a playful full-body costume and dark fabric. The decorative silhouette is an appearance study: its mounts and clearances are not validated. Show frame & motor to inspect the drive inside. Wings retain their actual panel geometry.')
        write_viewer(original_frames,themed,original_dimensions,audit,path.with_name('bat_3d.html'))
