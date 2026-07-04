#!/usr/bin/env python3
"""Manage AsUsual topic.md and audit.jsonl.

AsUsual runtime state is audit-first. This public entrypoint delegates to
the internal as_usual_topic_log package while preserving the CLI contract.
"""

from __future__ import annotations

import sys

from as_usual_topic_log.cli import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
