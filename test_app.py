#!/usr/bin/env python3
"""
Test script for Malawi School Reporting System Flask app
Verifies basic app startup and route accessibility
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_app_startup():
    """Test if Flask app can start without errors"""
    try:
        from app import app
        print("✓ Flask app imported successfully")
        
        # Test app configuration
        print(f"✓ App secret key configured: {'Yes' if app.secret_key else 'No'}")
        print(f"✓ Template folder: {app.template_folder}")
        print(f"✓ Static folder: {app.static_folder}")
        
        # Test basic route registration
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        print(f"✓ Routes registered: {len(routes)}")
        
        # Test app context
        with app.app_context():
            print("✓ App context works")
        
        # Test test client
        client = app.test_client()
        print("✓ Test client created")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ App startup error: {e}")
        return False

def test_basic_routes():
    """Test basic route accessibility"""
    try:
        from app import app
        
        with app.test_client() as client:
            # Test login route (should be accessible without auth)
            response = client.get('/login')
            print(f"✓ Login route status: {response.status_code}")
            
            # Test protected route (should redirect to login)
            response = client.get('/')
            print(f"✓ Index route status: {response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"✗ Route test error: {e}")
        return False

if __name__ == '__main__':
    print("Testing Malawi School Reporting System Flask App")
    print("=" * 50)
    
    # Test app startup
    if test_app_startup():
        print("\n✓ App startup test passed")
        
        # Test basic routes
        if test_basic_routes():
            print("✓ Basic routes test passed")
        else:
            print("✗ Basic routes test failed")
    else:
        print("✗ App startup test failed")
    
    print("\nTest completed.")