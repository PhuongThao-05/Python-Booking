from django.shortcuts import render, redirect

#------------------------admin------------------------------------
def admin_login(request):
    return render(request, 'admin/login-admin.html')

def admin_home(request):
    return render(request, 'admin/home-admin.html')

def admin_manage_user(request):
    return render(request, 'admin/manage_user.html')

def admin_manage_hotel(request):
    return render(request, 'admin/manage_hotels.html')

def admin_manage_order(request):
    return render(request, 'admin/manage_orders.html')

def admin_revenue_report(request):
    return render(request, 'admin/revenue_report.html')

def admin_traffic_report(request):
    return render(request, 'admin/hotel_traffic_report.html')

def admin_customer_report(request):
    return render(request, 'admin/customer_report.html')