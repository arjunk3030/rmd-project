"""Movies/posters use exactly the same per-design frames as the browser viewer."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation,FFMpegWriter,PillowWriter,writers
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def box_faces(box):
    c=np.array(box['center']);h=np.array(box['size'])/2
    p=np.array([c+[x*h[0],y*h[1],z*h[2]] for x in (-1,1) for y in (-1,1) for z in (-1,1)])
    return [p[i] for i in ([0,1,3,2],[4,5,7,6],[0,1,5,4],[2,3,7,6],[0,2,6,4],[1,3,7,5])]


def draw_frame(ax,frame,meta):
    ax.clear()
    bat=meta.get('bat_preview',False)
    for b in ([] if bat else meta['boxes']+meta['plates']):ax.add_collection3d(Poly3DCollection(box_faces(b),facecolor='slategray',edgecolor='gray',alpha=.12,linewidth=.4))
    for n,q in frame['panels'].items():ax.add_collection3d(Poly3DCollection([q],facecolor=('#342a39' if 'inner' in n else '#443347') if bat else ('teal' if 'inner' in n else 'tan'),alpha=1 if bat else .5,edgecolor='black',linewidth=.4))
    for p in frame['parts']:
        n=p['name']
        if bat and not ('spar' in n or '_finger_' in n):continue
        color='#c2aa82' if '_finger_' in n else '#e8ecf1' if 'spar' in n else '#438bff' if 'crank1' in n or 'coupler1' in n or (meta.get('integrated_crank') and 'crank2' in n) else '#17becf' if 'rocker1' in n else '#ff8c1a' if 'crank2' in n or 'rod2' in n else '#ef5959' if 'horn' in n else '#9faab6'
        ax.plot(*zip(p['p'],p['q']),color='#806675' if bat else color,lw=2 if 'pin_' not in n else .8)
    for p in frame['parts']:
        if not bat and p['name'].endswith('_pulley'):
            c=(np.array(p['p'])+p['q'])/2;t=np.linspace(0,2*np.pi,80);q=np.column_stack((np.full(80,c[0]),c[1]+p['radius']*np.cos(t),c[2]+p['radius']*np.sin(t)))
            ax.add_collection3d(Poly3DCollection([q],facecolor='gray',edgecolor='black',linewidth=.3))
    for face in ([] if bat else frame.get('rigid_faces',[])):
        rgba=[float(v) for v in face['color'].removeprefix('rgba(').removesuffix(')').split(',')]
        ax.add_collection3d(Poly3DCollection([face['points']],facecolor=tuple(v/255 for v in rgba[:3]),alpha=rgba[3]))
    for g in ([] if bat else frame['gears']):
        profile=np.array(meta['gear_profiles'][g['profile']]);c=g['center'];ca,sa=np.cos(g['phase']),np.sin(g['phase']);m=g['mirror']
        pts=np.column_stack((np.full(len(profile),c[0]),c[1]+m*(profile[:,0]*ca-profile[:,1]*sa),c[2]+profile[:,0]*sa+profile[:,1]*ca))
        ax.add_collection3d(Poly3DCollection([pts],facecolor='steelblue',alpha=.7,edgecolor='navy',linewidth=.3))
    low,high=np.array(meta['bounds_min']),np.array(meta['bounds_max'])
    ax.set_xlim(low[0],high[0]);ax.set_ylim(low[1],high[1]);ax.set_zlim(low[2],high[2]);ax.set_box_aspect(high-low,zoom=1.6)
    ax.view_init(elev=25,azim=-170)
    ax.set_axis_off()
    if bat:
        ax.computed_zorder=False
        for i,face in enumerate(meta['costume']):
            ax.add_collection3d(Poly3DCollection([face['points']],facecolor=face['color'],edgecolor='none',zorder=101 if i>=20 else 100 if i==0 else 99))


def video(frames,meta,out):
    fig=plt.figure(figsize=(11,7));ax=fig.add_subplot(111,projection='3d')
    anim=FuncAnimation(fig,lambda i:draw_frame(ax,frames[i],meta),frames=len(frames))
    if writers.is_available('ffmpeg'):anim.save(out/'wing_3d.mp4',writer=FFMpegWriter(fps=len(frames)/meta['cycle_seconds'],bitrate=2400))
    else:anim.save(out/'wing_3d.gif',writer=PillowWriter(fps=len(frames)/meta['cycle_seconds']))
    plt.close(fig);print('Wrote movie:',out)
