# Copyright (C) 2015-2019: The University of Edinburgh
#                 Authors: Craig Warren and Antonis Giannopoulos
#
# This file is part of gprMax.
#
# gprMax is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gprMax is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gprMax.  If not, see <http://www.gnu.org/licenses/>.

from string import Template

kernels_template_pml_magnetic_HORIPML = Template("""

// Macros for converting subscripts to linear index:
#define INDEX2D_R(m, n) (m)*(NY_R)+(n)
#define INDEX2D_MAT(m, n) (m)*($NY_MATCOEFFS)+(n)
#define INDEX3D_FIELDS(i, j, k) (i)*($NY_FIELDS)*($NZ_FIELDS)+(j)*($NZ_FIELDS)+(k)
#define INDEX4D_ID(p, i, j, k) (p)*($NX_ID)*($NY_ID)*($NZ_ID)+(i)*($NY_ID)*($NZ_ID)+(j)*($NZ_ID)+(k)
#define INDEX4D_PHI1(p, i, j, k) (p)*(NX_PHI1)*(NY_PHI1)*(NZ_PHI1)+(i)*(NY_PHI1)*(NZ_PHI1)+(j)*(NZ_PHI1)+(k)
#define INDEX4D_PHI2(p, i, j, k) (p)*(NX_PHI2)*(NY_PHI2)*(NZ_PHI2)+(i)*(NY_PHI2)*(NZ_PHI2)+(j)*(NZ_PHI2)+(k)

// Material coefficients (read-only) in constant memory (64KB)
__device__ __constant__ $REAL updatecoeffsH[$N_updatecoeffsH];


__global__ void order1_xminus(int xs, int xf, int ys, int yf, int zs, int zf, int NX_PHI1, int NY_PHI1, int NZ_PHI1, int NX_PHI2, int NY_PHI2, int NZ_PHI2, int NY_R, const unsigned int* __restrict__ ID, const $REAL* __restrict__ Ex, const $REAL* __restrict__ Ey, const $REAL* __restrict__ Ez, const $REAL* __restrict__ Hx, $REAL *Hy, $REAL *Hz, $REAL *PHI1, $REAL *PHI2, const $REAL* __restrict__ RA, const $REAL* __restrict__ RB, const $REAL* __restrict__ RE, const $REAL* __restrict__ RF, $REAL d) {

    //  This function updates the Hy and Hz field components for the xminus slab.
    //
    //  Args:
    //      xs, xf, ys, yf, zs, zf: Cell coordinates of PML slab
    //      NX_PHI, NY_PHI, NZ_PHI, NY_R: Dimensions of PHI1, PHI2, and R PML arrays
    //      ID, E, H: Access to ID and field component arrays
    //      Phi, RA, RB, RE, RF: Access to PML magnetic coefficient arrays
    //      d: Spatial discretisation, e.g. dx, dy or dz

    // Obtain the linear index corresponding to the current tREad
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Convert the linear index to subscripts for PML PHI1 (4D) arrays
    int p1 = idx / (NX_PHI1 * NY_PHI1 * NZ_PHI1);
    int i1 = (idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) / (NY_PHI1 * NZ_PHI1);
    int j1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) / NZ_PHI1;
    int k1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) % NZ_PHI1;

    // Convert the linear index to subscripts for PML PHI2 (4D) arrays
    int p2 = idx / (NX_PHI2 * NY_PHI2 * NZ_PHI2);
    int i2 = (idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) / (NY_PHI2 * NZ_PHI2);
    int j2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) / NZ_PHI2;
    int k2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) % NZ_PHI2;

    $REAL RA01, RB0, RE0, RF0, dEy, dEz;
    $REAL dx = d;
    int ii, jj, kk, materialHy, materialHz;
    int nx = xf - xs;
    int ny = yf - ys;
    int nz = zf - zs;

    if (p1 == 0 && i1 < nx && j1 < ny && k1 < nz) {
        // Subscripts for field arrays
        ii = xf - (i1 + 1);
        jj = j1 + ys;
        kk = k1 + zs;

        // PML coefficients
        RA01 = RA[INDEX2D_R(0,i1)] - 1;
        RB0 = RB[INDEX2D_R(0,i1)];
        RE0 = RE[INDEX2D_R(0,i1)];
        RF0 = RF[INDEX2D_R(0,i1)];

        // Hy
        materialHy = ID[INDEX4D_ID(4,ii,jj,kk)];
        dEz = (Ez[INDEX3D_FIELDS(ii+1,jj,kk)] - Ez[INDEX3D_FIELDS(ii,jj,kk)]) / dx;
        Hy[INDEX3D_FIELDS(ii,jj,kk)] = Hy[INDEX3D_FIELDS(ii,jj,kk)] + updatecoeffsH[INDEX2D_MAT(materialHy,4)] * (RA01 * dEz + RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(0,i1,j1,k1)] = RE0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] - RF0 * dEz;
    }

    if (p2 == 0 && i2 < nx && j2 < ny && k2 < nz) {
        // Subscripts for field arrays
        ii = xf - (i2 + 1);
        jj = j2 + ys;
        kk = k2 + zs;

        // PML coefficients
        RA01 = RA[INDEX2D_R(0,i2)] - 1;
        RB0 = RB[INDEX2D_R(0,i2)];
        RE0 = RE[INDEX2D_R(0,i2)];
        RF0 = RF[INDEX2D_R(0,i2)];

        // Hz
        materialHz = ID[INDEX4D_ID(5,ii,jj,kk)];
        dEy = (Ey[INDEX3D_FIELDS(ii+1,jj,kk)] - Ey[INDEX3D_FIELDS(ii,jj,kk)]) / dx;
        Hz[INDEX3D_FIELDS(ii,jj,kk)] = Hz[INDEX3D_FIELDS(ii,jj,kk)] - updatecoeffsH[INDEX2D_MAT(materialHz,4)] * (RA01 * dEy + RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(0,i2,j2,k2)] = RE0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] - RF0 * dEy;
    }
}


__global__ void order2_xminus(int xs, int xf, int ys, int yf, int zs, int zf, int NX_PHI1, int NY_PHI1, int NZ_PHI1, int NX_PHI2, int NY_PHI2, int NZ_PHI2, int NY_R, const unsigned int* __restrict__ ID, const $REAL* __restrict__ Ex, const $REAL* __restrict__ Ey, const $REAL* __restrict__ Ez, const $REAL* __restrict__ Hx, $REAL *Hy, $REAL *Hz, $REAL *PHI1, $REAL *PHI2, const $REAL* __restrict__ RA, const $REAL* __restrict__ RB, const $REAL* __restrict__ RE, const $REAL* __restrict__ RF, $REAL d) {

    //  This function updates the Hy and Hz field components for the xminus slab.
    //
    //  Args:
    //      xs, xf, ys, yf, zs, zf: Cell coordinates of PML slab
    //      NX_PHI, NY_PHI, NZ_PHI, NY_R: Dimensions of PHI1, PHI2, and R PML arrays
    //      ID, E, H: Access to ID and field component arrays
    //      Phi, RA, RB, RE, RF: Access to PML magnetic coefficient arrays
    //      d: Spatial discretisation, e.g. dx, dy or dz

    // Obtain the linear index corresponding to the current tREad
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Convert the linear index to subscripts for PML PHI1 (4D) arrays
    int p1 = idx / (NX_PHI1 * NY_PHI1 * NZ_PHI1);
    int i1 = (idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) / (NY_PHI1 * NZ_PHI1);
    int j1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) / NZ_PHI1;
    int k1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) % NZ_PHI1;

    // Convert the linear index to subscripts for PML PHI2 (4D) arrays
    int p2 = idx / (NX_PHI2 * NY_PHI2 * NZ_PHI2);
    int i2 = (idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) / (NY_PHI2 * NZ_PHI2);
    int j2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) / NZ_PHI2;
    int k2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) % NZ_PHI2;

    $REAL RA0, RB0, RE0, RF0, RA1, RB1, RE1, RF1, RA01, dEy, dEz;
    $REAL dx = d;
    int ii, jj, kk, materialHy, materialHz;
    int nx = xf - xs;
    int ny = yf - ys;
    int nz = zf - zs;

    if (p1 == 0 && i1 < nx && j1 < ny && k1 < nz) {
        // Subscripts for field arrays
        ii = xf - (i1 + 1);
        jj = j1 + ys;
        kk = k1 + zs;

        // PML coefficients
        RA0 = RA[INDEX2D_R(0,i1)];
        RB0 = RB[INDEX2D_R(0,i1)];
        RE0 = RE[INDEX2D_R(0,i1)];
        RF0 = RF[INDEX2D_R(0,i1)];
        RA1 = RA[INDEX2D_R(1,i1)];
        RB1 = RB[INDEX2D_R(1,i1)];
        RE1 = RE[INDEX2D_R(1,i1)];
        RF1 = RF[INDEX2D_R(1,i1)];
        RA01 = RA[INDEX2D_R(0,i1)] * RA[INDEX2D_R(1,i1)] - 1;

        // Hy
        materialHy = ID[INDEX4D_ID(4,ii,jj,kk)];
        dEz = (Ez[INDEX3D_FIELDS(ii+1,jj,kk)] - Ez[INDEX3D_FIELDS(ii,jj,kk)]) / dx;
        Hy[INDEX3D_FIELDS(ii,jj,kk)] = Hy[INDEX3D_FIELDS(ii,jj,kk)] + updatecoeffsH[INDEX2D_MAT(materialHy,4)] * (RA01 * dEz + RA1 * RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] + RB1 * PHI1[INDEX4D_PHI1(1,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(1,i1,j1,k1)] = RE1 * PHI1[INDEX4D_PHI1(1,i1,j1,k1)] - RF1 * (RA0 * dEz + RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(0,i1,j1,k1)] = RE0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] - RF0 * dEz;
    }

    if (p2 == 0 && i2 < nx && j2 < ny && k2 < nz) {
        // Subscripts for field arrays
        ii = xf - (i2 + 1);
        jj = j2 + ys;
        kk = k2 + zs;

        // PML coefficients
        RA0 = RA[INDEX2D_R(0,i2)];
        RB0 = RB[INDEX2D_R(0,i2)];
        RE0 = RE[INDEX2D_R(0,i2)];
        RF0 = RF[INDEX2D_R(0,i2)];
        RA1 = RA[INDEX2D_R(1,i2)];
        RB1 = RB[INDEX2D_R(1,i2)];
        RE1 = RE[INDEX2D_R(1,i2)];
        RF1 = RF[INDEX2D_R(1,i2)];
        RA01 = RA[INDEX2D_R(0,i2)] * RA[INDEX2D_R(1,i2)] - 1;

        // Hz
        materialHz = ID[INDEX4D_ID(5,ii,jj,kk)];
        dEy = (Ey[INDEX3D_FIELDS(ii+1,jj,kk)] - Ey[INDEX3D_FIELDS(ii,jj,kk)]) / dx;
        Hz[INDEX3D_FIELDS(ii,jj,kk)] = Hz[INDEX3D_FIELDS(ii,jj,kk)] - updatecoeffsH[INDEX2D_MAT(materialHz,4)] * (RA01 * dEy + RA1 * RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] + RB1 * PHI2[INDEX4D_PHI2(1,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(1,i2,j2,k2)] = RE1 * PHI2[INDEX4D_PHI2(1,i2,j2,k2)] - RF1 * (RA0 * dEy + RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(0,i2,j2,k2)] = RE0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] - RF0 * dEy;
    }
}


__global__ void order1_xplus(int xs, int xf, int ys, int yf, int zs, int zf, int NX_PHI1, int NY_PHI1, int NZ_PHI1, int NX_PHI2, int NY_PHI2, int NZ_PHI2, int NY_R, const unsigned int* __restrict__ ID, const $REAL* __restrict__ Ex, const $REAL* __restrict__ Ey, const $REAL* __restrict__ Ez, const $REAL* __restrict__ Hx, $REAL *Hy, $REAL *Hz, $REAL *PHI1, $REAL *PHI2, const $REAL* __restrict__ RA, const $REAL* __restrict__ RB, const $REAL* __restrict__ RE, const $REAL* __restrict__ RF, $REAL d) {

    //  This function updates the Hy and Hz field components for the xplus slab.
    //
    //  Args:
    //      xs, xf, ys, yf, zs, zf: Cell coordinates of PML slab
    //      NX_PHI, NY_PHI, NZ_PHI, NY_R: Dimensions of PHI1, PHI2, and R PML arrays
    //      ID, E, H: Access to ID and field component arrays
    //      Phi, RA, RB, RE, RF: Access to PML magnetic coefficient arrays
    //      d: Spatial discretisation, e.g. dx, dy or dz

    // Obtain the linear index corresponding to the current tREad
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Convert the linear index to subscripts for PML PHI1 (4D) arrays
    int p1 = idx / (NX_PHI1 * NY_PHI1 * NZ_PHI1);
    int i1 = (idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) / (NY_PHI1 * NZ_PHI1);
    int j1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) / NZ_PHI1;
    int k1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) % NZ_PHI1;

    // Convert the linear index to subscripts for PML PHI2 (4D) arrays
    int p2 = idx / (NX_PHI2 * NY_PHI2 * NZ_PHI2);
    int i2 = (idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) / (NY_PHI2 * NZ_PHI2);
    int j2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) / NZ_PHI2;
    int k2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) % NZ_PHI2;

    $REAL RA01, RB0, RE0, RF0, dEy, dEz;
    $REAL dx = d;
    int ii, jj, kk, materialHy, materialHz;
    int nx = xf - xs;
    int ny = yf - ys;
    int nz = zf - zs;

    if (p1 == 0 && i1 < nx && j1 < ny && k1 < nz) {
        // Subscripts for field arrays
        ii = i1 + xs;
        jj = j1 + ys;
        kk = k1 + zs;

        // PML coefficients
        RA01 = RA[INDEX2D_R(0,i1)] - 1;
        RB0 = RB[INDEX2D_R(0,i1)];
        RE0 = RE[INDEX2D_R(0,i1)];
        RF0 = RF[INDEX2D_R(0,i1)];

        // Hy
        materialHy = ID[INDEX4D_ID(4,ii,jj,kk)];
        dEz = (Ez[INDEX3D_FIELDS(ii+1,jj,kk)] - Ez[INDEX3D_FIELDS(ii,jj,kk)]) / dx;
        Hy[INDEX3D_FIELDS(ii,jj,kk)] = Hy[INDEX3D_FIELDS(ii,jj,kk)] + updatecoeffsH[INDEX2D_MAT(materialHy,4)] * (RA01 * dEz + RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(0,i1,j1,k1)] = RE0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] - RF0 * dEz;
    }

    if (p2 == 0 && i2 < nx && j2 < ny && k2 < nz) {
        // Subscripts for field arrays
        ii = i2 + xs;
        jj = j2 + ys;
        kk = k2 + zs;

        // PML coefficients
        RA01 = RA[INDEX2D_R(0,i2)] - 1;
        RB0 = RB[INDEX2D_R(0,i2)];
        RE0 = RE[INDEX2D_R(0,i2)];
        RF0 = RF[INDEX2D_R(0,i2)];

        // Hz
        materialHz = ID[INDEX4D_ID(5,ii,jj,kk)];
        dEy = (Ey[INDEX3D_FIELDS(ii+1,jj,kk)] - Ey[INDEX3D_FIELDS(ii,jj,kk)]) / dx;
        Hz[INDEX3D_FIELDS(ii,jj,kk)] = Hz[INDEX3D_FIELDS(ii,jj,kk)] - updatecoeffsH[INDEX2D_MAT(materialHz,4)] * (RA01 * dEy + RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(0,i2,j2,k2)] = RE0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] - RF0 * dEy;
    }
}


__global__ void order2_xplus(int xs, int xf, int ys, int yf, int zs, int zf, int NX_PHI1, int NY_PHI1, int NZ_PHI1, int NX_PHI2, int NY_PHI2, int NZ_PHI2, int NY_R, const unsigned int* __restrict__ ID, const $REAL* __restrict__ Ex, const $REAL* __restrict__ Ey, const $REAL* __restrict__ Ez, const $REAL* __restrict__ Hx, $REAL *Hy, $REAL *Hz, $REAL *PHI1, $REAL *PHI2, const $REAL* __restrict__ RA, const $REAL* __restrict__ RB, const $REAL* __restrict__ RE, const $REAL* __restrict__ RF, $REAL d) {

    //  This function updates the Hy and Hz field components for the xplus slab.
    //
    //  Args:
    //      xs, xf, ys, yf, zs, zf: Cell coordinates of PML slab
    //      NX_PHI, NY_PHI, NZ_PHI, NY_R: Dimensions of PHI1, PHI2, and R PML arrays
    //      ID, E, H: Access to ID and field component arrays
    //      Phi, RA, RB, RE, RF: Access to PML magnetic coefficient arrays
    //      d: Spatial discretisation, e.g. dx, dy or dz

    // Obtain the linear index corresponding to the current tREad
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Convert the linear index to subscripts for PML PHI1 (4D) arrays
    int p1 = idx / (NX_PHI1 * NY_PHI1 * NZ_PHI1);
    int i1 = (idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) / (NY_PHI1 * NZ_PHI1);
    int j1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) / NZ_PHI1;
    int k1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) % NZ_PHI1;

    // Convert the linear index to subscripts for PML PHI2 (4D) arrays
    int p2 = idx / (NX_PHI2 * NY_PHI2 * NZ_PHI2);
    int i2 = (idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) / (NY_PHI2 * NZ_PHI2);
    int j2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) / NZ_PHI2;
    int k2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) % NZ_PHI2;

    $REAL RA0, RB0, RE0, RF0, RA1, RB1, RE1, RF1, RA01, dEy, dEz;
    $REAL dx = d;
    int ii, jj, kk, materialHy, materialHz;
    int nx = xf - xs;
    int ny = yf - ys;
    int nz = zf - zs;

    if (p1 == 0 && i1 < nx && j1 < ny && k1 < nz) {
        // Subscripts for field arrays
        ii = i1 + xs;
        jj = j1 + ys;
        kk = k1 + zs;

        // PML coefficients
        RA0 = RA[INDEX2D_R(0,i1)];
        RB0 = RB[INDEX2D_R(0,i1)];
        RE0 = RE[INDEX2D_R(0,i1)];
        RF0 = RF[INDEX2D_R(0,i1)];
        RA1 = RA[INDEX2D_R(1,i1)];
        RB1 = RB[INDEX2D_R(1,i1)];
        RE1 = RE[INDEX2D_R(1,i1)];
        RF1 = RF[INDEX2D_R(1,i1)];
        RA01 = RA[INDEX2D_R(0,i1)] * RA[INDEX2D_R(1,i1)] - 1;

        // Hy
        materialHy = ID[INDEX4D_ID(4,ii,jj,kk)];
        dEz = (Ez[INDEX3D_FIELDS(ii+1,jj,kk)] - Ez[INDEX3D_FIELDS(ii,jj,kk)]) / dx;
        Hy[INDEX3D_FIELDS(ii,jj,kk)] = Hy[INDEX3D_FIELDS(ii,jj,kk)] + updatecoeffsH[INDEX2D_MAT(materialHy,4)] * (RA01 * dEz + RA1 * RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] + RB1 * PHI1[INDEX4D_PHI1(1,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(1,i1,j1,k1)] = RE1 * PHI1[INDEX4D_PHI1(1,i1,j1,k1)] - RF1 * (RA0 * dEz + RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(0,i1,j1,k1)] = RE0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] - RF0 * dEz;
    }

    if (p2 == 0 && i2 < nx && j2 < ny && k2 < nz) {
        // Subscripts for field arrays
        ii = i2 + xs;
        jj = j2 + ys;
        kk = k2 + zs;

        // PML coefficients
        RA0 = RA[INDEX2D_R(0,i2)];
        RB0 = RB[INDEX2D_R(0,i2)];
        RE0 = RE[INDEX2D_R(0,i2)];
        RF0 = RF[INDEX2D_R(0,i2)];
        RA1 = RA[INDEX2D_R(1,i2)];
        RB1 = RB[INDEX2D_R(1,i2)];
        RE1 = RE[INDEX2D_R(1,i2)];
        RF1 = RF[INDEX2D_R(1,i2)];
        RA01 = RA[INDEX2D_R(0,i2)] * RA[INDEX2D_R(1,i2)] - 1;

        // Hz
        materialHz = ID[INDEX4D_ID(5,ii,jj,kk)];
        dEy = (Ey[INDEX3D_FIELDS(ii+1,jj,kk)] - Ey[INDEX3D_FIELDS(ii,jj,kk)]) / dx;
        Hz[INDEX3D_FIELDS(ii,jj,kk)] = Hz[INDEX3D_FIELDS(ii,jj,kk)] - updatecoeffsH[INDEX2D_MAT(materialHz,4)] * (RA01 * dEy + RA1 * RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] + RB1 * PHI2[INDEX4D_PHI2(1,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(1,i2,j2,k2)] = RE1 * PHI2[INDEX4D_PHI2(1,i2,j2,k2)] - RF1 * (RA0 * dEy + RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(0,i2,j2,k2)] = RE0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] - RF0 * dEy;
    }
}


__global__ void order1_yminus(int xs, int xf, int ys, int yf, int zs, int zf, int NX_PHI1, int NY_PHI1, int NZ_PHI1, int NX_PHI2, int NY_PHI2, int NZ_PHI2, int NY_R, const unsigned int* __restrict__ ID, const $REAL* __restrict__ Ex, const $REAL* __restrict__ Ey, const $REAL* __restrict__ Ez, $REAL *Hx, const $REAL* __restrict__ Hy, $REAL *Hz, $REAL *PHI1, $REAL *PHI2, const $REAL* __restrict__ RA, const $REAL* __restrict__ RB, const $REAL* __restrict__ RE, const $REAL* __restrict__ RF, $REAL d) {

    //  This function updates the Hx and Hz field components for the yminus slab.
    //
    //  Args:
    //      xs, xf, ys, yf, zs, zf: Cell coordinates of PML slab
    //      NX_PHI, NY_PHI, NZ_PHI, NY_R: Dimensions of PHI1, PHI2, and R PML arrays
    //      ID, E, H: Access to ID and field component arrays
    //      Phi, RA, RB, RE, RF: Access to PML magnetic coefficient arrays
    //      d: Spatial discretisation, e.g. dx, dy or dz

    // Obtain the linear index corresponding to the current tREad
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Convert the linear index to subscripts for PML PHI1 (4D) arrays
    int p1 = idx / (NX_PHI1 * NY_PHI1 * NZ_PHI1);
    int i1 = (idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) / (NY_PHI1 * NZ_PHI1);
    int j1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) / NZ_PHI1;
    int k1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) % NZ_PHI1;

    // Convert the linear index to subscripts for PML PHI2 (4D) arrays
    int p2 = idx / (NX_PHI2 * NY_PHI2 * NZ_PHI2);
    int i2 = (idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) / (NY_PHI2 * NZ_PHI2);
    int j2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) / NZ_PHI2;
    int k2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) % NZ_PHI2;

    $REAL RA01, RB0, RE0, RF0, dEx, dEz;
    $REAL dy = d;
    int ii, jj, kk, materialHx, materialHz;
    int nx = xf - xs;
    int ny = yf - ys;
    int nz = zf - zs;

    if (p1 == 0 && i1 < nx && j1 < ny && k1 < nz) {
        // Subscripts for field arrays
        ii = i1 + xs;
        jj = yf - (j1 + 1);
        kk = k1 + zs;

        // PML coefficients
        RA01 = RA[INDEX2D_R(0,j1)] - 1;
        RB0 = RB[INDEX2D_R(0,j1)];
        RE0 = RE[INDEX2D_R(0,j1)];
        RF0 = RF[INDEX2D_R(0,j1)];

        // Hx
        materialHx = ID[INDEX4D_ID(3,ii,jj,kk)];
        dEz = (Ez[INDEX3D_FIELDS(ii,jj+1,kk)] - Ez[INDEX3D_FIELDS(ii,jj,kk)]) / dy;
        Hx[INDEX3D_FIELDS(ii,jj,kk)] = Hx[INDEX3D_FIELDS(ii,jj,kk)] - updatecoeffsH[INDEX2D_MAT(materialHx,4)] * (RA01 * dEz + RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(0,i1,j1,k1)] = RE0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] - RF0 * dEz;
    }

    if (p2 == 0 && i2 < nx && j2 < ny && k2 < nz) {
        // Subscripts for field arrays
        ii = i2 + xs;
        jj = yf - (j2 + 1);
        kk = k2 + zs;

        // PML coefficients
        RA01 = RA[INDEX2D_R(0,j2)] - 1;
        RB0 = RB[INDEX2D_R(0,j2)];
        RE0 = RE[INDEX2D_R(0,j2)];
        RF0 = RF[INDEX2D_R(0,j2)];

        // Hz
        materialHz = ID[INDEX4D_ID(5,ii,jj,kk)];
        dEx = (Ex[INDEX3D_FIELDS(ii,jj+1,kk)] - Ex[INDEX3D_FIELDS(ii,jj,kk)]) / dy;
        Hz[INDEX3D_FIELDS(ii,jj,kk)] = Hz[INDEX3D_FIELDS(ii,jj,kk)] + updatecoeffsH[INDEX2D_MAT(materialHz,4)] * (RA01 * dEx + RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(0,i2,j2,k2)] = RE0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] - RF0 * dEx;
    }
}


__global__ void order2_yminus(int xs, int xf, int ys, int yf, int zs, int zf, int NX_PHI1, int NY_PHI1, int NZ_PHI1, int NX_PHI2, int NY_PHI2, int NZ_PHI2, int NY_R, const unsigned int* __restrict__ ID, const $REAL* __restrict__ Ex, const $REAL* __restrict__ Ey, const $REAL* __restrict__ Ez, $REAL *Hx, const $REAL* __restrict__ Hy, $REAL *Hz, $REAL *PHI1, $REAL *PHI2, const $REAL* __restrict__ RA, const $REAL* __restrict__ RB, const $REAL* __restrict__ RE, const $REAL* __restrict__ RF, $REAL d) {

    //  This function updates the Hx and Hz field components for the yminus slab.
    //
    //  Args:
    //      xs, xf, ys, yf, zs, zf: Cell coordinates of PML slab
    //      NX_PHI, NY_PHI, NZ_PHI, NY_R: Dimensions of PHI1, PHI2, and R PML arrays
    //      ID, E, H: Access to ID and field component arrays
    //      Phi, RA, RB, RE, RF: Access to PML magnetic coefficient arrays
    //      d: Spatial discretisation, e.g. dx, dy or dz

    // Obtain the linear index corresponding to the current tREad
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Convert the linear index to subscripts for PML PHI1 (4D) arrays
    int p1 = idx / (NX_PHI1 * NY_PHI1 * NZ_PHI1);
    int i1 = (idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) / (NY_PHI1 * NZ_PHI1);
    int j1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) / NZ_PHI1;
    int k1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) % NZ_PHI1;

    // Convert the linear index to subscripts for PML PHI2 (4D) arrays
    int p2 = idx / (NX_PHI2 * NY_PHI2 * NZ_PHI2);
    int i2 = (idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) / (NY_PHI2 * NZ_PHI2);
    int j2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) / NZ_PHI2;
    int k2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) % NZ_PHI2;

    $REAL RA0, RB0, RE0, RF0, RA1, RB1, RE1, RF1, RA01, dEx, dEz;
    $REAL dy = d;
    int ii, jj, kk, materialHx, materialHz;
    int nx = xf - xs;
    int ny = yf - ys;
    int nz = zf - zs;

    if (p1 == 0 && i1 < nx && j1 < ny && k1 < nz) {
        // Subscripts for field arrays
        ii = i1 + xs;
        jj = yf - (j1 + 1);
        kk = k1 + zs;

        // PML coefficients
        RA0 = RA[INDEX2D_R(0,j1)];
        RB0 = RB[INDEX2D_R(0,j1)];
        RE0 = RE[INDEX2D_R(0,j1)];
        RF0 = RF[INDEX2D_R(0,j1)];
        RA1 = RA[INDEX2D_R(1,j1)];
        RB1 = RB[INDEX2D_R(1,j1)];
        RE1 = RE[INDEX2D_R(1,j1)];
        RF1 = RF[INDEX2D_R(1,j1)];
        RA01 = RA[INDEX2D_R(0,j1)] * RA[INDEX2D_R(1,j1)] - 1;

        // Hx
        materialHx = ID[INDEX4D_ID(3,ii,jj,kk)];
        dEz = (Ez[INDEX3D_FIELDS(ii,jj+1,kk)] - Ez[INDEX3D_FIELDS(ii,jj,kk)]) / dy;
        Hx[INDEX3D_FIELDS(ii,jj,kk)] = Hx[INDEX3D_FIELDS(ii,jj,kk)] - updatecoeffsH[INDEX2D_MAT(materialHx,4)] * (RA01 * dEz + RA1 * RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] + RB1 * PHI1[INDEX4D_PHI1(1,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(1,i1,j1,k1)] = RE1 * PHI1[INDEX4D_PHI1(1,i1,j1,k1)] - RF1 * (RA0 * dEz + RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(0,i1,j1,k1)] = RE0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] - RF0 * dEz;
    }

    if (p2 == 0 && i2 < nx && j2 < ny && k2 < nz) {
        // Subscripts for field arrays
        ii = i2 + xs;
        jj = yf - (j2 + 1);
        kk = k2 + zs;

        // PML coefficients
        RA0 = RA[INDEX2D_R(0,j2)];
        RB0 = RB[INDEX2D_R(0,j2)];
        RE0 = RE[INDEX2D_R(0,j2)];
        RF0 = RF[INDEX2D_R(0,j2)];
        RA1 = RA[INDEX2D_R(1,j2)];
        RB1 = RB[INDEX2D_R(1,j2)];
        RE1 = RE[INDEX2D_R(1,j2)];
        RF1 = RF[INDEX2D_R(1,j2)];
        RA01 = RA[INDEX2D_R(0,j2)] * RA[INDEX2D_R(1,j2)] - 1;

        // Hz
        materialHz = ID[INDEX4D_ID(5,ii,jj,kk)];
        dEx = (Ex[INDEX3D_FIELDS(ii,jj+1,kk)] - Ex[INDEX3D_FIELDS(ii,jj,kk)]) / dy;
        Hz[INDEX3D_FIELDS(ii,jj,kk)] = Hz[INDEX3D_FIELDS(ii,jj,kk)] + updatecoeffsH[INDEX2D_MAT(materialHz,4)] * (RA01 * dEx + RA1 * RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] + RB1 * PHI2[INDEX4D_PHI2(1,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(1,i2,j2,k2)] = RE1 * PHI2[INDEX4D_PHI2(1,i2,j2,k2)] - RF1 * (RA0 * dEx + RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(0,i2,j2,k2)] = RE0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] - RF0 * dEx;
    }
}


__global__ void order1_yplus(int xs, int xf, int ys, int yf, int zs, int zf, int NX_PHI1, int NY_PHI1, int NZ_PHI1, int NX_PHI2, int NY_PHI2, int NZ_PHI2, int NY_R, const unsigned int* __restrict__ ID, const $REAL* __restrict__ Ex, const $REAL* __restrict__ Ey, const $REAL* __restrict__ Ez, $REAL *Hx, const $REAL* __restrict__ Hy, $REAL *Hz, $REAL *PHI1, $REAL *PHI2, const $REAL* __restrict__ RA, const $REAL* __restrict__ RB, const $REAL* __restrict__ RE, const $REAL* __restrict__ RF, $REAL d) {

    //  This function updates the Hx and Hz field components for the yplus slab.
    //
    //  Args:
    //      xs, xf, ys, yf, zs, zf: Cell coordinates of PML slab
    //      NX_PHI, NY_PHI, NZ_PHI, NY_R: Dimensions of PHI1, PHI2, and R PML arrays
    //      ID, E, H: Access to ID and field component arrays
    //      Phi, RA, RB, RE, RF: Access to PML magnetic coefficient arrays
    //      d: Spatial discretisation, e.g. dx, dy or dz

    // Obtain the linear index corresponding to the current tREad
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Convert the linear index to subscripts for PML PHI1 (4D) arrays
    int p1 = idx / (NX_PHI1 * NY_PHI1 * NZ_PHI1);
    int i1 = (idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) / (NY_PHI1 * NZ_PHI1);
    int j1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) / NZ_PHI1;
    int k1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) % NZ_PHI1;

    // Convert the linear index to subscripts for PML PHI2 (4D) arrays
    int p2 = idx / (NX_PHI2 * NY_PHI2 * NZ_PHI2);
    int i2 = (idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) / (NY_PHI2 * NZ_PHI2);
    int j2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) / NZ_PHI2;
    int k2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) % NZ_PHI2;

    $REAL RA01, RB0, RE0, RF0, dEx, dEz;
    $REAL dy = d;
    int ii, jj, kk, materialHx, materialHz;
    int nx = xf - xs;
    int ny = yf - ys;
    int nz = zf - zs;

    if (p1 == 0 && i1 < nx && j1 < ny && k1 < nz) {
        // Subscripts for field arrays
        ii = i1 + xs;
        jj = j1 + ys;
        kk = k1 + zs;

        // PML coefficients
        RA01 = RA[INDEX2D_R(0,j1)] - 1;
        RB0 = RB[INDEX2D_R(0,j1)];
        RE0 = RE[INDEX2D_R(0,j1)];
        RF0 = RF[INDEX2D_R(0,j1)];

        // Hx
        materialHx = ID[INDEX4D_ID(3,ii,jj,kk)];
        dEz = (Ez[INDEX3D_FIELDS(ii,jj+1,kk)] - Ez[INDEX3D_FIELDS(ii,jj,kk)]) / dy;
        Hx[INDEX3D_FIELDS(ii,jj,kk)] = Hx[INDEX3D_FIELDS(ii,jj,kk)] - updatecoeffsH[INDEX2D_MAT(materialHx,4)] * (RA01 * dEz + RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(0,i1,j1,k1)] = RE0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] - RF0 * dEz;
    }

    if (p2 == 0 && i2 < nx && j2 < ny && k2 < nz) {
        // Subscripts for field arrays
        ii = i2 + xs;
        jj = j2 + ys;
        kk = k2 + zs;

        // PML coefficients
        RA01 = RA[INDEX2D_R(0,j2)] - 1;
        RB0 = RB[INDEX2D_R(0,j2)];
        RE0 = RE[INDEX2D_R(0,j2)];
        RF0 = RF[INDEX2D_R(0,j2)];

        // Hz
        materialHz = ID[INDEX4D_ID(5,ii,jj,kk)];
        dEx = (Ex[INDEX3D_FIELDS(ii,jj+1,kk)] - Ex[INDEX3D_FIELDS(ii,jj,kk)]) / dy;
        Hz[INDEX3D_FIELDS(ii,jj,kk)] = Hz[INDEX3D_FIELDS(ii,jj,kk)] + updatecoeffsH[INDEX2D_MAT(materialHz,4)] * (RA01 * dEx + RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(0,i2,j2,k2)] = RE0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] - RF0 * dEx;
    }
}


__global__ void order2_yplus(int xs, int xf, int ys, int yf, int zs, int zf, int NX_PHI1, int NY_PHI1, int NZ_PHI1, int NX_PHI2, int NY_PHI2, int NZ_PHI2, int NY_R, const unsigned int* __restrict__ ID, const $REAL* __restrict__ Ex, const $REAL* __restrict__ Ey, const $REAL* __restrict__ Ez, $REAL *Hx, const $REAL* __restrict__ Hy, $REAL *Hz, $REAL *PHI1, $REAL *PHI2, const $REAL* __restrict__ RA, const $REAL* __restrict__ RB, const $REAL* __restrict__ RE, const $REAL* __restrict__ RF, $REAL d) {

    //  This function updates the Hx and Hz field components for the yplus slab.
    //
    //  Args:
    //      xs, xf, ys, yf, zs, zf: Cell coordinates of PML slab
    //      NX_PHI, NY_PHI, NZ_PHI, NY_R: Dimensions of PHI1, PHI2, and R PML arrays
    //      ID, E, H: Access to ID and field component arrays
    //      Phi, RA, RB, RE, RF: Access to PML magnetic coefficient arrays
    //      d: Spatial discretisation, e.g. dx, dy or dz

    // Obtain the linear index corresponding to the current tREad
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Convert the linear index to subscripts for PML PHI1 (4D) arrays
    int p1 = idx / (NX_PHI1 * NY_PHI1 * NZ_PHI1);
    int i1 = (idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) / (NY_PHI1 * NZ_PHI1);
    int j1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) / NZ_PHI1;
    int k1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) % NZ_PHI1;

    // Convert the linear index to subscripts for PML PHI2 (4D) arrays
    int p2 = idx / (NX_PHI2 * NY_PHI2 * NZ_PHI2);
    int i2 = (idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) / (NY_PHI2 * NZ_PHI2);
    int j2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) / NZ_PHI2;
    int k2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) % NZ_PHI2;

    $REAL RA0, RB0, RE0, RF0, RA1, RB1, RE1, RF1, RA01, dEx, dEz;
    $REAL dy = d;
    int ii, jj, kk, materialHx, materialHz;
    int nx = xf - xs;
    int ny = yf - ys;
    int nz = zf - zs;

    if (p1 == 0 && i1 < nx && j1 < ny && k1 < nz) {
        // Subscripts for field arrays
        ii = i1 + xs;
        jj = j1 + ys;
        kk = k1 + zs;

        // PML coefficients
        RA0 = RA[INDEX2D_R(0,j1)];
        RB0 = RB[INDEX2D_R(0,j1)];
        RE0 = RE[INDEX2D_R(0,j1)];
        RF0 = RF[INDEX2D_R(0,j1)];
        RA1 = RA[INDEX2D_R(1,j1)];
        RB1 = RB[INDEX2D_R(1,j1)];
        RE1 = RE[INDEX2D_R(1,j1)];
        RF1 = RF[INDEX2D_R(1,j1)];
        RA01 = RA[INDEX2D_R(0,j1)] * RA[INDEX2D_R(1,j1)] - 1;

        // Hx
        materialHx = ID[INDEX4D_ID(3,ii,jj,kk)];
        dEz = (Ez[INDEX3D_FIELDS(ii,jj+1,kk)] - Ez[INDEX3D_FIELDS(ii,jj,kk)]) / dy;
        Hx[INDEX3D_FIELDS(ii,jj,kk)] = Hx[INDEX3D_FIELDS(ii,jj,kk)] - updatecoeffsH[INDEX2D_MAT(materialHx,4)] * (RA01 * dEz + RA1 * RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] + RB1 * PHI1[INDEX4D_PHI1(1,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(1,i1,j1,k1)] = RE1 * PHI1[INDEX4D_PHI1(1,i1,j1,k1)] - RF1 * (RA0 * dEz + RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(0,i1,j1,k1)] = RE0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] - RF0 * dEz;
    }

    if (p2 == 0 && i2 < nx && j2 < ny && k2 < nz) {
        // Subscripts for field arrays
        ii = i2 + xs;
        jj = j2 + ys;
        kk = k2 + zs;

        // PML coefficients
        RA0 = RA[INDEX2D_R(0,j2)];
        RB0 = RB[INDEX2D_R(0,j2)];
        RE0 = RE[INDEX2D_R(0,j2)];
        RF0 = RF[INDEX2D_R(0,j2)];
        RA1 = RA[INDEX2D_R(1,j2)];
        RB1 = RB[INDEX2D_R(1,j2)];
        RE1 = RE[INDEX2D_R(1,j2)];
        RF1 = RF[INDEX2D_R(1,j2)];
        RA01 = RA[INDEX2D_R(0,j2)] * RA[INDEX2D_R(1,j2)] - 1;

        // Hz
        materialHz = ID[INDEX4D_ID(5,ii,jj,kk)];
        dEx = (Ex[INDEX3D_FIELDS(ii,jj+1,kk)] - Ex[INDEX3D_FIELDS(ii,jj,kk)]) / dy;
        Hz[INDEX3D_FIELDS(ii,jj,kk)] = Hz[INDEX3D_FIELDS(ii,jj,kk)] + updatecoeffsH[INDEX2D_MAT(materialHz,4)] * (RA01 * dEx + RA1 * RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] + RB1 * PHI2[INDEX4D_PHI2(1,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(1,i2,j2,k2)] = RE1 * PHI2[INDEX4D_PHI2(1,i2,j2,k2)] - RF1 * (RA0 * dEx + RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(0,i2,j2,k2)] = RE0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] - RF0 * dEx;
    }
}


__global__ void order1_zminus(int xs, int xf, int ys, int yf, int zs, int zf, int NX_PHI1, int NY_PHI1, int NZ_PHI1, int NX_PHI2, int NY_PHI2, int NZ_PHI2, int NY_R, const unsigned int* __restrict__ ID, const $REAL* __restrict__ Ex, const $REAL* __restrict__ Ey, const $REAL* __restrict__ Ez, $REAL *Hx, $REAL *Hy, const $REAL* __restrict__ Hz, $REAL *PHI1, $REAL *PHI2, const $REAL* __restrict__ RA, const $REAL* __restrict__ RB, const $REAL* __restrict__ RE, const $REAL* __restrict__ RF, $REAL d) {

    //  This function updates the Hx and Hy field components for the zminus slab.
    //
    //  Args:
    //      xs, xf, ys, yf, zs, zf: Cell coordinates of PML slab
    //      NX_PHI, NY_PHI, NZ_PHI, NY_R: Dimensions of PHI1, PHI2, and R PML arrays
    //      ID, E, H: Access to ID and field component arrays
    //      Phi, RA, RB, RE, RF: Access to PML magnetic coefficient arrays
    //      d: Spatial discretisation, e.g. dx, dy or dz

    // Obtain the linear index corresponding to the current tREad
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Convert the linear index to subscripts for PML PHI1 (4D) arrays
    int p1 = idx / (NX_PHI1 * NY_PHI1 * NZ_PHI1);
    int i1 = (idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) / (NY_PHI1 * NZ_PHI1);
    int j1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) / NZ_PHI1;
    int k1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) % NZ_PHI1;

    // Convert the linear index to subscripts for PML PHI2 (4D) arrays
    int p2 = idx / (NX_PHI2 * NY_PHI2 * NZ_PHI2);
    int i2 = (idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) / (NY_PHI2 * NZ_PHI2);
    int j2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) / NZ_PHI2;
    int k2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) % NZ_PHI2;

    $REAL RA01, RB0, RE0, RF0, dEx, dEy;
    $REAL dz = d;
    int ii, jj, kk, materialHx, materialHy;
    int nx = xf - xs;
    int ny = yf - ys;
    int nz = zf - zs;

    if (p1 == 0 && i1 < nx && j1 < ny && k1 < nz) {
        // Subscripts for field arrays
        ii = i1 + xs;
        jj = j1 + ys;
        kk = zf - (k1 + 1);

        // PML coefficients
        RA01 = RA[INDEX2D_R(0,k1)] - 1;
        RB0 = RB[INDEX2D_R(0,k1)];
        RE0 = RE[INDEX2D_R(0,k1)];
        RF0 = RF[INDEX2D_R(0,k1)];

        // Hx
        materialHx = ID[INDEX4D_ID(3,ii,jj,kk)];
        dEy = (Ey[INDEX3D_FIELDS(ii,jj,kk+1)] - Ey[INDEX3D_FIELDS(ii,jj,kk)]) / dz;
        Hx[INDEX3D_FIELDS(ii,jj,kk)] = Hx[INDEX3D_FIELDS(ii,jj,kk)] + updatecoeffsH[INDEX2D_MAT(materialHx,4)] * (RA01 * dEy + RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(0,i1,j1,k1)] = RE0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] - RF0 * dEy;
    }

    if (p2 == 0 && i2 < nx && j2 < ny && k2 < nz) {
        // Subscripts for field arrays
        ii = i2 + xs;
        jj = j2 + ys;
        kk = zf - (k2 + 1);

        // PML coefficients
        RA01 = RA[INDEX2D_R(0,k2)] - 1;
        RB0 = RB[INDEX2D_R(0,k2)];
        RE0 = RE[INDEX2D_R(0,k2)];
        RF0 = RF[INDEX2D_R(0,k2)];

        // Hy
        materialHy = ID[INDEX4D_ID(4,ii,jj,kk)];
        dEx = (Ex[INDEX3D_FIELDS(ii,jj,kk+1)] - Ex[INDEX3D_FIELDS(ii,jj,kk)]) / dz;
        Hy[INDEX3D_FIELDS(ii,jj,kk)] = Hy[INDEX3D_FIELDS(ii,jj,kk)] - updatecoeffsH[INDEX2D_MAT(materialHy,4)] * (RA01 * dEx + RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(0,i2,j2,k2)] = RE0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] - RF0 * dEx;
    }
}


__global__ void order2_zminus(int xs, int xf, int ys, int yf, int zs, int zf, int NX_PHI1, int NY_PHI1, int NZ_PHI1, int NX_PHI2, int NY_PHI2, int NZ_PHI2, int NY_R, const unsigned int* __restrict__ ID, const $REAL* __restrict__ Ex, const $REAL* __restrict__ Ey, const $REAL* __restrict__ Ez, $REAL *Hx, $REAL *Hy, const $REAL* __restrict__ Hz, $REAL *PHI1, $REAL *PHI2, const $REAL* __restrict__ RA, const $REAL* __restrict__ RB, const $REAL* __restrict__ RE, const $REAL* __restrict__ RF, $REAL d) {

    //  This function updates the Hx and Hy field components for the zminus slab.
    //
    //  Args:
    //      xs, xf, ys, yf, zs, zf: Cell coordinates of PML slab
    //      NX_PHI, NY_PHI, NZ_PHI, NY_R: Dimensions of PHI1, PHI2, and R PML arrays
    //      ID, E, H: Access to ID and field component arrays
    //      Phi, RA, RB, RE, RF: Access to PML magnetic coefficient arrays
    //      d: Spatial discretisation, e.g. dx, dy or dz

    // Obtain the linear index corresponding to the current tREad
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Convert the linear index to subscripts for PML PHI1 (4D) arrays
    int p1 = idx / (NX_PHI1 * NY_PHI1 * NZ_PHI1);
    int i1 = (idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) / (NY_PHI1 * NZ_PHI1);
    int j1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) / NZ_PHI1;
    int k1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) % NZ_PHI1;

    // Convert the linear index to subscripts for PML PHI2 (4D) arrays
    int p2 = idx / (NX_PHI2 * NY_PHI2 * NZ_PHI2);
    int i2 = (idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) / (NY_PHI2 * NZ_PHI2);
    int j2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) / NZ_PHI2;
    int k2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) % NZ_PHI2;

    $REAL RA0, RB0, RE0, RF0, RA1, RB1, RE1, RF1, RA01, dEx, dEy;
    $REAL dz = d;
    int ii, jj, kk, materialHx, materialHy;
    int nx = xf - xs;
    int ny = yf - ys;
    int nz = zf - zs;

    if (p1 == 0 && i1 < nx && j1 < ny && k1 < nz) {
        // Subscripts for field arrays
        ii = i1 + xs;
        jj = j1 + ys;
        kk = zf - (k1 + 1);

        // PML coefficients
        RA0 = RA[INDEX2D_R(0,k1)];
        RB0 = RB[INDEX2D_R(0,k1)];
        RE0 = RE[INDEX2D_R(0,k1)];
        RF0 = RF[INDEX2D_R(0,k1)];
        RA1 = RA[INDEX2D_R(1,k1)];
        RB1 = RB[INDEX2D_R(1,k1)];
        RE1 = RE[INDEX2D_R(1,k1)];
        RF1 = RF[INDEX2D_R(1,k1)];
        RA01 = RA[INDEX2D_R(0,k1)] * RA[INDEX2D_R(1,k1)] - 1;

        // Hx
        materialHx = ID[INDEX4D_ID(3,ii,jj,kk)];
        dEy = (Ey[INDEX3D_FIELDS(ii,jj,kk+1)] - Ey[INDEX3D_FIELDS(ii,jj,kk)]) / dz;
        Hx[INDEX3D_FIELDS(ii,jj,kk)] = Hx[INDEX3D_FIELDS(ii,jj,kk)] + updatecoeffsH[INDEX2D_MAT(materialHx,4)] * (RA01 * dEy + RA1 * RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] + RB1 * PHI1[INDEX4D_PHI1(1,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(1,i1,j1,k1)] = RE1 * PHI1[INDEX4D_PHI1(1,i1,j1,k1)] - RF1 * (RA0 * dEy + RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(0,i1,j1,k1)] = RE0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] - RF0 * dEy;
    }

    if (p2 == 0 && i2 < nx && j2 < ny && k2 < nz) {
        // Subscripts for field arrays
        ii = i2 + xs;
        jj = j2 + ys;
        kk = zf - (k2 + 1);

        // PML coefficients
        RA0 = RA[INDEX2D_R(0,k2)];
        RB0 = RB[INDEX2D_R(0,k2)];
        RE0 = RE[INDEX2D_R(0,k2)];
        RF0 = RF[INDEX2D_R(0,k2)];
        RA1 = RA[INDEX2D_R(1,k2)];
        RB1 = RB[INDEX2D_R(1,k2)];
        RE1 = RE[INDEX2D_R(1,k2)];
        RF1 = RF[INDEX2D_R(1,k2)];
        RA01 = RA[INDEX2D_R(0,k2)] * RA[INDEX2D_R(1,k2)] - 1;

        // Hy
        materialHy = ID[INDEX4D_ID(4,ii,jj,kk)];
        dEx = (Ex[INDEX3D_FIELDS(ii,jj,kk+1)] - Ex[INDEX3D_FIELDS(ii,jj,kk)]) / dz;
        Hy[INDEX3D_FIELDS(ii,jj,kk)] = Hy[INDEX3D_FIELDS(ii,jj,kk)] - updatecoeffsH[INDEX2D_MAT(materialHy,4)] * (RA01 * dEx + RA1 * RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] + RB1 * PHI2[INDEX4D_PHI2(1,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(1,i2,j2,k2)] = RE1 * PHI2[INDEX4D_PHI2(1,i2,j2,k2)] - RF1 * (RA0 * dEx + RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(0,i2,j2,k2)] = RE0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] - RF0 * dEx;
    }
}


__global__ void order1_zplus(int xs, int xf, int ys, int yf, int zs, int zf, int NX_PHI1, int NY_PHI1, int NZ_PHI1, int NX_PHI2, int NY_PHI2, int NZ_PHI2, int NY_R, const unsigned int* __restrict__ ID, const $REAL* __restrict__ Ex, const $REAL* __restrict__ Ey, const $REAL* __restrict__ Ez, $REAL *Hx, $REAL *Hy, const $REAL* __restrict__ Hz, $REAL *PHI1, $REAL *PHI2, const $REAL* __restrict__ RA, const $REAL* __restrict__ RB, const $REAL* __restrict__ RE, const $REAL* __restrict__ RF, $REAL d) {

    //  This function updates the Hx and Hy field components for the zplus slab.
    //
    //  Args:
    //      xs, xf, ys, yf, zs, zf: Cell coordinates of PML slab
    //      NX_PHI, NY_PHI, NZ_PHI, NY_R: Dimensions of PHI1, PHI2, and R PML arrays
    //      ID, E, H: Access to ID and field component arrays
    //      Phi, RA, RB, RE, RF: Access to PML magnetic coefficient arrays
    //      d: Spatial discretisation, e.g. dx, dy or dz

    // Obtain the linear index corresponding to the current tREad
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Convert the linear index to subscripts for PML PHI1 (4D) arrays
    int p1 = idx / (NX_PHI1 * NY_PHI1 * NZ_PHI1);
    int i1 = (idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) / (NY_PHI1 * NZ_PHI1);
    int j1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) / NZ_PHI1;
    int k1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) % NZ_PHI1;

    // Convert the linear index to subscripts for PML PHI2 (4D) arrays
    int p2 = idx / (NX_PHI2 * NY_PHI2 * NZ_PHI2);
    int i2 = (idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) / (NY_PHI2 * NZ_PHI2);
    int j2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) / NZ_PHI2;
    int k2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) % NZ_PHI2;

    $REAL RA01, RB0, RE0, RF0, dEx, dEy;
    $REAL dz = d;
    int ii, jj, kk, materialHx, materialHy;
    int nx = xf - xs;
    int ny = yf - ys;
    int nz = zf - zs;

    if (p1 == 0 && i1 < nx && j1 < ny && k1 < nz) {
        // Subscripts for field arrays
        ii = i1 + xs;
        jj = j1 + ys;
        kk = k1 + zs;

        // PML coefficients
        RA01 = RA[INDEX2D_R(0,k1)] - 1;
        RB0 = RB[INDEX2D_R(0,k1)];
        RE0 = RE[INDEX2D_R(0,k1)];
        RF0 = RF[INDEX2D_R(0,k1)];

        // Hx
        materialHx = ID[INDEX4D_ID(3,ii,jj,kk)];
        dEy = (Ey[INDEX3D_FIELDS(ii,jj,kk+1)] - Ey[INDEX3D_FIELDS(ii,jj,kk)]) / dz;
        Hx[INDEX3D_FIELDS(ii,jj,kk)] = Hx[INDEX3D_FIELDS(ii,jj,kk)] + updatecoeffsH[INDEX2D_MAT(materialHx,4)] * (RA01 * dEy + RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(0,i1,j1,k1)] = RE0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] - RF0 * dEy;
    }

    if (p2 == 0 && i2 < nx && j2 < ny && k2 < nz) {
        // Subscripts for field arrays
        ii = i2 + xs;
        jj = j2 + ys;
        kk = k2 + zs;

        // PML coefficients
        RA01 = RA[INDEX2D_R(0,k2)] - 1;
        RB0 = RB[INDEX2D_R(0,k2)];
        RE0 = RE[INDEX2D_R(0,k2)];
        RF0 = RF[INDEX2D_R(0,k2)];

        // Hy
        materialHy = ID[INDEX4D_ID(4,ii,jj,kk)];
        dEx = (Ex[INDEX3D_FIELDS(ii,jj,kk+1)] - Ex[INDEX3D_FIELDS(ii,jj,kk)]) / dz;
        Hy[INDEX3D_FIELDS(ii,jj,kk)] = Hy[INDEX3D_FIELDS(ii,jj,kk)] - updatecoeffsH[INDEX2D_MAT(materialHy,4)] * (RA01 * dEx + RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(0,i2,j2,k2)] = RE0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] - RF0 * dEx;
    }
}


__global__ void order2_zplus(int xs, int xf, int ys, int yf, int zs, int zf, int NX_PHI1, int NY_PHI1, int NZ_PHI1, int NX_PHI2, int NY_PHI2, int NZ_PHI2, int NY_R, const unsigned int* __restrict__ ID, const $REAL* __restrict__ Ex, const $REAL* __restrict__ Ey, const $REAL* __restrict__ Ez, $REAL *Hx, $REAL *Hy, const $REAL* __restrict__ Hz, $REAL *PHI1, $REAL *PHI2, const $REAL* __restrict__ RA, const $REAL* __restrict__ RB, const $REAL* __restrict__ RE, const $REAL* __restrict__ RF, $REAL d) {

    //  This function updates the Hx and Hy field components for the zplus slab.
    //
    //  Args:
    //      xs, xf, ys, yf, zs, zf: Cell coordinates of PML slab
    //      NX_PHI, NY_PHI, NZ_PHI, NY_R: Dimensions of PHI1, PHI2, and R PML arrays
    //      ID, E, H: Access to ID and field component arrays
    //      Phi, RA, RB, RE, RF: Access to PML magnetic coefficient arrays
    //      d: Spatial discretisation, e.g. dx, dy or dz

    // Obtain the linear index corresponding to the current tREad
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Convert the linear index to subscripts for PML PHI1 (4D) arrays
    int p1 = idx / (NX_PHI1 * NY_PHI1 * NZ_PHI1);
    int i1 = (idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) / (NY_PHI1 * NZ_PHI1);
    int j1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) / NZ_PHI1;
    int k1 = ((idx % (NX_PHI1 * NY_PHI1 * NZ_PHI1)) % (NY_PHI1 * NZ_PHI1)) % NZ_PHI1;

    // Convert the linear index to subscripts for PML PHI2 (4D) arrays
    int p2 = idx / (NX_PHI2 * NY_PHI2 * NZ_PHI2);
    int i2 = (idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) / (NY_PHI2 * NZ_PHI2);
    int j2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) / NZ_PHI2;
    int k2 = ((idx % (NX_PHI2 * NY_PHI2 * NZ_PHI2)) % (NY_PHI2 * NZ_PHI2)) % NZ_PHI2;

    $REAL RA0, RB0, RE0, RF0, RA1, RB1, RE1, RF1, RA01, dEx, dEy;
    $REAL dz = d;
    int ii, jj, kk, materialHx, materialHy;
    int nx = xf - xs;
    int ny = yf - ys;
    int nz = zf - zs;

    if (p1 == 0 && i1 < nx && j1 < ny && k1 < nz) {
        // Subscripts for field arrays
        ii = i1 + xs;
        jj = j1 + ys;
        kk = k1 + zs;

        // PML coefficients
        RA0 = RA[INDEX2D_R(0,k1)];
        RB0 = RB[INDEX2D_R(0,k1)];
        RE0 = RE[INDEX2D_R(0,k1)];
        RF0 = RF[INDEX2D_R(0,k1)];
        RA1 = RA[INDEX2D_R(1,k1)];
        RB1 = RB[INDEX2D_R(1,k1)];
        RE1 = RE[INDEX2D_R(1,k1)];
        RF1 = RF[INDEX2D_R(1,k1)];
        RA01 = RA[INDEX2D_R(0,k1)] * RA[INDEX2D_R(1,k1)] - 1;

        // Hx
        materialHx = ID[INDEX4D_ID(3,ii,jj,kk)];
        dEy = (Ey[INDEX3D_FIELDS(ii,jj,kk+1)] - Ey[INDEX3D_FIELDS(ii,jj,kk)]) / dz;
        Hx[INDEX3D_FIELDS(ii,jj,kk)] = Hx[INDEX3D_FIELDS(ii,jj,kk)] + updatecoeffsH[INDEX2D_MAT(materialHx,4)] * (RA01 * dEy + RA1 * RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] + RB1 * PHI1[INDEX4D_PHI1(1,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(1,i1,j1,k1)] = RE1 * PHI1[INDEX4D_PHI1(1,i1,j1,k1)] - RF1 * (RA0 * dEy + RB0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)]);
        PHI1[INDEX4D_PHI1(0,i1,j1,k1)] = RE0 * PHI1[INDEX4D_PHI1(0,i1,j1,k1)] - RF0 * dEy;
    }

    if (p2 == 0 && i2 < nx && j2 < ny && k2 < nz) {
        // Subscripts for field arrays
        ii = i2 + xs;
        jj = j2 + ys;
        kk = k2 + zs;

        // PML coefficients
        RA0 = RA[INDEX2D_R(0,k2)];
        RB0 = RB[INDEX2D_R(0,k2)];
        RE0 = RE[INDEX2D_R(0,k2)];
        RF0 = RF[INDEX2D_R(0,k2)];
        RA1 = RA[INDEX2D_R(1,k2)];
        RB1 = RB[INDEX2D_R(1,k2)];
        RE1 = RE[INDEX2D_R(1,k2)];
        RF1 = RF[INDEX2D_R(1,k2)];
        RA01 = RA[INDEX2D_R(0,k2)] * RA[INDEX2D_R(1,k2)] - 1;

        // Hy
        materialHy = ID[INDEX4D_ID(4,ii,jj,kk)];
        dEx = (Ex[INDEX3D_FIELDS(ii,jj,kk+1)] - Ex[INDEX3D_FIELDS(ii,jj,kk)]) / dz;
        Hy[INDEX3D_FIELDS(ii,jj,kk)] = Hy[INDEX3D_FIELDS(ii,jj,kk)] - updatecoeffsH[INDEX2D_MAT(materialHy,4)] * (RA01 * dEx + RA1 * RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] + RB1 * PHI2[INDEX4D_PHI2(1,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(1,i2,j2,k2)] = RE1 * PHI2[INDEX4D_PHI2(1,i2,j2,k2)] - RF1 * (RA0 * dEx + RB0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)]);
        PHI2[INDEX4D_PHI2(0,i2,j2,k2)] = RE0 * PHI2[INDEX4D_PHI2(0,i2,j2,k2)] - RF0 * dEx;
    }
}

""")
