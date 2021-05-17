"""
Module which computes time-independent properties from the average-atom setup
"""

# standard packages

# external packages
import numpy as np
from math import sqrt, pi

# internal modules
import config
import numerov
import mathtools


class Orbitals:
    """
    The orbitals object has the following attributes:
    - eigfuncs (numpy array)    :   the orbitals defined on the numerical grid
    - eigvals  (numpy array)    :   KS orbital eigenvalues
    - occnums  (numpy array)    :   KS orbital occupation numbers
    """

    def __init__(self):
        """
        Initializes the orbital attributes to empty numpy arrays
        """
        self.eigfuncs = np.zeros(
            (config.spindims, config.lmax, config.nmax, config.grid_params["ngrid"])
        )
        self.eigvals = np.zeros((config.spindims, config.lmax, config.nmax))
        self.occnums = np.zeros((config.spindims, config.lmax, config.nmax))
        self.lbound = np.zeros((config.spindims, config.lmax, config.nmax))

    def SCF_init(self, atom):
        """
        Initializes the KS orbitals before an SCF cycle using the bare clmb potential
        """

        # compute the bare coulomb potential
        # v_en = -atom.at_chrg * np.exp(-config.xgrid)

        v_en = np.zeros((config.spindims, config.grid_params["ngrid"]))

        for i in range(config.spindims):
            v_en[i] = -atom.at_chrg * np.exp(-config.xgrid)

        # solve the KS equations with the bare coulomb potential
        self.eigfuncs, self.eigvals = numerov.matrix_solve(self, v_en, config.xgrid)

        # compute the lbound array
        self.make_lbound()

        # initial guess for the chemical potential
        config.mu = np.zeros((config.spindims))

    def occupy(self):
        """
        Occupies the orbitals according to Fermi Dirac statistics.
        The chemical potential is calculated to satisfy charge neutrality
        within the Voronoi sphere
        """

        # compute the chemical potential using the eigenvalues
        config.mu = mathtools.chem_pot(self)

        # compute the occupation numbers using the chemical potential
        self.occnums = self.calc_occnums(config.mu)

        return True

    def calc_occnums(self, mu):
        """
        Computes the Fermi-Dirac occupations for the eigenvalues
        """

        occnums = np.zeros_like(self.eigvals)

        for i in range(config.spindims):
            if config.nele[i] != 0:
                occnums[i] = self.lbound[i] * mathtools.fermi_dirac(
                    self.eigvals[i], mu[i], config.beta
                )

        return occnums

    def make_lbound(self):
        """
        Constructs the 'lbound' attribute
        For each spin channel, lbound(l,n)=(2l+1)*Theta(eps_n)
        """

        for l in range(config.lmax):
            self.lbound[:, l] = np.where(self.eigvals[:, l] < 0, 2 * l + 1.0, 0.0)


class Density:
    """
    The Density object has the following attributes:
    - rho_bound (np array)     : the bound part of the density n(r)
    - rho_unbound (np array)   : the unbound part of the density n(r)
    - N_bound (np array)       : the number of bound electrons
    - N_unbound (np array)     : the number of unbound electrons
    """

    def __init__(self):

        self.rho_bound = np.zeros((config.spindims, config.grid_params["ngrid"]))
        self.rho_unbound = np.zeros_like(self.rho_bound)
        self.N_bound = np.zeros((config.spindims))
        self.N_unbound = np.zeros_like(self.N_bound)

    def construct(self, orbs):
        """
        Constructs the density

        Inputs:
        - orbs (object)    : the orbitals object
        """

        # construct the bound part of the density
        self.construct_rho_bound(orbs)
        # construct the unbound part
        self.construct_rho_unbound(orbs)

    def construct_rho_bound(self, orbs):
        """
        Constructs the bound part of the density

        Inputs:
        - orbs (object)    : the orbitals object
        """

        # first of all construct the density
        # rho_b(r) = \sum_{n,l} (2l+1) f_{nl} |R_{nl}(r)|^2
        # occnums in AvAtom are defined as (2l+1)*f_{nl}

        # R_{nl}(r) = exp(x/2) P_{nl}(x), P(x) are eigfuncs
        orbs_R = np.exp(-config.xgrid / 2.0) * orbs.eigfuncs
        orbs_R_sq = orbs_R ** 2.0

        # sum over the (l,n) dimensions of the orbitals to get the density
        self.rho_bound = np.einsum("ijk,ijkl->il", orbs.occnums, orbs_R_sq)

        # compute the number of unbound electrons
        self.N_bound = np.sum(orbs.occnums, axis=(1, 2))

    def construct_rho_unbound(self, orbs):
        """
        Constructs the bound part of the density

        Inputs:
        - orbs (object)    : the orbitals object
        """

        # so far only the ideal approximation is implemented
        if config.unbound == "ideal":

            # unbound density is constant
            for i in range(config.spindims):
                prefac = config.nele[i] / (sqrt(2) * pi ** 2)
                n_ub = prefac * mathtools.fd_int_complete(
                    config.mu[i], config.beta, 0.5
                )
                self.rho_unbound[i] = n_ub
                self.N_unbound[i] = n_ub * config.sph_vol

    def write_to_file(self):
        # this routine should probably be moved to a more appropriate place
        """
        Writes the density (on the r-grid) to file
        """

        fname = "density.csv"

        if config.spinpol == True:
            headstr = (
                "r"
                + 7 * " "
                + "n^up_b"
                + 4 * " "
                + "n^up_ub"
                + 3 * " "
                + "n^dw_b"
                + 4 * " "
                + "n^dw_ub"
                + 3 * " "
            )
            data = np.column_stack(
                [
                    config.rgrid,
                    self.rho_bound[0],
                    self.rho_unbound[0],
                    self.rho_bound[1],
                    self.rho_unbound[1],
                ]
            )
        else:
            headstr = "r" + 8 * " " + "n_b" + 6 * " " + "n^_ub" + 3 * " "
            data = np.column_stack(
                [config.rgrid, self.rho_bound[0], self.rho_unbound[0]]
            )

        np.savetxt(fname, data, fmt="%8.3e", header=headstr)
