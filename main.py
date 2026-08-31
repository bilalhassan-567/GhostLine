"""Vercel / generic ASGI entrypoint. The real app lives in ghostline.console.app."""

from ghostline.console.app import app

__all__ = ["app"]
