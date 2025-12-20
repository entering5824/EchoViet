# Audio processing package
# Ensure FFmpeg is configured early so that downstream imports (e.g., librosa/audioread)
# see the configured ffmpeg binary and PATH before they try to detect backends.
try:
    from .ffmpeg_setup import ensure_ffmpeg
    # Best-effort setup (silent): do not raise if setup fails here
    ensure_ffmpeg(silent=True)
except Exception:
    # If setup fails at package import time, don't break importers; errors will be shown
    # at runtime where audio is required.
    pass

