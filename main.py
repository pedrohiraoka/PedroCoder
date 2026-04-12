#!/usr/bin/env python3
"""
AstroLink - Your Intelligent Astronomical Laboratory

Main entry point for the AstroLink application.

Usage:
    python main.py [--debug]
    
Options:
    --debug     Enable debug logging
"""

import sys


def main():
    """Main entry point."""
    print("=" * 60)
    print("🌌 AstroLink - Your Intelligent Astronomical Laboratory")
    print("=" * 60)
    print()
    
    try:
        from astrolink.core.app import run
        
        print("Starting AstroLink v1.0.0...")
        print()
        
        exit_code = run()
        
        return exit_code
        
    except ImportError as e:
        print(f"Error: Missing required dependency: {e}")
        print()
        print("Please install dependencies:")
        print("  pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
