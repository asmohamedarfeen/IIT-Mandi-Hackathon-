"""Explicit offline evaluation; --verify audits the published OOF run without fitting."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.model_quality.evaluation import evaluate_dataset, verify_run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=ROOT / 'extention of Z-Alizadeh sani dataset.xlsx')
    parser.add_argument('--bundle', type=Path, default=ROOT / 'artifacts/cardiovision_ensemble.joblib')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/model_quality')
    parser.add_argument('--verify', action='store_true', help='Recompute every stored diagnostic from private OOF records; no model fitting')
    args = parser.parse_args()
    if args.verify:
        verify_run(args.output)
    else:
        run = evaluate_dataset(args.dataset, args.bundle, args.output)
        print(f'Published completed evaluation: {run}', flush=True)
        verify_run(args.output)


if __name__ == '__main__':
    main()
