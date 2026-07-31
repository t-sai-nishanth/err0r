"""Traceback frame walking helpers."""

from __future__ import annotations

import linecache
import sys
import traceback
from types import TracebackType

from bookerrror.tracer.models import FrameInfo


def _is_user_frame(filename: str) -> bool:
    if filename.startswith("<ipython-input-"):
        return True
    if filename.startswith("<stdin>") or filename.startswith("<string>"):
        return True
    if filename.startswith("<frozen "):
        return False
    return "/site-packages/" not in filename and "/lib/python" not in filename


def _cell_id_from_filename(filename: str) -> str:
    if filename.startswith("<ipython-input-"):
        return filename[1:-1]
    return filename


def _walk_traceback(traceback_object: TracebackType | None) -> FrameInfo | None:
    selected = None
    while traceback_object is not None:
        frame = traceback_object.tb_frame
        filename = frame.f_code.co_filename
        lineno = traceback_object.tb_lineno
        source_line = linecache.getline(filename, lineno).strip()
        candidate = FrameInfo(
            filename=filename,
            lineno=lineno,
            source_line=source_line,
            cell_id=_cell_id_from_filename(filename),
            locals=dict(frame.f_locals),
        )
        if _is_user_frame(filename):
            selected = candidate
        elif selected is None:
            selected = candidate
        traceback_object = traceback_object.tb_next
    return selected


def find_failure_frame(exception) -> FrameInfo | None:
    """Return the innermost user-code frame for an exception."""

    traceback_object = exception.__traceback__ if isinstance(exception, BaseException) else None
    if traceback_object is None:
        return None
    return _walk_traceback(traceback_object)
