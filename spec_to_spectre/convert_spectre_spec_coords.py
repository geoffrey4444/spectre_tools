import argparse
import h5py
import numpy as np
import shutil

def rename_variables(legend_line):
    """Takes a string containing space-delimited tensor names and
    returns the restring with some tensors renamed:
        psi, kappa, H and GradH (i.e., flattened SpacetimeDerivH)
        ->
        SpacetimeMetric, Pi/Phi, GaugeH, and SpacetimeDerivGaugeH
    """
    legend_line = legend_line.replace('psi', 'SpacetimeMetric_')
    legend_line = legend_line.replace('kappat', 'Pi_')
    legend_line = legend_line.replace('kappax', 'Phi_x').replace('kappay', 'Phi_y').replace('kappaz', 'Phi_z')
    legend_line = legend_line.replace('GradH', 'SpacetimeDerivInitialGaugeH_')
    legend_line = legend_line.replace(' H', ' InitialGaugeH_')
    return legend_line.rstrip()

def get_spectre_points_per_block(spectre_file):
    """Reads a file produced by spectre's ExportCoordinates
    and returns two lists: i) the number of points in each block
    and ii) the names of the blocks."""
    observation_id = list(spectre_file['element_data.vol'].keys())[0]
    coords_dict = dict(spectre_file['element_data.vol'][observation_id])
    components = ['InertialCoordinates_x', 'InertialCoordinates_y', 'InertialCoordinates_z']

    blocks = list(coords_dict.keys())[:]

    points_per_block = []
    for block in blocks:
        points_per_block.append(len(coords_dict[block][components[0]]))
    return np.array(points_per_block), np.array(blocks)

def get_spec_points(spectre_file):
    """Converts points from a file produced by spectre's ExportCoordinates
    to a flat list of points, suitable for SpEC to read in (e.g.,
    for interpolating data onto those points)"""
    observation_id = list(spectre_file['element_data.vol'].keys())[0]
    coords_dict = dict(spectre_file['element_data.vol'][observation_id])

    blocks = list(coords_dict.keys())[:]
    components = ['InertialCoordinates_x', 'InertialCoordinates_y', 'InertialCoordinates_z']
    dim = len(components)

    coords = []
    for component in components:
        coords.append([])

    for block in blocks:
        for i,component in enumerate(components):
            coords[i].append(coords_dict[block][component])
    return np.transpose(np.array([np.concatenate(x) for x in coords]))

def get_spectre_values_from_spec_values(array_1D, blocks, points_per_block):
    """Take a 1D array of values, listed point-by-point (as returned by spec),
    and return a dictionary, keyed by block name, of the values at each
    spectre point. Here blocks is a list of blocks from a spectre volume file,
    e.g., the file output by ExportCoordinates, and points_per_block is
    a list containing the number of points in each block."""
    spectre_values = {}
    for i,block in enumerate(blocks):
        start = np.sum(points_per_block[:i])
        end = start + points_per_block[i]
        spectre_values[block] = array_1D[start:end]
    return spectre_values

def write_spec_points_file(spectre_points_filename, spec_points_filename):
    """Read the coordinates from a spectre domain and write them in a
    file readable by spec's InterpolateToSpecifiedPoints. The input arguments
    are the name of a spectre points file (e.g. 'VolumeData0.h5') and
    the name of the spec points file to write (e.g. 'PointsList.txt')."""
    spectre_file = h5py.File(spectre_points_filename, 'r')
    points_per_block, blocks = get_spectre_points_per_block(spectre_file)
    points = get_spec_points(spectre_file)
    spectre_file.close()
    np.savetxt(spec_points_filename, points)

def insert_spec_data(spectre_points_filename, spec_data_filename):
    """Insert tensor data given in the spectre volume-data file
    named spec_data_filename (typically output by spec's
    InterpolateToSpecifiedPoints) into the spectre volume-data file named
    spectre_points_filename. Note that this function will rename some
    variables if it finds them by calling rename_variables()"""
    # Read the interpolated data into a numpy array
    data_to_insert = np.genfromtxt(spec_data_filename)

    # Get the legend
    spec_file = open(spec_data_filename, 'r')
    lines = spec_file.readlines()

    # spec output lists the components as a comment on the second line
    # in the format '# psitt psitx ...'
    legend_line = lines[1][2:]
    legend_line = rename_variables(legend_line)
    legend = legend_line.split(" ")

    legend_dict = {}
    for i, key in enumerate(legend):
        legend_dict[key] = i
    spec_file.close()

    # Open file read-only to determine block names, etc.
    spectre_file = h5py.File(spectre_points_filename, 'r')
    points_per_block, blocks = get_spectre_points_per_block(spectre_file)
    observation_id = list(spectre_file['element_data.vol'].keys())[0]
    spectre_file.close()

    # Open file ready to append data
    output_file = h5py.File(spectre_points_filename, 'a')

    # Loop over keys
    for key in legend_dict:
        print("Inserting " + key)
        spec_data = data_to_insert[:, legend_dict[key]]
        spectre_data = get_spectre_values_from_spec_values(spec_data,
                                                           blocks,
                                                           points_per_block)
        for block in blocks:
            output_file['element_data.vol'][observation_id][block][key] \
                = spectre_data[block]

    output_file.close()
    return legend_dict, data_to_insert

if __name__ == "__main__":
    help = """Convert data between spec and spectre. This script reads
    the spectre domain from a spectre volume-data file specified by
    --spectre-points-filename, output e.g. by
    spectre's ExportCoordinates3D executable. If the option
    --output-spec-points-filename is given, this script will write the
    spectre grid coordinates into a file to be read by spec's
    InterpolateToSpecifiedPoints. If the option
    --spec-data-to-insert-filename is given, this script will read data
    from the specified file, which contains output from spec's
    InterpolateToSpecifiedPoints (with option DumpAllDataIntoSingleFile=yes).
    Then, this script will insert that data into a copy of the spectre
    volume-data file specified by --output-spectre-points-filename.
    """
    parser = argparse.ArgumentParser(description=help)
    parser.add_argument('--spectre-points-filename', required=True,
                        help = """Name of spectre volume data file
                        containing the x,y,z coordinates of a
                        spectre domain.""")
    parser.add_argument('--output-spec-points-filename', required=False,
                        help = """If specified, output coordinates in spec
                        format to this file""")
    parser.add_argument('--spec-data-to-insert-filename', required=False,
                        help = """If specified, insert data from this file
                        into the spectre volume data file given by
                        --output-spectre-points-filename (if specified).""")
    parser.add_argument('--output-spectre-points-filename', required=False,
                        help = """If --spec-data-to-insert-filename is
                        specified and this option is specified,
                        copy the file given by --spectre-points-filename
                        to a new file with name
                        --output-spectre-points-filename, and then insert
                        the data contained in the file given by
                        --spec-data-to-insert-filename.""")
    args = parser.parse_args()

    if args.output_spec_points_filename is not None:
        write_spec_points_file(args.spectre_points_filename,
                               args.output_spec_points_filename)

    if args.spec_data_to_insert_filename is not None:
        print("Inserting data from " + args.spec_data_to_insert_filename)
        if args.output_spectre_points_filename is not None:
            print("Inserting into " + args.output_spectre_points_filename)
            shutil.copyfile(args.spectre_points_filename,
                            args.output_spectre_points_filename)
            insert_spec_data(args.output_spectre_points_filename,
                             args.spec_data_to_insert_filename)
