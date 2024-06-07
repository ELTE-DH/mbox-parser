from argparse import ArgumentParser
from collections import defaultdict, Counter

from json_header_grep import grep_header
from mboxparser.utils import OpenFileOrSTDStreams, stdin_or_existing_file


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-i', '--input', type=stdin_or_existing_file, default='-', metavar='FILENAME',
                        help='JSON file name (default: STDIN)')
    parser.add_argument('-o', '--output', type=str, metavar='FILENAME', default='-',
                        help='File to write the output into (default: STDOUT)')
    parser.add_argument('-r', '--header', type=str, required=True,
                        help='Header name to grep')

    args = parser.parse_args()

    return args


def main():
    args = parse_args()

    h = grep_header(args.input, args.header)

    d = defaultdict(Counter)

    # Gather different names with their frequencies for each address
    for address_list, freq in h:
        for name, address in address_list:
            d[address][name] += freq

    with OpenFileOrSTDStreams(args.output, 'w', encoding='UTF-8') as out_fh:
        for address, names in sorted(d.items(), key=lambda x: (x[1].total(), x[0]), reverse=True):
            print(address, names.total(), sep='\t', file=out_fh)
            # Print out the names with decreasing frequency tabulated
            for name, freq in names.most_common():
                print('', name, freq, sep='\t', file=out_fh)


if __name__ == '__main__':
    main()
