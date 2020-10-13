"""
    used to conver byte string to appropriate file size.
"""


def file_size(size):
    """ size must be a # of bytes """

    size = int(size) if isinstance(size, int) else int(size[:-1])
    old_size = size
    # for bits
    if size < 1000:
        return str(size) + " bytes"

    # for kb
    size = size / 1000
    if size < 1000:
        return str(round(size, 2)) + " KB"

    # for mb
    size = size / 1000
    if size < 1000:
        return str(round(size, 2)) + " MB"

    # for gb
    size = size / 1000
    if size < 1000:
        return str(round(size, 2)) + " GB"

    # for tb
    size = size / 1000
    if size < 1000:
        return str(round(size, 2)) + " TB"

    return str(old_size) + " bytes"
