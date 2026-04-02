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
 
    
    def __str__(self):
        return self.hotel_name
class Amenity(models.Model):
    
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
class Room(models.Model):
    ROOM_TYPES = [
        ('Single', 'Single'),
        ('Double', 'Double'),
        ('Deluxe', 'Deluxe'),
        ('Suite', 'Suite'),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms')
    room_type = models.CharField(max_length=50, choices=ROOM_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_rooms = models.IntegerField()
    available_rooms = models.IntegerField(blank=True,null=True)
    description = models.TextField(blank=True, null=True)
  

    def __str__(self):
        return f"{self.hotel.hotel_name} - {self.room_type}"
    
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

    def __str__(self):
        return self.name
class Task(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)  # ✅ FIX

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
