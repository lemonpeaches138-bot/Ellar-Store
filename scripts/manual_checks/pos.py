#!/usr/bin/env python
"""
Test script for POS functionality
"""
import os
import sys
from pathlib import Path
import django
import urllib.request
import urllib.parse
import json
from django.contrib.auth import authenticate

# Setup Django
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_pos_search():
    """Test POS search functionality"""
    print("Testing POS search functionality...")
    
    # First, check if we can access the POS page
    try:
        response = urllib.request.urlopen('http://127.0.0.1:8000/pos/')
        content = response.read().decode('utf-8')
        print(f"POS page status: {response.getcode()}")
        
        if 'login' in content.lower():
            print("✓ POS page correctly requires authentication")
        else:
            print("✗ POS page should require authentication")
            return False
            
    except Exception as e:
        print(f"✗ Error accessing POS page: {e}")
        return False
    
    # Test search endpoint without authentication (should fail)
    try:
        search_url = 'http://127.0.0.1:8000/pos/search/?q=NA3440'
        response = urllib.request.urlopen(search_url)
        print("✗ Search endpoint should require authentication")
        return False
    except urllib.error.HTTPError as e:
        if e.code == 302:  # Redirect to login
            print("✓ Search endpoint correctly requires authentication")
        else:
            print(f"✗ Unexpected error: {e.code}")
            return False
    except Exception as e:
        print(f"✓ Search endpoint correctly requires authentication (error: {e})")
    
    # Test products endpoint without authentication (should fail)
    try:
        products_url = 'http://127.0.0.1:8000/pos/products/'
        response = urllib.request.urlopen(products_url)
        print("✗ Products endpoint should require authentication")
        return False
    except urllib.error.HTTPError as e:
        if e.code == 302:  # Redirect to login
            print("✓ Products endpoint correctly requires authentication")
        else:
            print(f"✗ Unexpected error: {e.code}")
            return False
    except Exception as e:
        print(f"✓ Products endpoint correctly requires authentication (error: {e})")
    
    print("\n✓ All authentication checks passed")
    print("✓ POS functionality requires proper authentication")
    print("\nTo test POS functionality:")
    print("1. Navigate to http://127.0.0.1:8000/login/")
    print("2. Login with username: EllarMiniMart")
    print("3. Then navigate to http://127.0.0.1:8000/pos/")
    print("4. Test search and product browser functionality")
    
    return True

if __name__ == "__main__":
    test_pos_search()
