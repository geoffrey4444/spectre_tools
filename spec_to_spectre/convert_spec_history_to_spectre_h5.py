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
    # SpECTRE currently supports 2nd order or 3rd order piecewise polynomials,
    # which have 8 or 9 columns, respectively.
    if len(history_line_values) == 8 or len(history_line_values) == 9:
        return history_line_values
    else:
        sys.exit("Error: wrong number of columns in history file")


def parse_history_file(lines):
    matrix = []
    for line in lines:
        matrix.append(parse_history_line(line))
    return matrix


def remove_nonmonotonic_times(parsed_history_data):
    # Keep the latest occurance, so reverse the list, so latest times are first
    reversed = parsed_history_data
    reversed.reverse()

    # Check last update time for uniqueness, since that is what SpECTRE checks
    # Time of last update is in column 1
    next_time = reversed[0][1]
    prev_time = next_time
    first_row = False

    result = []

    for row in parsed_history_data:
        if (first_row):
            result.append(row)
            first_row = True
            prev_time = row[1]
        elif row[1] < prev_time:
            result.append(row)
            prev_time = row[1]
    result.reverse()
    return result


def legend(converted_history_data):
    legend_second_order = [
        "Time", "TimeLastUpdate", "Nc", "DerivOrder", "Version", "f", "dtf",
        "dt2f"
    ]
    legend_third_order = [
        "Time", "TimeLastUpdate", "Nc", "DerivOrder", "Version", "f", "dtf",
        "dt2f", "dt3f"
    ]
    if len(converted_history_data[0]) == 8:
        return legend_second_order
    else:
        return legend_third_order


def parse_history_file_name(name):
    # Name has form "Hist-FuncNAME.txt" (no quotes). Return NAME
    return name.split('.')[0].split("Func")[-1]


def append_to_file(converted_history_data, output, name):
    file_spec = spectre_h5.H5File(file_name=output, append_to_file=True)
    file_spec.insert_dat(path="/" + name,
                         legend=legend(converted_history_data),
                         version=0)
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
        append_to_file(
            remove_nonmonotonic_times(
                parse_history_file(read_history_file(history_file))),
            args.output, parse_history_file_name(history_file.split("/")[-1]))
