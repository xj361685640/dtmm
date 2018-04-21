#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 19 14:18:38 2018

@author: andrej
"""

import dtmm
import numpy as np
import matplotlib.pyplot as plt

betas = np.linspace(0.00,0.9999,100)
phi = 0*np.pi/2

n0 = 1.
n1 = 1.5

a,f,fi = dtmm.alphaffi_xy(betas,phi,[0,0.2,0.0],dtmm.refind2eps([n1,n1,n1]))
a0,f0,fi0 = dtmm.alphaffi_xy(betas,phi,[0,2.0,0.0],dtmm.refind2eps([n0,n0,n0]))

aiso,fiso,fiiso = dtmm.alphaffi_xy_iso(betas,phi,[0,0.,0.0],dtmm.refind2eps([n1,n1,n1]))
a0iso,f0iso,fi0iso = dtmm.alphaffi_xy_iso(betas,phi,[0,0.,0.0],dtmm.refind2eps([n0,n0,n0]))

dot = dtmm.linalg.dotmm
dotd = dtmm.linalg.dotmd

ad = dtmm.phasem(a,1)

m = dot(fi0iso,dot(dotd(f,ad),dot(fi,fiso)))

det = m[...,0,0]*m[...,2,2]-m[...,0,2]*m[...,2,0]

rpp = (m[...,1,0]*m[...,2,2]-m[...,1,2]*m[...,2,0])/det
rss = (m[...,0,0]*m[...,3,2]-m[...,0,2]*m[...,3,1])/det
tpp = m[...,2,2]/det
tss = m[...,0,0]/det

plt.plot(betas,rss)
plt.plot(betas,rpp)
