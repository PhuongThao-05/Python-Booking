from django.shortcuts import render, redirect
def set_role(request):
    return render(request, 'user/set_role.html')
#------------------------customer------------------------------------
def customer_home(request):
    user_data = request.session.get('user_data', {})
    return render(request, 'customer/home-customer.html', user_data)

def customer_hotels(request):
    return render(request, 'customer/list_hotel.html')

def customer_detail_hotel(request,id):
    return render(request, 'customer/detail_hotel.html',{'hotel_id':id})

def customer_cart(request):
    return render(request, 'customer/cart.html')

def customer_order(request, id):
    return render(request, 'customer/order.html',{'room_id':id})

def customer_cart_to_order(request):
    return render(request, 'customer/order.html')

def customer_profile(request):
    return render(request, 'customer/profile_customer.html')

def customer_pay_return(request):
    return render(request, 'customer/payment_result.html')

def customer_my_order(request):
    return render(request, 'customer/my_order.html')

def customer_review(request):
    return render(request, 'customer/review.html')
