from __future__ import absolute_import, print_function, division

import numpy as np


#import math,cmath
from math import cos, sin
from numba import jit

import numba as nb


from dtmm.conf import NCDTYPE, NFDTYPE, CDTYPE, FDTYPE, UDTYPE,NUMBA_TARGET, NUMBA_CACHE, NUMBA_FASTMATH


def _check_matrix(mat, shape, dtype):
    if not (mat.shape == shape and mat.dtype == dtype):
        raise TypeError('Input matrix must be a numpy array of shape %s and %s dtype' % (shape, dtype))     

def _output_matrix(mat, shape, dtype):
    if mat is None:
        mat = np.empty(shape, dtype = dtype)
    else:
        _check_matrix(mat, shape,dtype)
    return mat

def _input_matrix(mat, shape, dtype):
    if not isinstance(mat, np.ndarray):
        mat = np.array(mat, dtype = dtype)  
    else:  
        _check_matrix(mat, shape, dtype)
    return mat


def rotation_matrix(yaw,theta,phi, output = None):
    """
    Calculates complete rotation matrix for rotations yaw, theta, phi.
    If output is specified.. it should be 3x3 float matrix
    
    >>> a = rotation_matrix(0.12,0.245,0.78)
    
    The same can be obtained by:
        
    >>> Ry = rotation_matrix_z(0.12)
    >>> Rt = rotation_matrix_y(0.245)
    >>> Rf = rotation_matrix_z(0.78)
      
    >>> b = np.dot(Rf,np.dot(Rt,Ry))
    >>> np.allclose(a,b)
    True
    """
    output = _output_matrix(output,(3,3),FDTYPE)
    _rotation_matrix(yaw,theta,phi,output)
    return output

@nb.njit([(NFDTYPE,NFDTYPE[:])], cache = NUMBA_CACHE, fastmath = NUMBA_FASTMATH)
def _rotation_vector2(angle, out):
    c = np.cos(angle)
    s = np.sin(angle)
    out[0] = c
    out[1] = s

@nb.njit([(NFDTYPE,NFDTYPE[:,:])], cache = NUMBA_CACHE, fastmath = NUMBA_FASTMATH)
def _rotation_matrix2(angle, out):
    c = np.cos(angle)
    s = np.sin(angle)
    out[0,0] = c
    out[1,0] = s
    out[0,1] = -s
    out[1,1] = c 
    
@nb.guvectorize([(NFDTYPE[:],NFDTYPE[:],NFDTYPE[:,:])], "(),(n)->(n,n)", 
                 target = NUMBA_TARGET, cache = NUMBA_CACHE, fastmath = NUMBA_FASTMATH)
def _rotation_matrix2_vec(angle,dummy, out):
    _rotation_matrix2(angle[0], out)
    
@nb.guvectorize([(NFDTYPE[:],NFDTYPE[:],NFDTYPE[:])], "(),(n)->(n)", 
                 target = NUMBA_TARGET, cache = NUMBA_CACHE, fastmath = NUMBA_FASTMATH)
def _rotation_vector2_vec(angle,dummy, out):
    _rotation_vector2(angle[0], out)

_dummy_array = np.empty(shape = (2,), dtype = FDTYPE)

def rotation_matrix2(angle, out = None):
    return _rotation_matrix2_vec(angle,_dummy_array, out)

def rotation_vector2(angle, out = None):
    return _rotation_vector2_vec(angle,_dummy_array, out)

def rotation_matrix_z(angle):
    return np.array([[cos(angle),-sin(angle),0],[sin(angle),cos(angle),0],[0,0,1.]])  

def rotation_matrix_y(angle):
    return np.array([[cos(angle),0,-sin(angle)],[0,1.,0.],[sin(angle),0,cos(angle)]])       
 
           
@jit([NFDTYPE[:,:](NFDTYPE,NFDTYPE,NFDTYPE,NFDTYPE[:,:])],nopython = True, cache = NUMBA_CACHE, fastmath = NUMBA_FASTMATH) 
def _rotation_matrix(yaw,theta,phi, R):
    """Fills rotation matrix values R = Rphi.Rtheta.Ryaw, where rphi and Ryaw are 
    rotations around y and Rtheta around z axis. 
    """
    cosyaw = cos(yaw)
    sinyaw = sin(yaw)
    costheta = cos(theta)
    sintheta = sin(theta)
    cosphi = cos(phi)
    sinphi = sin(phi)

    sinphi_sinyaw = sinphi * sinyaw
    sinphi_cosyaw = sinphi * cosyaw    

    cosphi_sinyaw = cosphi * sinyaw
    cosphi_cosyaw = cosphi * cosyaw
    
    R[0,0] = costheta * cosphi_cosyaw - sinphi_sinyaw
    R[0,1] = - costheta * cosphi_sinyaw - sinphi_cosyaw
    R[0,2] = - cosphi * sintheta
    R[1,0] = costheta * sinphi_cosyaw + cosphi_sinyaw
    R[1,1] = cosphi_cosyaw - costheta * sinphi_sinyaw
    R[1,2] = - sintheta * sinphi
    R[2,0] = cosyaw * sintheta
    R[2,1] = -sintheta*sinyaw
    R[2,2] = costheta
    
    return R  

def rotation_matrix_uniaxial(theta,phi, output = None):
    """
    Calculates rotation matrix for rotations  theta, phi.
    If output is specified.. it should be 3x3 float matrix
    
    >>> a = rotation_matrix_uniaxial(0.245,0.78)
    
    The same can be obtained by:
        
    >>> Rt = rotation_matrix_y(0.245)
    >>> Rf = rotation_matrix_z(0.78)
      
    >>> b = np.dot(Rf,Rt)
    >>> np.allclose(a,b)
    True
    """
    output = _output_matrix(output,(3,3),FDTYPE)
    _rotation_matrix_uniaxial(theta,phi,output)
    return output

@jit([NFDTYPE[:,:](NFDTYPE,NFDTYPE,NFDTYPE[:,:])],nopython = True, cache = NUMBA_CACHE, fastmath = NUMBA_FASTMATH) 
def _rotation_matrix_uniaxial(theta,phi, R):
    """Fills rotation matrix values R = Rphi.Rtheta, where rphiis
    rotations around y and Rtheta around z axis. 
    """
    costheta = cos(theta)
    sintheta = sin(theta)
    cosphi = cos(phi)
    sinphi = sin(phi)
 
    R[0,0] = costheta * cosphi
    R[0,1] =  - sinphi 
    R[0,2] = - cosphi * sintheta
    R[1,0] = costheta * sinphi  
    R[1,1] = cosphi
    R[1,2] = - sintheta * sinphi
    R[2,0] = sintheta
    R[2,1] = 0.
    R[2,2] = costheta
    
    return R  

def rotate_diagonal_tensor(R,diagonal,output = None):
    """Rotates a diagonal tensor, based on the rotation matrix provided
    
    >>> R = rotation_matrix(0.12,0.245,0.78)
    >>> diag = np.array([1.3,1.4,1.5], dtype = 'complex')
    >>> tensor = rotate_diagonal_tensor(R, diag)
    >>> matrix = tensor_to_matrix(tensor)
    
    The same can be obtained by:

    >>> Ry = rotation_matrix_z(0.12)
    >>> Rt = rotation_matrix_y(0.245)
    >>> Rf = rotation_matrix_z(0.78)   
    >>> R = np.dot(Rf,np.dot(Rt,Ry)) 
    
    >>> diag = np.diag([1.3,1.4,1.5]) + 0j
    >>> matrix2 = np.dot(R,np.dot(diag, R.transpose()))
    
    >>> np.allclose(matrix2,matrix)
    True
    """
    output = _output_matrix(output,(6,),CDTYPE)
    diagonal = _input_matrix(diagonal, (3,), CDTYPE)
    R = _input_matrix(R,(3,3),FDTYPE)
    _rotate_diagonal_tensor(R,diagonal,output)
    return output 
        
@jit([NCDTYPE[:,:](NFDTYPE[:,:],NCDTYPE[:],NCDTYPE[:,:])],nopython = True, cache = NUMBA_CACHE, fastmath = NUMBA_FASTMATH)
def _rotate_diagonal_tensor(R,diagonal,out):
    """Calculates out = R.diagonal.RT of a diagonal tensor"""
    for i in range(3):
        out[i] = diagonal[0]*R[i,0]*R[i,0] + diagonal[1]*R[i,1]*R[i,1] + diagonal[2]*R[i,2]*R[i,2]
    out[3] = diagonal[0]*R[0,0]*R[1,0] + diagonal[1]*R[0,1]*R[1,1] + diagonal[2]*R[0,2]*R[1,2]
    out[4] = diagonal[0]*R[0,0]*R[2,0] + diagonal[1]*R[0,1]*R[2,1] + diagonal[2]*R[0,2]*R[2,2]          
    out[5] = diagonal[0]*R[1,0]*R[2,0] + diagonal[1]*R[1,1]*R[2,1] + diagonal[2]*R[1,2]*R[2,2]
    return out
    
def tensor_to_matrix(tensor, output = None):
    """Converts tensor of shape (6,) to matrix of shape (3,3)
    """
    output = _output_matrix(output,(3,3),CDTYPE)
    tensor = _input_matrix(tensor,(6,),CDTYPE)
    _tensor_to_matrix(tensor, output)
    return output

def diagional_tensor_to_matrix(tensor, output = None):
    """Converts tensor of shape (3,) to matrix of shape (3,3)
    """
    output = _output_matrix(output,(3,3),CDTYPE)
    tensor = _input_matrix(tensor,(3,),CDTYPE)
    _diagonal_tensor_to_matrix(tensor, output)
    return output

@jit([NCDTYPE[:,:](NCDTYPE[:],NCDTYPE[:,:])],nopython = True, cache = NUMBA_CACHE, fastmath = NUMBA_FASTMATH)
def _tensor_to_matrix(tensor, matrix):
    matrix[0,0] = tensor[0]
    matrix[1,1] = tensor[1]
    matrix[2,2] = tensor[2]
    matrix[0,1] = tensor[3]
    matrix[1,0] = tensor[3]
    matrix[0,2] = tensor[4]
    matrix[2,0] = tensor[4]
    matrix[1,2] = tensor[5]
    matrix[2,1] = tensor[5]
    return matrix

@jit([NCDTYPE[:,:](NCDTYPE[:],NCDTYPE[:,:])],nopython = True, cache = NUMBA_CACHE, fastmath = NUMBA_FASTMATH)
def _diagonal_tensor_to_matrix(tensor, matrix):
    matrix[0,0] = tensor[0]
    matrix[1,1] = tensor[1]
    matrix[2,2] = tensor[2]
    matrix[0,1] = 0.
    matrix[1,0] = 0.
    matrix[0,2] = 0.
    matrix[2,0] = 0.
    matrix[1,2] = 0.
    matrix[2,1] = 0.
    return matrix

@jit([NFDTYPE[:,:](NFDTYPE,NFDTYPE[:],NFDTYPE[:,:])],nopython = True, cache = NUMBA_CACHE, fastmath = NUMBA_FASTMATH) 
def _calc_rotations_uniaxial(phi0,element,R):
    theta = element[1]
    phi = element[2] -phi0
    _rotation_matrix_uniaxial(theta,phi, R)
    return R    

@jit([NFDTYPE[:,:](NFDTYPE,NFDTYPE[:,:])],nopython = True, cache = NUMBA_CACHE, fastmath = NUMBA_FASTMATH) 
def _calc_rotations_isotropic(phi0,R):
    theta = np.pi/2
    #theta = 0.
    phi = -phi0
    _rotation_matrix_uniaxial(theta,phi, R)
    return R  

@jit([NFDTYPE[:,:](NFDTYPE,NFDTYPE[:],NFDTYPE[:,:])],nopython = True, cache = NUMBA_CACHE, fastmath = NUMBA_FASTMATH) 
def _calc_rotations(phi0,element,R):
    yaw = 0
    theta = element[1]
    phi = element[2] -phi0
    _rotation_matrix(yaw,theta,phi, R)
    return R      