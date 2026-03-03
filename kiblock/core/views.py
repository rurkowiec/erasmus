from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Q
from functools import wraps
import hashlib
import os
from .models import User, Block, CopiedBlock, CartItem, ProjectUpload


def require_user_login(view_func):
    """
    Decorator to require user login for normal user pages.
    Redirects to login page if user is not authenticated or if user doesn't exist.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            messages.warning(request, 'Please log in to access this page.')
            return redirect('login')
        
        # Verify the user still exists in the database
        user_id = request.session.get('user_id')
        try:
            User.objects.get(id=user_id)
        except User.DoesNotExist:
            # User was deleted, clear the session
            request.session.flush()
            messages.warning(request, 'Your account no longer exists. Please log in again.')
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def get_logged_in_user(request):
    """
    Helper function to get the currently logged-in user from session.
    Returns User object or None.
    """
    user_id = request.session.get('user_id')
    if user_id:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    return None


def login_view(request):
    """
    Login page for normal users (first_name + last_name, no password).
    Uses cookies to remember accounts on the same device.
    """
    # If already logged in, redirect to blocks page
    if 'user_id' in request.session:
        return redirect('block_list')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        if not first_name or not last_name:
            messages.error(request, 'Please enter both first name and last name.')
            return render(request, 'core/login.html')
        
        # Create a unique cookie key using hash of the name combination
        # This handles special characters and ensures valid cookie names
        name_combination = f'{first_name}_{last_name}'.lower()
        name_hash = hashlib.sha256(name_combination.encode('utf-8')).hexdigest()[:16]
        cookie_key = f'user_account_{name_hash}'
        
        # Check if there's a cookie for this name combination
        existing_user_id = request.COOKIES.get(cookie_key)
        user = None
        
        if existing_user_id:
            # Try to find the existing user
            try:
                user = User.objects.get(id=int(existing_user_id), first_name=first_name, last_name=last_name)
                messages.success(request, f'Welcome back, {user}!')
            except (User.DoesNotExist, ValueError):
                # Cookie exists but user doesn't, create new user
                user = None
        
        # If no existing user found, create a new one
        if not user:
            user = User.objects.create(
                first_name=first_name,
                last_name=last_name
            )
            messages.success(request, f'Welcome, {user}! New account created.')
        
        # Store user ID in session
        request.session['user_id'] = user.id
        request.session['user_name'] = str(user)
        
        # Create response and set cookie
        response = redirect('block_list')
        # Cookie expires in 10 years (effectively permanent)
        response.set_cookie(
            cookie_key, 
            user.id, 
            max_age=315360000,  # 10 years in seconds
            httponly=True,
            samesite='Lax'
        )
        return response
    
    return render(request, 'core/login.html')


def logout_view(request):
    """
    Logout view - clears session but keeps cookies for account persistence.
    """
    # Get user name before clearing session
    user_name = request.session.get('user_name', 'User')
    
    # Clear the session (but cookies remain)
    request.session.flush()
    
    messages.success(request, f'Goodbye, {user_name}! You have been logged out.')
    return redirect('login')


@require_user_login
def block_list(request):
    """
    Main block browser page - displays all available KiCad blocks.
    """
    user = get_logged_in_user(request)
    
    blocks = Block.objects.all().order_by('name')
    
    # Calculate user's current cart total
    cart_items = CartItem.objects.filter(user=user)
    cart_total = sum(item.get_total_cost() for item in cart_items)
    cart_count = cart_items.count()
    
    context = {
        'user': user,
        'blocks': blocks,
        'cart_total': cart_total,
        'cart_count': cart_count,
        'cost_limit': user.cost_limit,
    }
    return render(request, 'core/block_list.html', context)


@require_user_login
def search_blocks(request):
    """
    AJAX endpoint for real-time block search.
    Returns filtered blocks as JSON.
    """
    search_query = request.GET.get('search', '').strip()
    
    blocks = Block.objects.all()
    if search_query:
        blocks = blocks.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
    
    blocks = blocks.order_by('name')
    
    # Serialize blocks data
    blocks_data = [{
        'id': block.id,
        'name': block.name,
        'description': block.description or 'No description provided.',
        'cost': float(block.cost),
        'block_type': block.block_type,
        'block_type_display': block.get_block_type_display(),
        'voltage': float(block.voltage) if block.voltage else 0,
        'current': float(block.current) if block.current else 0,
    } for block in blocks]
    
    return JsonResponse({
        'blocks': blocks_data,
        'count': len(blocks_data),
        'search_query': search_query,
    })


@require_user_login
@require_POST
def copy_block(request, block_id):
    """
    Records when a user copies a block's KiCad code.
    Returns the KiCad code as JSON for clipboard copying.
    """
    user = get_logged_in_user(request)
    block = get_object_or_404(Block, id=block_id)
    
    # Record the copy action
    CopiedBlock.objects.create(user=user, block=block)
    
    return JsonResponse({
        'success': True,
        'kicad_code': block.kicad_code,
        'message': f'Copied {block.name} to clipboard!'
    })


@require_user_login
@require_POST
def add_to_cart(request, block_id):
    """
    Adds a block to the user's cart or increments quantity if already present.
    """
    user = get_logged_in_user(request)
    block = get_object_or_404(Block, id=block_id)
    
    # Check if block already in cart
    cart_item, created = CartItem.objects.get_or_create(
        user=user,
        block=block,
        defaults={'quantity': 1}
    )
    
    if not created:
        # Block already in cart, increment quantity
        cart_item.quantity += 1
        cart_item.save()
        message = f'Increased {block.name} quantity to {cart_item.quantity}'
    else:
        message = f'Added {block.name} to cart'
    
    # Calculate new cart total
    cart_items = CartItem.objects.filter(user=user)
    cart_total = sum(item.get_total_cost() for item in cart_items)
    cart_count = cart_items.count()
    
    # Check if over limit
    over_limit = cart_total > user.cost_limit
    
    return JsonResponse({
        'success': True,
        'message': message,
        'cart_total': cart_total,
        'cart_count': cart_count,
        'cost_limit': user.cost_limit,
        'over_limit': over_limit,
    })


@require_user_login
def cart_view(request):
    """
    Display user's shopping cart with all items.
    """
    user = get_logged_in_user(request)
    cart_items = CartItem.objects.filter(user=user).select_related('block')
    
    cart_total = sum(item.get_total_cost() for item in cart_items)
    cart_count = cart_items.count()
    
    # Calculate current and voltage requirements
    total_current_consumption = 0.0
    total_current_supply = 0.0
    battery_voltage = None
    component_voltage = None
    has_components = False
    has_battery = False
    has_regulator = False
    warnings = []
    
    for item in cart_items:
        if item.block.is_battery():
            # This is a battery - adds to supply
            total_current_supply += item.block.current * item.quantity
            has_battery = True
            if item.block.voltage > 0:
                if battery_voltage is None:
                    battery_voltage = item.block.voltage
                elif battery_voltage != item.block.voltage:
                    warnings.append("Warning: You have batteries with different voltages in your cart!")
        else:
            # Check if this is a voltage regulator
            if 'regulator' in item.block.name.lower():
                has_regulator = True
            
            # This is a component - adds to consumption
            total_current_consumption += item.block.current * item.quantity
            if item.block.current > 0 or item.block.voltage > 0:
                has_components = True
            if item.block.voltage > 0:
                if component_voltage is None:
                    component_voltage = item.block.voltage
                elif component_voltage != item.block.voltage:
                    warnings.append("Warning: You have components with different voltage requirements!")
    
    # Check current supply
    if has_components and total_current_consumption > 0:
        if not has_battery:
            warnings.append(f"Your cart requires {total_current_consumption:.2f}A but has no battery/power source!")
        elif total_current_supply < total_current_consumption:
            warnings.append(f"Your cart requires {total_current_consumption:.2f}A but batteries can only supply {total_current_supply:.2f}A!")
    
    # Check voltage compatibility
    if has_components and component_voltage and has_battery and battery_voltage:
        if has_regulator:
            # With a regulator, we're more lenient
            if battery_voltage < component_voltage:
                warnings.append(f"Battery voltage ({battery_voltage}V) is lower than component requirements ({component_voltage}V)! Voltage regulator cannot boost voltage.")
        else:
            # Without a regulator, voltages must match closely
            if battery_voltage < component_voltage:
                warnings.append(f"Battery voltage ({battery_voltage}V) is lower than component requirements ({component_voltage}V)! Add a voltage regulator or use compatible voltage.")
            elif battery_voltage > component_voltage * 1.2:  # Allow 20% tolerance
                warnings.append(f"Battery voltage ({battery_voltage}V) is significantly higher than component requirements ({component_voltage}V)! Add a voltage regulator to step down voltage.")
    elif has_components and component_voltage and not has_battery:
        warnings.append(f"Components require {component_voltage}V but there's no battery in the cart!")
    
    context = {
        'user': user,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_count': cart_count,
        'cost_limit': user.cost_limit,
        'over_limit': cart_total > user.cost_limit,
        'warnings': warnings,
        'total_current_consumption': total_current_consumption,
        'total_current_supply': total_current_supply,
        'battery_voltage': battery_voltage,
        'component_voltage': component_voltage,
        'has_regulator': has_regulator,
    }
    return render(request, 'core/cart.html', context)


@require_user_login
@require_POST
def increase_cart_item(request, item_id):
    """
    Increase the quantity of a cart item by 1.
    """
    user = get_logged_in_user(request)
    cart_item = get_object_or_404(CartItem, id=item_id, user=user)
    
    cart_item.quantity += 1
    cart_item.save()
    
    # Recalculate totals
    cart_items = CartItem.objects.filter(user=user)
    cart_total = sum(item.get_total_cost() for item in cart_items)
    over_limit = cart_total > user.cost_limit
    
    return JsonResponse({
        'success': True,
        'quantity': cart_item.quantity,
        'item_total': cart_item.get_total_cost(),
        'cart_total': cart_total,
        'over_limit': over_limit,
    })


@require_user_login
@require_POST
def decrease_cart_item(request, item_id):
    """
    Decrease the quantity of a cart item by 1.
    Minimum quantity is 1 (use remove to delete).
    """
    user = get_logged_in_user(request)
    cart_item = get_object_or_404(CartItem, id=item_id, user=user)
    
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    
    # Recalculate totals
    cart_items = CartItem.objects.filter(user=user)
    cart_total = sum(item.get_total_cost() for item in cart_items)
    over_limit = cart_total > user.cost_limit
    
    return JsonResponse({
        'success': True,
        'quantity': cart_item.quantity,
        'item_total': cart_item.get_total_cost(),
        'cart_total': cart_total,
        'over_limit': over_limit,
    })


@require_user_login
@require_POST
def remove_cart_item(request, item_id):
    """
    Remove a cart item completely.
    """
    user = get_logged_in_user(request)
    cart_item = get_object_or_404(CartItem, id=item_id, user=user)
    
    block_name = cart_item.block.name
    cart_item.delete()
    
    # Recalculate totals
    cart_items = CartItem.objects.filter(user=user)
    cart_total = sum(item.get_total_cost() for item in cart_items)
    over_limit = cart_total > user.cost_limit
    
    return JsonResponse({
        'success': True,
        'message': f'Removed {block_name} from cart',
        'cart_total': cart_total,
        'cart_count': cart_items.count(),
        'over_limit': over_limit,
    })


@require_user_login
def copied_history_view(request):
    """
    Display user's history of copied blocks.
    """
    user = get_logged_in_user(request)
    copied_blocks = CopiedBlock.objects.filter(user=user).select_related('block').order_by('-copied_at')
    
    context = {
        'user': user,
        'copied_blocks': copied_blocks,
    }
    return render(request, 'core/copied_history.html', context)


@require_user_login
@require_POST
def upload_project(request):
    """
    Upload a KiCad project file from a student.
    File is saved with format: firstname_lastname.extension
    """
    user = get_logged_in_user(request)
    
    if 'file' not in request.FILES:
        return JsonResponse({
            'success': False,
            'message': 'No file uploaded'
        }, status=400)
    
    uploaded_file = request.FILES['file']
    
    # Get original filename and extension
    original_filename = uploaded_file.name
    file_extension = os.path.splitext(original_filename)[1]
    
    # Validate file type (accept only archive formats)
    allowed_extensions = ['.zip', '.rar', '.7z', '.tar', '.gz']
    if file_extension.lower() not in allowed_extensions:
        return JsonResponse({
            'success': False,
            'message': f'File type not supported. Allowed: {', '.join(allowed_extensions)}'
        }, status=400)
    
    try:
        # Create new filename: firstname_lastname.extension
        new_filename = f"{user.first_name}_{user.last_name}{file_extension}"
        
        # Check if user already uploaded a file with this extension
        existing_upload = ProjectUpload.objects.filter(
            user=user,
            file__endswith=file_extension
        ).first()
        
        if existing_upload:
            # Delete old file
            if existing_upload.file:
                if os.path.isfile(existing_upload.file.path):
                    os.remove(existing_upload.file.path)
            existing_upload.delete()
        
        # Save the file with new name
        uploaded_file.name = new_filename
        project_upload = ProjectUpload.objects.create(
            user=user,
            file=uploaded_file,
            original_filename=original_filename
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Project uploaded successfully as {new_filename}',
            'filename': new_filename
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error uploading file: {str(e)}'
        }, status=400)
