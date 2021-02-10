import argparse
import numpy as np
import sys

# Requires spectre python bindings to be installed
from spectre import DataStructures
import spectre.IO.H5 as spectre_h5


def read_history_file(path):
    history_file = open(path, 'r')
    lines = history_file.readlines()
    return lines


def parse_history_line(line):
    key_value_pairs = line.split(';')
    history_line_values = []
    for pair in key_value_pairs:
        try:
            history_line_values.append(float(pair.split('=')[-1]))
        except:
            continue
    # History file should have 9 columns for 3rd order piecewise polynomials,
    # which is what SpECTRE expects. If 8 columns, assume that the history
    # file is a 2nd order piecewise polynomial, and set the third derivative
    # to zero.
    if len(history_line_values) == 8 and history_line_values[3] == 2.0:
        history_line_values.append(0.0)
        return history_line_values
    elif len(history_line_values) == 9:
        return history_line_values
    else:
        sys.exit("Error: wrong number of columns in history file")


def parse_history_file(lines):
    matrix = []
    for line in lines:
        matrix.append(parse_history_line(line))
    return matrix


def legend():
    return [
        "Time", "TimeLastUpdate", "Nc", "DerivOrder", "Version", "f", "dtf",
        "dt2f", "dt3f"
    ]


def parse_history_file_name(name):
    # Name has form "Hist-FuncNAME.txt" (no quotes). Return NAME
    return name.split('.')[0].split("Func")[-1]


def append_to_file(converted_history_data, output, name):
    file_spec = spectre_h5.H5File(file_name=output, append_to_file=True)
    file_spec.insert_dat(path="/" + name, legend=legend(), version=0)
    datfile = file_spec.get_dat(path="/" + name)
    for row in converted_history_data:
        datfile.append(list(row))
    file_spec.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description='Convert spec history files into a spectre H5 Dat file')
    p.add_argument('--output',
                   help='Name of output file (including .h5 suffix)')
    p.add_argument('files',
                   metavar='files',
                   nargs='+',
                   help="SpEC history files to convert")
    args = p.parse_args()

    for history_file in args.files:
        print("Converting " + history_file)
        append_to_file(parse_history_file(read_history_file(history_file)),
                       args.output,
                       parse_history_file_name(history_file.split("/")[-1]))
