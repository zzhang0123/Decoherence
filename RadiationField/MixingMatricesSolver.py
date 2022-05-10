import math
import numpy as np
from . import mpiutil
import h5py

def TransferMatrix_rowN(Chi, N):
    return math.sqrt((Chi - 2 * N - 1) * (Chi - 2 * N) * (N + 1))

def solve_Chi_eigen_sys(Chi):
    Nmax = math.floor(Chi / 2)
    A = np.zeros((Nmax + 1, Nmax + 1))
    for i in range(Nmax):
        A[i, i + 1] = A[i + 1, i] = TransferMatrix_rowN(Chi, i + 1)
    eig_vals, eig_vecs = np.linalg.eigh(A)
    return eig_vals, eig_vecs

def solve_whole_system_and_save_3(chimax):
    rank=mpiutil.rank
    size=mpiutil.size
    nbatch = math.floor(chimax/size)
    for i in range(nbatch+1):
        mpiutil.barrier()
        chi: int = rank + size * i
        eigvals, eigvecs = solve_Chi_eigen_sys(chi)
        f1 = h5py.File('eigenvalues.hdf5', 'w', driver='mpio', comm=mpiutil._comm)
        f1.create_dataset(str(chi), data=eigvals)
        f2 = h5py.File('eigenvectors.hdf5', 'w', driver='mpio', comm=mpiutil._comm)
        f2.create_dataset(str(chi), data=eigvecs, chunks=True)
        mpiutil.barrier()
        f1.close()
        f2.close()
    return None

def solve_whole_system_and_save_2(chimax):
    f1 = h5py.File('eigenvalues.hdf5', 'w', driver='mpio', comm=mpiutil._comm)
    f2 = h5py.File('eigenvectors.hdf5', 'w', driver='mpio', comm=mpiutil._comm)

    def solve_Chi_eigen_sys_2(Chi):
        Nmax = math.floor(Chi / 2)
        A = np.zeros((Nmax + 1, Nmax + 1))
        for i in range(Nmax):
            A[i, i + 1] = A[i + 1, i] = TransferMatrix_rowN(Chi, i + 1)
        eig_vals, eig_vecs = np.linalg.eigh(A)
        f1.create_dataset(str(Chi), data=eig_vals)
        f2.create_dataset(str(Chi), data=eig_vecs)
        return None

    chi_array = list(np.arange(chimax + 1))
    mpiutil.parallel_jobs_no_gather(solve_Chi_eigen_sys_2, chi_array, method="alt")
    f1.close()
    f2.close()
    return None

def solve_whole_system_and_save_1(chimin, chimax):
    chi_array = list(np.arange(chimin, chimax + 1))
    Result = mpiutil.parallel_map(solve_Chi_eigen_sys, chi_array, method="alt")
    eig_vals_list, eig_vecs_list = list(zip(*Result))
    if mpiutil.rank0:
        f1 = h5py.File('eigenvalues.hdf5', 'w')
        f1.create_dataset(str(chimax), data=eig_vals_list, chunks=True)
        f1.close()
        f2 = h5py.File('eigenvectors.hdf5', 'w')
        f2.create_dataset(str(chimax), data=eig_vecs_list , chunks=True)
        f2.close()
    return

