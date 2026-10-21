"""Shared geometric predicates used by both compact design clearance audits."""
import itertools
import numpy as np
from . import model
from .config import FIXED, BUILD


def segment_distance(p, q, a, b):
    """Vectorized exact distance between finite centerline segments."""
    u,v,w = q-p,b-a,p-a
    dot = lambda x,y: np.sum(x*y,axis=-1)
    aa,bb,cc,dd,ee = dot(u,u),dot(u,v),dot(v,v),dot(u,w),dot(v,w)
    den = aa*cc-bb*bb
    safe = np.where(abs(den)>1e-12,den,1.)
    s,t = (bb*ee-cc*dd)/safe,(aa*ee-bb*dd)/safe
    valid = (abs(den)>1e-12)&(s>=0)&(s<=1)&(t>=0)&(t<=1)
    interior = np.linalg.norm(w+s[...,None]*u-t[...,None]*v,axis=-1)
    def point_line(x,a,b):
        ab=b-a
        t=np.clip(dot(x-a,ab)/np.maximum(dot(ab,ab),1e-15),0,1)
        return np.linalg.norm(x-a-t[...,None]*ab,axis=-1)
    return np.minimum.reduce([np.where(valid,interior,np.inf),point_line(p,a,b),point_line(q,a,b),point_line(a,p,q),point_line(b,p,q)])


def _triangle_hit(p,q,a,b,c):
    direction=q-p; e1=b-a; e2=c-a
    h=np.cross(direction,e2); det=np.sum(e1*h,axis=-1)
    inv=1/np.where(abs(det)>1e-10,det,1.)
    s=p-a; u=inv*np.sum(s*h,axis=-1)
    r=np.cross(s,e1); v=inv*np.sum(direction*r,axis=-1)
    t=inv*np.sum(e2*r,axis=-1)
    return (abs(det)>1e-10)&(u>1e-6)&(v>1e-6)&(u+v<1-1e-6)&(t>1e-6)&(t<1-1e-6)



def point_triangle_distance(p,a,b,c):
    """Vectorized point/triangle distance, including boundary and degenerate cases."""
    ab=b-a;ac=c-a;normal=np.cross(ab,ac);n2=np.sum(normal*normal,axis=-1)
    signed=np.sum((p-a)*normal,axis=-1)/np.maximum(n2,1e-20)
    projection=p-signed[...,None]*normal;v=projection-a
    d00=np.sum(ab*ab,axis=-1);d01=np.sum(ab*ac,axis=-1);d11=np.sum(ac*ac,axis=-1)
    d20=np.sum(v*ab,axis=-1);d21=np.sum(v*ac,axis=-1);den=d00*d11-d01*d01
    u=(d11*d20-d01*d21)/np.maximum(den,1e-20);w=(d00*d21-d01*d20)/np.maximum(den,1e-20)
    inside=(n2>1e-16)&(u>=0)&(w>=0)&(u+w<=1)
    plane=np.abs(signed)*np.sqrt(n2)
    edges=np.minimum.reduce([segment_distance(p,p,a,b),segment_distance(p,p,b,c),segment_distance(p,p,c,a)])
    return np.where(inside,plane,edges)


def segment_triangle_distance(p,q,a,b,c):
    distance=np.minimum.reduce([point_triangle_distance(p,a,b,c),point_triangle_distance(q,a,b,c),
        segment_distance(p,q,a,b),segment_distance(p,q,b,c),segment_distance(p,q,c,a)])
    return np.where(_triangle_hit(p,q,a,b,c),0,distance)
