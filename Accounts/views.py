from django.shortcuts import render, redirect
from .models import Hotel,Amenity,Room,Department,Staff,Task
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt

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

    print(f"[DEBUG] {hotel.hotel_name} amenities: {[a.name for a in amenities]}")

    return render(request, "property.html", {
        "hotel": hotel,
        "amenities": amenities
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

        # assuming logged-in hotel (you can change logic)
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
def add_staff(request):
    if request.method == "POST":
        hotel_id = request.session.get("hotel_id")

        Staff.objects.create(
            hotel_id=hotel_id,
            name=request.POST.get("name"),
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            department_id=request.POST.get("department"),
            role=request.POST.get("role"),
            password=request.POST.get("password")
        )

        return redirect("staff_page")
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

    tasks = Task.objects.filter(
        staff__hotel_id=hotel_id
    ).select_related("staff")

    task_list = []
    for t in tasks:
        task_list.append({
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "staff": t.staff.name,
            "status": t.status
        })

    return JsonResponse({
        "tasks": task_list,
        "count": tasks.count()
    })
