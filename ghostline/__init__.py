"""Ghostline — a phone-powered data-verification engine.

Give it a table of records and a claim pack; it calls the numbers via CALL-E, extracts
what the human actually said with a mandatory verbatim evidence span, and returns
MATCH / MISMATCH / UNCLEAR / NO CONTACT — never a guess it cannot support.
"""

__version__ = "0.1.0"
