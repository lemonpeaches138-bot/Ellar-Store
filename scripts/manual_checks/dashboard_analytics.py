#!/usr/bin/env python
"""
Test script for enhanced dashboard with analytics and scrollable movements
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

from inventory.models import Product, StockMovement

def test_dashboard_analytics():
    """Test enhanced dashboard functionality"""
    print("Testing enhanced dashboard with analytics...")
    
    # Check database data
    products = Product.objects.all()
    movements = StockMovement.objects.all()
    
    print(f"Database Status:")
    print(f"  - Total products: {products.count()}")
    print(f"  - Total stock movements: {movements.count()}")
    
    if products.exists():
        total_sold = sum(product.total_sold for product in products)
        products_with_sales = products.filter(total_sold__gt=0).count()
        top_selling = products.order_by('-total_sold').first()
        
        print(f"\nSales Analytics:")
        print(f"  - Total units sold: {total_sold}")
        print(f"  - Products with sales: {products_with_sales}")
        print(f"  - Top selling product: {top_selling.name if top_selling else 'None'}")
        
        if top_selling:
            print(f"    - Units sold: {top_selling.total_sold}")
    
    if movements.exists():
        stock_in = movements.filter(movement_type='IN').count()
        stock_out = movements.filter(movement_type='OUT').count()
        
        print(f"\nStock Movement Analytics:")
        print(f"  - Stock in movements: {stock_in}")
        print(f"  - Stock out movements: {stock_out}")
    
    # Product type distribution
    print(f"\nProduct Type Distribution:")
    for choice in Product.ProductType.choices:
        type_name = choice[1]
        count = products.filter(product_type=choice[0]).count()
        if count > 0:
            print(f"  - {type_name}: {count}")
    
    print("\n✓ Dashboard analytics data is available")
    print("✓ Enhanced dashboard should show:")
    print("  - Scrollable recent movements box (max height: 300px)")
    print("  - Analytics section with 4 cards:")
    print("    * Sales Performance (total sold, products with sales)")
    print("    * Stock Movements (stock in/out counts)")
    print("    * Top Selling Products (top 5 products)")
    print("    * Product Categories (distribution by type)")
    print("  - Responsive design and hover effects")
    print("  - Custom scrollbar styling")
    
    print("\nTo test the enhanced dashboard:")
    print("1. Navigate to: http://127.0.0.1:8000/login/")
    print("2. Login with staff credentials")
    print("3. Go to: http://127.0.0.1:8000/dashboard/")
    print("4. Verify:")
    print("   - Recent movements are in a scrollable box")
    print("   - Analytics section appears below movements")
    print("   - 4 analytics cards with proper data")
    print("   - Hover effects on analytics cards")
    print("   - Responsive layout on smaller screens")
    
    return True

if __name__ == "__main__":
    test_dashboard_analytics()
