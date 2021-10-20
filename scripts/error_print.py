"""Used for getting full stack trace exception messages."""

import sys
import traceback


def full_stack():
    """Return full stack trace of an exception."""
    exc = sys.exc_info()[0]
    if exc is not None:
        frame = sys.exc_info()[-1].tb_frame.f_back
        stack = traceback.extract_stack(frame)
    else:
        stack = traceback.extract_stack()[:-1]  # last one would be full_stack()
    trc = "Traceback (most recent call last):\n"
    stackstr = trc + "".join(traceback.format_list(stack))
    if exc is not None:
        # pylint: disable=bad-str-strip-call
        stackstr += "  " + traceback.format_exc().lstrip(trc)
    return stackstr
