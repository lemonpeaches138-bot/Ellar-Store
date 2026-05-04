#!/usr/bin/env python
"""
Test script for enhanced sold products display
"""
import os
import sys
from pathlib import Path
import django

# Setup Django
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from inventory.models import Product

def test_sold_products_display():
    """Test sold products functionality"""
    print("Testing enhanced sold products display...")
    
    # Check if products have total_sold field
    products = Product.objects.all()
    print(f"Total products in database: {products.count()}")
    
    if products.exists():
        print("\nProducts with sold data:")
        for product in products[:5]:  # Show first 5 products
            print(f"  - {product.name}: {product.total_sold} sold")
        
        # Calculate statistics
        total_sold = sum(product.total_sold for product in products)
        products_with_sales = products.filter(total_sold__gt=0).count()
        top_selling = products.order_by('-total_sold').first()
        
        print(f"\nSales Statistics:")
        print(f"  - Total units sold: {total_sold}")
        print(f"  - Products with sales: {products_with_sales}")
        print(f"  - Top selling product: {top_selling.name if top_selling else 'None'}")
        
        if top_selling:
            print(f"    - Units sold: {top_selling.total_sold}")
        
        print("\n✓ Sold products data is available")
        print("✓ Enhanced display should show:")
        print("  - Color-coded sold indicators (green/orange/blue)")
        print("  - Sales summary cards at the top")
        print("  - Hover effects and tooltips")
        
    else:
        print("No products found in database")
    
    print("\nTo test the enhanced sold products display:")
    print("1. Navigate to: http://127.0.0.1:8000/login/")
    print("2. Login with staff credentials")
    print("3. Go to: http://127.0.0.1:8000/products/")
    print("4. Look for:")
    print("   - Sales Overview section with summary cards")
    print("   - 'No. Sold' column with color indicators:")
    print("     * Green badge: 50+ units sold (high volume)")
    print("     * Orange badge: 20-49 units sold (medium volume)")
    print("     * Blue badge: 1-19 units sold (low volume)")
    print("     * Gray text: 0 units sold")
    print("   - Hover effects on sold indicators")
    
    return True

if __name__ == "__main__":
    test_sold_products_display()
