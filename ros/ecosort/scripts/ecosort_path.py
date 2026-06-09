import os
import sys


def setup_ecosort_src_path():
    try:
        import rospkg

        pkg_path = rospkg.RosPack().get_path("ecosort")
        repo_src = os.path.abspath(os.path.join(pkg_path, "..", "..", "src"))
    except Exception:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        repo_src = os.path.abspath(os.path.join(script_dir, "..", "..", "..", "src"))

    if repo_src not in sys.path:
        sys.path.insert(0, repo_src)
    return repo_src
