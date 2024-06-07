from email.utils import getaddresses
from email.header import decode_header


def decode_addresslike_values(values):
    name_address_pairs = []
    # 1. Split all values to name-address pairs
    for name, address in getaddresses(values):
        # 2. Decode (quoted printable, base64, etc. AND charset) to string
        name_decoded = decode_elem(name)
        address = decode_elem(address)  # There are rare cases when decoding the address is needed
        # 3. Collect name address pairs to list
        name_address_pairs.append((name_decoded, address))

    return tuple(name_address_pairs)


def decode_elem(elem):
    elem_chunks = []
    # 1. Decdoe (quoted printable, base64, etc.) elem to chunk-charset pairs
    elem_decoded = decode_header(elem)
    for elem_part, enc in elem_decoded:
        # 2a. Decode by charset if there is any
        if enc is not None:
            elem_part = elem_part.decode(enc)
        elif not isinstance(elem_part, str):
            # 2b. Last resort decoding
            if elem_part.isascii():
                elem_part = elem_part.decode('ASCII')
            else:
                raise NotImplementedError(f'This should be str: {elem_decoded} {elem}')  # This should not happen
        elem_chunks.append(elem_part)

    # 3. Join decoded string parts to one string
    elem_part_joined = ''.join(elem_chunks)

    return elem_part_joined


def decode_with_fallback(payload, content_charset):
    try:
        msg = payload.decode(content_charset)
    except UnicodeDecodeError:
        # Decode with replacements. The text is mostly OK, with some broken part at the end or beyond repair
        # Empirically charted makes it all worse.
        # Idea: The string should be split at the first error and for the second part different encoding should be tried
        msg = payload.decode(content_charset, errors='backslashreplace')
    return msg
