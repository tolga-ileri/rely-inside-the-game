"""Entrypoint: uvicorn main:app --host 127.0.0.1 --port 8100"""
from rely_brain.api import app

__all__ = ["app"]
