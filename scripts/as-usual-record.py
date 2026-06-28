#!/usr/bin/env python3
"""Compatibility wrapper for the AsUsual audit-first topic helper.

The official runtime helper is scripts/topic-log.py. This wrapper remains so
older references to scripts/as-usual-record.py still append audit-first topic
events through the same helper.
"""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("topic-log.py")), run_name="__main__")
