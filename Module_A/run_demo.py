"""
Run ACID Demonstration
Run from Module_A directory: python run_demo.py
"""

import sys
from pathlib import Path

# Add parent directory to path so 'Module_A.database' can be imported
module_a_path = Path(__file__).parent
parent_path = module_a_path.parent
if str(parent_path) not in sys.path:
    sys.path.insert(0, str(parent_path))

# Import and run demonstration
from Module_A.database.acid_demonstration import ACIDDemonstrator

if __name__ == "__main__":
    demo = ACIDDemonstrator()
    demo.run_all_demonstrations()
