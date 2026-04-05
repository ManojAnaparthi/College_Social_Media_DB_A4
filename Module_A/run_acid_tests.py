"""
Simple test runner for Module A
Run from Module_A directory: python run_acid_tests.py
"""

import sys
import unittest
from pathlib import Path

# Add parent directory to path so 'database' can be imported as a package
module_a_path = Path(__file__).parent
parent_path = module_a_path.parent
if str(parent_path) not in sys.path:
    sys.path.insert(0, str(parent_path))

# Now run the tests
if __name__ == "__main__":
    print("=" * 80)
    print("  MODULE A: ACID VALIDATION TEST SUITE")
    print("=" * 80)
    print()
    
    # Import the test module
    from Module_A.database import test_acid_multirelation
    
    # Load and run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_acid_multirelation)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n ALL TESTS PASSED!")
    else:
        print("\n SOME TESTS FAILED")
    
    sys.exit(0 if result.wasSuccessful() else 1)
