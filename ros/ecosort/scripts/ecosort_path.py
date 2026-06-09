import os
import sys


def setup_ecosort_src_path():
    """Add ecosort package root so ecosort_core can be imported."""
    try:
        import rospkg
        pkg_path = rospkg.RosPack().get_path("ecosort")
    except Exception:
        pkg_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if pkg_path not in sys.path:
        sys.path.insert(0, pkg_path)
    return pkg_path
