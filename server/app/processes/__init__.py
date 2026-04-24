"""Importing this package registers all processes via side effect."""
from . import patient_intake   # noqa: F401
from . import patientenakte    # noqa: F401
from . import placeholders     # noqa: F401
from .registry import all_processes, get_process, ProcessSpec

__all__ = ["all_processes", "get_process", "ProcessSpec"]
