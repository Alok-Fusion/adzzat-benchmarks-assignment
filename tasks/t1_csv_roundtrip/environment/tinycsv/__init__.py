"""tinycsv: a dependency-free CSV reader/writer for constrained Python runtimes."""
from .reader import read
from .writer import write

__all__ = ["read", "write"]
__version__ = "0.3.1"
