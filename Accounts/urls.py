from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views
urlpatterns =[
    # ADMIN
    path("superadmin/", admin_login, name="admin_login"),
    path("superadmin/dashboard/", superuser_dashboard, name="superuser_dashboard"),
    path("approve-hotel/<int:id>/", approve_hotel, name="approve_hotel"),
    path("reject-hotel/<int:id>/", reject_hotel, name="reject_hotel"),
    path('save-hotel-modules/<int:hotel_id>/',save_hotel_modules, name='save_hotel_modules'),

    

    path("", index, name="index"),
     path("register/", hotel_register, name="hotel_register"),
    path("login/", hotel_login, name="hotel_login"),
    path("dashboard/", dashboard, name="dashboard"),
    path('amenities/', amenities_page, name='amenities_page'),
    path('add-amenity/', add_amenity, name='add_amenity'),
      path('get-amenities/',get_amenities, name='get_amenities'),
      path("delete-amenity/<int:amenity_id>/", delete_amenity, name="delete_amenity"),
    path('save-selected-amenities/', save_selected_amenities, name='save_selected_amenities'),
    
    path("rooms/", room_page, name="room_page"),
    path('add-room/', add_room, name='add_room'),
    path('get-room/', get_rooms, name='get_rooms'),        
    path('get-room/<int:room_id>/', get_room, name='get_room'), 
    path("staff/", staff_page, name="staff_page"),
     path("add-department/", add_department, name="add_department"),
    path("add-staff/", add_staff, name="add_staff"),
     path('delete-staff/', delete_staff, name='delete_staff'),
     path('update-staff/', update_staff, name='update_staff'),
      path('update-staff-profile/', update_staff_profile, name='update_staff_profile'),
     path('get-staff/', get_staff, name='get_staff'),
    path("assign-task/", assign_task, name="assign_task"),
    path("get-tasks/", get_tasks, name="get_tasks"),
     path("get-bookings/", get_bookings, name="get_bookings"),
     path("gets-inventory/", gets_inventory, name="gets_inventory"),

    path("get-departments/", get_departments, name="get_departments"),
    path("get-staff/", get_staff, name="get_staff"),
    path("assign-shift/", assign_shift, name="assign_shift"),
    path("update-shift/", update_shift, name="update_shift"),
     path('weekly-schedule/', weekly_schedule, name='weekly_schedule'),
    path("get-shifts/", get_shifts, name="get_shifts"),
    path("staff-by-shift/", staff_by_shift, name="staff_by_shift"),
    # STAFF LOGIN
    path("staff-login/", staff_login, name="staff_login"),

    # DASHBOARDS
    path("housekeeping/", housekeeping_dashboard, name="housekeeping_dashboard"),
    path("hr/", hr_dashboard, name="hr_dashboard"),
    path("frontoffice/", frontoffice_dashboard, name="frontoffice_dashboard"),
    path("accountant/", accountant_dashboard, name="accountant_dashboard"),
    # FROND END DASHBOARDS
      path("api/create-booking/", create_booking, name="create_booking"),

    # 🔹 Check-In / Check-Out
    path("api/check-in/", check_in, name="check_in"),
    path("api/check-out/", check_out, name="check_out"),

    # 🔹 Housekeeping
    path("api/assign-housekeeping-task/", assign_housekeeping_task, name="assign_housekeeping_task"),
    path("api/get-bill/", get_bill, name="get_bill"),
    path('api/start-cleaning/', start_cleaning, name='start_cleaning'),
    path('api/complete-cleaning/', complete_cleaning, name='complete_cleaning'),
    path('api/add-inventory/', add_inventory, name='add_inventory'),
    path("api/get-inventory/", get_inventory, name="get_inventory"),

    path('api/update-inventory/<int:item_id>/', update_inventory, name='update_inventory'),
    path('api/delete-inventory/<int:item_id>/', delete_inventory, name='delete_inventory'),
   # Hr Dashboaed
   path('attendance/mark/', mark_attendance, name='mark_attendance'),
    path('attendance/live/', live_attendance, name='live_attendance'),
    path('attendance/daily/', daily_report, name='daily_report'),
    path('attendance/monthly/', monthly_report, name='monthly_report'),
    path("leave/update/<int:leave_id>/", update_leave_status, name="update_leave_status"),
    path("leave/requests/", leave_requests, name="leave_requests"),
    path("leave/apply/", apply_leave, name="apply_leave"),
    path("payroll/generate/", generate_payroll),
   path("payroll/dashboard/",payroll_dashboard),
   path("payroll/payslip/<int:payroll_id>/",payslip),

  # forgot password

  

      path('password-reset/',
     auth_views.PasswordResetView.as_view(
         template_name='auth/password_reset_form.html',
         success_url='/password-reset/',
         extra_context={'show_message': True}  
     ),
     name='password_reset'),

    
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='auth/password_reset_confirm.html',
             success_url='/reset/done/'
         ),
         name='password_reset_confirm'),


    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='auth/password_reset_confirm.html'
         ),
         name='password_reset_complete'),
]

 
