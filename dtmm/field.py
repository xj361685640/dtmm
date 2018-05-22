# -*- coding: utf-8 -*-
"""


"""

from __future__ import absolute_import, print_function, division

import numpy as np

from dtmm.conf import NCDTYPE,NFDTYPE, FDTYPE, CDTYPE, NUMBA_PARALLEL, NUMBA_CACHE, BETAMAX
from dtmm.wave import planewave
from dtmm.diffract import diffracted_field

import numba as nb
from numba import prange

if NUMBA_PARALLEL == False:
    prange = range
    
sqrt = np.sqrt

def illumination_betaphi(NA, nrays = 13):
    """Returns beta, phi values for illumination.
    
    This function can be used to define beta and phi arrays that can be used to
    construct illumination data with the :func:`illumination_data` function.
    The resulting beta,phi parameters define directions of rays for the input 
    light with a homogeneous angular distribution of rays - input
    light with a given numerical aperture.
    
    Parameters
    ----------
    NA : float
        Approximate numerical aperture of the illumination.
    nrays : int, optional
        Approximate number of rays. 
        
    Returns
    -------
    array, array
        beta, phi arrays 
        
    """
    radius = (nrays/np.pi)**0.5
    shape = (1+2*int(radius),1+2*int(radius))
    ay, ax = [np.arange(-l // 2 + 1., l // 2 + 1.) for l in shape]
    xx, yy = np.meshgrid(ax, ay,copy = False, indexing = "xy") 
    phi = np.arctan2(yy,xx)
    beta = np.sqrt(xx**2 + yy**2)/radius*NA
    mask = (beta <= NA)
    return beta[mask], phi[mask]

def illumination_waves(shape, k0, beta = 0., phi = 0., window = None, out = None):
    """Builds scalar illumination wave. 
    """
    k0 = np.asarray(k0)
    beta = np.asarray(beta)[...,np.newaxis]
    phi = np.asarray(phi)[...,np.newaxis]
    if not k0.ndim in (0,1):
        raise ValueError("k0, must be an array with dimesion 1")
    out = planewave(shape, k0, beta, phi, out)
    if window is None:
        return out
    else:
        return np.multiply(out, window, out = out)
    
def waves2field(waves, k0, beta = 0., phi = 0., n = 1., focus = 0., jones = None, mode = "t", betamax = BETAMAX):
    """Converts scalar waves to vector field data."""
    beta = np.asarray(beta)
    phi = np.asarray(phi)
    k0 = np.asarray(k0)
    nrays = 1
    if jones is None:
        nrays = 2
    if beta.ndim == 1:
        nrays = len(beta)*nrays
        
    waves = waves/(nrays**0.5)   
        
    if jones is None:
        fieldv = np.zeros(beta.shape + (2,) + k0.shape + (4,) + waves.shape[-2:], dtype = CDTYPE)
    else:
        c,s = jones
        fieldv = np.zeros(beta.shape + k0.shape + (4,) + waves.shape[-2:], dtype = CDTYPE)
    
    if beta.ndim == 1: 
        for i,data in enumerate(fieldv):
            if jones is None:
                data[0,...,0,:,:] = waves[i]
                data[0,...,1,:,:] = waves[i]
                
                data[1,...,2,:,:] = waves[i]
                data[1,...,3,:,:] = -waves[i]
            else:
                data[...,0,:,:] = waves[i]*c
                data[...,1,:,:] = waves[i]*c
                data[...,2,:,:] = waves[i]*s
                data[...,3,:,:] = -waves[i]*s
                
    else:
        if jones is None:
            fieldv[0,...,0,:,:] = waves
            fieldv[0,...,1,:,:] = waves
            
            fieldv[1,...,2,:,:] = waves
            fieldv[1,...,3,:,:] = -waves
        else:
            fieldv[...,0,:,:] = waves*c
            fieldv[...,1,:,:] = waves*c
            fieldv[...,2,:,:] = waves*s
            fieldv[...,3,:,:] = -waves*s    
            
    return diffracted_field(fieldv,k0, d = -focus, n = n, mode = mode, betamax = betamax)


def illumination_data(shape, wavelengths, pixelsize = 1., beta = 0., phi = 0., 
                      n = 1., focus = 0., window = None, backdir = False, 
                      jones = None, betamax = 0.9):
    """Constructs forward (or backward) propagating input illumination field data.
    
    Parameters
    ----------
    shape : (int,int)
        Shape of the illumination
    wavelengths : array_like
        A list of wavelengths.
    pixelsize : float, optional
        Size of the pixel in nm.
    beta : float or array_like of floats, optional
        Beta parameter(s) of the illumination. (Default 0. - normal incidence) 
    phi : float or array_like of floats, optional
        Azimuthal angle(s) of the illumination. 
    n : float, optional
        Refractive index of the media that this illumination field is assumed to
        be propagating in (default 1.)
    focus : float, optional
        Focal plane of the field. By default it is set at z=0. 
    window : array or None, optional
        If None, no window function is applied. This window function
        is multiplied with the constructed plane waves to define field diafragm
        of the input light. See :func:`.window.aperture`.
    backdir : bool, optional
        Whether field is bacward propagating, instead of being forward
        propagating (default)
    jones : jones vector or None, optional
        If specified it has to be a valid jones vector that defines polarization
        of the light. If not given (default), the resulting field will have two
        polarization components. See documentation for details and examples.
    betamax : float, optional
        The betamax parameter of the propagating field.
    """
    wavelengths = np.asarray(wavelengths)
    wavenumbers = 2*np.pi/wavelengths * pixelsize
    if wavenumbers.ndim not in (1,):
        raise ValueError("Wavelengths should be 1D array")
    waves = illumination_waves(shape, wavenumbers, beta = beta, phi = phi, window = window)
    mode = "r" if backdir else "t"
    field = waves2field(waves, wavenumbers, beta = beta, phi = phi, n = n,
                        focus = focus, jones = jones, mode = mode, betamax = betamax)
    
    return (field, wavelengths, pixelsize)


def jonesvec(pol):
    """Returns normalized jones vector from an input length 2 vector. 
    Numpy broadcasting rules apply.
    
    Example
    -------
    
    >>> jonesvec((1,1j)) #left-handed circuar polarization
    array([ 0.70710678+0.j        ,  0.00000000+0.70710678j])
    
    """
    pol = np.asarray(pol)
    assert pol.shape[-1] == 2
    norm = (pol[...,0] * pol[...,0].conj() + pol[...,1] * pol[...,1].conj())**0.5
    return pol/norm[...,np.newaxis]

@nb.njit([(NCDTYPE[:,:,:],NFDTYPE[:,:])], parallel = NUMBA_PARALLEL, cache = NUMBA_CACHE)
def _field2intensity(field, out):
    for j in range(field.shape[1]):
        for k in range(field.shape[2]):
            tmp1 = (field[0,j,k].real * field[1,j,k].real + field[0,j,k].imag * field[1,j,k].imag)
            tmp2 = (field[2,j,k].real * field[3,j,k].real + field[2,j,k].imag * field[3,j,k].imag)
            out[j,k] = tmp1-tmp2 

@nb.guvectorize([(NCDTYPE[:,:,:],NFDTYPE[:,:])],"(k,n,m)->(n,m)", target = "parallel", cache = NUMBA_CACHE)
def field2intensity(field, out):
    """field2intensity(field)
    
Converts field array of shape [...,4,height,width] to specter array
of shape [...,height,width]. For each pixel element, a normal
component of Poynting vector is computed.
    
Parameters
----------
field : array_like
    Input field array
cmf : array_like
    Color matching function
    
Returns
-------
spec : ndarray
    Computed intensity array"""  
    _field2intensity(field, out)

@nb.njit([(NCDTYPE[:,:,:,:],NFDTYPE[:,:,:])], parallel = NUMBA_PARALLEL, cache = NUMBA_CACHE)
def _field2specter(field, out):     
    for j in prange(field.shape[2]):
        for i in range(field.shape[0]):
            for k in range(field.shape[3]):
                tmp1 = (field[i,0,j,k].real * field[i,1,j,k].real + field[i,0,j,k].imag * field[i,1,j,k].imag)
                tmp2 = (field[i,2,j,k].real * field[i,3,j,k].real + field[i,2,j,k].imag * field[i,3,j,k].imag)
                out[j,k,i] = tmp1-tmp2 

@nb.njit([(NCDTYPE[:,:,:,:,:],NFDTYPE[:,:,:])], parallel = NUMBA_PARALLEL, cache = NUMBA_CACHE)
def _field2spectersum(field, out):
    for n in prange(field.shape[0]):
        for j in range(field.shape[3]):
            for i in range(field.shape[1]):
                for k in range(field.shape[4]):
                    tmp1 = (field[n,i,0,j,k].real * field[n,i,1,j,k].real + field[n,i,0,j,k].imag * field[n,i,1,j,k].imag)
                    tmp2 = (field[n,i,2,j,k].real * field[n,i,3,j,k].real + field[n,i,2,j,k].imag * field[n,i,3,j,k].imag)
                    if n == 0:
                        out[j,k,i] = tmp1 - tmp2
                    else:
                        out[j,k,i] += (tmp1 -tmp2)

@nb.guvectorize([(NCDTYPE[:,:,:,:],NFDTYPE[:,:,:])],"(w,k,n,m)->(n,m,w)", target = "cpu", cache = NUMBA_CACHE)
def field2specter(field, out):
    """field2specter(field)
    
Converts field array of shape [...,nwavelengths,4,height,width] to specter array
of shape [...,height,width,nwavelengths]. For each pixel element, a normal
componentof Poynting vector is computed
    
Parameters
----------
field : array_like
    Input field array
cmf : array_like
    Color matching function
    
Returns
-------
spec : ndarray
    Computed specter array""" 
    _field2specter(field, out)

@nb.guvectorize([(NCDTYPE[:,:,:,:,:],NFDTYPE[:,:,:])],"(l,w,k,n,m)->(n,m,w)", target = "cpu", cache = NUMBA_CACHE)
def field2spectersum(field, out):
    _field2spectersum(field, out)    

def validate_field_data(data):
    """Validates field data.
    
    This function inspects validity of the field data, and makes proper data
    conversions to match the field data format. In case data is not valid and 
    it cannot be converted to a valid data it raises an exception (ValueError). 
    
    Parameters
    ----------
    data : tuple of field data
        A valid field data tuple.
    
    Returns
    -------
    data : tuple
        Validated field data tuple. 
    """
    field, wavelengths, pixelsize = data
    field = np.asarray(field, dtype = CDTYPE)
    wavelengths = np.asarray(wavelengths, dtype = FDTYPE)
    pixelsize = float(pixelsize)
    if field.ndim < 4:
        raise ValueError("Invald field dimensions")
    if field.shape[-4] != len(wavelengths) or wavelengths.ndim != 1:
        raise ValueError("Incompatible wavelengths shape.")

    return field, wavelengths, pixelsize


MAGIC = b"dtmf" #legth 4 magic number for file ID
VERSION = b"\x00"

def save_field(file, field_data):
    """Saves field data to a binary file in ``.dtmf`` format.
    
    Parameters
    ----------
    file : file, str, or pathlib.Path
        File or filename to which the data is saved.  If file is a file-object,
        then the filename is unchanged.  If file is a string, a ``.dtmf``
        extension will be appended to the file name if it does not already
        have one.
    field_data: (field,wavelengths,pixelsize)
        A valid field data tuple
    
    """    
    own_fid = False
    field, wavelengths,pixelsize = validate_field_data(field_data)
    try:
        if isinstance(file, str):
            if not file.endswith('.dtmf'):
                file = file + '.dtmf'
            f = open(file, "wb")
            own_fid = True
        else:
            f = file
        f.write(MAGIC)
        f.write(VERSION)
        np.save(f,field)
        np.save(f,wavelengths)
        np.save(f,pixelsize)
    finally:
        if own_fid == True:
            f.close()


def load_field(file):
    """Load field data from file
    
    Parameters
    ----------
    file : file, str
        The file or filenam to read.
    """
    own_fid = False
    try:
        if isinstance(file, str):
            f = open(file, "rb")
            own_fid = True
        else:
            f = file
        magic = f.read(len(MAGIC))
        if magic == MAGIC:
            if f.read(1) != VERSION:
                raise OSError("This file was created with a more recent version of dtmm. Please upgrade your dtmm package!".format(file))
            field = np.load(f)
            wavelengths = np.load(f)
            pixelsize = float(np.load(f))
            return field, wavelengths, pixelsize
        else:
            raise OSError("Failed to interpret file {}".format(file))
    finally:
        if own_fid == True:
            f.close()
    
__all__ = ["load_field", "save_field", "validate_field_data", "jonesvec","field2specter","field2intensity", "illumination_data","illumination_betaphi"]