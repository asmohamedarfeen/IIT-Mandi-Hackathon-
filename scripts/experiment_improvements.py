#!/usr/bin/env python3
"""Compatibility entrypoint for the isolated model quality evaluator.

The former same-OOF weight and threshold optimization experiment is retired.
This command uses the shared evaluator and never replaces production models.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def run_test():
    from scripts.evaluate_model_quality import main
    return main()


if __name__ == "__main__":
    raise SystemExit(run_test())
