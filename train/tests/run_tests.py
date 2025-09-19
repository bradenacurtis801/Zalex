#!/usr/bin/env python3
"""
Test runner for ScanPro training tests.
"""

import sys
from pathlib import Path

# Add the train directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_trained_model import test_trained_model, test_with_custom_text

def main():
    """Run all tests."""
    print("🧪 Running ScanPro Training Tests")
    print("=" * 60)
    
    # Test with existing documents
    success = test_trained_model()
    
    if success:
        # Test with custom text
        test_with_custom_text()
        print("\n🎉 All tests completed successfully!")
        return True
    else:
        print("\n❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
