#!/usr/bin/env python3
"""CLI tool for validating AI Integrator configuration files.

Usage:
    python scripts/validate_config.py config.yaml
    python scripts/validate_config.py --env  # Uses AI_INTEGRATOR_CONFIG
    
Exit codes:
    0 - Valid configuration
    1 - Validation errors
    2 - File not found or parse error
"""

import sys
import argparse
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_integrator.utils.config_loader import load_config
from ai_integrator.core.validation import validate_config, ConfigValidationError


def main():
    parser = argparse.ArgumentParser(
        description="Validate AI Integrator configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s config.yaml                    # Validate specific file
    %(prog)s --env                          # Use AI_INTEGRATOR_CONFIG env var
    %(prog)s config.yaml --strict           # Treat warnings as errors
    %(prog)s config.yaml --quiet            # Only show errors
        """,
    )
    parser.add_argument(
        "config_file",
        nargs="?",
        help="Path to configuration file (YAML or JSON)",
    )
    parser.add_argument(
        "--env",
        action="store_true",
        help="Load config from AI_INTEGRATOR_CONFIG environment variable",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only show errors, not warnings or success messages",
    )
    
    args = parser.parse_args()
    
    # Determine config source
    if args.env:
        config_path = None
    elif args.config_file:
        config_path = args.config_file
    else:
        parser.error("Either config_file or --env is required")
    
    # Load configuration
    try:
        config = load_config(config_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"ERROR: Failed to parse config: {e}", file=sys.stderr)
        sys.exit(2)
    
    # Validate
    result = validate_config(config)
    
    # Report errors
    if result.errors:
        for error in result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
    
    # Report warnings
    if result.warnings and not args.quiet:
        for warning in result.warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
    
    # Determine exit code
    if result.errors:
        sys.exit(1)
    elif result.warnings and args.strict:
        print("FAILED: Warnings treated as errors (--strict)", file=sys.stderr)
        sys.exit(1)
    else:
        if not args.quiet:
            providers = list(result.settings.providers.keys()) if result.settings else []
            print(f"OK: Configuration valid. Providers: {providers}")
        sys.exit(0)


if __name__ == "__main__":
    main()
