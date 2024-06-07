from collections import Counter
from argparse import ArgumentParser
from json import load as json_load, loads as json_loads

from mboxparser.utils import OpenFileOrSTDStreams, stdin_or_existing_file


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-i', '--input', type=stdin_or_existing_file, default='-', metavar='FILENAME',
                        help='JSON file name (default: STDIN)')
    parser.add_argument('-o', '--output', type=str, metavar='FILENAME', default='-',
                        help='File to write the output into (default: STDOUT)')

    args = parser.parse_args()

    return args


def main():
    args = parse_args()

    with OpenFileOrSTDStreams(args.input, encoding='UTF-8') as infile_fh:
        # Restore tuple keys for dict from JSON in JSON representation
        #  (JSON does not allow tuple (list) as dictionary key)
        payload_types = {tuple(json_loads(key)): freq
                         for key, freq in sorted(json_load(infile_fh).items(),
                                                 key=lambda x: (x[1], x[0]), reverse=True)
                         }

    # Make simplifications for easier handling
    new_payload_types = Counter()
    for k, v in payload_types.items():
        k = list(k)
        k[4] = k[4] is not None  # We don't care for the actual encoding
        k[-1] = k[-1] is not None  # We don't care for the actual filenames
        k = tuple(k)
        new_payload_types[k] += v

    with OpenFileOrSTDStreams(args.output, 'w', encoding='UTF-8') as out_fh:
        print('Has payload?', 'Is multipart', 'Has parts', 'Content disposition', 'Has encoding?',
              'Content type (MIME)', 'Detected Content type (MIME)', 'Has filename?', 'Freq',
              sep='\t', file=out_fh)
        # Print out the feature tuples with decreasing frequency tabulated
        for feats, freq in new_payload_types.most_common():
            print(*feats, freq, sep='\t', file=out_fh)


if __name__ == '__main__':
    main()
