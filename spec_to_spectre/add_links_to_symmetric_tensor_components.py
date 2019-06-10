import argparse
import h5py
import numpy as np
import shutil

if __name__ == "__main__":
    help = """Takes a spectre-volume-data-format HDF5 file
    that contains SpacetimeMetric, Pi, and Phi, and makes
    soft links for off-diagonal components. This script
    assumes that the data in the HDF5 file consits of
    the spacetime components tt, tx, ty, tz, xx, xy, xz, yy, yz, zz.
    The soft links map xt -> tx, yx -> xy, etc.
    """
    parser = argparse.ArgumentParser(description=help)
    parser.add_argument('--input', required=True,
                        help = """Name of HDF5 file""")
    args = parser.parse_args()

    spacetime_components = ["t", "x", "y", "z"]
    symmetric_tensors_in_file = ["Phi_x",  "Phi_y", "Phi_z", "Pi_",
                                 "SpacetimeMetric_"]

    file = h5py.File(args.input, 'a')
    base = "element_data.vol"
    for obs_id in file[base].keys():
        for cell in file[base][obs_id].keys():
            for tensor in symmetric_tensors_in_file:
                for i,comp1 in enumerate(spacetime_components):
                    for j,comp2 in enumerate(spacetime_components):
                        if i > j:
                            file[base][obs_id][cell][tensor+comp1+comp2] = \
                              h5py.SoftLink("/" + base + "/" + obs_id + "/"
                                            + cell + "/" + tensor
                                            + comp2 + comp1)
    file.close()
