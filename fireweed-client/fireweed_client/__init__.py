"""fireweed-client — the official Python SDK for the Fireweed Memory API (thin HTTP wrapper)."""
from .client import FireweedClient, FireweedError

__version__ = "0.1.0"
__all__ = ["FireweedClient", "FireweedError"]
