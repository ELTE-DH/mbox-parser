from magic import from_buffer as magic_from_buffer

from .decoders import decode_elem, decode_with_fallback


def process_payload_r(email_data, type_count):
    # 1. Retrive features
    filename = email_data.get_filename()
    is_multipart = email_data.is_multipart()
    content_type = email_data.get_content_type()
    payload = email_data.get_payload(decode=True)
    content_charset = email_data.get_content_charset()
    content_disposition = email_data.get_content_disposition()  # Empirically unusable
    coded_payload = email_data.get_payload()  # Helper for has_parts
    has_parts = isinstance(coded_payload, list) and len(coded_payload) > 0

    # 2. Detect content type if there is content
    detected_content_type, has_payload = None, False
    if payload is not None:
        # Has content (other than list of payload parts which results in None when decode=True in get_payload() )
        has_payload = True
        detected_content_type = magic_from_buffer(payload[:2048], mime=True)
    # 3. Decode filename
    if filename is not None:
        filename = decode_elem(filename)

    # 4. Gather statistics for gaining insight
    type_count[(has_payload, is_multipart, has_parts, content_disposition, content_charset, content_type,
                detected_content_type, filename)] += 1

    # 5. Process parts recursively
    ret = []
    if is_multipart:  # Emmpirically: is_multipart == not has_payload == has_parts
        # Multipart -> Iterate subparts and go down a level
        parts = email_data.get_payload()  # No decoding -> Get the list of subparts
        for part in parts:
            ret.extend(process_payload_r(part, type_count))  # Recursion
    elif filename is not None:
        ret.append(('attachment', filename))  # Add attachment filename
    elif content_charset is None and content_type not in {'text/plain', 'text/rfc822-headers', 'text/html'}:
        pass  # Erroneous files (mostly inline images) WITHOUT filename -> Ignore
    elif content_charset is None and content_type in {'text/plain', 'text/rfc822-headers', 'text/html'}:
        # Erroneous texts WITHOUT encoding
        payload = payload.strip()
        if len(payload) > 0:  # Filter dummy (0 long) payloads
            msg = decode_with_fallback(payload, 'UTF-8')
            ret.append((content_type, msg))
    elif (content_charset is not None and detected_content_type in {'application/x-empty',
                                                                    'application/x-bytecode.python',
                                                                    'application/octet-stream',
                                                                    'audio/x-mp4a-latm',
                                                                    'message/rfc822',
                                                                    'text/calendar',
                                                                    'text/csv'}):
        # Erroneous texts WITH encoding
        payload = payload.strip()
        if len(payload) > 1:  # Filter dummy (0 or 1 long) payloads e.g. 'g', '.', '-'
            msg = decode_with_fallback(payload, content_charset)
            ret.append((content_type, msg))
    else:  # Not multipart, not has filename, has charset, not eroneous stuff -> Should be OK
        msg = decode_with_fallback(payload, content_charset)
        ret.append((content_type, msg))

    return ret
