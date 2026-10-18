"""Entry point. Run from the project root with the project venv, e.g.

    .venv\\Scripts\\python code\\run.py stack up
    .venv\\Scripts\\python code\\run.py validate --trials 3          (quick)
    .venv\\Scripts\\python code\\run.py validate                     (full: 10 trials per cell)
    .venv\\Scripts\\python code\\run.py stack down
    .venv\\Scripts\\python code\\run.py grid --name dev_smoke --preset smoke --workers 3
    .venv\\Scripts\\python code\\run.py grid --name dev_grid --preset dev --dry
    .venv\\Scripts\\python code\\run.py freeze [--check]            (pre-registration freeze, docs/PROTOCOL.md)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "stack":
        from actrec import stack
        sub = rest[0] if rest else "status"
        if sub == "up":
            stack.up(engine="--engine" in rest)
        elif sub == "down":
            stack.down()
        else:
            stack.status()
    elif cmd == "validate":
        from actrec import validate_env
        validate_env.main(rest)
    elif cmd == "child":
        from actrec.episode import child_main
        child_main(rest[0])
    elif cmd == "freeze":
        from actrec import freeze
        freeze.main(rest)
    elif cmd == "grid":
        from actrec import runner
        runner.main(rest)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
