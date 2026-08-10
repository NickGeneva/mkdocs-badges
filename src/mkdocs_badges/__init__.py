"""Status badges and interactive filters for Zensical and MkDocs."""

from .plugin import BadgesPlugin
from .zensical import ZensicalBadgesExtension

__all__ = ["BadgesPlugin", "ZensicalBadgesExtension"]
__version__ = "0.3.0"
