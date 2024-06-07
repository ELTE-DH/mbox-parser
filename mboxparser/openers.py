import builtins
from mailbox import mbox
from pathlib import Path
from zipfile import ZipFile


def _mbox_w_fake_open(fh):
    """Hack to be able to open a mailbox from file-handle"""
    # 1. Save open()
    original_open = builtins.open

    # 2. Define fake open() to intercept the call
    def fake_open(*_):
        return fh

    # 3. Set the fake open()
    builtins.open = fake_open

    # 4. Open the mailbox with fake open()
    opened_mbox = mbox('FAKE PATH')

    # 5. Restore open()
    builtins.open = original_open

    # 6. Return the opened mbox
    return opened_mbox


def _mbox_from_zip_file(inp_zip_path: Path, mbox_path_in_zip: Path, out_mbox_path: Path = None):
    """Opens (and optionally extracts) an MBOX file in ZIP files e.g. Google Takeout archives"""
    with ZipFile(inp_zip_path) as zipfh:
        # Zipfile.open() does not yet (?) support Path as filename
        with zipfh.open(str(mbox_path_in_zip)) as mbox_fh:  # bytes
            if out_mbox_path is not None:
                with open(out_mbox_path, 'wb') as out_fh:
                    out_fh.writelines(mbox_fh)
                ret = mbox(out_mbox_path)
            else:
                ret = _mbox_w_fake_open(mbox_fh)

    return ret


def open_mbox(mbox_path: Path = None, inp_zip_path: Path = None, mbox_path_in_zip: Path = None):
    """Open plain MBOX file or one in from ZIP file optionally extracting it if all three variables are set"""
    if mbox_path.is_file():
        # a) The MBOX file (mbox_path) is already exists -> Open it
        my_mbox = mbox(mbox_path)
    elif inp_zip_path is not None and inp_zip_path.is_file() and mbox_path_in_zip is not None:
        # b) ZIP file (inp_zip_path) and MBOX path in ZIP file (mbox_path_in_zip) are supplied to open from the archive
        # c) All three variables are supplied to extract the MBOX path (mbox_path_in_zip)
        #    form ZIP file (inp_zip_path) to the MBOX file (mbox_path)
        my_mbox = _mbox_from_zip_file(inp_zip_path, mbox_path_in_zip, mbox_path)
    else:
        raise ValueError(f'Either mbox_path should be an existing file ({mbox_path}) or'
                         f' both inp_zip_path ({inp_zip_path}) and mbox_path_in_zip (mbox_path_in_zip) should be set!')

    return my_mbox
