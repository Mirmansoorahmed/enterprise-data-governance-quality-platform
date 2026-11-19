"""`make hybrid-status` — print which hybrid adapters are live vs mocked.

Reads only DG_* env. With no credentials everything is mocked. Never contacts a
live service. Standard-library only.
"""

from __future__ import annotations

import json

from . import status


def main() -> int:
    summary = status.summary()
    print(json.dumps(summary, indent=2))
    print("\nall mocked:", status.all_mocked(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
