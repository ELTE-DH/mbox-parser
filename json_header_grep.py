import re
import sys
from argparse import ArgumentParser
from json import load as json_load, loads as json_loads

from mboxparser.utils import OpenFileOrSTDStreams, stdin_or_existing_file


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-i', '--input', type=stdin_or_existing_file, default='-', metavar='FILENAME',
                        help='JSON file name (default: STDIN)')
    parser.add_argument('-o', '--output', type=str, default='-', metavar='FILENAME',
                        help='File to write the output (default: STDOUT)')
    parser.add_argument('-r', '--header', type=str, required=True,
                        help='Header name to grep')
    args = parser.parse_args()

    return args


def remove_newlines(string):
    return re.sub('[ \t]*(\r\n|\r|\n)[ \t]*', ' ', string)


def value_freq_pairs(header_values):
    ret = []
    for key, freq in sorted(header_values.items(), key=lambda x: (x[1], x[0]), reverse=True):
        # Decode JSON in JSON (because JSON does not allow tuple (list) as dictionary key)
        key = json_loads(key)
        new_key = []
        for k in key:
            if isinstance(k, str):  # Only Normal headers may have newlines (address-like ones stored in lists are not)
                k = remove_newlines(k)
            new_key.append(k)
        ret.append((new_key, freq))

    return ret


def grep_header(input_filename, header):
    # Open and load the JSON from STDIN or from the given file
    with OpenFileOrSTDStreams(input_filename, encoding='UTF-8') as infile_fh:
        headers = json_load(infile_fh)

    header_values = headers.get(header)
    if header_values is None:  # Header check
        print(f'There is no such header ({header})!', file=sys.stderr)
        sys.exit(1)

    return value_freq_pairs(header_values)


def main():
    args = parse_args()

    header = args.header.strip('"').strip("'")
    header_values_and_freqs = grep_header(args.input, header)

    with OpenFileOrSTDStreams(args.output, 'w', encoding='UTF-8') as fh:
        print(header, file=fh)
        # Print out the values for the header with decreasing frequency tabulated
        for value, freq in header_values_and_freqs:
            print('', freq, value, sep='\t', file=fh)


if __name__ == '__main__':
    main()
