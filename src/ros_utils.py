import os
import sys


def add_src_to_path():
    src_dir = os.path.dirname(os.path.abspath(__file__))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)


def get_capture_dir():
    return os.getenv("ECOSORT_CAPTURE_DIR", "captures")
