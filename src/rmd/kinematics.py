"""Vector geometry shared by the two supported compact mechanisms."""
import numpy as np


def dirs(t):
    return np.column_stack((np.cos(t),np.sin(t)))


def intersection(center,radius,pins,rod,branch):
    """Fixed-side circle intersection; return points and squared toggle margin.

    Negative h² is reported, never accepted as assembled by the validator.
    Clipping here only gives the numerical optimizer finite trial residuals.
    """
    dv=pins-center;distance=np.linalg.norm(dv,axis=1)
    ex=dv/np.maximum(distance[:,None],1e-12)
    along=(radius*radius-rod*rod+distance*distance)/(2*np.maximum(distance,1e-12))
    h2=radius*radius-along*along
    q=center+along[:,None]*ex+branch*np.sqrt(np.maximum(h2,0))[:,None]*np.column_stack((-ex[:,1],ex[:,0]))
    return q,h2


def sine_angle(a,b):
    return abs(a[:,0]*b[:,1]-a[:,1]*b[:,0])/np.maximum(np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1),1e-12)


def effective_angle(a,b):
    return np.degrees(np.arcsin(np.clip(sine_angle(a,b),0,1)))
