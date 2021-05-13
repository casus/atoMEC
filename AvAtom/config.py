"""
65;6003;1cConfiguration file to store global parameters
"""

# physical parameters
nmax = 20  # maximum quantum number n of eigenfunctions
lmax = 3  # maximum quantum number l of eigenfunctions

# model parameters
spinpol = False  # spin-polarized functional
xfunc = "lda"  # exchange functional (libxc ref)
cfunc = "lda_pw"  # correlation functional (libxc ref)
bc = "dirichlet"  # boundary condition: Dirchlet means X(r_s)=0, Neumann means [dX(r)/dr]_(r=r_s)=0
unbound = "ideal"  # treatment for unbound electrons


# numerical grid for static calculations
grid_params = {"ngrid": 1000, "x0": -10}
# convergence parameters for static calculations
conv_params = {"econv": 1e-6, "nconv": 1e-6, "numconv": 1e-6}
# scf parameters
scf_params = {"maxscf": 50, "mixfrac": 0.3}
