from django.db import models


class User(models.Model):
    """Custom user model for KiBlock (no password authentication)"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    cost_limit = models.FloatField(default=100.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Block(models.Model):
    """Represents a copyable KiCad block/snippet"""
    BLOCK_TYPE_CHOICES = [
        ('component', 'Component'),
        ('battery', 'Battery/Power Source'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    kicad_code = models.TextField(help_text="Full KiCad snippet code")
    cost = models.FloatField()
    block_type = models.CharField(max_length=20, choices=BLOCK_TYPE_CHOICES, default='component')
    voltage = models.FloatField(default=0.0, help_text="Operating voltage in V (for components) or output voltage (for batteries)")
    current = models.FloatField(default=0.0, help_text="Current consumption in A (for components) or max supply current (for batteries)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def is_battery(self):
        """Check if this block is a battery/power source"""
        return self.block_type == 'battery'


class CopiedBlock(models.Model):
    """Tracks when a user copies a block"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='copied_blocks'
    )
    block = models.ForeignKey(
        Block,
        on_delete=models.CASCADE,
        related_name='copied_by'
    )
    copied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-copied_at']

    def __str__(self):
        return f"{self.user} copied {self.block} at {self.copied_at}"


class CartItem(models.Model):
    """Represents blocks added to a user's cart"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    block = models.ForeignKey(
        Block,
        on_delete=models.CASCADE,
        related_name='in_carts'
    )
    quantity = models.IntegerField(default=1)

    class Meta:
        unique_together = ['user', 'block']
        ordering = ['user', 'block']

    def __str__(self):
        return f"{self.user} - {self.block} (x{self.quantity})"

    def get_total_cost(self):
        """Calculate total cost for this cart item"""
        return self.block.cost * self.quantity


class ProjectUpload(models.Model):
    """Tracks uploaded KiCad project files from students"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_projects'
    )
    file = models.FileField(upload_to='projects/')
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user} - {self.original_filename}"
