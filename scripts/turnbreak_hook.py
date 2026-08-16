# Convenience importable wrapper for the hook script (underscore name).
from . import turnbreak_hook as impl

# Re-export main and helpers
main = impl.main
_detect_event = impl._detect_event
