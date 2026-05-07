from decimal import Decimal
import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, password_validation
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import escape
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_sameorigin
import uuid

from .forms import ProductForm, StockMovementForm, UserRegistrationForm
from .models import Product, StockMovement, Transaction, TransactionItem, UserRegistration, Notification, UserProfile


def is_staff(user):
    """Check if user is a staff member."""
    return user.is_staff


def _get_user_profile(user):
    """Return a profile for theme preferences, creating it for older users."""
    profile, _created = UserProfile.objects.get_or_create(user=user)
    return profile


def login_view(request):
    """Handle user login."""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_staff:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")

                # Create login notification for admin
                admin = User.objects.filter(username='EllarMiniMart').first()
                if admin:
                    Notification.objects.create(
                        type=Notification.NotificationType.USER_REGISTERED,
                        title=f"Staff Login: {user.username}",
                        message=f"{user.username} ({user.first_name} {user.last_name}) logged in.",
                        created_by=user,
                    )

                return redirect("inventory:dashboard")
            else:
                messages.error(request, "Only staff members can access this application.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "inventory/modern_login.html")


def logout_view(request):
    """Handle user logout."""
    user = request.user
    logout(request)
    messages.success(request, "You have been logged out successfully.")

    # Create logout notification for admin
    if user.is_authenticated or user.is_staff:
        admin = User.objects.filter(username='EllarMiniMart').first()
        if admin:
            Notification.objects.create(
                type=Notification.NotificationType.USER_REGISTERED,
                title=f"Staff Logout: {user.username}",
                message=f"{user.username} ({user.first_name} {user.last_name}) logged out.",
                created_by=user,
            )

    return redirect("inventory:login")


def register_user(request):
    """Handle user registration for staff accounts."""
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your registration has been submitted. Please wait for admin approval.")
            return redirect("inventory:login")
    else:
        form = UserRegistrationForm()

    return render(request, "inventory/user_register.html", {"form": form})


def index_redirect(request):
    """Redirect root path to dashboard or login based on auth status."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("inventory:dashboard")
    else:
        return redirect("inventory:login")


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def dashboard(request):
    products = Product.objects.all()
    low_stock = products.filter(quantity__lte=F("reorder_level"))

    stock_value_expression = ExpressionWrapper(
        F("quantity") * F("unit_price"), output_field=DecimalField(max_digits=12, decimal_places=2)
    )
    cost_value_expression = ExpressionWrapper(
        F("quantity") * F("purchase_price"), output_field=DecimalField(max_digits=12, decimal_places=2)
    )
    profit_expression = ExpressionWrapper(
        F("quantity") * (F("unit_price") - F("purchase_price")),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )

    total_stock_value = products.aggregate(total=Sum(stock_value_expression))["total"] or Decimal("0.00")
    total_cost_value = products.aggregate(total=Sum(cost_value_expression))["total"] or Decimal("0.00")
    total_expected_profit = products.aggregate(total=Sum(profit_expression))["total"] or Decimal("0.00")

    # Calculate analytics data
    total_sold = sum(product.total_sold for product in products)
    products_with_sales = products.filter(total_sold__gt=0).count()
    top_selling_products = products.order_by('-total_sold')[:5]

    # Stock movement analytics
    stock_in_count = StockMovement.objects.filter(movement_type='IN').count()
    stock_out_count = StockMovement.objects.filter(movement_type='OUT').count()

    # Product type analytics
    product_type_counts = {}
    for choice in Product.ProductType.choices:
        type_name = choice[1]
        count = products.filter(product_type=choice[0]).count()
        product_type_counts[type_name] = count

    # Stock trends data (last 6 months)
    from django.utils import timezone
    from datetime import timedelta
    import calendar
    import json

    stock_trends_data = {
        'labels': [],
        'stock_in': [],
        'stock_out': []
    }

    for i in range(6):
        month_date = timezone.now() - timedelta(days=30*i)
        month_name = calendar.month_abbr[month_date.month]
        stock_trends_data['labels'].insert(0, month_name)

        month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i == 0:
            month_end = timezone.now()
        else:
            next_month = month_date.replace(day=28) + timedelta(days=4)
            month_end = next_month - timedelta(days=next_month.day) + timezone.timedelta(hours=23, minutes=59, seconds=59)

        stock_in = StockMovement.objects.filter(
            movement_type='IN',
            created_at__gte=month_start,
            created_at__lte=month_end
        ).count()

        stock_out = StockMovement.objects.filter(
            movement_type='OUT',
            created_at__gte=month_start,
            created_at__lte=month_end
        ).count()

        stock_trends_data['stock_in'].insert(0, stock_in)
        stock_trends_data['stock_out'].insert(0, stock_out)

    context = {
        "product_count": products.count(),
        "low_stock_count": low_stock.count(),
        "total_stock_value": total_stock_value,
        "total_cost_value": total_cost_value,
        "total_expected_profit": total_expected_profit,
        "recent_movements": StockMovement.objects.select_related("product")[:10],
        # Analytics data
        "total_sold": total_sold,
        "products_with_sales": products_with_sales,
        "top_selling_products": top_selling_products,
        "stock_in_count": stock_in_count,
        "stock_out_count": stock_out_count,
        "product_type_counts": product_type_counts,
        "stock_trends_data": stock_trends_data,
        "stock_trends_json": json.dumps(stock_trends_data),
        "product_type_counts_json": json.dumps(product_type_counts),
    }
    return render(request, "inventory/modern_dashboard.html", context)


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def product_list(request):
    products = Product.objects.all()
    selected_product_type = request.GET.get("type", "")
    valid_types = {choice[0] for choice in Product.ProductType.choices}
    if selected_product_type in valid_types:
        products = products.filter(product_type=selected_product_type)
    else:
        selected_product_type = ""

    # Calculate sales statistics
    total_sold = sum(product.total_sold for product in products)
    products_with_sales = products.filter(total_sold__gt=0).count()
    top_selling_product = products.order_by('-total_sold').first()

    context = {
        "products": products,
        "product_types": Product.ProductType.choices,
        "selected_product_type": selected_product_type,
        "total_sold": total_sold,
        "products_with_sales": products_with_sales,
        "top_selling_product": top_selling_product,
    }
    return render(request, "inventory/modern_product_list.html", context)


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def product_create(request):
    form = ProductForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product created successfully.")
        return redirect("inventory:product-list")
    return render(request, "inventory/modern_product_form.html", {"form": form, "title": "Add Product"})


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product updated successfully.")
        return redirect("inventory:product-list")
    return render(request, "inventory/modern_product_form.html", {"form": form, "title": "Edit Product"})


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect("inventory:product-list")
    return render(request, "inventory/product_confirm_delete.html", {"product": product})


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def stock_adjust(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = StockMovementForm(request.POST or None)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if request.method == "POST" and form.is_valid():
        movement = form.save(commit=False)
        movement.product = product

        if movement.movement_type == StockMovement.MovementType.STOCK_OUT and movement.quantity > product.quantity:
            form.add_error("quantity", "Cannot stock out more than available quantity.")
        else:
            if movement.movement_type == StockMovement.MovementType.STOCK_IN:
                product.quantity += movement.quantity
                # Create stock in notification
                Notification.objects.create(
                    type=Notification.NotificationType.STOCK_IN,
                    title=f"Stock In: {product.name}",
                    message=f"{request.user.username} added {movement.quantity} units of {product.name} to inventory.",
                    created_by=request.user,
                    product=product,
                    quantity=movement.quantity
                )
            else:
                product.quantity -= movement.quantity
                # Create stock out notification
                Notification.objects.create(
                    type=Notification.NotificationType.STOCK_OUT,
                    title=f"Stock Out: {product.name}",
                    message=f"{request.user.username} removed {movement.quantity} units of {product.name} from inventory.",
                    created_by=request.user,
                    product=product,
                    quantity=movement.quantity
                )
            product.save()
            movement.save()
            messages.success(request, "Stock updated successfully.")
            if is_ajax:
                return JsonResponse({
                    "success": True,
                    "message": "Stock updated successfully.",
                    "product_id": product.pk,
                    "quantity": product.quantity,
                })
            return redirect("inventory:product-list")

    if request.method == "POST" and is_ajax:
        message = "Unable to update stock."
        for errors in form.errors.values():
            if errors:
                message = errors[0]
                break
        return JsonResponse({"success": False, "message": message}, status=400)

    context = {
        "product": product,
        "form": form,
    }
    return render(request, "inventory/modern_stock_adjust.html", context)


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def reports(request):
    products = Product.objects.all()
    low_stock = products.filter(quantity__lte=F("reorder_level"))

    # Calculate statistics
    stock_value_expression = ExpressionWrapper(
        F("quantity") * F("unit_price"), output_field=DecimalField(max_digits=12, decimal_places=2)
    )
    total_stock_value = products.aggregate(total=Sum(stock_value_expression))["total"] or Decimal("0.00")

    total_sold = sum(product.total_sold for product in products)
    low_stock_count = low_stock.count()

    # Stock movement analytics
    stock_in_count = StockMovement.objects.filter(movement_type='IN').count()
    stock_out_count = StockMovement.objects.filter(movement_type='OUT').count()
    total_movements = stock_in_count + stock_out_count

    # Top products
    top_products = products.filter(total_sold__gt=0).order_by('-total_sold')[:10]

    # Product type counts for charts
    product_type_counts = {}
    for choice in Product.ProductType.choices:
        type_name = choice[1]
        count = products.filter(product_type=choice[0]).count()
        product_type_counts[type_name] = count

    context = {
        "total_products": products.count(),
        "total_value": total_stock_value,
        "low_stock_count": low_stock_count,
        "total_sales": total_sold,
        "stock_in_count": stock_in_count,
        "stock_out_count": stock_out_count,
        "total_movements": total_movements,
        "top_products": top_products,
        "product_type_counts": product_type_counts,
    }
    return render(request, "inventory/modern_reports.html", context)


def _excel_response(filename, title, headers, rows):
    response = HttpResponse(content_type="application/vnd.ms-excel")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    table_headers = "".join(f"<th>{escape(header)}</th>" for header in headers)
    table_rows = []
    for row in rows:
        cells = "".join(f"<td>{escape(value)}</td>" for value in row)
        table_rows.append(f"<tr>{cells}</tr>")

    response.write(
        f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                table {{ border-collapse: collapse; }}
                th, td {{ border: 1px solid #999; padding: 6px; }}
                th {{ background: #f6c1d9; }}
            </style>
        </head>
        <body>
            <h2>{escape(title)}</h2>
            <table>
                <thead><tr>{table_headers}</tr></thead>
                <tbody>{''.join(table_rows)}</tbody>
            </table>
        </body>
        </html>
        """
    )
    return response


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def inventory_export(request):
    headers = [
        "SKU",
        "Name",
        "Type",
        "Quantity",
        "Sold",
        "Purchase Price",
        "Selling Price",
        "Expiration Date",
        "Profit / Unit",
        "Total Profit",
        "Reorder Level",
    ]
    rows = [
        [
            product.sku,
            product.name,
            product.get_product_type_display(),
            product.quantity,
            product.total_sold,
            product.purchase_price,
            product.unit_price,
            product.expiration_date or "No expiration",
            product.profit_per_unit,
            product.total_profit,
            product.reorder_level,
        ]
        for product in Product.objects.all()
    ]
    return _excel_response("inventory-report.xls", "Inventory Report", headers, rows)


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def stock_report(request):
    movements = StockMovement.objects.select_related("product")
    stock_in_total = movements.filter(movement_type=StockMovement.MovementType.STOCK_IN).aggregate(
        total=Sum("quantity")
    )["total"] or 0
    stock_out_total = movements.filter(movement_type=StockMovement.MovementType.STOCK_OUT).aggregate(
        total=Sum("quantity")
    )["total"] or 0

    context = {
        "movements": movements,
        "total_movements": movements.count(),
        "stock_in_total": stock_in_total,
        "stock_out_total": stock_out_total,
        "net_movement": stock_in_total - stock_out_total,
    }
    return render(request, "inventory/modern_stock_report.html", context)


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def stock_export(request):
    headers = ["Date", "SKU", "Product", "Type", "Quantity", "Note"]
    rows = [
        [
            movement.created_at.strftime("%Y-%m-%d %H:%M"),
            movement.product.sku,
            movement.product.name,
            movement.get_movement_type_display(),
            movement.quantity,
            movement.note or "-",
        ]
        for movement in StockMovement.objects.select_related("product")
    ]
    return _excel_response("stock-report.xls", "Stock Report", headers, rows)


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def admin_profile(request):
    """Display the admin user profile."""
    user = request.user
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("inventory:admin-profile")

    context = {
        "user": user,
    }
    return render(request, "inventory/modern_admin_profile.html", context)


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def user_approvals(request):
    """Display and handle user registration approvals."""
    # Check if current user is the admin (EllarMiniMart)
    if request.user.username != 'EllarMiniMart':
        messages.error(request, "Only EllarMiniMart can approve user registrations.")
        return redirect("inventory:dashboard")

    pending_registrations = UserRegistration.objects.filter(is_approved=False)

    context = {
        "pending_registrations": pending_registrations,
    }
    return render(request, "inventory/user_approvals.html", context)


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def approve_user(request, registration_id):
    """Approve a user registration."""
    # Check if current user is the admin (EllarMiniMart)
    if request.user.username != 'EllarMiniMart':
        messages.error(request, "Only EllarMiniMart can approve user registrations.")
        return redirect("inventory:dashboard")

    registration = get_object_or_404(UserRegistration, id=registration_id)

    if request.method == "POST":
        # Create the user account
        user = User.objects.create_user(
            username=registration.username,
            email=registration.email,
            password='',  # Will be set below
            first_name=registration.first_name,
            last_name=registration.last_name,
            is_staff=True  # All approved users are staff
        )
        # Set the hashed password directly
        user.password = registration.password
        user.save()

        # Mark registration as approved
        registration.is_approved = True
        registration.approved_at = timezone.now()
        registration.approved_by = request.user
        registration.save()

        messages.success(request, f"User {registration.username} has been approved and can now log in.")
        return redirect("inventory:user-approvals")

    return render(request, "inventory/approve_user.html", {"registration": registration})


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def reject_user(request, registration_id):
    """Reject a user registration."""
    # Check if current user is the admin (EllarMiniMart)
    if request.user.username != 'EllarMiniMart':
        messages.error(request, "Only EllarMiniMart can reject user registrations.")
        return redirect("inventory:dashboard")

    registration = get_object_or_404(UserRegistration, id=registration_id)

    if request.method == "POST":
        username = registration.username
        registration.delete()
        messages.success(request, f"User registration for {username} has been rejected.")
        return redirect("inventory:user-approvals")

    return render(request, "inventory/reject_user.html", {"registration": registration})


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def staff_list(request):
    """Display all staff members in the system."""
    staff_members = User.objects.filter(is_staff=True).order_by('-date_joined')

    context = {
        "staff_members": staff_members,
        "total_staff": staff_members.count(),
    }
    return render(request, "inventory/staff_list.html", context)


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def staff_set_password(request, staff_id):
    """Allow the system admin to reset a staff member password."""
    if request.user.username != 'EllarMiniMart':
        messages.error(request, "Only EllarMiniMart can manage staff passwords.")
        return redirect("inventory:dashboard")

    staff_user = get_object_or_404(User, id=staff_id, is_staff=True)

    if staff_user.username == 'EllarMiniMart':
        messages.error(request, "The system admin account cannot be managed here.")
        return redirect("inventory:staff-list")

    if request.method == "POST":
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not new_password:
            messages.error(request, "Enter a new password.")
        elif new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
        else:
            try:
                password_validation.validate_password(new_password, staff_user)
            except ValidationError as error:
                messages.error(request, " ".join(error.messages))
            else:
                staff_user.set_password(new_password)
                staff_user.save(update_fields=["password"])
                messages.success(request, f"{staff_user.username}'s password has been reset.")

    return redirect("inventory:staff-list")


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def staff_remove(request, staff_id):
    """Remove a staff member from the system."""
    if request.user.username != 'EllarMiniMart':
        messages.error(request, "Only EllarMiniMart can remove staff members.")
        return redirect("inventory:dashboard")

    staff_user = get_object_or_404(User, id=staff_id, is_staff=True)

    if request.method == "POST":
        if staff_user.username == 'EllarMiniMart' or staff_user == request.user or staff_user.is_superuser:
            messages.error(request, "This staff account cannot be removed.")
        else:
            username = staff_user.username
            staff_user.delete()
            messages.success(request, f"{username} has been removed from staff members.")

    return redirect("inventory:staff-list")


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def notifications(request):
    """Display system notifications for admin."""
    # Only EllarMiniMart can see notifications
    if request.user.username != 'EllarMiniMart':
        messages.error(request, "Only EllarMiniMart can view notifications.")
        return redirect("inventory:dashboard")

    notifications = Notification.objects.all().order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()

    context = {
        "notifications": notifications,
        "unread_count": unread_count,
    }
    return render(request, "inventory/notifications.html", context)


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def mark_notification_read(request, notification_id):
    """Mark a notification as read."""
    # Only EllarMiniMart can mark notifications as read
    if request.user.username != 'EllarMiniMart':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})

    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = True
    notification.save()

    return JsonResponse({'success': True})


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def api_notifications(request):
    """API endpoint for notifications."""
    # Only EllarMiniMart can access notifications
    if request.user.username != 'EllarMiniMart':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    notifications = Notification.objects.all().order_by('-created_at')[:10]
    unread_count = Notification.objects.filter(is_read=False).count()

    notification_data = []
    for notification in notifications:
        notification_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.type,
            'created_at': notification.created_at.isoformat(),
            'is_read': notification.is_read,
            'created_by': notification.created_by.username if notification.created_by else None,
        })

    return JsonResponse({
        'notifications': notification_data,
        'unread_count': unread_count,
    })


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def pos(request):
    """Point of Sale main page."""
    cart = request.session.get('cart', {})
    cart_json = json.dumps(cart)
    return render(request, "inventory/modern_pos.html", {
        "cart_json": cart_json,
        "product_types": Product.ProductType.choices
    })


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def pos_search_product(request):
    """Search product by SKU, barcode, or name."""
    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse({'success': False, 'message': 'Please enter a search term'})

    # Search by SKU first (exact match), then by name (contains)
    products = Product.objects.filter(quantity__gt=0).filter(
        Q(sku__iexact=query) | Q(name__icontains=query)
    )

    if products.exists():
        product = products.first()
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'unit_price': float(product.unit_price),
                'quantity': product.quantity
            }
        })
    else:
        return JsonResponse({'success': False, 'message': 'Product not found or out of stock'})


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def pos_get_products(request):
    """Get products filtered by type for POS browser."""
    product_type = request.GET.get('type', '')
    products = Product.objects.filter(quantity__gt=0)  # Only show products with stock

    if product_type:
        valid_types = {choice[0] for choice in Product.ProductType.choices}
        if product_type in valid_types:
            products = products.filter(product_type=product_type)

    products_data = []
    for product in products[:50]:  # Limit to 50 products for performance
        products_data.append({
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'unit_price': float(product.unit_price),
            'quantity': product.quantity,
            'product_type': product.get_product_type_display()
        })

    return JsonResponse({
        'success': True,
        'products': products_data
    })


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def pos_add_item(request):
    """Add item to cart."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})

    try:
        product_id = request.POST.get('product_id')
        if not product_id:
            return JsonResponse({'success': False, 'message': 'Product ID is required'})

        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Invalid quantity'})

        if quantity <= 0:
            return JsonResponse({'success': False, 'message': 'Quantity must be greater than 0'})

        product = Product.objects.get(id=product_id)

        if quantity > product.quantity:
            return JsonResponse({'success': False, 'message': 'Insufficient stock'})

        cart = request.session.get('cart', {})

        if str(product_id) in cart:
            cart[str(product_id)]['quantity'] += quantity
        else:
            cart[str(product_id)] = {
                'product_id': product.id,
                'name': product.name,
                'sku': product.sku,
                'price': float(product.unit_price),
                'quantity': quantity
            }

        request.session['cart'] = cart
        request.session.modified = True  # Explicitly mark session as modified

        subtotal = sum(item['price'] * item['quantity'] for item in cart.values())
        discount = request.session.get('discount', 0)
        total = subtotal - discount

        return JsonResponse({
            'success': True,
            'cart_items': len(cart),
            'subtotal': float(subtotal),
            'discount': float(discount),
            'total': float(total),
            'cart': cart  # Return the full cart data
        })
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error in pos_add_item: {str(e)}')
        return JsonResponse({'success': False, 'message': f'Error adding item: {str(e)}'})


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def pos_remove_item(request):
    """Remove item from cart."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})

    try:
        product_id = request.POST.get('product_id')
        if not product_id:
            return JsonResponse({'success': False, 'message': 'Product ID is required'})

        cart = request.session.get('cart', {})

        if str(product_id) in cart:
            del cart[str(product_id)]
            request.session['cart'] = cart
            request.session.modified = True

            subtotal = sum(item['price'] * item['quantity'] for item in cart.values()) if cart else 0
            discount = request.session.get('discount', 0)
            total = subtotal - discount

            return JsonResponse({
                'success': True,
                'cart_items': len(cart),
                'subtotal': float(subtotal),
                'discount': float(discount),
                'total': float(total),
                'cart': cart  # Return the full cart data
            })

        return JsonResponse({'success': False, 'message': 'Item not found in cart'})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error in pos_remove_item: {str(e)}')
        return JsonResponse({'success': False, 'message': f'Error removing item: {str(e)}'})


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def pos_update_quantity(request):
    """Update item quantity in cart."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})

    try:
        product_id = request.POST.get('product_id')
        if not product_id:
            return JsonResponse({'success': False, 'message': 'Product ID is required'})

        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Invalid quantity'})

        if quantity <= 0:
            return JsonResponse({'success': False, 'message': 'Quantity must be greater than 0'})

        product = Product.objects.get(id=product_id)

        if quantity > product.quantity:
            return JsonResponse({'success': False, 'message': 'Insufficient stock'})

        cart = request.session.get('cart', {})

        if str(product_id) in cart:
            cart[str(product_id)]['quantity'] = quantity
            request.session['cart'] = cart
            request.session.modified = True

            subtotal = sum(item['price'] * item['quantity'] for item in cart.values())
            discount = request.session.get('discount', 0)
            total = subtotal - discount

            return JsonResponse({
                'success': True,
                'subtotal': float(subtotal),
                'discount': float(discount),
                'total': float(total),
                'item_subtotal': float(cart[str(product_id)]['price'] * quantity),
                'cart': cart  # Return the full cart data
            })

        return JsonResponse({'success': False, 'message': 'Item not found in cart'})
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error in pos_update_quantity: {str(e)}')
        return JsonResponse({'success': False, 'message': f'Error updating quantity: {str(e)}'})


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def pos_apply_discount(request):
    """Apply discount to cart."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})

    try:
        try:
            discount = Decimal(request.POST.get('discount', 0))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Invalid discount amount'})

        cart = request.session.get('cart', {})

        if not cart:
            return JsonResponse({'success': False, 'message': 'Cart is empty'})

        subtotal = sum(item['price'] * item['quantity'] for item in cart.values())

        if discount > subtotal:
            return JsonResponse({'success': False, 'message': 'Discount cannot exceed subtotal'})

        if discount < 0:
            return JsonResponse({'success': False, 'message': 'Discount cannot be negative'})

        request.session['discount'] = float(discount)
        total = subtotal - discount

        return JsonResponse({
            'success': True,
            'subtotal': float(subtotal),
            'discount': float(discount),
            'total': float(total),
            'cart': cart  # Return the full cart data
        })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error in pos_apply_discount: {str(e)}')
        return JsonResponse({'success': False, 'message': f'Error applying discount: {str(e)}'})


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def pos_checkout(request):
    """Process payment and create transaction."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})

    try:
        # Parse JSON data from request body
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({'success': False, 'message': 'Invalid JSON data'})

        try:
            cash_received = Decimal(str(data.get('cash_received', 0)))
            discount = Decimal(str(data.get('discount', 0)))
            items = data.get('items', [])
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Invalid data format'})

        if not items:
            return JsonResponse({'success': False, 'message': 'Cart is empty'})

        # Calculate totals
        subtotal = Decimal('0.00')
        for item in items:
            try:
                product = Product.objects.get(id=item['product_id'])
                subtotal += product.unit_price * Decimal(str(item['quantity']))
            except Product.DoesNotExist:
                return JsonResponse({'success': False, 'message': f'Product {item["product_id"]} not found'})

        total = subtotal - discount

        if cash_received < total:
            return JsonResponse({'success': False, 'message': 'Insufficient cash'})

        change = cash_received - total

        # Create transaction
        transaction_id = f"TXN{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
        transaction = Transaction.objects.create(
            transaction_id=transaction_id,
            subtotal=subtotal,
            discount=discount,
            total=total,
            cash_received=cash_received,
            change=change
        )

        # Create transaction items and update stock
        for item in items:
            product = Product.objects.get(id=item['product_id'])
            TransactionItem.objects.create(
                transaction=transaction,
                product=product,
                quantity=item['quantity'],
                unit_price=product.unit_price,
                subtotal=product.unit_price * Decimal(str(item['quantity']))
            )

            # Update product quantity and track sold
            product.quantity -= item['quantity']
            product.total_sold += item['quantity']
            product.save()

            # Record stock movement
            StockMovement.objects.create(
                product=product,
                movement_type=StockMovement.MovementType.STOCK_OUT,
                quantity=item['quantity'],
                note=f"POS Transaction {transaction_id}"
            )

        # Create sale notification
        total_items = sum(item['quantity'] for item in items)
        Notification.objects.create(
            type=Notification.NotificationType.SALE,
            title=f"Sale Completed - {transaction_id}",
            message=f"{request.user.username} completed a sale of {total_items} items totaling ₱{total:.2f}. Transaction ID: {transaction_id}",
            created_by=request.user,
            transaction=transaction,
            quantity=total_items
        )

        # Clear cart and discount from session
        request.session['cart'] = {}
        request.session['discount'] = 0
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'transaction_id': transaction.transaction_id,
            'redirect_url': f'/pos/receipt/{transaction.id}/'
        })
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error in pos_checkout: {str(e)}')
        return JsonResponse({'success': False, 'message': f'Error processing checkout: {str(e)}'})


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
@xframe_options_sameorigin
def pos_receipt(request, transaction_id):
    """Display transaction receipt."""
    transaction = get_object_or_404(Transaction, transaction_id=transaction_id)
    context = {
        'transaction': transaction,
        'items': transaction.items.all(),
        'is_embedded': request.GET.get('embed') == 'modal',
    }
    return render(request, "inventory/modern_pos_receipt.html", context)


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def settings_view(request):
    """User settings page with theme customization and profile management."""
    from .forms import ThemePreferenceForm, PasswordChangeForm, UserProfileForm

    user_profile = _get_user_profile(request.user)
    form_type = request.POST.get('form_type') if request.method == 'POST' else None

    theme_form = ThemePreferenceForm(
        request.POST if form_type == 'theme' else None,
        instance=user_profile,
        prefix='theme',
    )
    password_form = PasswordChangeForm(
        request.POST if form_type == 'password' else None,
        prefix='password',
    )
    profile_form = UserProfileForm(
        request.POST if form_type == 'profile' else None,
        instance=request.user,
        prefix='profile',
    )

    context = {
        'theme_form': theme_form,
        'password_form': password_form,
        'profile_form': profile_form,
    }

    if request.method == 'POST':
        if form_type == 'theme' and theme_form.is_valid():
            theme_form.save()
            messages.success(request, 'Theme preferences updated successfully.')
            return redirect('inventory:settings')

        elif form_type == 'profile' and profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('inventory:settings')

        elif form_type == 'password':
            old_password = request.POST.get('password-old_password', '')
            new_password = request.POST.get('password-new_password', '')
            confirm_password = request.POST.get('password-confirm_password', '')

            if not request.user.check_password(old_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                login(request, request.user)  # Re-authenticate user
                messages.success(request, 'Password changed successfully.')
                return redirect('inventory:settings')

    return render(request, 'inventory/settings.html', context)


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def api_theme_config(request):
    """API endpoint to get the user's theme configuration."""
    theme_config = _get_user_profile(request.user).theme_config
    return JsonResponse(theme_config)


@login_required(login_url="inventory:login")
@user_passes_test(is_staff, login_url="inventory:login")
def api_update_theme(request):
    """API endpoint to update theme preferences."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body)
        profile = _get_user_profile(request.user)

        if 'dark_mode' in data:
            dark_mode = data['dark_mode']
            if isinstance(dark_mode, str):
                dark_mode = dark_mode.lower() in {'1', 'true', 'yes', 'on'}
            profile.dark_mode = bool(dark_mode)
        if 'primary_color' in data:
            valid_colors = {choice[0] for choice in UserProfile.COLOR_CHOICES}
            primary_color = data['primary_color']
            if primary_color not in valid_colors:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid primary color',
                }, status=400)
            profile.primary_color = primary_color

        profile.save(update_fields=['dark_mode', 'primary_color', 'updated_at'])
        return JsonResponse({
            'success': True,
            'message': 'Theme updated successfully',
            'config': profile.theme_config
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
