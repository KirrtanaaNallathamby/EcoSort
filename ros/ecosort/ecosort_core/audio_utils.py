import contextlib
import os


@contextlib.contextmanager
def quiet_alsa(enabled=True):
    """Suppress harmless ALSA stderr from PyAudio / sound_play on robot hardware."""
    if not enabled:
        yield
        return

    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    os.dup2(devnull, 2)
    try:
        yield
    finally:
        os.dup2(old_stderr, 2)
        os.close(devnull)
        os.close(old_stderr)
