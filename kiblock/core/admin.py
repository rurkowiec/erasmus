from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import User, Block, CopiedBlock, CartItem, ProjectUpload, Settings


class CartItemInline(admin.TabularInline):
    """Inline editor for cart items within User admin"""
    model = CartItem
    extra = 1
    autocomplete_fields = ['block']
    fields = ['block', 'quantity', 'get_total_cost']
    readonly_fields = ['get_total_cost']
    
    def get_total_cost(self, obj):
        if obj.id:
            return f"{obj.get_total_cost()} credits"
        return "-"
    get_total_cost.short_description = 'Subtotal'


class CopiedBlockInline(admin.TabularInline):
    """Inline viewer for copied blocks within User admin"""
    model = CopiedBlock
    extra = 0
    can_delete = True
    autocomplete_fields = ['block']
    fields = ['block', 'copied_at']
    readonly_fields = ['copied_at']
    ordering = ['-copied_at']


class ProjectUploadInline(admin.TabularInline):
    """Inline viewer for uploaded projects within User admin"""
    model = ProjectUpload
    extra = 0
    can_delete = True
    fields = ['original_filename', 'file', 'uploaded_at']
    readonly_fields = ['uploaded_at']
    ordering = ['-uploaded_at']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'cart_total', 'cart_count', 'created_at']
    search_fields = ['first_name', 'last_name']
    list_filter = ['created_at']
    ordering = ['last_name', 'first_name']
    readonly_fields = ['created_at', 'cart_total', 'cart_count', 'copied_count']
    
    fieldsets = (
        ('User Information', {
            'fields': ('first_name', 'last_name')
        }),
        ('Statistics', {
            'fields': ('cart_total', 'cart_count', 'copied_count', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [CartItemInline, CopiedBlockInline, ProjectUploadInline]
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'
    full_name.admin_order_field = 'last_name'
    
    def cart_total(self, obj):
        total = sum(item.get_total_cost() for item in obj.cart_items.all())
        settings = Settings.get_settings()
        if total > settings.global_cost_limit:
            return f"{total} credits (OVER LIMIT)"
        return f"{total} credits"
    cart_total.short_description = 'Cart Total'
    
    def cart_count(self, obj):
        return obj.cart_items.count()
    cart_count.short_description = 'Cart Items'
    
    def copied_count(self, obj):
        return obj.copied_blocks.count()
    copied_count.short_description = 'Blocks Copied'


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ['global_cost_limit', 'updated_at']
    fieldsets = (
        ('Global Cost Limit', {
            'fields': ('global_cost_limit',),
            'description': 'This cost limit applies to all users. Any new account created will have this limit.'
        }),
        ('System Info', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['updated_at']
    
    def has_add_permission(self, request):
        # Only allow one Settings instance
        return not Settings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Never allow deleting the settings
        return False


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ['name', 'block_type', 'voltage_display', 'current', 'cost', 'has_image', 'times_copied', 'times_in_cart', 'created_at']
    search_fields = ['name', 'description', 'kicad_code']
    list_filter = ['created_at', 'cost', 'block_type']
    ordering = ['name']
    readonly_fields = ['created_at', 'times_copied', 'times_in_cart', 'image_preview']
    
    fieldsets = (
        ('Block Information', {
            'fields': ('name', 'description', 'block_type', 'cost')
        }),
        ('Image', {
            'fields': ('image', 'image_preview'),
            'description': 'Optional block image (will be displayed as a square on the site)'
        }),
        ('Electrical Properties', {
            'fields': ('voltage_min', 'voltage_max', 'current'),
            'description': 'For components: voltage range = operating voltage range, current = consumption. For batteries: voltage_min = voltage_max = output voltage, current = max supply.'
        }),
        ('KiCad Code', {
            'fields': ('kicad_code',),
            'classes': ('monospace',)
        }),
        ('Statistics', {
            'fields': ('times_copied', 'times_in_cart', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def voltage_display(self, obj):
        return obj.get_voltage_display()
    voltage_display.short_description = 'Voltage'
    
    def has_image(self, obj):
        return bool(obj.image)
    has_image.short_description = 'Image'
    has_image.boolean = True
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img id="preview-image" src="{}" style="max-width: 200px; max-height: 200px; border: 1px solid #ddd; border-radius: 4px;" />', obj.image.url)
        return mark_safe('<div id="preview-image" style="color: #999; font-style: italic;">No image uploaded</div>')
    image_preview.short_description = 'Preview'
    
    class Media:
        js = ('admin/js/block_image_preview.js',)
    
    def times_copied(self, obj):
        count = obj.copied_by.count()
        return f"{count} times"
    times_copied.short_description = 'Times Copied'
    
    def times_in_cart(self, obj):
        count = obj.in_carts.count()
        return f"{count} carts"
    times_in_cart.short_description = 'In Carts'


@admin.register(CopiedBlock)
class CopiedBlockAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'block_name', 'block_cost', 'copied_at']
    list_filter = ['copied_at', 'user', 'block']
    search_fields = ['user__first_name', 'user__last_name', 'block__name']
    ordering = ['-copied_at']
    autocomplete_fields = ['user', 'block']
    readonly_fields = ['copied_at']
    date_hierarchy = 'copied_at'
    
    def user_name(self, obj):
        return str(obj.user)
    user_name.short_description = 'User'
    user_name.admin_order_field = 'user__last_name'
    
    def block_name(self, obj):
        return obj.block.name
    block_name.short_description = 'Block'
    block_name.admin_order_field = 'block__name'
    
    def block_cost(self, obj):
        return f"{obj.block.cost} credits"
    block_cost.short_description = 'Cost'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'block_name', 'quantity', 'cost_per_item', 'get_total_cost', 'over_limit']
    list_filter = ['user']
    search_fields = ['user__first_name', 'user__last_name', 'block__name']
    ordering = ['user', 'block']
    autocomplete_fields = ['user', 'block']
    
    def user_name(self, obj):
        return str(obj.user)
    user_name.short_description = 'User'
    user_name.admin_order_field = 'user__last_name'
    
    def block_name(self, obj):
        return obj.block.name
    block_name.short_description = 'Block'
    block_name.admin_order_field = 'block__name'
    
    def cost_per_item(self, obj):
        return f"{obj.block.cost} credits"
    cost_per_item.short_description = 'Unit Cost'

    def get_total_cost(self, obj):
        return f"{obj.get_total_cost()} credits"
    get_total_cost.short_description = 'Subtotal'
    
    def over_limit(self, obj):
        user_cart_total = sum(item.get_total_cost() for item in obj.user.cart_items.all())
        settings = Settings.get_settings()
        if user_cart_total > settings.global_cost_limit:
            return "YES"
        return "No"
    over_limit.short_description = 'Over Limit?'


@admin.register(ProjectUpload)
class ProjectUploadAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'original_filename', 'saved_filename', 'file_size', 'uploaded_at']
    list_filter = ['uploaded_at', 'user']
    search_fields = ['user__first_name', 'user__last_name', 'original_filename']
    ordering = ['-uploaded_at']
    readonly_fields = ['uploaded_at', 'file_size', 'saved_filename']
    date_hierarchy = 'uploaded_at'
    autocomplete_fields = ['user']
    
    fieldsets = (
        ('Upload Information', {
            'fields': ('user', 'file', 'original_filename', 'saved_filename')
        }),
        ('Metadata', {
            'fields': ('file_size', 'uploaded_at'),
        }),
    )
    
    def user_name(self, obj):
        return str(obj.user)
    user_name.short_description = 'User'
    user_name.admin_order_field = 'user__last_name'
    
    def saved_filename(self, obj):
        if obj.file:
            return obj.file.name.split('/')[-1]
        return "-"
    saved_filename.short_description = 'Saved As'
    
    def file_size(self, obj):
        if obj.file:
            size_bytes = obj.file.size
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.2f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.2f} MB"
        return "-"
    file_size.short_description = 'File Size'
