#!/usr/bin/env python3
"""Manage AsUsual find-cause issue journals.

Issue runtime state is journal-first. This public entrypoint delegates to
the internal as_usual_journal_log package while preserving the CLI contract.
"""

from __future__ import annotations

import sys

from as_usual_journal_log.cli import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
