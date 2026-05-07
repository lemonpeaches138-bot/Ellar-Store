# Ellar Mini Mart IMS - User Guide

## Getting Started

### 1. Initial Setup
**Admin User Creation** (Run in Django shell):
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
admin = User.objects.create_user(
    username='EllarMiniMart',
    email='admin@ellarminimart.com',
    password='AdminPassword123!',
    is_staff=True,
    is_superuser=True
)
```

### 2. Staff Registration Flow
1. Click "Create Staff Account" on login page
2. Fill registration form:
   - Username (unique)
   - Email (unique)
   - First Name & Last Name
   - **Phone Number** (optional)
   - **Location** (optional)
   - **Branch** (select from dropdown)
   - Password (minimum 8 characters)

3. Admin reviews in "User Approvals"
4. Admin approves/rejects
5. Approved user can now login

---

## User Roles & Permissions

### Admin (EllarMiniMart)
**Access:**
- ✅ Full system access
- ✅ User Approvals
- ✅ View/Manage Staff
- ✅ Notifications & Admin insights
- ✅ All reports & exports
- ✅ Product management

**Sidebar Additional Sections:**
- User Approvals
- View Staff

### Staff Members
**Access:**
- ✅ Dashboard (read-only)
- ✅ Point of Sale (POS)
- ✅ Products (view/manage own entries)
- ✅ Reports (limited)
- ✅ Settings (personal profile & theme)

**Restrictions:**
- ❌ Cannot approve/manage users
- ❌ Cannot view staff list
- ❌ Cannot manage other staff

---

## Feature Walkthroughs

### Dashboard
1. **Navigate**: Click "Dashboard" in sidebar
2. **View KPIs**:
   - Total Products count
   - Total Sold units
   - Low Stock Items needing restocking
   - Top Selling Product

3. **Analytics**:
   - Category distribution
   - Stock movement trends (last 6 months)
   - Top 5 products by sales

4. **Quick Actions**:
   - Add Product
   - New Sale (POS)
   - Manage Stock
   - Generate Report

---

### Point of Sale (POS)
1. **Access**: Click "Point of Sale" in sidebar
2. **Search Products**:
   - Enter SKU or product name
   - Results show in real-time
   - Click product to add to cart

3. **Manage Cart**:
   - Adjust quantities
   - View item prices and totals
   - Remove items with delete button

4. **Apply Discount**:
   - Enter discount amount in "Discount" field
   - Automatic change calculation
   - Display shows: Subtotal → Discount → Total

5. **Checkout**:
   - Enter cash received
   - System calculates change
   - Click "Complete Transaction"
   - E-Receipt prints automatically
   - Stock automatically deducted

6. **Receipt**:
   - Shows transaction ID, items, total
   - Print-friendly format
   - Exit button to return to POS

---

### Product Management
1. **Access**: Click "Products" in sidebar
2. **View Products**:
   - Table shows: SKU, Name, Category, Stock, Sold, Purchase Price, Selling Price, Profit/Unit, Total Profit, Expiration

3. **Filter by Category**:
   - Select category from dropdown
   - Click "Filter" button
   - View filtered results
   - Click "Clear" to reset

4. **Add Product**:
   - Click "Add Product" button
   - Fill form: Name, SKU, Type, Quantity, Prices, etc.
   - Click "Save"

5. **Edit Product**:
   - Click edit icon on product row
   - Update fields
   - Click "Save"

6. **Adjust Stock**:
   - Click "Adjust Stock" for any product
   - Select "Stock In" or "Stock Out"
   - Enter quantity
   - Add note (optional)
   - Click "Save"

7. **Delete Product**:
   - Click delete icon
   - Confirm deletion

---

### Reports
1. **Access**: Click "Reports" in sidebar
2. **View Dashboard**:
   - Total Products, Total Value, Low Stock Count
   - Total Sales, Stock In/Out counts
   - Top 10 products by sales
   - Product type distribution

3. **Export Inventory Report**:
   - Click "Download Inventory Report (.xls)"
   - File downloads with all product details

4. **View Stock Report**:
   - Click "Stock Report" tab
   - See all movements (In/Out)
   - View totals and net movement
   - Click "Download Stock Report (.xls)"

---

### Settings
1. **Access**: Click "Settings" in sidebar
2. **Profile Tab**:
   - View email (editable)
   - First name (read-only)
   - Last name (read-only)
   - Click "Save Profile"

3. **Theme Tab**:
   - Toggle "Enable Dark Mode"
   - Select primary color (8 options):
     - Pink
     - Blue
     - Green
     - Purple
     - Orange
     - Red
     - Teal
     - Indigo
   - Click color swatch to select
   - Click "Save Theme"
   - Changes apply immediately

4. **Security Tab**:
   - Enter current password
   - Enter new password (min 8 chars)
   - Confirm new password
   - Click "Change Password"
   - Or click "Logout" button

---

### User Approvals (Admin Only)
1. **Access**: Click "User Approvals" (admin only)
2. **View Pending**:
   - Table shows pending registrations
   - Name, email, branch, phone, location

3. **Approve User**:
   - Click approve icon
   - Confirm action
   - User receives notification (future)
   - User can now login

4. **Reject User**:
   - Click reject icon
   - Confirm action
   - Registration deleted

---

### Staff Management (Admin Only)
1. **Access**: Click "View Staff" (admin only)
2. **View Active Staff**:
   - List of all staff members
   - Join dates, usernames
   - Action buttons

3. **Reset Password**:
   - Click reset password icon
   - Enter new password
   - User must use new password on next login

4. **Remove Staff**:
   - Click remove icon
   - Confirm action
   - User account deleted

---

### Notifications (Admin Only)
1. **Access**: Click bell icon in top right (admin only)
2. **Dropdown View**:
   - Shows 10 most recent notifications
   - Unread badge shows count
   - Click "View All" for full list

3. **On Notifications Page**:
   - See all notifications with types
   - Types: LOGIN, LOGOUT, STOCK_IN, STOCK_OUT, SALE
   - Mark as read by clicking notification
   - Timeline view of all events

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+/` | Focus search (on products page) |
| `Esc` | Close modals/dropdowns |
| `Enter` | Submit forms |
| `Tab` | Navigate form fields |

---

## Theme Customization

### Available Colors
Each color has a gradient applied:
- **Pink**: `#ec4899` → `#f472b6` (romantic, professional)
- **Blue**: `#3b82f6` → `#60a5fa` (trustworthy, corporate)
- **Green**: `#10b981` → `#34d399` (growth, health)
- **Purple**: `#8b5cf6` → `#a78bfa` (creative, premium)
- **Orange**: `#f97316` → `#fb923c` (energetic, warm)
- **Red**: `#ef4444` → `#f87171` (urgent, attention)
- **Teal**: `#14b8a6` → `#2dd4bf` (balance, calm)
- **Indigo**: `#6366f1` → `#818cf8` (innovative, tech)

### Dark Mode Features
- Reduces eye strain in low-light environments
- Better for extended use
- Automatic font contrast adjustment
- All UI elements adapt to theme

---

## Common Tasks

### Adding a New Product
1. Products → Add Product
2. Fill in details
3. Set purchase and selling prices
4. Click Save

### Doing a Sale
1. POS → Search for product
2. Enter quantity
3. Repeat for more items
4. Click "Complete Transaction"
5. Print receipt

### Checking Stock Status
1. Dashboard → View "Low Stock Items"
2. Or Products → Filter category → Check quantities
3. Adjust stock as needed

### Generating Reports
1. Reports → Select report type
2. View statistics
3. Download .xls file for Excel

### Changing Your Theme
1. Settings → Theme tab
2. Choose color
3. Toggle dark mode if desired
4. Click "Save Theme"
5. Refresh page to see changes

---

## Troubleshooting

### I forgot my password
- Cannot self-reset currently
- Contact admin to reset your password

### Sales not showing in reports
- Check that transactions were completed (not saved as draft)
- Reports update in real-time
- Refresh page to see latest data

### Product not appearing in search
- Verify product exists in database
- Check product name/SKU spelling
- Ensure product is not deleted

### Theme not saving
- Ensure you clicked "Save Theme" button
- Check browser cache
- Try logging out and back in

### Cannot approve users
- Only EllarMiniMart account can approve
- Check if you are logged in as admin
- Visit /user-approvals/ directly if sidebar link missing

---

## Important Notes

⚠️ **Security:**
- Never share your login credentials
- Change password regularly
- Admin account is critical - protect it well
- Session times out after 25 minutes of inactivity

📊 **Data:**
- Backup database regularly
- Export reports for records
- Stock adjustments create permanent records
- Transactions cannot be deleted once completed

🎨 **Customization:**
- Theme changes apply only to your account
- Other users have their own preferences
- Admin and staff have independent themes

---

## Support

For technical issues or feature requests:
1. Check this guide first
2. Review the Implementation Report
3. Contact system administrator

---

**Last Updated**: May 5, 2026
**Version**: 1.0
**Status**: Production Ready
