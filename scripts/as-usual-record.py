#!/usr/bin/env python3
"""Manage AsUsual work-unit records (contexts.md + audit.jsonl).

One helper serves all three work units — topic, direct-work, and issue. This
public entrypoint delegates to the internal as_usual_record package while
preserving the CLI contract.
"""

from __future__ import annotations

import sys

from as_usual_record.cli import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
