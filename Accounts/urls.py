from django.urls import path
from .views import *
urlpatterns =[
    path("", index, name="index"),
     path("register/", hotel_register, name="hotel_register"),
    path("login/", hotel_login, name="hotel_login"),
    path("dashboard/", dashboard, name="dashboard"),
    path('amenities/', amenities_page, name='amenities_page'),
    path('add-amenity/', add_amenity, name='add_amenity'),
      path('get-amenities/',get_amenities, name='get_amenities'),
    path('save-selected-amenities/', save_selected_amenities, name='save_selected_amenities'),
    
    path("rooms/", room_page, name="room_page"),
    path('add-room/', add_room, name='add_room'),
    path('get-room/', get_rooms, name='get_rooms'),        
    path('get-room/<int:room_id>/', get_room, name='get_room'), 
    path("staff/", staff_page, name="staff_page"),
     path("add-department/", add_department, name="add_department"),
    path("add-staff/", add_staff, name="add_staff"),
    path("assign-task/", assign_task, name="assign_task"),
    path("get-tasks/", get_tasks, name="get_tasks"),
    path("get-departments/", get_departments, name="get_departments"),
    path("get-staff/", get_staff, name="get_staff"),
    path("assign-shift/", assign_shift, name="assign_shift"),
    path("update-shift/", update_shift, name="update_shift"),
    path("get-shifts/", get_shifts, name="get_shifts"),
    path("staff-by-shift/", staff_by_shift, name="staff_by_shift"),
    # STAFF LOGIN
    path("staff-login/", staff_login, name="staff_login"),

    # DASHBOARDS
    path("housekeeping/", housekeeping_dashboard, name="housekeeping_dashboard"),
    path("hr/", hr_dashboard, name="hr_dashboard"),
    path("frontoffice/", frontoffice_dashboard, name="frontoffice_dashboard"),
    path("accountant/", accountant_dashboard, name="accountant_dashboard"),
    
]
 
