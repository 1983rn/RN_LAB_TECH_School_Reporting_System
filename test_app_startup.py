#!/usr/bin/env python3
"""
Quick test to verify Flask application starts properly
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_app_startup():
    """Test if the Flask app can be imported and initialized"""
    try:
        print("Testing Flask application startup...")
        
        # Import the app
        from app import app
        
        # Test app configuration
        print(f"✓ App imported successfully")
        print(f"✓ App name: {app.name}")
        print(f"✓ Template folder: {app.template_folder}")
        print(f"✓ Static folder: {app.static_folder}")
        print(f"✓ Secret key configured: {'Yes' if app.secret_key else 'No'}")
        
        # Test app context
        with app.app_context():
            print("✓ App context created successfully")
        
        # Test test client
        client = app.test_client()
        print("✓ Test client created successfully")
        
        print("\n🎉 Flask application startup test PASSED!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during startup test: {e}")
        return False

if __name__ == "__main__":
    success = test_app_startup()
    sys.exit(0 if success else 1)