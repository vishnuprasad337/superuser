from django.db import models
from django.utils import timezone
class Hotel(models.Model):
    
    hotel_name = models.CharField(max_length=100,unique=True)
    email = models.EmailField(null=True, blank=True)
    owner_name = models.CharField(max_length=100)
    address = models.TextField(max_length=200)
    city = models.CharField(max_length=100)
    property_type = models.CharField(max_length=50, default="Hotel")
    image = models.ImageField(upload_to="property_images/", null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    amenities = models.TextField(blank=True, null=True)
    password = models.CharField(max_length=100) 
    properties=models.ManyToManyField('Amenity', blank=True)
    is_approved = models.BooleanField(default=False)
    
    is_subscribed = models.BooleanField(default=False)
 
    
    def __str__(self):
        return self.hotel_name
class Amenity(models.Model):
    AMENITY_TYPE = (
        ("default", "Default"),
        ("premium", "Premium"),
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    amenity_type = models.CharField(
        max_length=10,
        choices=AMENITY_TYPE,
        default="default"  
    )

    def __str__(self):
        return self.name
class Room(models.Model):
    ROOM_TYPES = [
        ('Single', 'Single'),
        ('Double', 'Double'),
        ('Deluxe', 'Deluxe'),
        ('Suite', 'Suite'),
    ]

    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Occupied', 'Occupied'),
        ('Dirty', 'Dirty'),
        ('Cleaning', 'Cleaning'),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms')
    room_type = models.CharField(max_length=50, choices=ROOM_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_rooms = models.IntegerField()
    available_rooms = models.IntegerField(default=0) 
    description = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available') 
    def __str__(self):
        return f"{self.hotel.hotel_name} - {self.room_type}"
class RoomUnit(models.Model):
    UNIT_STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Occupied', 'Occupied'),
        ('Dirty', 'Dirty'),
        ('Reserved', 'Reserved'),
        ('Cleaning', 'Cleaning'),
        ('Maintenance', 'Maintenance'),
    ]
    
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="units")
    room_number = models.CharField(max_length=10, unique=True)
    status = models.CharField(max_length=20, choices=UNIT_STATUS_CHOICES, default='Available')

    def __str__(self):
        return self.room_number
    
class Department(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Staff(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="staffs")
    name = models.CharField(max_length=100,unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    role = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name
class Task(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="tasks")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)  
    room_unit = models.ForeignKey(RoomUnit, on_delete=models.CASCADE, null=True, blank=True) 
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    status = models.CharField(max_length=50, default="Pending")

    def __str__(self):
        return f"{self.title} - {self.staff.name}"
class Shift(models.Model):
    SHIFT_CHOICES = [
        ("Morning", "Morning"),
        ("Evening", "Evening"),
        ("Night", "Night"),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)

    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.staff.name} - {self.shift}"
class Guest(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)

    email = models.EmailField(blank=True, null=True)
    nationality = models.CharField(max_length=50, blank=True, null=True)

    id_type = models.CharField(max_length=50, blank=True, null=True)
    id_photo = models.ImageField(upload_to="guest_ids/", blank=True, null=True)
    id_number = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.full_name
class Booking(models.Model):
    STATUS_CHOICES = [
        ("confirmed", "Confirmed"),
        ("checked_in", "Checked In"),
        ("checked_out", "Checked Out"),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    room_unit = models.ForeignKey(RoomUnit, on_delete=models.SET_NULL, null=True, blank=True) 
    check_in = models.DateField()
    check_out = models.DateField()

    actual_check_in = models.DateTimeField(null=True, blank=True)
    actual_check_out = models.DateTimeField(null=True, blank=True)

    guests_count = models.IntegerField(default=1)
    special_requests = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="confirmed")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.guest.full_name} - {self.room.room_type}"
class Payment(models.Model):
    PAYMENT_METHODS = [
        ("Cash", "Cash"),
        ("Card", "Card"),
        ("UPI", "UPI"),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)

    room_charges = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, null=True, blank=True)
    payment_status = models.CharField(max_length=20, default="pending")

    paid_at = models.DateTimeField(null=True, blank=True)
    collected_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Payment - {self.booking.id}"
class InventoryItem(models.Model):
    CATEGORY_CHOICES = [
        ('cleaning', 'Cleaning Supplies'),
        ('linen', 'Linen & Towels'),
        ('amenities', 'Guest Amenities'),
        ('equipment', 'Equipment'),
    ]
    
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='inventory_items')
    room = models.ForeignKey(RoomUnit, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_items')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='cleaning')
    quantity = models.IntegerField(default=0)
    unit = models.CharField(max_length=50, default='pieces')
    reorder_level = models.IntegerField(default=10)
    description = models.TextField(blank=True, null=True)
    assigned_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_inventory')
    assigned_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        room_info = f" - Room {self.room.room_number}" if self.room else ""
        return f"{self.name} - {self.quantity} {self.unit}{room_info}"