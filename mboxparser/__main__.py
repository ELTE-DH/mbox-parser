import sys
from pathlib import Path
from email.header import Header
from argparse import ArgumentParser
from pickle import dump as pickle_dump
from collections import Counter, defaultdict
from email.utils import parsedate_to_datetime
from json import dump as json_dump, dumps as json_dumps

from mboxparser.openers import open_mbox
from mboxparser.payload import process_payload_r
from mboxparser.utils import OpenFileOrSTDStreams, existing_file
from mboxparser.decoders import decode_addresslike_values, decode_elem


def parse_args():
    parser = ArgumentParser()
    group1 = parser.add_argument_group('Input properties',
                                       'Choose if the input is a plain MBOX file or one in a ZIP file')
    group1.add_argument('-m', '--mbox_file', type=Path, default=None, metavar='FILENAME.MBOX',
                        help='Path to the plain MBOX file (if the exitsts the other two arguments are ignored'
                             ' else this file is written from the other two argument if this argument is supplied)')
    # These two must be specified together if used or the one above must be an existent file!
    group1.add_argument('-i', '--input_zip', type=existing_file, default=None, metavar='FILENAME.ZIP',
                        help='Path to the ZIP file containing the MBOX file')
    # We cannot check this file for existence yet, just convert it to Path object for now
    group1.add_argument('-p', '--mbox_path_in_zip', type=Path, default=None, metavar='PATH/IN/ZIP/TO/FILENAME.MBOX',
                        help='Path to mbox file in ZIP file')

    parser.add_argument('-o', '--output', type=str, metavar='FILENAME', default='-',
                        help='File to write the output into (default: STDOUT)')

    group2 = parser.add_argument_group('Optional actions', 'Enable or keep disabled the following optional actions')
    group2.add_argument('-v', '--verbose', action='store_true',
                        help='Write additional info (slows down processing)')
    group2.add_argument('-k', '--process_payload', action='store_true',
                        help='Process payload together with headers')
    group2.add_argument('-t', '--header_toplist', action='store_true',
                        help='Write the freqency toplist of the lowercased headers to the output (specified by -o)')
    group2.add_argument('-c', '--header_casevariants', action='store_true',
                        help='Write the freqency toplist of header case variants to the output (specified by -o)')
    group2.add_argument('-b', '--bad_headers', action='store_true',
                        help='Write the pickled bad headers to the output (specified by -o)')
    group2.add_argument('-f', '--final_data', action='store_true',
                        help='Write the final (normalised) data as JSON Lines to the output (specified by -o)')
    group2.add_argument('-j', '--header_json', type=Path, default=None, metavar='FILENAME.JSON',
                        help='Write the frequencies of header-value pairs to JSON for further examination')
    group2.add_argument('-l', '--payload_type_json', type=Path, default=None, metavar='FILENAME.JSON',
                        help='Write the frequencies of payload parts to JSON for further examination')

    args = parser.parse_args()

    # Homebrewed mutual argument groups
    if (args.mbox_file is None or
            (not args.mbox_file.is_file() and (args.input_zip is None or args.mbox_path_in_zip is None))):
        parser.error('Either -m/--mbox_file must be an existing file'
                     ' or both -i/--input_zip and -p/--mbox_path_in_zip must be specified!')

    # Force processing payload if final data is printed
    args.process_payload |= args.final_data

    return args


ADDRESS_HEADER = {'to', 'from', 'cc', 'bcc', 'delivered-to', 'reply-to', 'sender'}


def handle_bad_header(k, v):
    # Put quirks here if needed!
    # Quirks can be classified by header names (we use lowercased header names)
    _ = k
    return str(v)


def process_one_email(email_obj, headers_dict, header_variants, bad_headers, payload_type_count, process_payload=False,
                      verbose=False):
    # I. Metadata
    # I/1. Collect the frequency of the varitants of each lowercased header key
    lower_headers = set()
    for k, value_list in email_obj.items():
        k_lower = k.lower()
        header_variants[k_lower][k] += 1  # Global lowercased and actual header key variants
        lower_headers.add(k_lower)  # The actual lowercased which belong to this email object

    # I/2. Iterate over the lowercased header key variants only
    header_value_pairs = {}
    for k in lower_headers:
        # get_all() retrieves all casing variant of header key k
        value_list = email_obj.get_all(k, [])
        # I/2a. Decode address type headers
        if k in ADDRESS_HEADER:
            value_list = decode_addresslike_values(value_list)
        else:
            new_value_list = []
            for val in value_list:
                # I/2b. Collect bad headers for inspection
                if isinstance(val, Header):
                    bad_headers.append((k, val))
                    val = handle_bad_header(k, val)
                # I/2c. Parse date (and reformat it to ISO timestamp) and decode other encoded header values
                if k == 'date':
                    val = val.replace(' -0000', ' +0000')  # Fix timestamp to contain UTC timezone
                    val = parsedate_to_datetime(val).isoformat()  # Reformat dates to ISO timestamps
                elif '=?' in val:
                    val = decode_elem(val)
                new_value_list.append(val)
            value_list = tuple(new_value_list)

        header_value_pairs[k] = value_list
        headers_dict[k][value_list] += 1

    # II. Payload
    parts = []
    if process_payload:
        # II/1. Recursively process payload and extract text parts (plain text, HTML) and attachment names
        parts = process_payload_r(email_obj, payload_type_count)
        if verbose:
            print('Parts len:', len(parts), file=sys.stderr)

    return {'headers': header_value_pairs, 'payload': parts}


def main():
    args = parse_args()

    # 1. Open MBOX (mbox_file.is_file() OR (mbox_file is not None or (input_zip AND mbox_path_in_zip)))
    my_mbox = open_mbox(args.mbox_file, args.input_zip, args.mbox_path_in_zip)

    with OpenFileOrSTDStreams(args.output, 'w', encoding='UTF-8') as out_fh:
        if args.verbose:
            # len() is slow to compute on big mbox files!
            print('Number of entries in mbox:', len(my_mbox), file=sys.stderr)

        # 2. Process each email individually one after another
        # header_key -> header_value -> header_value_freq
        headers_dict = defaultdict(Counter)
        header_variants = defaultdict(Counter)
        # features_tuple -> features_tuple_freq
        payload_type_count = Counter()
        bad_headers = []
        for idx, email_obj in enumerate(my_mbox, start=1):
            if args.verbose:
                print(idx, file=sys.stderr)
            email_data = process_one_email(email_obj, headers_dict, header_variants, bad_headers, payload_type_count,
                                           args.process_payload, args.verbose)

            # 3. Print normalised data as JSON Lines
            if args.final_data:
                print(json_dumps(email_data, ensure_ascii=False), file=out_fh)

        # 4. Print statistics
        if args.header_toplist:
            # The freqency toplist of the lowercased headers (without their values) at a glance
            header_count = {key: value.total() for key, value in headers_dict.items()}
            print('Metadata (lowercased) toplist:', file=out_fh)
            for k, v in sorted(header_count.items(), key=lambda x: (x[1], x[0]), reverse=True):
                print(f'{k}:', v, file=out_fh)

        if args.header_casevariants:
            # The freqency toplist of the header case variants (without their values) at a glance
            print('Metadata (case variants) toplist:', file=out_fh)
            for k, v in sorted(header_variants.items(), key=lambda x: (x[1].total(), x[0]), reverse=True):
                for variant, freq in v.most_common():
                    print(k, variant, freq, sep='\t', file=out_fh)

    # 5. Dump diagnostics for further analysis
    if args.header_json is not None:
        # Header-value pairs and their frequency to JSON for further examination
        with open(args.header_json, 'w', encoding='UTF-8') as fh:
            # JSON does not allow tuple (list) as dictionary key -> Tuples are converted to JSON
            new_header_dict = defaultdict(Counter)
            for k, v in headers_dict.items():
                for k2, v2 in v.most_common():
                    new_header_dict[k][json_dumps(k2, ensure_ascii=False)] = v2
            json_dump(new_header_dict, fh, ensure_ascii=False, indent=4)

    if args.payload_type_json is not None:
        # Payload part features for each part in each email for further analysis
        with open(args.payload_type_json, 'w', encoding='UTF-8') as fh:
            # JSON does not allow tuple (list) as dictionary key -> Tuples are converted to JSON
            new_payload_type_count = {}
            for k, v in payload_type_count.most_common():
                new_payload_type_count[json_dumps(k, ensure_ascii=False)] = v
            json_dump(new_payload_type_count, fh, ensure_ascii=False, indent=4)

    if args.bad_headers:
        with OpenFileOrSTDStreams(args.output, 'wb') as out_fh:
            # Dump list of problematic Header classes for manual analysis (also can be used for email parts)
            pickle_dump(bad_headers, out_fh)


if __name__ == '__main__':
    main()
