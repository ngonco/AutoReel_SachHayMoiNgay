"""Batch using the same plans/settings as the studio. Shutdown is opt-in only."""
import sys
import subprocess
from app import main

if __name__ == '__main__':
    shutdown_requested = '--shutdown' in sys.argv
    if '--batch' not in sys.argv:
        sys.argv.append('--batch')
    main()
    if shutdown_requested:
        subprocess.run(['shutdown','/s','/t','120'],check=True)
