#!/usr/bin/env python
import argparse
import sys
from stockbit_analyzer.runner import main as run_analyzer

def parse_args():
    parser = argparse.ArgumentParser(description="Stockbit Broker Summary Analyzer")
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode"
    )
    parser.add_argument(
        "--manual-login",
        action="store_true",
        help="Enable manual login mode - browser will wait for you to log in manually"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    try:
        run_analyzer(manual_login=args.manual_login)
        return 0
    except Exception as e:
        if args.debug:
            raise
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 