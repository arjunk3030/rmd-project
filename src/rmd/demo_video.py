"""Optional MP4 exports of the same embedded poses used by the offline demos."""
import json
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter, writers
from matplotlib.patches import Polygon
from .config import ROOT, OUTPUT_DIR
from .animate3d import draw_frame


def export(selection='all'):
    if not writers.is_available('ffmpeg'):
        raise RuntimeError('MP4 export needs ffmpeg on PATH. The HTML demos work without it.')
    display=json.loads((ROOT/'config/presentation/display.json').read_text())
    out=OUTPUT_DIR/'videos';out.mkdir(exist_ok=True)
    for name in (['direct','single_face','2d','bat'] if selection=='all' else [selection]):
        source=OUTPUT_DIR/('direct_2d.html' if name=='2d' else name+'_3d.html')
        if not source.exists():raise RuntimeError('Run python3 run_all.py demo first.')
        html=source.read_text();fig=plt.figure(figsize=(10,6),facecolor='#11151c')
        if name=='2d':
            frames=json.loads(re.search(r'const POSES=(.*);\n',html)[1]);ax=fig.add_subplot(111)
            def draw(i):
                ax.clear();ax.set_facecolor('#11151c');p=frames[i]['points']
                for names,color in [('OAD','#438bff'),('SBE','#17becf')]:
                    ax.add_patch(Polygon([p[n] for n in names],color=color,alpha=.2))
                for a,b,color in [('O','S','#9faab6'),('O','A','#438bff'),('O','D','#ff8c1a'),('A','B','#438bff'),('S','B','#17becf'),('S','E','#e8ecf1'),('D','Q','#ff8c1a'),('E','Q','#ef5959'),('E','T','#e8ecf1')]:
                    ax.plot(*zip(p[a],p[b]),color=color,lw=2)
                for n,(x,y) in p.items():ax.text(x+2,y-3,n,color='white',fontsize=10)
                ax.set(xlim=(-45,265),ylim=(150,-150),aspect='equal');ax.set_axis_off()
                ax.set_title('Stephenson six-bar · actual solved motion',color='white')
        else:
            match=re.search(r'const DATA=(.*),META=(.*),DIMS=(.*),AUDIT=(.*);\n',html)
            frames,meta=json.loads(match[1]),json.loads(match[2]);ax=fig.add_subplot(111,projection='3d');ax.set_facecolor('#11151c')
            def draw(i):
                draw_frame(ax,frames[i],meta)
                if name=='single_face':ax.set_title('Same-face packaging experiment · known interference',color='white',fontsize=12)
        draw(0);fig.savefig(out/(name+'.png'),dpi=display['video_dpi'])
        movie=FuncAnimation(fig,draw,frames=len(frames))
        movie.save(out/(name+'.mp4'),writer=FFMpegWriter(fps=len(frames)/display['cycle_seconds'],bitrate=display['video_bitrate_kbps']),dpi=display['video_dpi'])
        plt.close(fig);print('Wrote',out/(name+'.mp4'),flush=True)
