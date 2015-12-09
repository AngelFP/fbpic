"""
This file is part of the Fourier-Bessel Particle-In-Cell code (FB-PIC)
It defines the optimized fields methods that use cuda on a GPU
"""
from numbapro import cuda
from scipy.constants import c, epsilon_0, mu_0
c2 = c**2

# ------------------
# Erasing functions
# ------------------

@cuda.jit('void(complex128[:,:], complex128[:,:])')
def cuda_erase_scalar( mode0, mode1 ) :
    """
    Set the two input arrays to 0

    These arrays are typically interpolation grid arrays, and they
    are set to zero before depositing the currents

    Parameters :
    ------------
    mode0, mode1 : 2darrays of complexs
       Arrays that represent the fields on the grid
       (The first axis corresponds to z and the second axis to r) d
    """
    
    # Cuda 2D grid
    iz, ir = cuda.grid(2)

    # Set the elements of the array to 0
    if (iz < mode0.shape[0]) and (ir < mode0.shape[1]) :
        mode0[iz, ir] = 0
        mode1[iz, ir] = 0

@cuda.jit('void(complex128[:,:], complex128[:,:], \
                complex128[:,:], complex128[:,:], \
                complex128[:,:], complex128[:,:])')
def cuda_erase_vector(mode0r, mode1r, mode0t, mode1t, mode0z, mode1z) :
    """
    Set the two input arrays to 0

    These arrays are typically interpolation grid arrays, and they
    are set to zero before depositing the currents

    Parameters :
    ------------
    mode0r, mode1r, mode0t, mode1t, mode0z, mode1z : 2darrays of complexs
       Arrays that represent the fields on the grid
       (The first axis corresponds to z and the second axis to r)
    """
    
    # Cuda 2D grid
    iz, ir = cuda.grid(2)

    # Set the elements of the array to 0
    if (iz < mode0r.shape[0]) and (ir < mode0r.shape[1]) :
        mode0r[iz, ir] = 0
        mode0t[iz, ir] = 0
        mode0z[iz, ir] = 0
        mode1r[iz, ir] = 0
        mode1t[iz, ir] = 0
        mode1z[iz, ir] = 0

# ---------------------------
# Divide by volume functions
# ---------------------------
        
@cuda.jit('void(complex128[:,:], complex128[:,:], \
           float64[:], float64[:] )')
def cuda_divide_scalar_by_volume( mode0, mode1, invvol0, invvol1 ) :
    """
    Multiply the input arrays by the corresponding invvol

    Parameters :
    ------------
    mode0, mode1 : 2darrays of complexs
       Arrays that represent the fields on the grid
       (The first axis corresponds to z and the second axis to r)

    invvol0, invvol1 : 1darrays of floats
       Arrays that contain the inverse of the volume of the cell
       The axis corresponds to r
       
    Nz, Nr : ints
       The dimensions of the arrays
    """
    
    # Cuda 2D grid
    iz, ir = cuda.grid(2)

    # Multiply by inverse volume
    if (iz < mode0.shape[0]) and (ir < mode0.shape[1]) :
        mode0[iz, ir] = mode0[iz, ir] * invvol0[ir]
        mode1[iz, ir] = mode1[iz, ir] * invvol1[ir]

        
@cuda.jit('void(complex128[:,:], complex128[:,:], \
           complex128[:,:], complex128[:,:], \
           complex128[:,:], complex128[:,:], \
           float64[:], float64[:])')
def cuda_divide_vector_by_volume( mode0r, mode1r, mode0t, mode1t,
                    mode0z, mode1z, invvol0, invvol1 ) :
    """
    Multiply the input arrays by the corresponding invvol

    Parameters :
    ------------
    mode0r, mode1r, mode0t, mode1t, mode0z, mode1z : 2darrays of complexs
       Arrays that represent the fields on the grid
       (The first axis corresponds to z and the second axis to r)

    invvol0, invvol1 : 1darrays of floats
       Arrays that contain the inverse of the volume of the cell
       The axis corresponds to r

    Nz, Nr : ints
       The dimensions of the arrays
    """
    
    # Cuda 2D grid
    iz, ir = cuda.grid(2)

    # Multiply by inverse volume
    if (iz < mode0r.shape[0]) and (ir < mode0r.shape[1]) :
        mode0r[iz, ir] = mode0r[iz, ir] * invvol0[ir]
        mode0t[iz, ir] = mode0t[iz, ir] * invvol0[ir]
        mode0z[iz, ir] = mode0z[iz, ir] * invvol0[ir]
        mode1r[iz, ir] = mode1r[iz, ir] * invvol1[ir]
        mode1t[iz, ir] = mode1t[iz, ir] * invvol1[ir]
        mode1z[iz, ir] = mode1z[iz, ir] * invvol1[ir]

# -----------------------------------
# Methods of the SpectralGrid object
# -----------------------------------

@cuda.jit('void(complex128[:,:], complex128[:,:], \
           complex128[:,:], complex128[:,:], complex128[:,:], \
           float64[:,:], float64[:,:], float64[:,:], \
           complex128[:,:], complex128[:,:], \
           float64, int32, int32)')
def cuda_correct_currents( rho_prev, rho_next, Jp, Jm, Jz,
                            kz, kr, inv_k2, 
                            j_corr_coef, T,
                            inv_dt, Nz, Nr ) :
    """
    Correct the currents in spectral space

    Parameters :
    ------------
    rho_prev, rho_next, Jp, Jm, Jz : 2darrays of complex
        Fields in spectral space.
        
    kz, kr, inv_k2, j_corr_coef : 2darrays of reals
        Constant coefficients that depend on the spectral grid

    inv_dt : float
        Inverse of the timestep

    Nz, Nr : ints
        The dimensions of the arrays
    """
    
    # Cuda 2D grid
    iz, ir = cuda.grid(2)

    # Perform the current correction
    if (iz < Nz) and (ir < Nr) :
        
        # Calculate the intermediate variable F
        F = - inv_k2[iz, ir] * ( j_corr_coef[iz, ir] \
            * (rho_next[iz, ir] - rho_prev[iz, ir]*T[iz, ir]) \
            + 1.j*kz[iz, ir]*Jz[iz, ir] \
            + kr[iz, ir]*( Jp[iz, ir] - Jm[iz, ir] ) )

        # Correct the currents accordingly
        Jp[iz, ir] +=  0.5 * kr[iz, ir] * F
        Jm[iz, ir] += -0.5 * kr[iz, ir] * F
        Jz[iz, ir] += -1.j * kz[iz, ir] * F


@cuda.jit('void(complex128[:,:], complex128[:,:], complex128[:,:], \
           complex128[:,:], complex128[:,:], complex128[:,:], \
           complex128[:,:], complex128[:,:], complex128[:,:], \
           complex128[:,:], complex128[:,:], \
           complex128[:,:], complex128[:,:], complex128[:,:], \
           float64[:,:], float64[:,:], complex128[:,:], complex128[:,:], \
           float64[:,:], float64[:,:], float64, float64, \
           int8, int8, int32, int32)')
def cuda_push_eb_with( Ep, Em, Ez, Bp, Bm, Bz, Jp, Jm, Jz,
                       rho_prev, rho_next, 
                       rho_prev_coef, rho_next_coef, j_coef, 
                       C, S_w, T, T_rho,
                       kr, kz, dt, V, 
                       ptcl_feedback, use_true_rho, Nz, Nr) :
    """
    Push the fields over one timestep, using the psatd algorithm

    See the documentation of SpectralGrid.push_eb_with
    """
    
    # Cuda 2D grid
    iz, ir = cuda.grid(2)

    # Push the fields
    if (iz < Nz) and (ir < Nr) :

        # Save the electric fields, since it is needed for the B push
        Ep_old = Ep[iz, ir]
        Em_old = Em[iz, ir]
        Ez_old = Ez[iz, ir]

        # With particle feedback
        if ptcl_feedback :

            # Calculate useful auxiliary arrays
            if use_true_rho :
                # Evaluation using the rho projected on the grid
                rho_diff = rho_next_coef[iz, ir] * rho_next[iz, ir] \
                        - rho_prev_coef[iz, ir] * rho_prev[iz, ir]
            else :
                # Evaluation using div(E) and div(J)
                divE = kr[iz, ir]*( Ep[iz, ir] - Em[iz, ir] ) \
                    + 1.j*kz[iz, ir]*Ez[iz, ir]
                divJ = kr[iz, ir]*( Jp[iz, ir] - Jm[iz, ir] ) \
                    + 1.j*kz[iz, ir]*Jz[iz, ir]

                rho_diff = ( T[iz,ir] * rho_next_coef[iz, ir] \
                  - rho_prev_coef[iz, ir] ) \
                  * epsilon_0 * divE + T_rho[iz, ir] \
                  * rho_next_coef[iz, ir] * dt * divJ

            # Push the E field
            Ep[iz, ir] = \
                T[iz, ir]*C[iz, ir]*Ep[iz, ir] + 0.5*kr[iz, ir]*rho_diff \
                + j_coef[iz, ir]*1.j*kz[iz, ir]*V*Jp[iz, ir] \
                + c2*T[iz, ir]*S_w[iz, ir]*( -1.j*0.5*kr[iz, ir]*Bz[iz, ir] \
                + kz[iz, ir]*Bp[iz, ir] - mu_0*Jp[iz, ir] )

            Em[iz, ir] = \
                T[iz, ir]*C[iz, ir]*Em[iz, ir] - 0.5*kr[iz, ir]*rho_diff \
                + j_coef[iz, ir]*1.j*kz[iz, ir]*V*Jm[iz, ir] \
                + c2*T[iz, ir]*S_w[iz, ir]*( -1.j*0.5*kr[iz, ir]*Bz[iz, ir] \
                - kz[iz, ir]*Bm[iz, ir] - mu_0*Jm[iz, ir] )
                
            Ez[iz, ir] = \
                T[iz, ir]*C[iz, ir]*Ez[iz, ir] - 1.j*kz[iz, ir]*rho_diff \
                + j_coef[iz, ir]*1.j*kz[iz, ir]*V*Jz[iz, ir] \
                + c2*T[iz, ir]*S_w[iz, ir]*( 1.j*kr[iz, ir]*Bp[iz, ir] \
                + 1.j*kr[iz, ir]*Bm[iz, ir] - mu_0*Jz[iz, ir] )

            # Push the B field
            Bp[iz, ir] = T[iz, ir]*C[iz, ir]*Bp[iz, ir] \
                - T[iz, ir]*S_w[iz, ir]*( -1.j*0.5*kr[iz, ir]*Ez_old \
                            + kz[iz, ir]*Ep_old ) \
                + j_coef[iz, ir]*( -1.j*0.5*kr[iz, ir]*Jz[iz, ir] \
                            + kz[iz, ir]*Jp[iz, ir] )

            Bm[iz, ir] = T[iz, ir]*C[iz, ir]*Bm[iz, ir] \
                - T[iz, ir]*S_w[iz, ir]*( -1.j*0.5*kr[iz, ir]*Ez_old \
                            - kz[iz, ir]*Em_old ) \
                + j_coef[iz, ir]*( -1.j*0.5*kr[iz, ir]*Jz[iz, ir] \
                            - kz[iz, ir]*Jm[iz, ir] )

            Bz[iz, ir] = T[iz, ir]*C[iz, ir]*Bz[iz, ir] \
                - T[iz, ir]*S_w[iz, ir]*( 1.j*kr[iz, ir]*Ep_old \
                            + 1.j*kr[iz, ir]*Em_old ) \
                + j_coef[iz, ir]*( 1.j*kr[iz, ir]*Jp[iz, ir] \
                            + 1.j*kr[iz, ir]*Jm[iz, ir] )

        # Without particle feedback
        else :

            # Push the E field
            Ep[iz, ir] = T[iz, ir]*C[iz, ir]*Ep[iz, ir] \
                + c2*T[iz, ir]*S_w[iz, ir]*( -1.j*0.5*kr[iz, ir]*Bz[iz, ir] \
                + kz[iz, ir]*Bp[iz, ir] )

            Em[iz, ir] = T[iz, ir]*C[iz, ir]*Em[iz, ir]  \
                + c2*T[iz, ir]*S_w[iz, ir]*( -1.j*0.5*kr[iz, ir]*Bz[iz, ir] \
                - kz[iz, ir]*Bm[iz, ir] )
                
            Ez[iz, ir] = T[iz, ir]*C[iz, ir]*Ez[iz, ir]  \
                + c2*T[iz, ir]*S_w[iz, ir]*( 1.j*kr[iz, ir]*Bp[iz, ir] \
                + 1.j*kr[iz, ir]*Bm[iz, ir] )

            # Push the B field
            Bp[iz, ir] = T[iz, ir]*C[iz, ir]*Bp[iz, ir] \
                - T[iz, ir]*S_w[iz, ir]*( -1.j*0.5*kr[iz, ir]*Ez_old \
                            + kz[iz, ir]*Ep_old ) 

            Bm[iz, ir] = T[iz, ir]*C[iz, ir]*Bm[iz, ir] \
                - T[iz, ir]*S_w[iz, ir]*( -1.j*0.5*kr[iz, ir]*Ez_old \
                            - kz[iz, ir]*Em_old ) 

            Bz[iz, ir] = T[iz, ir]*C[iz, ir]*Bz[iz, ir] \
                - T[iz, ir]*S_w[iz, ir]*( 1.j*kr[iz, ir]*Ep_old \
                            + 1.j*kr[iz, ir]*Em_old )


@cuda.jit('void(complex128[:,:], complex128[:,:], int32, int32)')
def cuda_push_rho( rho_prev, rho_next, Nz, Nr ) :
    """
    Transfer the values of rho_next to rho_prev,
    and set rho_next to zero

    Parameters :
    ------------
    rho_prev, rho_next : 2darrays
        Arrays that represent rho in spectral space

    Nz, Nr : ints
        Dimensions of the arrays
    """
    
    # Cuda 2D grid
    iz, ir = cuda.grid(2)

    # Push the fields
    if (iz < Nz) and (ir < Nr) :

        rho_prev[iz, ir] = rho_next[iz, ir]
        rho_next[iz, ir] = 0.

@cuda.jit('void(complex128[:,:], float64[:,:], int32, int32)')
def cuda_filter_scalar( field, filter_array, Nz, Nr) :
    """
    Multiply the input field by the filter_array

    Parameters :
    ------------
    field : 2darray of complexs
        An array that represent the fields in spectral space

    filter_array : 2darray of reals
        An array that damps the fields at high k

    Nz, Nr : ints
        Dimensions of the arrays
    """
    
    # Cuda 2D grid
    iz, ir = cuda.grid(2)

    # Filter the field
    if (iz < Nz) and (ir < Nr) :

        field[iz, ir] = filter_array[iz, ir]*field[iz, ir]

@cuda.jit('void(complex128[:,:], complex128[:,:], complex128[:,:], \
           float64[:,:], int32, int32)')
def cuda_filter_vector( fieldr, fieldt, fieldz, filter_array, Nz, Nr) :
    """
    Multiply the input field by the filter_array

    Parameters :
    ------------
    field : 2darray of complexs
        An array that represent the fields in spectral space

    filter_array : 2darray of reals
        An array that damps the fields at high k

    Nz, Nr : ints
        Dimensions of the arrays
    """
    
    # Cuda 2D grid
    iz, ir = cuda.grid(2)

    # Filter the field
    if (iz < Nz) and (ir < Nr) :

        fieldr[iz, ir] = filter_array[iz, ir]*fieldr[iz, ir]
        fieldt[iz, ir] = filter_array[iz, ir]*fieldt[iz, ir]
        fieldz[iz, ir] = filter_array[iz, ir]*fieldz[iz, ir]
