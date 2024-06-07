import sys
from typing import Union
from pathlib import Path
from argparse import ArgumentTypeError


class OpenFileOrSTDStreams:
    """Unified opener for files and STD streams (STDIN, STDOUT)"""
    _MODE_FOR_STD_STREAMS = {'r': sys.stdin,
                             'rb': sys.stdin.buffer,
                             'w': sys.stdout,
                             'wb': sys.stdout.buffer
                             }

    def __init__(self, path: Union[Path, str], mode: str = 'r', **kwargs):
        if path == '-':
            fh = self._MODE_FOR_STD_STREAMS.get(mode)
            if fh is None:
                ValueError(f'Mode ({mode}) is invalid for STD stream (-)!'
                           f' Options are {list(self._MODE_FOR_STD_STREAMS.keys())} !')
            close = False
        else:
            fh = None
            close = True

        self._fh = fh
        self._close = close
        self._path = Path(path)
        self._mode = mode
        self._kwargs = kwargs

    def __enter__(self):
        if self._fh is None:
            self._fh = open(self._path, self._mode, **self._kwargs)
        return self._fh

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self._close:
            self._fh.close()


# Argparse helpers
def stdin_or_existing_file(string) -> Union[Path, str]:
    string_path = Path(string)
    if string == '-':  # STDIN is denoted as - !
        return string
    elif not string_path.is_file():
        raise ArgumentTypeError(f'{string} is not an existing file!')

    return string_path


def existing_file(string):
    stirng_path = Path(string)
    if not stirng_path.is_file():
        raise ArgumentTypeError(f'{string} does not an existing file!')

    return stirng_path
