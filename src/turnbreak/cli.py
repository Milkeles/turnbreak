from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    print(f"turnbreak: no commands implemented yet (got: {args!r})", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
