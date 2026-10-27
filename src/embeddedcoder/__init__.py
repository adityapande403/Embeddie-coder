"""
EmbeddedCoder AI: Universal Embedded Systems Engineering Small Language Model
"""

__version__ = "0.1.0"
__author__ = "EmbeddedCoder AI Team"

try:
    from embeddedcoder.inference.engine import EmbeddedCoder
    __all__ = ["EmbeddedCoder", "__version__"]
except ImportError:
    __all__ = ["__version__"]
