from django.shortcuts import render, redirect


#------------------------partner------------------------------------
def partner_home(request):
    user_data = request.session.get('user_data', {})
    return render(request, 'partner/home-partner.html', user_data)

def partner_hotel(request):
    return render(request, 'partner/hotels.html')

def partner_add_hotel(request):
    return render(request, 'partner/create_hotel.html')

def partner_edit_hotel(request,id):
    return render(request, 'partner/edit_hotel.html',{'hotel_id': id})

def partner_get_typeroom(request,id):
    return render(request, 'partner/details-hotel.html', {'hotel_id': id})

def partner_add_typeroom(request,id):
    return render(request, 'partner/create_typeroom.html', {'hotel_id': id})

def partner_edit_typeroom(request,id,hotel):
    return render(request, 'partner/edit_typeroom.html', {'typeroom_id': id,'hotel_id':hotel})

def partner_get_room(request,id,hotel):
    return render(request, 'partner/list_room.html', {'typeroom_id': id,'hotel_id':hotel})

def partner_add_room(request,id,hotel):
    return render(request, 'partner/add_detail_room.html', {'typeroom_id': id,'hotel_id':hotel})

def partner_edit_room(request,id,type,hotel):
    return render(request, 'partner/edit_detail_room.html', {'room_id': id,'typeroom_id': type,'hotel_id':hotel})

def partner_profile(request):
    return render(request, 'partner/profile.html')

def partner_order(request,id):
    return render(request, 'partner/order.html',{'hotel_id': id})

def partner_statistic(request):
    return render(request, 'partner/revenue_statistic.html')
