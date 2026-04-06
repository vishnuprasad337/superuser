from django.shortcuts import render, redirect
from .models import Hotel,Amenity,Room,Department,Staff,Task,Shift,Guest,Booking,Payment,RoomUnit,InventoryItem
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from django.views.decorators.csrf import csrf_exempt
def index(request):
    return render(request, "index.html")
def hotel_register(request):
    approved = None
    error = None
    success = None

    if request.method == "POST":
        email = request.POST.get("email")

        existing = Hotel.objects.filter(email=email).first()

        if existing:
            if existing.is_approved:
                approved = "Your account is approved! You can login now."
            else:
                error = "Already registered. Waiting for admin approval."
        else:
            hotel_name = request.POST.get("hotel_name")
            owner_name = request.POST.get("owner_name")
            address = request.POST.get("address")
            city = request.POST.get("city")
            property_type = request.POST.get("property_type")
            description = request.POST.get("description")
            amenities = request.POST.get("amenities")
            password = request.POST.get("password")
            image = request.FILES.get("image")

            Hotel.objects.create(
                hotel_name=hotel_name,
                email=email,
                owner_name=owner_name,
                address=address,
                city=city,
                property_type=property_type,
                description=description,
                amenities=amenities,
                password=password,
                image=image
            )

            success = "Registration sent for admin approval!"

    return render(request, "register.html", {
        "success": success,
        "error": error,
        "approved": approved
    })
def hotel_login(request):
    success_msg = request.GET.get("approved")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            hotel = Hotel.objects.get(email=email, password=password)

            if not hotel.is_approved:
                return render(request, "login.html", {
                    "error": "Waiting for admin approval"
                })

            request.session['hotel_id'] = hotel.id

            return redirect("amenities_page")

        except Hotel.DoesNotExist:
            return render(request, "login.html", {
                "error": "Invalid credentials"
            })

    return render(request, "login.html", {
        "success": success_msg
    })
def amenities_page(request):
    amenities = Amenity.objects.all()
    return render(request, "amenities.html", {"amenities": amenities})



@csrf_exempt
def add_amenity(request):
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name")
            
            
            
            if not name:
                return JsonResponse({"error": "Name required"}, status=400)
            
            
            amenity, created = Amenity.objects.get_or_create(name=name)
            
            print(f"[DEBUG] Amenity {'created' if created else 'retrieved'}: ID={amenity.id}, Name={amenity.name}")
            
            return JsonResponse({
                "id": amenity.id,
                "name": amenity.name,
                "created": created
            })
        except Exception as e:
            print(f"[ERROR] Exception in add_amenity: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)


def get_amenities(request):
    
    try:
        amenities = Amenity.objects.all().values("id", "name")
        return JsonResponse({
            "amenities": list(amenities)
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



@csrf_exempt
def save_selected_amenities(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            selected_ids = data.get("amenities", [])

            selected_ids = [int(i) for i in selected_ids if str(i).isdigit()]

            hotel_id = request.session.get('hotel_id')

            if not hotel_id:
                return JsonResponse({"error": "Hotel not logged in"}, status=400)

            hotel = Hotel.objects.get(id=hotel_id)

            
            hotel.properties.set(selected_ids)

            print(f"[DEBUG] Saved for {hotel.hotel_name}: {selected_ids}")

            return JsonResponse({
                "success": True,
                "saved_count": len(selected_ids)
            })

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)

def dashboard(request):
    hotel_id = request.session.get('hotel_id')

    if not hotel_id:
        return redirect("hotel_login")

    hotel = Hotel.objects.get(id=hotel_id)

   
    amenities = hotel.properties.all()

   
    total_rooms = Room.objects.filter(hotel=hotel).count()

    
    total_staff = Staff.objects.filter(hotel=hotel).count()

    print(f"[DEBUG] {hotel.hotel_name} amenities: {[a.name for a in amenities]}")

    return render(request, "property.html", {
        "hotel": hotel,
        "amenities": amenities,
        "total_rooms": total_rooms,  
        "total_staff": total_staff    
    })
 ##----------------------ROOM MODULE----------------------
def room_page(request):
    hotel_id = request.session.get('hotel_id')

    if not hotel_id:
        return redirect("hotel_login")

    hotel = Hotel.objects.get(id=hotel_id)

   
    if request.method == "POST":
        room_type = request.POST.get("room_type")
        price = request.POST.get("price")
        total_rooms = request.POST.get("total_rooms")
        description = request.POST.get("description")
        image = request.FILES.get("image")

        Room.objects.create(
            hotel=hotel,
            room_type=room_type,
            price=price,
            total_rooms=total_rooms,
            available_rooms=total_rooms,
            description=description,
            image=image
        )

    
    selected_type = request.GET.get("type")

    if selected_type:
        rooms = Room.objects.filter(hotel=hotel, room_type=selected_type)
    else:
        rooms = Room.objects.filter(hotel=hotel)

    return render(request, "room.html", {
        "rooms": rooms,
        "selected_type": selected_type
    })

@csrf_exempt
def add_room(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            hotel_id = request.session.get('hotel_id')

            if not hotel_id:
                return JsonResponse({"error": "Not logged in"}, status=401)

            hotel = Hotel.objects.get(id=hotel_id)

            total_rooms = int(data.get('total_rooms'))
            room_type = data.get('room_type')

            # Create main room type
            room = Room.objects.create(
                hotel=hotel,
                room_type=room_type,
                price=data.get('price'),
                total_rooms=total_rooms,
                available_rooms=total_rooms,
                description=data.get('description', '')
            )

            prefix_map = {
                "Single": "S",
                "Double": "D",
                "Deluxe": "DL",
                "Suite": "SU"
            }

            prefix = prefix_map.get(room_type, "R")

            
            existing_count = RoomUnit.objects.filter(room__hotel=hotel, room__room_type=room_type).count()

            units = []
            for i in range(1, total_rooms + 1):
                number = f"{prefix}{existing_count + i}"
                units.append(RoomUnit(room=room, room_number=number))

            RoomUnit.objects.bulk_create(units)

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

def get_rooms(request):
    try:
        hotel_id = request.session.get('hotel_id')
        if not hotel_id:
            return JsonResponse({"error": "Not logged in"}, status=401)

        hotel = Hotel.objects.get(id=hotel_id)
        rooms = Room.objects.filter(hotel=hotel)

        room_type = request.GET.get('type')
        if room_type:
            rooms = rooms.filter(room_type=room_type)

        room_list = []

        for room in rooms:
            # Get all room units for this room type
            room_units = room.units.all().order_by('room_number')
            
            total_units = room_units.count()
            available_units = room_units.filter(status="Available").count()
            
            # Create list of room units with their numbers, status, and color
            units_list = []
            for unit in room_units:
                # Determine color based on status
                if unit.status == "Available":
                    color = "green"
                    status_display = "Available"
                elif unit.status == "Occupied":
                    color = "red"
                    status_display = "Occupied"
                elif unit.status == "Dirty":
                    color = "yellow"
                    status_display = "Dirty - Needs Cleaning"
                elif unit.status == "Reserved":
                    color = "blue"
                    status_display = "Reserved"
                else:
                    color = "gray"
                    status_display = unit.status
                    
                units_list.append({
                    "number": unit.room_number,
                    "status": unit.status,
                    "status_display": status_display,
                    "color": color,
                    "id": unit.id
                })

            room_list.append({
                "id": room.id,
                "room_type": room.room_type,
                "price": str(room.price),
                "total_rooms": total_units,
                "available_rooms": available_units,
                "description": room.description,
                "room_units": units_list
            })

        return JsonResponse({
            "rooms": room_list,
            "hotel_name": hotel.hotel_name
        })

    except Hotel.DoesNotExist:
        return JsonResponse({"error": "Hotel not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
def get_room(request, room_id):
    try:
        room = Room.objects.get(id=room_id)
        return JsonResponse({
            "id": room.id,
            "room_type": room.room_type,
            "price": str(room.price),
            "total_rooms": room.total_rooms,
            "available_rooms": room.available_rooms,
            "description": room.description
        })
    except Room.DoesNotExist:
        return JsonResponse({"error": "Room not found"}, status=404)

##----------------------STAFF MODULE----------------------

def staff_page(request):
    hotel_id = request.session.get("hotel_id")
    departments = Department.objects.filter(hotel_id=hotel_id)

    return render(request, "staff.html", {
        "departments": departments
    })
def add_department(request):
    if request.method == "POST":
        name = request.POST.get("name")

       
        hotel = request.session.get("hotel_id")

        if hotel:
            hotel_obj = Hotel.objects.get(id=hotel)

            Department.objects.create(
                hotel=hotel_obj,
                name=name
            )

        return redirect('staff_page')
def get_staff(request):
    hotel_id = request.session.get("hotel_id")
    
    staff = Staff.objects.filter(hotel_id=hotel_id).select_related('department')
    
    staff_list = []
    for s in staff:
        staff_list.append({
            "id": s.id,
            "name": s.name,
            "email": s.email if s.email else "-",
            "phone": s.phone if s.phone else "",
            "department_id": s.department_id if s.department_id else None,
            "department_name": s.department.name if s.department else "N/A",
            "role": s.role if s.role else "Staff",
        })
    
    return JsonResponse(staff_list, safe=False)

@csrf_exempt
@require_http_methods(["POST"])
def add_staff(request):
    
    try:
        hotel_id = request.session.get("hotel_id")
        
        # Debug: Print to console to check if hotel_id exists
        print(f"Hotel ID from session: {hotel_id}")
        
        if not hotel_id:
            return JsonResponse({
                "error": "Hotel not found in session. Please login first."
            }, status=400)
        
        # Get form data
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        department_id = request.POST.get("department")
        role = request.POST.get("role")
        password = request.POST.get("password")
        
        
        print(f"Adding staff - Name: {name}, Department: {department_id}, Role: {role}")
        
        # Validation
        if not name:
            return JsonResponse({"error": "Staff name is required"}, status=400)
        if not department_id:
            return JsonResponse({"error": "Department is required"}, status=400)
        
        # Create staff member
        staff = Staff.objects.create(
            hotel_id=hotel_id,
            name=name,
            email=email or "",
            phone=phone or "",
            department_id=department_id,
            role=role,
            password=password 
        )
        
        # Debug: Print success
        print(f"Staff created successfully with ID: {staff.id}")
        
        # Return JSON response with staff data
        return JsonResponse({
            "success": True,
            "id": staff.id,
            "name": staff.name,
            "email": staff.email,
            "phone": staff.phone,
            "role": staff.role,
            "department_id": staff.department_id,
            "message": f"Staff '{name}' added successfully"
        }, status=200)
        
    except Exception as e:
        # Debug: Print error
        print(f"Error adding staff: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

def assign_task(request):
    if request.method == "POST":
        staff_id = request.POST.get("staff")
        title = request.POST.get("title")
        description = request.POST.get("description")

        Task.objects.create(
            staff_id=staff_id,
            title=title,
            description=description
        )

        return redirect("staff_page")
def get_departments(request):
    hotel_id = request.session.get("hotel_id")
    
    departments = Department.objects.filter(hotel_id=hotel_id)
    
    department_list = []
    for dept in departments:
        staff_count = Staff.objects.filter(department_id=dept.id, hotel_id=hotel_id).count()
        department_list.append({
            "id": dept.id,
            "name": dept.name,
            "staff_count": staff_count
        })
    
    return JsonResponse(department_list, safe=False)
def get_tasks(request):
    hotel_id = request.session.get("hotel_id")
    tasks = Task.objects.filter(staff__hotel_id=hotel_id).select_related("staff")
    
    task_list = []
    for t in tasks:
        task_list.append({
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "staff": t.staff.name,
            "staff_id": t.staff.id, 
            "status": t.status,
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(t, 'created_at') else None
        })
    
    return JsonResponse({"tasks": task_list, "count": tasks.count()})
def get_shifts(request):
    hotel_id = request.session.get("hotel_id")

    shifts = Shift.objects.filter(hotel_id=hotel_id).select_related("staff", "department")

    data = []
    for s in shifts:
        data.append({
            "id": s.id,
            "staff_id": s.staff.id,  
            "staff": s.staff.name,
            "department": s.department.name,
            "department_id": s.department.id,  # ADD THIS
            "shift": s.shift,
            "date": s.date.strftime("%Y-%m-%d") if s.date else None
        })

    return JsonResponse(data, safe=False)


def assign_shift(request):
    if request.method == "POST":
        hotel_id = request.session.get("hotel_id")
        staff_id = request.POST.get("staff")
        department_id = request.POST.get("department")
        shift_value = request.POST.get("shift")
        
        # Check if shift already exists for this staff
        existing_shift = Shift.objects.filter(
            hotel_id=hotel_id,
            staff_id=staff_id
        ).first()
        
        if existing_shift:
            # Update existing shift
            existing_shift.shift = shift_value
            existing_shift.department_id = department_id
            existing_shift.save()
            return JsonResponse({"success": True, "message": "Shift updated"})
        else:
            # Create new shift
            Shift.objects.create(
                hotel_id=hotel_id,
                staff_id=staff_id,
                department_id=department_id,
                shift=shift_value
            )
            return JsonResponse({"success": True, "message": "Shift assigned"})

    return JsonResponse({"error": "Method not allowed"}, status=405)


def update_shift(request):
    if request.method == "POST":
        shift_id = request.POST.get("shift_id")
        new_shift = request.POST.get("shift")
        
        try:
            shift = Shift.objects.get(id=shift_id)
            shift.shift = new_shift
            shift.save()
            return JsonResponse({"success": True})
        except Shift.DoesNotExist:
            return JsonResponse({"error": "Shift not found"}, status=404)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)
def staff_by_shift(request):
    hotel_id = request.session.get("hotel_id")
    shift = request.GET.get("shift")

    staff = Shift.objects.filter(
        hotel_id=hotel_id,
        shift=shift
    ).select_related("staff")

    data = [{
        "name": s.staff.name,
        "role": s.staff.role
    } for s in staff]

    return JsonResponse(data, safe=False)
#----------------------STAFF MODULE----------------------
def staff_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        selected_dept = request.POST.get("department").lower()

        try:
            staff = Staff.objects.get(email=email, password=password)

            actual_dept = staff.department.name.lower()

            
            if selected_dept != actual_dept:
                return render(request, "staff_login.html", {
                    "error": "Department mismatch"
                })

            
            request.session["staff_id"] = staff.id
            request.session["department"] = actual_dept

            
            if actual_dept == "housekeeping":
                return redirect("housekeeping_dashboard")

            elif actual_dept == "hr":
                return redirect("hr_dashboard")

            elif actual_dept == "front desk":
                return redirect("frontoffice_dashboard")

            elif actual_dept == "accountant":
                return redirect("accountant_dashboard")

            else:
                return redirect("staff_login")

        except Staff.DoesNotExist:
            return render(request, "staff_login.html", {
                "error": "Invalid credentials"
            })

    return render(request, "staff_login.html")
#----------------------HOUSEKEEPING MODULE----------------------
def housekeeping_dashboard(request):
    staff_id = request.session.get("staff_id")

    if not staff_id:
        return redirect("staff_login")

    staff = Staff.objects.select_related("hotel").get(id=staff_id)
    hotel = staff.hotel
    
    all_tasks = Task.objects.filter(staff_id=staff_id).order_by('-created_at')
    
    for task in all_tasks:
        if task.room_unit and task.room_unit.status == "Available":
            if task.status != "Completed":
                task.status = "Completed"
                task.save()
    
    tasks = Task.objects.filter(staff_id=staff_id, status="Pending")
    all_tasks = Task.objects.filter(staff_id=staff_id).order_by('-created_at')
    
    shift = Shift.objects.filter(staff_id=staff_id).select_related("department").first()
    
    assigned_room_ids = Task.objects.filter(
        staff_id=staff_id, 
        room_unit__isnull=False
    ).values_list('room_unit_id', flat=True).distinct()
    
    room_units = RoomUnit.objects.filter(
        id__in=assigned_room_ids
    ).select_related('room')
    
    all_room_units = RoomUnit.objects.filter(room__hotel=hotel).select_related('room')
    
    rooms_list = []
    clean_count = 0
    dirty_count = 0
    maintenance_count = 0
    cleaning_count = 0
    
    for unit in room_units:
        room_data = {
            "number": unit.room_number,
            "status": unit.status.lower(),
            "room_type": unit.room.room_type,
            "id": unit.id,
            "notes": ""
        }
        
        if unit.status == "Available":
            clean_count += 1
        elif unit.status == "Dirty":
            dirty_count += 1
        elif unit.status == "Maintenance":
            maintenance_count += 1
        elif unit.status == "Cleaning":
            cleaning_count += 1
            room_data["status"] = "cleaning"
        
        rooms_list.append(room_data)
    
    inventory_items = []
    total_items = 0
    in_stock_items = 0
    low_stock_items = 0
    
    context = {
        "staff": staff,
        "hotel": hotel,
        "tasks": tasks,
        "all_tasks": all_tasks,
        "shift": shift,
        "rooms": rooms_list,
        "all_rooms": all_room_units,
        "clean_rooms": clean_count,
        "dirty_rooms": dirty_count,
        "maintenance_rooms": maintenance_count,
        "cleaning_rooms": cleaning_count,
        "pending_tasks": tasks.count(),
        "inventory_items": inventory_items,
        "total_items": total_items,
        "in_stock_items": in_stock_items,
        "low_stock_items": low_stock_items,
    }
    
    return render(request, "housekeeping.html", context)
@csrf_exempt
def start_cleaning(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            room_unit_id = data.get("room_unit_id")
            
            room_unit = RoomUnit.objects.get(id=room_unit_id)
            old_status = room_unit.status
            
            if old_status == "Dirty":
                room_unit.status = "Cleaning"
                room_unit.save()
                
                task = Task.objects.create(
                    staff_id=request.session.get("staff_id"),
                    room_unit=room_unit,
                    room=room_unit.room,
                    title=f"Clean Room {room_unit.room_number}",
                    description="Room cleaning in progress",
                    status="Pending"
                )
                
                return JsonResponse({
                    "success": True,
                    "message": f"Started cleaning Room {room_unit.room_number}",
                    "new_status": "Cleaning",
                    "task_id": task.id
                })
            else:
                return JsonResponse({
                    "error": f"Room status is {old_status}, cannot start cleaning"
                }, status=400)
                
        except RoomUnit.DoesNotExist:
            return JsonResponse({"error": "Room not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def complete_cleaning(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            room_unit_id = data.get("room_unit_id")
            task_id = data.get("task_id")
            
            room_unit = RoomUnit.objects.get(id=room_unit_id)
            
            if room_unit.status == "Cleaning":
                room_unit.status = "Available"
                room_unit.save()
                
                room = room_unit.room
                room.available_rooms += 1
                room.save()
                
                if task_id:
                    try:
                        task = Task.objects.get(id=task_id)
                        task.status = "Completed"
                        task.save()
                    except Task.DoesNotExist:
                        pass
                
                return JsonResponse({
                    "success": True,
                    "message": f"Room {room_unit.room_number} is now clean and available",
                    "new_status": "Available"
                })
            else:
                return JsonResponse({
                    "error": f"Room status is {room_unit.status}, cannot complete cleaning"
                }, status=400)
                
        except RoomUnit.DoesNotExist:
            return JsonResponse({"error": "Room not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)
@csrf_exempt
def add_inventory(request):
    if request.method == "POST":
        try:
            staff = Staff.objects.get(id=request.session.get("staff_id"))
            hotel = staff.hotel
            
            name = request.POST.get("name")
            category = request.POST.get("category")
            quantity = int(request.POST.get("quantity", 0))
            unit = request.POST.get("unit", "pieces")
            reorder_level = int(request.POST.get("reorder_level", 10))
            description = request.POST.get("description", "")
            room_id = request.POST.get("room_id")
            
            if not name:
                return JsonResponse({"error": "Item name is required"}, status=400)
            
            if not room_id:
                return JsonResponse({"error": "Please select a room"}, status=400)
            
            room = RoomUnit.objects.get(id=room_id)
            
            inventory_item = InventoryItem.objects.create(
                hotel=hotel,
                room=room,
                name=name,
                category=category,
                quantity=quantity,
                unit=unit,
                reorder_level=reorder_level,
                description=description,
                assigned_by=staff
            )
            
            return JsonResponse({"success": True, "id": inventory_item.id})
        except RoomUnit.DoesNotExist:
            return JsonResponse({"error": "Room not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)
def get_inventory(request):
    try:
        staff = Staff.objects.get(id=request.session.get("staff_id"))
        hotel = staff.hotel

        items = InventoryItem.objects.filter(hotel=hotel).select_related("room")

        data = []
        for item in items:
            data.append({
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "quantity": item.quantity,
                "unit": item.unit,
                "room_number": item.room.room_number, 
                "description": item.description
            })

        return JsonResponse({"items": data})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def update_inventory(request, item_id):
    if request.method == "POST":
        try:
            item = InventoryItem.objects.get(id=item_id)
            
            name = request.POST.get("name")
            category = request.POST.get("category")
            quantity = request.POST.get("quantity")
            unit = request.POST.get("unit")
            reorder_level = request.POST.get("reorder_level")
            description = request.POST.get("description", "")
            room_id = request.POST.get("room_id")
            
            if name:
                item.name = name
            if category:
                item.category = category
            if quantity:
                item.quantity = int(quantity)
            if unit:
                item.unit = unit
            if reorder_level:
                item.reorder_level = int(reorder_level)
            if description is not None:
                item.description = description
            if room_id:
                item.room = RoomUnit.objects.get(id=room_id)
            
            item.save()
            
            return JsonResponse({"success": True})
        except InventoryItem.DoesNotExist:
            return JsonResponse({"error": "Inventory item not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def delete_inventory(request, item_id):
    if request.method == "DELETE":
        try:
            item = InventoryItem.objects.get(id=item_id)
            item.delete()
            return JsonResponse({"success": True})
        except InventoryItem.DoesNotExist:
            return JsonResponse({"error": "Inventory item not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)

def hr_dashboard(request):
    staff_id = request.session.get("staff_id")

    if not staff_id:
        return redirect("staff_login")

    staff = Staff.objects.select_related("hotel").get(id=staff_id)
    hotel = staff.hotel

    employees = Staff.objects.filter(hotel=hotel).select_related("department")

    total_staff = employees.count()
    total_departments = Department.objects.filter(hotel=hotel).count()

    tasks = Task.objects.filter(staff__hotel=hotel)
    shifts = Shift.objects.filter(hotel=hotel).select_related("staff", "department")

   
    payroll_data = []
    for emp in employees:
        salary = getattr(emp, "salary", 0)
        bonus = getattr(emp, "bonus", 0)
        deduction = getattr(emp, "deduction", 0)

        payroll_data.append({
            "name": emp.name,
            "role": emp.role,
            "salary": salary,
            "bonus": bonus,
            "deduction": deduction,
            "net": salary + bonus - deduction
        })

    return render(request, "hr.html", {
        "staff": staff,
        "hotel": hotel,
        "employees": employees,
        "total_staff": total_staff,
        "total_departments": total_departments,
        "tasks": tasks,
        "shifts": shifts,
        "payroll": payroll_data
    })

def accountant_dashboard(request):
    return render(request, "accountant.html")
#----------------------FRONTDESK MODULE----------------------

def frontoffice_dashboard(request):
    staff_id = request.session.get("staff_id")
    if not staff_id:
        return redirect("staff_login")

    staff = Staff.objects.select_related("hotel").get(id=staff_id)
    hotel = staff.hotel

    
    rooms = Room.objects.filter(hotel=hotel)
    room_list = []
    for room in rooms:
        total_units = room.units.count()
        available_units = room.units.filter(status="Available").count()
        
        room_list.append({
            "room_type": room.room_type,
            "total_rooms": total_units,
            "available_rooms": available_units,
            "price": room.price,
            "id": room.id,
            "description": room.description or ""
        })

    housekeeping_staff = Staff.objects.filter(
        hotel=hotel,
        department__name__icontains="housekeeping",
        is_available=True,
    ).select_related("department")

    today = timezone.now().date()

    total_bookings = Booking.objects.filter(hotel=hotel).count()

    arrivals = Booking.objects.filter(
        hotel=hotel,
        check_in=today,
        status="confirmed"
    ).select_related('guest', 'room', 'room_unit')

    departures = Booking.objects.filter(
        hotel=hotel,
        check_out=today,
        status="checked_in"
    ).select_related('guest', 'room', 'room_unit')

    occupied_rooms = Booking.objects.filter(
        hotel=hotel,
        status="checked_in"
    ).count()

    #
    bookings = Booking.objects.filter(hotel=hotel).select_related(
        'guest', 'room', 'room_unit'
    ).order_by('-created_at')
    
    recent_bookings = bookings[:5]
    
    
    recent_tasks = Task.objects.filter(
        staff__hotel=hotel
    ).select_related('staff', 'room_unit', 'room').order_by("-created_at")[:5]

    
    recent_activity = list(recent_bookings) + list(recent_tasks)
    recent_activity = sorted(
        recent_activity,
        key=lambda x: x.created_at,
        reverse=True
    )[:10]

    
    room_units = RoomUnit.objects.filter(room__hotel=hotel).select_related('room')

    return render(request, "frontoffice.html", {
        "rooms": room_list,
        "staff": staff,
        "hotel": hotel,
        "housekeeping_staff": housekeeping_staff,
        "total_bookings": total_bookings,
        "occupied_rooms": occupied_rooms,
        "arrivals_count": arrivals.count(),
        "departures_count": departures.count(),
        "arrivals": arrivals,
        "departures": departures,
        "bookings": bookings,
        "recent_activity": recent_activity,
        "recent_tasks": recent_tasks,
        "room_units": room_units,
    })
@csrf_exempt
def create_booking(request):
    if request.method == "POST":
        try:
            staff = Staff.objects.get(id=request.session.get("staff_id"))
            hotel = staff.hotel

            name = request.POST.get("name")
            phone = request.POST.get("phone")
            room_type = request.POST.get("room_type")
            check_in = request.POST.get("check_in")
            check_out = request.POST.get("check_out")
            guests = request.POST.get("guests")
            requests_text = request.POST.get("requests")

            id_photo = request.FILES.get("id_photo")

            # Get or create guest
            guest, created = Guest.objects.get_or_create(
                phone=phone,
                hotel=hotel,
                defaults={
                    "full_name": name,
                    "email": request.POST.get("email", ""),
                    "nationality": request.POST.get("nationality", ""),
                    "id_photo": id_photo
                }
            )

            if not created and guest.full_name != name:
                guest.full_name = name
                guest.save()

            if id_photo and not guest.id_photo:
                guest.id_photo = id_photo
                guest.save()

            
            try:
                room = Room.objects.get(hotel=hotel, room_type=room_type)
            except Room.DoesNotExist:
                return JsonResponse({"error": f"Room type '{room_type}' not found"}, status=400)
            except Room.MultipleObjectsReturned:
                # If multiple rooms with same type exist, get the first one
                room = Room.objects.filter(hotel=hotel, room_type=room_type).first()
                if not room:
                    return JsonResponse({"error": f"Room type '{room_type}' not found"}, status=400)

            
            unit = RoomUnit.objects.filter(room=room, status="Available").first()

            if not unit:
                return JsonResponse({"error": f"No available rooms for type {room_type}"}, status=400)

            # Calculate nights
            from datetime import datetime
            check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
            check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
            nights = (check_out_date - check_in_date).days
            
            if nights <= 0:
                return JsonResponse({"error": "Check-out must be after check-in"}, status=400)

            unit.status = "Reserved"
            unit.save()

            # Create booking
            booking = Booking.objects.create(
                hotel=hotel,
                guest=guest,
                room=room,
                room_unit=unit,
                check_in=check_in,
                check_out=check_out,
                guests_count=guests or 1,
                special_requests=requests_text or "",
                status="confirmed"
            )

           
            room_charges = float(room.price) * nights
            tax = room_charges * 0.18
            total = room_charges + tax

            Payment.objects.create(
                booking=booking,
                room_charges=room_charges,
                tax=tax,
                total_amount=total
            )

            return JsonResponse({
                "success": True,
                "room_number": unit.room_number,
                "booking_id": booking.id
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)
from django.utils import timezone
@csrf_exempt
def check_in(request):
    if request.method == "POST":
        data = json.loads(request.body)

        booking = Booking.objects.get(id=data["booking_id"], status="confirmed")

        guest = booking.guest
        guest.id_type = data["id_type"]
        guest.id_number = data["id_number"]
        guest.save()

        booking.status = "checked_in"
        booking.actual_check_in = timezone.now()
        booking.save()

        unit = booking.room_unit
        unit.status = "Occupied"
        unit.save()

        room = booking.room
        room.available_rooms -= 1
        room.save()

        return JsonResponse({"success": True})

@csrf_exempt
def check_out(request):
    if request.method == "POST":
        data = json.loads(request.body)

        staff = Staff.objects.get(id=request.session.get("staff_id"))

        booking = Booking.objects.get(id=data["booking_id"], status="checked_in")

        booking.status = "checked_out"
        booking.actual_check_out = timezone.now()
        booking.save()

        unit = booking.room_unit
        unit.status = "Dirty"
        unit.save()

        payment = booking.payment
        payment.payment_method = data["method"]
        payment.payment_status = "paid"
        payment.paid_at = timezone.now()
        payment.collected_by = staff
        payment.save()

        return JsonResponse({"success": True})

@csrf_exempt
def get_bill(request):
    booking_id = request.GET.get("booking_id")
    try:
        booking = Booking.objects.get(id=booking_id)
        payment = booking.payment

        nights = (booking.check_out - booking.check_in).days or 1

        return JsonResponse({
            "room_type": booking.room.room_type,
            "room_number": booking.room_unit.room_number if booking.room_unit else None,
            "check_in": str(booking.check_in),
            "check_out": str(booking.check_out),
            "nights": nights,
            "room_charges": float(payment.room_charges),
            "tax": float(payment.tax),
            "total_amount": float(payment.total_amount),
        })
    except Booking.DoesNotExist:
        return JsonResponse({"error": "Booking not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
@csrf_exempt
def assign_housekeeping_task(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            staff_id = data.get("staff_id")
            room_unit_id = data.get("room_unit_id")
            task_type = data.get("task_type", "General Task")
            priority = data.get("priority", "Normal")
            duration = data.get("duration", "1 hour")
            notes = data.get("notes", "")

            if not staff_id:
                return JsonResponse({"error": "Staff ID is required"}, status=400)

            try:
                staff = Staff.objects.get(id=staff_id)
            except Staff.DoesNotExist:
                return JsonResponse({"error": "Staff not found"}, status=404)

            room_unit = None
            room = None
            
            if room_unit_id:
                try:
                    room_unit = RoomUnit.objects.get(id=room_unit_id)
                    room = room_unit.room  # Get the room from room_unit
                except RoomUnit.DoesNotExist:
                    pass  # Room unit optional

            # Create task with both room and room_unit
            task = Task.objects.create(
                staff=staff,
                room=room,
                room_unit=room_unit,  # Now this field exists
                title=task_type,
                description=f"Priority: {priority} | Duration: {duration} | Notes: {notes}".strip(" | "),
                status="Pending"
            )

            return JsonResponse({
                "success": True,
                "task_id": task.id,
                "message": f"Task '{task_type}' assigned to {staff.name}"
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)