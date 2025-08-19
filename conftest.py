import os
import sys

# Add vendors directory so bundled python-chess can be imported in tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'vendors')))
