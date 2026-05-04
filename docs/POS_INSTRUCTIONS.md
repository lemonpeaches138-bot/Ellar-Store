# POS System Testing Instructions

## Overview
The Point of Sale (POS) system has been enhanced with search and product filtering functionality. This document provides step-by-step instructions for testing all POS features.

## Prerequisites
1. Django development server must be running: `python manage.py runserver`
2. User must be logged in with staff credentials

## Login Credentials
- **Username**: EllarMiniMart
- **Password**: (You'll need to set this or use existing credentials)

## Testing Steps

### 1. Access the POS System
1. Navigate to: `http://127.0.0.1:8000/login/`
2. Login with staff credentials
3. Navigate to: `http://127.0.0.1:8000/pos/`

### 2. Test Search Functionality
1. In the search box, try these searches:
   - **SKU Search**: Enter "NA3440" (should find "3" Nail (per Kilo)")
   - **Name Search**: Enter "nail" (should find the same product)
   - **Partial Name**: Enter "nai" (should find the product)
   - **Invalid Search**: Enter "xyz123" (should show "Product not found" message)

### 3. Test Product Browser
1. Click the "Browse Products" button
2. A modal should open showing all products with stock
3. Test the filter dropdown:
   - Select "Hardware Supplies" (if any hardware products exist)
   - Select "School Supplies" (if any school products exist)
   - Click "Apply Filter" to filter products
   - Click "Clear" to show all products again

### 4. Test Adding Products to Cart
1. Search for a product (e.g., "NA3440")
2. Set quantity to 1
3. Click "Add to Cart"
4. Product should appear in the cart table
5. Try updating quantity in the cart
6. Try removing the item from cart

### 5. Test Checkout Process
1. Add at least one product to cart
2. Enter a cash amount greater than the total
3. Click "Complete Transaction"
4. Should redirect to receipt page
5. Verify transaction was created and stock was reduced

## Features Implemented

### ✅ Search Functionality
- Search by SKU (exact match)
- Search by product name (partial, case-insensitive)
- Only shows products with available stock
- Proper error handling for authentication issues

### ✅ Product Browser
- Modal interface for browsing products
- Filter by product type (Hardware, School Supplies, Canned Goods, etc.)
- Apply Filter and Clear buttons
- Only shows products with available stock

### ✅ Authentication Handling
- All POS endpoints require authentication
- Proper error messages when not logged in
- Automatic redirect to login page if authentication fails

### ✅ Error Handling
- Network error handling
- Authentication error handling
- User-friendly error messages

## Troubleshooting

### "Search doesn't work"
- Ensure you're logged in with a staff account
- Check browser console for JavaScript errors
- Verify the development server is running

### "Product browser doesn't open"
- Check if JavaScript is enabled
- Look for console errors
- Ensure you're logged in

### "Authentication required" errors
- Log out and log back in
- Ensure you're using a staff account
- Clear browser cache if needed

## Technical Details

### Endpoints
- `GET /pos/` - Main POS page
- `GET /pos/search/?q=query` - Search products
- `GET /pos/products/?type=TYPE` - Get filtered products
- `POST /pos/add-item/` - Add item to cart
- `POST /pos/remove-item/` - Remove item from cart
- `POST /pos/update-quantity/` - Update item quantity
- `POST /pos/checkout/` - Complete transaction

### Database Requirements
- Products must have `quantity > 0` to appear in search/browse
- User must be staff (`is_staff=True`) to access POS
- Products must have valid SKU, name, and price

## Support
If you encounter issues:
1. Check the Django development server output for errors
2. Check browser console for JavaScript errors
3. Verify user authentication status
4. Ensure products exist in the database with positive quantity
