#!/usr/bin/env python
import os
import sys

# Ensure that the src directory is in the Python module search path.
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import the main function from your main.py in src.
from main import main

if __name__ == "__main__":
    main()
