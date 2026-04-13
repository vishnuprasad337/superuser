from django.shortcuts import render, redirect
from .models import Hotel,Amenity,Room,Department,Staff,Task,Shift,Guest,Booking,Payment,RoomUnit,InventoryItem,Attendance,LeaveRequest,Payroll
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate ,login
from django.contrib.auth.decorators import login_required
import json
from django.contrib.auth.models import User

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from datetime import timedelta
from django.db.models import Count, Sum, Q
from django.shortcuts import get_object_or_404
def index(request):
    return render(request, "index.html")
##----------------------Superadmin Authentication----------------------

def admin_login(request): 
    error = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_superuser:
                login(request, user)
                return redirect("superuser_dashboard")
            else:
                error = "Not authorized as admin"
        else:
            error = "Invalid credentials"

    return render(request, "admin/login.html", {"error": error})




@login_required
def superuser_dashboard(request):
    if not request.user.is_superuser:
        return redirect("admin_login")

    
    hotels = Hotel.objects.all().order_by('-id')

    total_hotels = hotels.count()
    active_hotels = hotels.filter(is_approved=True).count()
    pending_hotels = hotels.filter(is_approved=False).count()

    pending_hotel_list = hotels.filter(is_approved=False)

    
    amenities = Amenity.objects.all()

    context = {
        "hotels": hotels,
        "total_hotels": total_hotels,
        "active_hotels": active_hotels,
        "pending_hotels": pending_hotels,
        "pending_hotel_list": pending_hotel_list,
        "amenities": amenities,
    }

    return render(request, "admin/dashboard.html", context)
@login_required
def approve_hotel(request, id):
    if not request.user.is_superuser:
        return redirect("admin_login")

    hotel = get_object_or_404(Hotel, id=id)
    hotel.is_approved = True
    hotel.save()

    return redirect("superuser_dashboard")


@login_required
def reject_hotel(request, id):
    if not request.user.is_superuser:
        return redirect("admin_login")

    hotel = get_object_or_404(Hotel, id=id)
    hotel.delete()
def save_hotel_modules(request, hotel_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            module_names = data.get("modules", [])

            hotel = Hotel.objects.get(id=hotel_id)
            amenities = Amenity.objects.filter(name__in=module_names)

            hotel.properties.set(amenities)  

            return JsonResponse({"success": True})

        except Hotel.DoesNotExist:
            return JsonResponse({"error": "Hotel not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)

##----------------------Hotel Authentication----------------------
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

            hotel= Hotel.objects.create(
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





@require_POST
def add_amenity(request):
    try:
        data = json.loads(request.body)

        name = data.get("name")
        description = data.get("description", "")
        amenity_type = data.get("amenity_type", "default")

        
        if not name:
            return JsonResponse({"error": "Name is required"}, status=400)

        if amenity_type not in ["default", "premium"]:
            return JsonResponse({"error": "Invalid amenity_type"}, status=400)

        
        amenity, created = Amenity.objects.get_or_create(
            name=name,
            defaults={
                "description": description,
                "amenity_type": amenity_type
            }
        )

        if not created:
            amenity.description = description
            amenity.amenity_type = amenity_type
            amenity.save()

        return JsonResponse({
            "id": amenity.id,
            "name": amenity.name,
            "description": amenity.description,
            "amenity_type": amenity.amenity_type,
            "created": created
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
def get_amenities(request):
    try:
        default_amenities = Amenity.objects.filter(
            amenity_type="default"
        ).values("id", "name", "description")

        premium_amenities = Amenity.objects.filter(
            amenity_type="premium"
        ).values("id", "name", "description")

        return JsonResponse({
            "default": list(default_amenities),
            "premium": list(premium_amenities)
        }, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_http_methods(["DELETE"])
def delete_amenity(request, amenity_id):
    try:
        amenity = get_object_or_404(Amenity, id=amenity_id)

        amenity.delete()

        return JsonResponse({
            "message": "Amenity deleted successfully",
            "id": amenity_id
        }, status=200)

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

    
    total_bookings = Booking.objects.filter(hotel=hotel).count()

    reserved_count = Booking.objects.filter(
        hotel=hotel,
        status="confirmed"  
    ).count()

    today = timezone.now().date()

   
    today_checkins = Booking.objects.filter(
        hotel=hotel,
        check_in=today,
        status="confirmed"
    ).count()

    
    today_checkouts = Booking.objects.filter(
        hotel=hotel,
        check_out=today,
        status="checked_in"
    ).count()

    
    occupied_rooms = Booking.objects.filter(
        hotel=hotel,
        status="checked_in"
    ).count()

    print(f"[DEBUG] {hotel.hotel_name} amenities: {[a.name for a in amenities]}")

    return render(request, "property.html", {
        "hotel": hotel,
        "amenities": amenities,
        "total_rooms": total_rooms,
        "total_staff": total_staff,

        
        "total_bookings": total_bookings,
        "reserved_count": reserved_count,
        "today_checkins": today_checkins,
        "today_checkouts": today_checkouts,
        "occupied_rooms": occupied_rooms,
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
           
            room_units = room.units.all().order_by('room_number')
            
            total_units = room_units.count()
            available_units = room_units.filter(status="Available").count()
            
           
            units_list = []
            for unit in room_units:
               
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
    if not hotel_id:
        return redirect("hotel_login")

    hotel = get_object_or_404(Hotel, id=hotel_id)
    today = timezone.now().date()
    now_dt = timezone.now()

    section = request.GET.get("section", "dashboard")
    filter_type = request.GET.get("filter", "today")
    sel_date_str = request.GET.get("date", str(today))
    sel_dept_id = request.GET.get("department")
    sel_shift = request.GET.get("shift")

    try:
        report_date = datetime.strptime(sel_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        report_date = today

    if filter_type == "week":
        start_date = today - timedelta(days=7)
    elif filter_type == "month":
        start_date = today.replace(day=1)
    else:
        start_date = today

    departments = Department.objects.filter(hotel=hotel)
    staff_members = Staff.objects.filter(hotel=hotel).select_related("department")
    total_staff = staff_members.count()

    if sel_dept_id:
        staff_members = staff_members.filter(department_id=sel_dept_id)

    today_attendance = Attendance.objects.filter(
        hotel=hotel,
        date=today
    ).select_related("staff", "staff__department")

    present_count = today_attendance.filter(
        status__in=["Present", "Late", "Half Day"]
    ).count()

    late_count = today_attendance.filter(status="Late").count()
    half_day_count = today_attendance.filter(status="Half Day").count()
    absent_count = total_staff - present_count

    attendance_records = []

    for att in today_attendance:
        check_in = att.check_in
        check_out = att.check_out

        hours = 0
        overtime = 0

        if check_in and check_out:
            diff = check_out - check_in
            hours = round(diff.total_seconds() / 3600, 2)
            overtime = round(max(hours - 8, 0), 2)

        attendance_records.append({
            "staff_name": att.staff.name,
            "date": att.date,
            "check_in": check_in,
            "check_out": check_out,
            "hours": hours,
            "overtime": overtime,
            "status": att.status
        })

    daily_attendance = Attendance.objects.filter(
        hotel=hotel,
        date=report_date
    ).select_related("staff", "staff__department").order_by("staff__name")

    if sel_dept_id:
        daily_attendance = daily_attendance.filter(
            staff__department_id=sel_dept_id
        )

    monthly_summary = Attendance.objects.filter(
        hotel=hotel,
        date__month=today.month,
        date__year=today.year
    ).values(
        "staff__id",
        "staff__name",
        "staff__department__name"
    ).annotate(
        present=Count("id", filter=Q(status="Present")),
        late=Count("id", filter=Q(status="Late")),
        half_day=Count("id", filter=Q(status="Half Day")),
        absent=Count("id", filter=Q(status="Absent")),
        overtime=Sum("overtime_hours")
    ).order_by("staff__name")

    total_overtime = Attendance.objects.filter(
        hotel=hotel,
        date__month=today.month,
        date__year=today.year
    ).aggregate(total=Sum("overtime_hours"))["total"] or 0

    shift_assignments = Shift.objects.filter(
        hotel=hotel,
        date__gte=start_date
    ).select_related("staff", "department").order_by("date", "shift")

    if sel_shift:
        shift_assignments = shift_assignments.filter(shift=sel_shift)

    today_shifts = Shift.objects.filter(
        hotel=hotel,
        date=today
    ).select_related("staff", "department")

    morning_count = today_shifts.filter(shift="Morning").count()
    evening_count = today_shifts.filter(shift="Evening").count()
    night_count = today_shifts.filter(shift="Night").count()

    leave_requests = LeaveRequest.objects.filter(
        hotel=hotel
    ).select_related("staff", "staff__department").order_by("-applied_at")

    pending_leaves = leave_requests.filter(status="Pending").count()

    approved_leaves = leave_requests.filter(
        status="Approved",
        from_date__lte=today,
        to_date__gte=today
    ).count()

    payrolls = Payroll.objects.filter(
        hotel=hotel,
        month=today.month,
        year=today.year
    ).select_related("staff")

    payroll_paid = payrolls.filter(paid_status=True).count()
    payroll_unpaid = payrolls.filter(paid_status=False).count()

    total_payroll = payrolls.aggregate(
        total=Sum("net_salary")
    )["total"] or 0

    tasks = Task.objects.filter(
        staff__hotel=hotel,
        created_at__date__gte=start_date
    ).select_related("staff", "room_unit", "room").order_by("-created_at")

    pending_tasks = tasks.filter(status="Pending").count()
    completed_tasks = tasks.filter(status="Completed").count()

    bookings = Booking.objects.filter(
        hotel=hotel,
        created_at__date__gte=start_date
    ).select_related("guest", "room").order_by("-created_at")

    total_bookings = bookings.count()
    checked_in = bookings.filter(status="checked_in").count()
    checked_out = bookings.filter(status="checked_out").count()
    confirmed = bookings.filter(status="confirmed").count()

    revenue = Payment.objects.filter(
        booking__hotel=hotel,
        booking__created_at__date__gte=start_date
    ).aggregate(total=Sum("total_amount"))["total"] or 0

    inventory = InventoryItem.objects.filter(hotel=hotel).order_by("-id")

    dept_breakdown = departments.annotate(
        staff_count=Count("staff")
    ).values("id", "name", "staff_count")

    context = {
        "hotel": hotel,
        "today": today,
        "section": section,
        "filter": filter_type,
        "report_date": report_date,
        "sel_dept_id": sel_dept_id,
        "sel_shift": sel_shift,

        "departments": departments,
        "dept_breakdown": dept_breakdown,
        "staff_members": staff_members,
        "total_staff": total_staff,

        "present_count": present_count,
        "late_count": late_count,
        "half_day_count": half_day_count,
        "absent_count": absent_count,

        "attendance_records": attendance_records,

        "daily_attendance": daily_attendance,
        "monthly_summary": monthly_summary,

        "shift_assignments": shift_assignments,
        "today_shifts": today_shifts,
        "morning_count": morning_count,
        "evening_count": evening_count,
        "night_count": night_count,

        "leave_requests": leave_requests,
        "pending_leaves": pending_leaves,
        "approved_leaves": approved_leaves,

        "payrolls": payrolls,
        "payroll_paid": payroll_paid,
        "payroll_unpaid": payroll_unpaid,
        "total_payroll": total_payroll,

        "tasks": tasks[:10],
        "pending_tasks": pending_tasks,
        "completed_tasks": completed_tasks,

        "bookings": bookings[:10],
        "total_bookings": total_bookings,
        "checked_in": checked_in,
        "checked_out": checked_out,
        "confirmed": confirmed,
        "revenue": revenue,

        "inventory": inventory
    }

    return render(request, "staff.html", context)
def get_bookings(request):
    hotel_id = request.session.get("hotel_id")

    if not hotel_id:
        return JsonResponse({"error": "Not logged in"}, status=401)

    bookings = Booking.objects.filter(
        hotel_id=hotel_id
    ).select_related(
        "guest", "room", "room_unit", "created_by"  
    ).order_by("-created_at")

    data = [
        {
            "id": b.id,
            "guest": b.guest.full_name if b.guest else "N/A",
            "phone": b.guest.phone if b.guest else "",
            "room_type": b.room.room_type if b.room else "N/A",
            "room_no": b.room_unit.room_number if b.room_unit else "N/A",
            "check_in": str(b.check_in),
            "check_out": str(b.check_out),
            "status": b.status,
            "staff": b.created_by.name if b.created_by else "N/A",  
            "total": float(b.payment.total_amount) if getattr(b, "payment", None) and b.payment.total_amount is not None else 0,
        }
        for b in bookings
    ]

    return JsonResponse(data, safe=False)
def gets_inventory(request):
    staff_id = request.session.get("staff_id")

    if not staff_id:
        return JsonResponse({"error": "Not logged in"}, status=401)

    staff = Staff.objects.get(id=staff_id)
    hotel = staff.hotel

    items = InventoryItem.objects.filter(
        hotel=hotel
    ).select_related(
        "room", "updated_by", "assigned_by"   
    ).order_by("-updated_at")

    data = [
        {
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "quantity": item.quantity,
            "unit": item.unit,
            "room_number": item.room.room_number if item.room else "N/A",

            "updated_by": item.updated_by.name if item.updated_by else "N/A",
            "assigned_by": item.assigned_by.name if item.assigned_by else "N/A",

            "description": item.description,
        }
        for item in items
    ]

    return JsonResponse(data, safe=False)
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
@csrf_exempt
def get_staff(request):
    try:
        hotel_id = request.session.get("hotel_id")

        if not hotel_id:
            return JsonResponse({"error": "Login required"}, status=400)

        staffs = Staff.objects.filter(hotel_id=hotel_id).select_related('department')

        staff_list = []

        for s in staffs:
            staff_list.append({
                "id": s.id,
                "employee_id": s.employee_id,  
                "name": s.name,
                "email": s.email if s.email else "-",
                "phone": s.phone if s.phone else "",
                
                "department_name": s.department.name if s.department else "N/A",
                "role": s.role if s.role else "Staff",
                "salary": str(s.salary),  
                "photo": s.photo.url if s.photo else None,  
                "joining_date": s.joining_date, 
               
            })

        return JsonResponse({
            "success": True,
            "count": len(staff_list),
            "staffs": staff_list
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
@csrf_exempt
@require_http_methods(["POST"])
def add_staff(request):
    
    try:
        hotel_id = request.session.get("hotel_id")
        
        
        print(f"Hotel ID from session: {hotel_id}")
        
        if not hotel_id:
            return JsonResponse({
                "error": "Hotel not found in session. Please login first."
            }, status=400)
        
        
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        department = request.POST.get("department")
        role = request.POST.get("role")
        password = request.POST.get("password")
        salary = request.POST.get("salary", 0)
        photo = request.FILES.get("photo")
        
        
        print(f"Adding staff - Name: {name}, Department: {department}, Role: {role}")
        
       
        if not name:
            return JsonResponse({"error": "Staff name is required"}, status=400)
        if not department:
            return JsonResponse({"error": "Department is required"}, status=400)
        
        user = User.objects.create_user(
        username=email,
    email=email,
    password=password
)

        staff = Staff.objects.create(
    hotel_id=hotel_id,
    name=name,
    email=email or "",
    phone=phone or "",
    department_id=department,
    role=role,
    password=make_password(password),  
    salary=salary,
    photo=photo
)
        
        print(f"Staff created successfully with ID: {staff.id}")
        
        return JsonResponse({
            "success": True,
            "id": staff.id,
            "name": staff.name,
            "email": staff.email,
            "phone": staff.phone,
            "role": staff.role,
            "department": staff.department.name if staff.department else "N/A",
            "department_id": staff.department.id if staff.department else None,
            "salary": str(staff.salary),
            "photo": staff.photo.url if staff.photo else None,
            "joining_date": staff.joining_date,
            
            "message": f"Staff '{name}' added successfully"
        }, status=200)
        
    except Exception as e:
       
        print(f"Error adding staff: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
def delete_staff(request):
    try:
        staff_id = request.POST.get("staff_id")
        hotel_id = request.session.get("hotel_id")

        if not hotel_id:
            return JsonResponse({"error": "Login required"}, status=401)

        if not staff_id:
            return JsonResponse({"error": "Staff ID required"}, status=400)

        staff = get_object_or_404(Staff, id=staff_id, hotel_id=hotel_id)

        staff.delete()

        return JsonResponse({
            "success": True,
            "message": "Employee deleted successfully"
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
@require_POST
def update_staff(request):
    try:
        staff_id = request.POST.get("staff_id")
        hotel_id = request.session.get("hotel_id")

        if not hotel_id:
            return JsonResponse({"error": "Login required"}, status=401)

        if not staff_id:
            return JsonResponse({"error": "Staff ID required"}, status=400)

        staff = get_object_or_404(Staff, id=staff_id, hotel_id=hotel_id)

        # Get updated values
        staff.name = request.POST.get("name", staff.name)
        staff.email = request.POST.get("email", staff.email)
        staff.phone = request.POST.get("phone", staff.phone)
        staff.role = request.POST.get("role", staff.role)
        staff.salary = request.POST.get("salary", staff.salary)

        department = request.POST.get("department")
        if department:
            staff.department_id = department

        
        if request.FILES.get("photo"):
            staff.photo = request.FILES.get("photo")

        staff.save()

        return JsonResponse({
            "success": True,
            "message": "Employee updated successfully",
            "staff": {
                "id": staff.id,
                "name": staff.name,
                "email": staff.email,
                "phone": staff.phone,
                "role": staff.role,
                "salary": str(staff.salary),
                "department": staff.department.name if staff.department else "N/A",
                "department_id": staff.department.id if staff.department else None,
                "photo": staff.photo.url if staff.photo else None,
            }
        })

    except Exception as e:
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
    date = request.GET.get("date") 

    shifts = Shift.objects.filter(hotel_id=hotel_id)

    if date:
        shifts = shifts.filter(date=date)

    shifts = shifts.select_related("staff", "department")

    data = [{
        "id": s.id,
        "staff": s.staff.name,
        "staff_id": s.staff.id,
        "department": s.department.name,
        "shift": s.shift,
        "date": s.date.strftime("%Y-%m-%d")
    } for s in shifts]

    return JsonResponse(data, safe=False)
from datetime import datetime


@require_POST
def assign_shift(request):
    try:
        hotel_id = request.session.get("hotel_id")
        staff_id = request.POST.get("staff")
        department_id = request.POST.get("department")
        shift_value = request.POST.get("shift")
        date = request.POST.get("date")

       
        if not hotel_id:
            return JsonResponse({"error": "Login required"}, status=401)

        if not all([staff_id, shift_value, date]):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        date_obj = datetime.strptime(date, "%Y-%m-%d").date()

       
        if not department_id:
            staff = get_object_or_404(Staff, id=staff_id)
            department_id = staff.department_id

        
        if not department_id:
            return JsonResponse({"error": "Department is required"}, status=400)

        shift_obj, created = Shift.objects.update_or_create(
            hotel_id=hotel_id,
            staff_id=staff_id,
            date=date_obj,
            defaults={
                "department_id": department_id,
                "shift": shift_value
            }
        )

        return JsonResponse({
            "success": True,
            "message": "Shift assigned" if created else "Shift updated"
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
def weekly_schedule(request):
    staff_id = request.session.get("staff_id")   
    start_date = request.GET.get("start_date")

    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = start_date + timedelta(days=6)

    shifts = Shift.objects.filter(
        staff_id=staff_id,                       
        date__range=[start_date, end_date]
    ).select_related("staff", "department")

    data = {}
    for s in shifts:
        day = s.date.strftime("%Y-%m-%d")
        if day not in data:
            data[day] = []
        data[day].append({
            "staff": s.staff.name,
            "shift": s.shift,
            "department": s.department.name
        })

    return JsonResponse(data)
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
    date = request.GET.get("date")

    staff = Shift.objects.filter(
        hotel_id=hotel_id,
        shift=shift,
        date=date
    ).select_related("staff")

    data = [{
        "name": s.staff.name,
        "role": s.staff.role
    } for s in staff]

    return JsonResponse(data, safe=False)
#----------------------STAFF MODULE----------------------
from django.contrib.auth.hashers import check_password, make_password

def staff_login(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        if not email or not password:
            return render(request, "staff_login.html", {
                "error": "Please enter email and password"
            })

        staff = Staff.objects.filter(email=email)\
            .select_related("department", "hotel")\
            .first()

        if not staff:
            return render(request, "staff_login.html", {
                "error": "Invalid email or password"
            })

       
        user = authenticate(request, username=email, password=password)

        if user:
            login(request, user)

        else:
            
            
            if staff.password == password:
                staff.password = make_password(password)  
                staff.save()

           
            elif not check_password(password, staff.password):
                return render(request, "staff_login.html", {
                    "error": "Invalid email or password"
                })

           
            user, created = User.objects.get_or_create(
                username=email,
                defaults={"email": email}
            )

            user.set_password(password)
            user.save()

           
            login(request, user)

       
        request.session["staff_id"] = staff.id
        request.session["department"] = staff.department.name.lower()
        request.session["hotel_id"] = staff.hotel.id   

        dept = staff.department.name.lower()

        if dept == "housekeeping":
            return redirect("housekeeping_dashboard")
        elif dept == "hr":
            return redirect("hr_dashboard")
        elif dept in ["front desk", "front office"]:
            return redirect("frontoffice_dashboard")
        elif dept == "accountant":
            return redirect("accountant_dashboard")

        return redirect("staff_dashboard")

    return render(request, "staff_login.html")
@require_POST
def update_staff_profile(request):
    try:
        staff_id = request.session.get("staff_id")  

        if not staff_id:
            return JsonResponse({"error": "Login required"}, status=401)

        staff = get_object_or_404(Staff, id=staff_id)

        
        staff.name  = request.POST.get("name", staff.name)
        staff.email = request.POST.get("email", staff.email)
        staff.phone = request.POST.get("phone", staff.phone)

        
        current_password = request.POST.get("current_password")
        new_password     = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password:
            if staff.password != current_password:
                return JsonResponse({"error": "Current password is incorrect"}, status=400)
            if new_password != confirm_password:
                return JsonResponse({"error": "New passwords do not match"}, status=400)
            staff.password = new_password

        
        if request.FILES.get("photo"):
            staff.photo = request.FILES["photo"]

        staff.save()

        return JsonResponse({
            "success": True,
            "name":  staff.name,
            "email": staff.email,
            "photo": staff.photo.url if staff.photo else None,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
#----------------------HOUSEKEEPING MODULE----------------------
from django.shortcuts import render, redirect
from django.utils import timezone

def housekeeping_dashboard(request):
    staff_id = request.session.get("staff_id")

    if not staff_id:
        return redirect("staff_login")

    staff = Staff.objects.select_related("hotel").get(id=staff_id)
    hotel = staff.hotel

    
    
    all_tasks = Task.objects.filter(staff_id=staff_id).select_related("room_unit").order_by('-created_at')

    
    
    for task in all_tasks:
        if task.room_unit and task.room_unit.status == "Available" and task.status != "Completed":
            task.status = "Completed"
            task.save()

   
   
    tasks = Task.objects.filter(
        staff_id=staff_id,
        status="Pending"
    ).select_related("room_unit")

   
    today = timezone.now().date()

    shift = Shift.objects.filter(
        staff_id=staff_id,
    date=today
).select_related("department").first()

   
    room_units = RoomUnit.objects.filter(
        task__staff_id=staff_id,
        task__status="Pending"
    ).distinct().select_related('room')

    
    all_assigned_rooms = RoomUnit.objects.filter(
        task__staff_id=staff_id
    ).distinct()

   
    clean_count = all_assigned_rooms.filter(status="Available").count()
    dirty_count = all_assigned_rooms.filter(status="Dirty").count()
    maintenance_count = all_assigned_rooms.filter(status="Maintenance").count()
    cleaning_count = all_assigned_rooms.filter(status="Cleaning").count()

    
    rooms_list = []
    for unit in room_units:
        rooms_list.append({
            "number": unit.room_number,
            "status": unit.status.lower(),
            "room_type": unit.room.room_type,
            "id": unit.id,
            "notes": ""
        })

   
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
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        
        hotel_id = request.session.get("hotel_id")
        staff_id = request.session.get("staff_id")

        if not hotel_id:
            return JsonResponse({"error": "Hotel not found in session"}, status=400)

       
        item = get_object_or_404(InventoryItem, id=item_id, hotel_id=hotel_id)

       
        staff = None
        if staff_id:
            staff = Staff.objects.filter(id=staff_id, hotel_id=hotel_id).first()

       
        name = request.POST.get("name")
        category = request.POST.get("category")
        quantity = request.POST.get("quantity")
        unit = request.POST.get("unit")
        reorder_level = request.POST.get("reorder_level")
        description = request.POST.get("description")
        room_id = request.POST.get("room_id")

        
        if name:
            item.name = name

        if category:
            item.category = category

        if quantity:
            try:
                item.quantity = int(quantity)
            except ValueError:
                return JsonResponse({"error": "Invalid quantity"}, status=400)

        if unit:
            item.unit = unit

        if reorder_level:
            try:
                item.reorder_level = int(reorder_level)
            except ValueError:
                return JsonResponse({"error": "Invalid reorder level"}, status=400)

        if description is not None:
            item.description = description

        if room_id:
            room = RoomUnit.objects.filter(id=room_id, hotel_id=hotel_id).first()
            if not room:
                return JsonResponse({"error": "Invalid room"}, status=400)
            item.room = room

        
        if staff:
            item.updated_by = staff

        item.save()

        return JsonResponse({
            "success": True,
            "message": "Inventory updated successfully"
        })

    except Exception as e:
        return JsonResponse({
            "error": str(e)
        }, status=500)
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
from datetime import time

SHIFT_TIMINGS = {
    "Morning": (time(9, 0), time(17, 0)),
    "Evening": (time(14, 0), time(22, 0)),
    "Night": (time(22, 0), time(6, 0)),
}

@require_POST
def mark_attendance(request):
    staff_id = request.session.get("staff_id")

    if not staff_id:
        return JsonResponse({"error": "Login required"}, status=401)

    try:
        staff = Staff.objects.get(id=staff_id)
    except Staff.DoesNotExist:
        return JsonResponse({"error": "Staff not found"}, status=404)

    now = timezone.now()
    today = now.date()

    attendance, created = Attendance.objects.get_or_create(
        staff=staff,
        hotel=staff.hotel,
        date=today
    )

   
    shift_obj = Shift.objects.filter(staff=staff, date=today).first()
    shift_name = shift_obj.shift if shift_obj else None

    shift_start, shift_end = None, None

    if shift_name in SHIFT_TIMINGS:
        shift_start, shift_end = SHIFT_TIMINGS[shift_name]

   
    if not attendance.check_in:
        attendance.check_in = now

        if shift_start and now.time() > shift_start:
            attendance.status = "Late"
        else:
            attendance.status = "Present"

        attendance.save()

        return JsonResponse({
            "success": True,
            "type": "checkin",
            "shift": shift_name,
            "check_in": attendance.check_in.isoformat(),
            "status": attendance.status
        })

    elif not attendance.check_out:
        attendance.check_out = now

        working_hours = (attendance.check_out - attendance.check_in).total_seconds() / 3600

        overtime = 0

      
        if shift_start and shift_end:
            shift_start_dt = datetime.combine(today, shift_start)
            shift_end_dt = datetime.combine(today, shift_end)

            if shift_end < shift_start:
                shift_end_dt += timedelta(days=1)

           
            if attendance.check_out > shift_end_dt:
                overtime = (attendance.check_out - shift_end_dt).total_seconds() / 3600

        attendance.overtime_hours = round(overtime, 2)

       
        if shift_start and shift_end:
            shift_duration = (shift_end_dt - shift_start_dt).total_seconds() / 3600

            if working_hours < (shift_duration / 2):
                attendance.status = "Half Day"
            elif attendance.status != "Late":
                attendance.status = "Present"

        attendance.save()

        return JsonResponse({
            "success": True,
            "type": "checkout",
            "shift": shift_name,
            "check_out": attendance.check_out.isoformat(),
            "working_hours": round(working_hours, 2),
            "overtime": attendance.overtime_hours,
            "status": attendance.status
        })

    return JsonResponse({
        "success": False,
        "message": "Already checked in and out"
    })


def live_attendance(request):
    hotel_id = request.session.get("hotel_id")

    if not hotel_id:
        return JsonResponse({"error": "Login required"}, status=401)

    today = timezone.now().date()

    records = Attendance.objects.filter(
        hotel_id=hotel_id,
        date=today
    ).select_related("staff").order_by("-check_in")

    data = []
    for r in records:
        if r.check_in and not r.check_out:
            status = "Working"
        elif r.check_in and r.check_out:
            status = "Left"
        else:
            status = "Absent"

        data.append({
            "name": r.staff.name,
            "check_in": r.check_in.isoformat() if r.check_in else None,
            "check_out": r.check_out.isoformat() if r.check_out else None,
            "overtime_hours": float(r.overtime_hours or 0),
            "status": status
        })

    return JsonResponse(data, safe=False)
def daily_report(request):
    hotel_id = request.session.get("hotel_id")
    if not hotel_id:
        return JsonResponse({"error": "Login required"}, status=401)

    date = request.GET.get("date")
    if not date:
        return JsonResponse({"error": "Date parameter required"}, status=400)

   
    shift_staff_ids = Shift.objects.filter(
        hotel_id=hotel_id,
        date=date
    ).values_list("staff_id", flat=True)

    all_staff = Staff.objects.filter(
        hotel_id=hotel_id,
        id__in=shift_staff_ids
    ).select_related("department")

    att_map = {
        a.staff_id: a
        for a in Attendance.objects.filter(hotel_id=hotel_id, date=date)
    }

    data = []
    for s in all_staff:
        a = att_map.get(s.id)
        data.append({
            "name": s.name,
            "department": s.department.name if s.department else "—",
            "date": date,
            "check_in": a.check_in.isoformat() if a and a.check_in else None,
            "check_out": a.check_out.isoformat() if a and a.check_out else None,
            "status": a.status if a else "Absent",
            "overtime": float(a.overtime_hours or 0) if a else 0.0
        })

    return JsonResponse(data, safe=False)
def monthly_report(request):
    hotel_id = request.session.get("hotel_id")

    if not hotel_id:
        return JsonResponse({"error": "Login required"}, status=401)

    today = timezone.now()
    month = today.month
    year = today.year

    records = Attendance.objects.filter(
        hotel_id=hotel_id,
        date__month=month,
        date__year=year
    ).values("staff__name").annotate(
        present=Count("id", filter=Q(status="Present")),
        absent=Count("id", filter=Q(status="Absent")),
        late=Count("id", filter=Q(status="Late")),
        overtime=Sum("overtime_hours")       
    ).order_by("staff__name")

    data = []
    for r in records:
        data.append({
            "staff__name": r["staff__name"],
            "present": r["present"],
            "absent": r["absent"],
            "late": r["late"],
            "overtime": round(float(r["overtime"] or 0), 2)
        })

    return JsonResponse(data, safe=False)
def apply_leave(request):
    if request.method == "POST":
        staff_id = request.session.get("staff_id")

        if not staff_id:
            return JsonResponse({"error": "Unauthorized"}, status=401)

        from_date = request.POST.get("from_date")
        to_date = request.POST.get("to_date")
        reason = request.POST.get("reason")

        if not from_date or not to_date:
            return JsonResponse({"error": "Dates required"}, status=400)

        LeaveRequest.objects.create(
            staff_id=staff_id,
            hotel_id=request.session.get("hotel_id"),
            from_date=datetime.strptime(from_date, "%Y-%m-%d").date(),
            to_date=datetime.strptime(to_date, "%Y-%m-%d").date(),
            reason=reason
        )

        return JsonResponse({"success": True, "message": "Leave applied"})

    return JsonResponse({"error": "Invalid method"}, status=405)
def leave_requests(request):
    hotel_id = request.session.get("hotel_id")

    leaves = LeaveRequest.objects.filter(
        hotel_id=hotel_id
    ).select_related("staff").order_by("-applied_at")

    data = []

    for l in leaves:
        data.append({
            "id": l.id,
            "staff": l.staff.name,
            "from_date": l.from_date,
            "to_date": l.to_date,
            "reason": l.reason,
            "status": l.status
        })

    return JsonResponse(data, safe=False)
def update_leave_status(request, leave_id):
    if request.method == "POST":
        action = request.POST.get("action") 
        staff_id = request.session.get("staff_id")

        try:
            leave = LeaveRequest.objects.get(id=leave_id)

            if action == "approve":
                leave.status = "Approved"
            elif action == "reject":
                leave.status = "Rejected"
            else:
                return JsonResponse({"error": "Invalid action"}, status=400)

            leave.action_by_id = staff_id
            leave.action_at = timezone.now()
            leave.save()

            return JsonResponse({"success": True})

        except LeaveRequest.DoesNotExist:
            return JsonResponse({"error": "Not found"}, status=404)

    return JsonResponse({"error": "Invalid method"}, status=405)
from decimal import Decimal

def calculate_payroll(staff, month, year):
    attendances = Attendance.objects.filter(
        staff=staff,
        date__month=month,
        date__year=year
    )

    total_days = attendances.count()
    absent_days = attendances.filter(status="Absent").count()

    overtime_hours = sum(
        (a.overtime_hours or 0) for a in attendances
    )

    basic_salary = Decimal(staff.salary or 0)

    per_day_salary = basic_salary / Decimal("30")

    deduction = Decimal(absent_days) * per_day_salary

    overtime_amount = Decimal(overtime_hours) * Decimal("100")

    net_salary = basic_salary - deduction + overtime_amount

    return {
        "basic": round(basic_salary, 2),
        "deduction": round(deduction, 2),
        "overtime": round(overtime_amount, 2),
        "net": round(net_salary, 2)
    }
def generate_payroll(request):
    if request.method == "POST":
        hotel_id = request.session.get("hotel_id")
        month = int(request.POST.get("month"))
        year = int(request.POST.get("year"))

        staffs = Staff.objects.filter(hotel_id=hotel_id)

        for staff in staffs:
            data = calculate_payroll(staff, month, year)

            Payroll.objects.update_or_create(
                staff=staff,
                hotel_id=hotel_id,
                month=month,
                year=year,
                defaults={
                    "basic_salary": data["basic"],
                    "overtime_amount": data["overtime"],
                    "deductions": data["deduction"],
                    "net_salary": data["net"]
                }
            )

        return JsonResponse({"success": True, "message": "Payroll generated"})
def payroll_dashboard(request):
    hotel_id = request.session.get("hotel_id")
    
    if not hotel_id:
        return JsonResponse({"error": "Login required"}, status=401)
    
    payrolls = Payroll.objects.filter(hotel_id=hotel_id).select_related("staff")
    
    data = []
    for p in payrolls:
        data.append({
            "id": p.id,  # ← ADD THIS LINE - it's missing!
            "staff": p.staff.name,
            "staff_id": p.staff.id,
            "month": p.month,
            "year": p.year,
            "basic_salary": str(p.basic_salary),
            "overtime_amount": str(p.overtime_amount),
            "deductions": str(p.deductions),
            "net_salary": str(p.net_salary),
            "paid_status": p.paid_status,
            "paid": p.paid_status == "Paid"
        })
    
    return JsonResponse(data, safe=False)
def payslip(request, payroll_id):
    try:
        p = Payroll.objects.select_related("staff").get(id=payroll_id)
        
        data = {
            "id": p.id,
            "staff": p.staff.name,
            "employee_id": p.staff.employee_id if p.staff.employee_id else f"EMP{p.staff.id}",
            "month": p.month,
            "year": p.year,
            "basic_salary": float(p.basic_salary),
            "overtime": float(p.overtime_amount),
            "deductions": float(p.deductions),
            "net_salary": float(p.net_salary),
            "paid_status": p.paid_status
        }
        return JsonResponse(data)
    except Payroll.DoesNotExist:
        return JsonResponse({"error": "Payslip not found"}, status=404)
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
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import BookingSerializer



@api_view(["POST"])
def create_booking(request):
    try:
        staff_id = request.session.get("staff_id")

        if not staff_id:
            return Response({"error": "Staff not logged in"}, status=401)

        staff = Staff.objects.get(id=staff_id)

        serializer = BookingSerializer(
            data=request.data,
            context={"request": request, "staff": staff}
        )

        if serializer.is_valid():
            booking = serializer.save()

            return Response({
                "success": True,
                "booking_id": booking.id,
                "room_number": booking.room_unit.room_number
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)
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

