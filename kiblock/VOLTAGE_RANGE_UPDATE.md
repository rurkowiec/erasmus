# Voltage Range Feature Update

## What Changed

The Block model now supports voltage ranges for components instead of single voltage values:

- **Old:** Components had a single `voltage` field (e.g., 5V)
- **New:** Components have `voltage_min` and `voltage_max` fields (e.g., 3.3-5V range)

## Benefits

1. **More Accurate Specifications:** Components can now specify their actual operating voltage range
2. **Better Cart Validation:** The system checks if battery voltage falls within component ranges
3. **Smarter Warnings:** Cart warnings now identify specific incompatible components

## Database Changes

The migration automatically:
- Removed the old `voltage` field
- Added `voltage_min` field (default 0.0)
- Added `voltage_max` field (default 0.0)
- Existing data will have both fields set to 0 (needs manual update)

## How to Update Existing Blocks

### In Django Admin:

1. Go to the admin panel: `/admin/core/block/`
2. Edit each block
3. Update voltage fields:
   - **For batteries:** Set `voltage_min` = `voltage_max` = output voltage (e.g., both 5V)
   - **For components with fixed voltage:** Set both to the same value (e.g., both 3.3V)
   - **For components with voltage range:** Set min and max (e.g., min=3.3V, max=5V)

### Using Django Shell:

```python
# Connect to the container
docker-compose exec web python manage.py shell

# Example: Update a specific block
from core.models import Block
block = Block.objects.get(name="LED Red")
block.voltage_min = 1.8
block.voltage_max = 3.3
block.save()

# Example: Batch update all batteries to have fixed voltage
batteries = Block.objects.filter(block_type='battery')
for battery in batteries:
    battery.voltage_min = 3.7  # or whatever voltage
    battery.voltage_max = 3.7
    battery.save()
```

## Display Format

- **Fixed voltage:** "5V" (when min = max)
- **Voltage range:** "3.3-5V" (when min ≠ max)
- **No voltage:** "N/A" (when both are 0)

## Cart Validation Logic

The cart now:
1. Checks if each component's voltage range is compatible with battery voltage
2. Lists specific incompatible components in warnings
3. Considers voltage regulators for more lenient validation
4. Shows voltage range requirements (e.g., "3.3-5V required")

## Deploy to Production

After updating your blocks data:

```bash
# Build and restart the Docker container
docker-compose down
docker-compose up -d --build

# Or just restart if no Dockerfile changes
docker-compose restart
```

## API Changes

The search API now returns:
- `voltage_min`: Minimum voltage
- `voltage_max`: Maximum voltage
- `voltage_display`: Formatted display string (e.g., "3.3-5V")

Old `voltage` field is removed.
