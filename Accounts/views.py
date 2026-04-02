from django.shortcuts import render, redirect
from .models import Hotel,Amenity,Room,Department,Staff,Task,Shift
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
def room_page(request):
    hotel_id = request.session.get('hotel_id')
    if not hotel_id:
        return redirect("hotel_login")
    
    hotel = Hotel.objects.get(id=hotel_id)
    rooms = Room.objects.filter(hotel=hotel).order_by('room_type')
    
    return render(request, "room.html", {
        "hotel": hotel,
        "rooms": rooms
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

            room = Room.objects.create(
                hotel=hotel,
                room_type=data.get('room_type'),
                price=data.get('price'),
                total_rooms=data.get('total_rooms'),
                
                description=data.get('description', '')
            )

            return JsonResponse({"success": True, "room_id": room.id})

        except Hotel.DoesNotExist:
            return JsonResponse({"error": "Hotel not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)



def get_rooms(request):
    try:
        hotel_id = request.session.get('hotel_id')
        if not hotel_id:
            return JsonResponse({"error": "Not logged in"}, status=401)

        hotel = Hotel.objects.get(id=hotel_id)          # ← get hotel object
        rooms = Room.objects.filter(hotel=hotel)

        room_type = request.GET.get('type', '')
        if room_type:
            rooms = rooms.filter(room_type=room_type)

        room_list = [
            {
                "id": room.id,
                "room_type": room.room_type,
                "price": str(room.price),
                "total_rooms": room.total_rooms,
                "available_rooms": room.available_rooms,
                "description": room.description
            }
            for room in rooms
        ]

        return JsonResponse({
            "rooms": room_list,
            "hotel_name": hotel.hotel_name   # ← add this line only
        })

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
    """Add staff member and return JSON response for AJAX"""
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
        
        # Debug: Print received data
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
            role=role or "Staff",
            password=password or "default123"
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
            "staff_id": t.staff.id,  # CRITICAL: Add this field
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
            "staff_id": s.staff.id,  # ADD THIS - critical for matching
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
def housekeeping_dashboard(request):
    staff_id = request.session.get("staff_id")

    if not staff_id:
        return redirect("staff_login")

    staff = Staff.objects.select_related("hotel").get(id=staff_id)
    tasks=Task.objects.filter(staff_id=staff_id)
    shift=Shift.objects.filter(staff_id=staff_id).select_related("department").first()


    return render(request, "housekeeping.html", {
        "staff": staff,
        "hotel": staff.hotel,
        "tasks": tasks,      
        "shift": shift 
    })

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
def frontoffice_dashboard(request):
    staff_id = request.session.get("staff_id")
    if not staff_id:
        return redirect("staff_login")

    staff = Staff.objects.select_related("hotel").get(id=staff_id)
    
    
    rooms = Room.objects.filter(hotel=staff.hotel)
    
    

    return render(request, "frontoffice.html", {
        "rooms": rooms,
        "staff": staff,
        "hotel": staff.hotel,
        
    })
def accountant_dashboard(request):
    return render(request, "accountant.html")

