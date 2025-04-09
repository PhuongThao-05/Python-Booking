from collections import defaultdict
from datetime import datetime
import json
import os

import pytz
from booking import settings
import booking
from myapp.authentication import authenticate_token, check_role
from ..models import account, booking_detail, capacity, service, type_customer, type_room, users, role,hotels,partner,customer,room_detail,utility,booking
from django.core import serializers
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.db.models import Prefetch,Q
@authenticate_token
@check_role(allowed_roles=['partner'])
def edit_profile(request):
    email_user = request.user['email']
    userinfo = users.objects.filter(email=email_user).first()
    
    if not userinfo:
        return JsonResponse({'error': 'Partner personal infomation does not exist.'}, status=403)
    
    if request.method == 'GET':
        user_data = {
            'name': str(userinfo.name),
            'phonenumber': str(userinfo.phonenumber),
            'email': str(userinfo.email),
        }
        return JsonResponse({'success': True, 'partnerinfo': user_data}, status=200)

    elif request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        name = data.get('name')
        phonenumber = data.get('phonenumber')
    
        try:
            userinfo.name = name
            userinfo.phonenumber = phonenumber
            userinfo.save()

            return JsonResponse({'success': True, 'message': 'Partner information updated successfully!','name':str(userinfo.name)}, status=200)
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid method. Use GET to view and POST to update profile.'}, status=405)

@authenticate_token
@check_role(allowed_roles=['partner'])
def get_list_hotel(request):
    email_user=request.user['email']
    partners = partner.objects.filter(user_id__email=email_user)
    if not partners.exists():
         return JsonResponse({'error': 'Partner does not exist.'}, status=403)

    hotels_list = hotels.objects.filter(idpartner__in=partners, is_delete=False)

    hotels_data = [
    {
        'id': hotel.idhotel,
        'name': hotel.htl_name,
        'image': hotel.htl_img,
        'address': hotel.address,
        'description': hotel.description,
        'confirm': hotel.is_confirm
    }
    for hotel in hotels_list
]
    return JsonResponse({'success': True,'hotels': hotels_data}, status=200)
@authenticate_token
@check_role(allowed_roles=['partner'])
def add_hotel(request):
    email_user=request.user['email']
    partners = partner.objects.filter(user_id__email=email_user)
    if not partners.exists():
         return JsonResponse({'error': 'Partner does not exist.'}, status=403)

    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        hotel_name = data.get('name')
        hotel_image = data.get('imagehotel')
        hotel_address = data.get('address')
        hotel_description = data.get('description')

        if not hotel_name or not hotel_address:
            return JsonResponse({'success': False,'error': 'Name and address are required.'}, status=400)
        try:
            hotel = hotels.objects.create(
                htl_name=hotel_name,
                htl_img=hotel_image,
                address=hotel_address,
                description=hotel_description,
                idpartner=partners.first()
            )
            return JsonResponse({'success':True,'message': 'Hotel added successfully!'}, status=201)
        except Exception as e:
            return JsonResponse({'success': False,'error': str(e)}, status=500)

    return JsonResponse({'success': False,'error': 'Invalid method. Use POST to add hotel.'}, status=405)

@authenticate_token
@check_role(allowed_roles=['partner'])
def edit_hotel(request, id):
    email_user = request.user['email']
    partners = partner.objects.filter(user_id__email=email_user)
    
    if not partners.exists():
        return JsonResponse({'error': 'Partner does not exist.'}, status=403)
    
    hotel = hotels.objects.filter(idhotel=id, idpartner=partners.first()).first()
    
    if not hotel:
        return JsonResponse({'error': 'Hotel not found.'}, status=404)
    
    if request.method == 'GET':
        hotel_data = {
            'name': hotel.htl_name,
            'imagehotel': hotel.htl_img,
            'address': hotel.address,
            'description': hotel.description,
        }
        return JsonResponse({'success': True, 'hotel': hotel_data}, status=200)

    elif request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        hotel_name = data.get('name')
        hotel_image = data.get('imagehotel')
        hotel_address = data.get('address')
        hotel_description = data.get('description')
    
        try:
            hotel.htl_name = hotel_name
            hotel.htl_img = hotel_image
            hotel.address = hotel_address
            hotel.description = hotel_description
            hotel.save()

            return JsonResponse({'success': True, 'message': 'Hotel information updated successfully!'}, status=200)
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid method. Use GET to view and POST to update hotel.'}, status=405)

@authenticate_token
@check_role(allowed_roles=['partner'])
def delete_hotel(request, id):
    if request.method == 'DELETE':
        try:
            hotel = hotels.objects.filter(idhotel=id).first()
            hotel.is_delete=True
            hotel.save()
            return JsonResponse({'success': True, 'message': 'Hotel deleted successfully!'}, status=200)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid method. Use DELETE to delete hotel.'}, status=405)

def upload_image(request):
    if request.method == 'POST' and request.FILES['image']:
        image = request.FILES['image']
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        extension = os.path.splitext(image.name)[1]
        new_filename = f"{os.path.splitext(image.name)[0]}_{timestamp}{extension}"
        upload_dir = os.path.join('myapp/static', 'partner/upload')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        fs = FileSystemStorage(location=upload_dir)
        filename = fs.save(new_filename, image) 
        file_url = os.path.join(settings.STATIC_URL, 'partner/upload', filename).replace('\\', '/')
        return JsonResponse({'success': True, 'file_path': file_url})
    
    return JsonResponse({'success': False, 'message': 'No file uploaded'}, status=400)
@authenticate_token
@check_role(allowed_roles=['partner'])
def get_list_typeroom(request):
    id=request.GET.get('id')
    hotel = hotels.objects.filter(idhotel=id)
    if not hotel:
        return JsonResponse({'error': 'Hotel does not exist.'}, status=404)

    typeroom_list = type_room.objects.filter(idhotel__in=hotel,is_delete=False)

    typeroom_data = [
    {
        'id':type.idtyperm,
        'roomname': type.type_room,
        'roomimage': type.room_img,
        'roomarea': type.area,
        'bed': type.bed
    }
    for type in typeroom_list
]
    return JsonResponse({'success': True,'typeroom': typeroom_data}, status=200)
@authenticate_token
@check_role(allowed_roles=['partner'])
def add_typeroom(request, id):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        room_name = data.get('room_name')
        room_image = data.get('room_image')
        area = data.get('area')
        bed=data.get('bed')
        hotel = hotels.objects.get(idhotel=id)
        try:
            type_rooms = type_room.objects.create(
                type_room=room_name,
                area=area,
                room_img=room_image,
                bed=bed,
                idhotel=hotel
            )
            return JsonResponse({'success':True,'message': 'Type room added successfully!'}, status=201)
        except Exception as e:
            return JsonResponse({'success': False,'error': str(e)}, status=500)

    return JsonResponse({'success': False,'error': 'Invalid method. Use POST to add hotel.'}, status=405)

@authenticate_token
@check_role(allowed_roles=['partner'])
def edit_typeroom(request, id):
    typeroom = type_room.objects.filter(idtyperm=id).first()
    
    if not typeroom:
        return JsonResponse({'error': 'Type room does not found.'}, status=404)
    
    if request.method == 'GET':
        typeroom_data = {
            'room_name': typeroom.type_room,
            'room_image': typeroom.room_img,
            'area': typeroom.area,
            'bed': typeroom.bed,
        }
        return JsonResponse({'success': True, 'typeroom': typeroom_data}, status=200)

    elif request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        room_name = data.get('room_name')
        room_image = data.get('room_image')
        area = data.get('area')
        bed=data.get('bed')
    
        try:
            typeroom.type_room = room_name
            typeroom.room_img = room_image
            typeroom.area = area
            typeroom.bed=bed
            typeroom.save()

            return JsonResponse({'success': True, 'message': 'Type room information updated successfully!'}, status=200)
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid method. Use GET to view and POST to update typeroom.'}, status=405)

@authenticate_token
@check_role(allowed_roles=['partner'])
def delete_typeroom(request, id):
    if request.method == 'DELETE':
        try:
            typeroom = type_room.objects.filter(idtyperm=id).first()
            typeroom.is_delete=True
            typeroom.save()
            return JsonResponse({'success': True, 'message': 'Typeroom deleted successfully!'}, status=200)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid method. Use DELETE to delete typeroom.'}, status=405)

@authenticate_token
@check_role(allowed_roles=['partner'])
def get_list_room(request):
    id=request.GET.get('id')
    type_rooms = type_room.objects.filter(idtyperm=id)
    if not type_room:
        return JsonResponse({'error': 'Type room does not exist.'}, status=404)

    room_list = room_detail.objects.filter(idtyperm__in=type_rooms).prefetch_related('capacity_set__idtypecusm','utility_set__idsv')
    room_data = [
    {
        'id':room.idroom,
        'price': room.price_only_day,
        'quantity': room.quantity,
        'utility': [
            {
              'service_name': utility.idsv.service
            }
            for utility in room.utility_set.all() 
        ],
        'capacity': [{
            'sum_person': capacity.quantity,
            'type_person': capacity.idtypecusm.type_customer
        } for capacity in room.capacity_set.all()
        ],
    }
    for room in room_list
]
    return JsonResponse({'success': True,'room': room_data}, status=200)

@authenticate_token
@check_role(allowed_roles=['partner'])
def get_list_utitlity(request):
    services=service.objects.values('idsv', 'service') 
    return JsonResponse({'success': True,'services': list(services)}, status=200)
@authenticate_token
@check_role(allowed_roles=['partner'])
def add_room(request, id):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        price = data.get('price')
        sum_room = data.get('sum_room')
        typeroom = type_room.objects.get(idtyperm=id)
        capacitys = data.get('capacity', [])
        utilities = data.get('utility', [])
        try:
            room = room_detail.objects.create(
                idtyperm=typeroom,
                price_only_day=price,
                quantity=sum_room
            )
            for cap in capacitys:
                capacity.objects.create(idroom=room, idtypecusm=type_customer.objects.get(idtypecusm=cap['idtypecusm']), quantity=cap['quantity'])
            if len(utilities)>0:
                for utl in utilities:
                    utility.objects.create(idroom=room, idsv=service.objects.get(idsv=utl['idsv']))
            min_price_room = room_detail.objects.filter(idtyperm=typeroom).order_by('price_only_day').first()
            if min_price_room:
                hotel = typeroom.idhotel
                if hotel:
                    hotel.begin_price = min_price_room.price_only_day
                    hotel.save()
            return JsonResponse({'success':True,'message': 'Room added successfully!'}, status=201)
        except Exception as e:
            return JsonResponse({'success': False,'error': str(e)}, status=500)

    return JsonResponse({'success': False,'error': 'Invalid method. Use POST to add room.'}, status=405)

@authenticate_token
@check_role(allowed_roles=['partner'])
def edit_room(request, id):
    room = room_detail.objects.prefetch_related('capacity_set__idtypecusm','utility_set__idsv').get(idroom=id)
    
    if not room:
        return JsonResponse({'error': 'Room does not found.'}, status=404)
    
    if request.method == 'GET':
        room_data = {
            'price': room.price_only_day,
            'quantity': room.quantity,
            'utility': [
            {
              'service_name': utility.idsv.service
            }
            for utility in room.utility_set.all() 
            ],
            'capacity': [{
                'sum_person': capacity.quantity,
                'type_person': capacity.idtypecusm.type_customer
            } for capacity in room.capacity_set.all()
            ],
        }
        return JsonResponse({'success': True, 'room': room_data}, status=200)

    elif request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        price = data.get('price')
        sum_room = data.get('sum_room')
        capacitys = data.get('capacity', [])
        utilities = data.get('utility', [])
    
        try:
            room.price_only_day = price
            room.quantity = sum_room
            room.save()
            capacity.objects.filter(idroom=room).delete()
            for cap in capacitys:
                capacity.objects.create(idroom=room, idtypecusm=type_customer.objects.get(idtypecusm=cap['idtypecusm']), quantity=cap['quantity'])
            if len(utilities)>0:
                utility.objects.filter(idroom=room).delete()
                for utl in utilities:
                    utility.objects.create(idroom=room, idsv=service.objects.get(idsv=utl['idsv']))
            min_price_room = room_detail.objects.filter(idtyperm=room.idtyperm.idtyperm).order_by('price_only_day').first()
            if min_price_room:
                hotel = type_room.objects.get(idtyperm=room.idtyperm.idtyperm).idhotel
                if hotel:
                    hotel.begin_price = min_price_room.price_only_day
                    hotel.save()
            return JsonResponse({'success': True, 'message': 'Room information updated successfully!'}, status=200)
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid method. Use GET to view and POST to update room.'}, status=405)

@authenticate_token
@check_role(allowed_roles=['partner'])
def delete_room(request, id):
    if request.method == 'DELETE':
        try:
            room = room_detail.objects.filter(idroom=id).first()
            if not room:
                return JsonResponse({'success': False, 'error': 'Room does not exist.'}, status=404)
            room.delete()
            return JsonResponse({'success': True, 'message': 'Room deleted successfully!'}, status=200)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid method. Use DELETE to delete Room.'}, status=405)
@authenticate_token
@check_role(allowed_roles=['partner'])
def lst_order(request,id):
    upcoming_orders=booking_detail.objects.filter(iscancel=False, idroom__idtyperm__idhotel__idhotel=id,idbook__iscancel=False,idbook__iscomplete=False)\
    .exclude(
    status__in=["Completed", "Canceled"]  
)   .select_related('idroom').order_by('-iddetail')
    complete_orders=booking_detail.objects.filter(iscancel=False,status='Completed',idroom__idtyperm__idhotel__idhotel=id)\
    .select_related('idroom').order_by('-iddetail')
    
    cancel_orders=booking_detail.objects.filter(iscancel=True,status='Canceled',idroom__idtyperm__idhotel__idhotel=id)\
    .select_related('idroom').order_by('-iddetail')
    
    upcoming=[]
    complete=[]
    cancel=[]
    for order in upcoming_orders:
        bookings = {
            "idbook": order.idbook.idbook,
            "customer": order.idbook.idcustomer.user_id.name,
            "payment": order.idbook.idpayment.payment_name,
            "total_cost":order.idbook.total_cost,
            "state":order.idbook.state,
            "details":[],
            }
        room = order.idroom
        room_info={
                'iddetail':order.iddetail,
                'idroom':room.idroom,
                'type_room':room.idtyperm.type_room,
                'hotel':room.idtyperm.idhotel.htl_name,
                'hotel_img':room.idtyperm.idhotel.htl_img,
                'room_img':room.idtyperm.room_img,
                'area':room.idtyperm.area,
                'bed':room.idtyperm.bed,
                'address':room.idtyperm.idhotel.address,
                'price': room.price_only_day,
                'price_total':((order.date_leave - order.date_arrive).days)*room.price_only_day,
                'utilities': [{'service_name': util.idsv.service} for util in room.utility_set.all()],
                'capacities': [{'type_person': cap.idtypecusm.type_customer, 'quantity': cap.quantity} for cap in room.capacity_set.all()],
                'date_arrive':order.date_arrive,
                'date_leave':order.date_leave,
                'status':order.status
            }
        bookings['details'].append(room_info)
        upcoming.append(bookings)
    for order in complete_orders:
            bookings = {
            "idbook": order.idbook.idbook,
            "customer": order.idbook.idcustomer.user_id.name,
            "payment": order.idbook.idpayment.payment_name,
            "total_cost":order.idbook.total_cost,
            "state":order.idbook.state,
            "details":[],
            }
            room = order.idroom
            room_info={
                    'iddetail':order.iddetail,
                    'is_review':order.is_review,
                    'idroom':room.idroom,
                    'type_room':room.idtyperm.type_room,
                    'hotel':room.idtyperm.idhotel.htl_name,
                    'hotel_img':room.idtyperm.idhotel.htl_img,
                    'room_img':room.idtyperm.room_img,
                    'area':room.idtyperm.area,
                    'bed':room.idtyperm.bed,
                    'address':room.idtyperm.idhotel.address,
                    'price': room.price_only_day,
                    'price_total':((order.date_leave - order.date_arrive).days)*room.price_only_day,
                    'utilities': [{'service_name': util.idsv.service} for util in room.utility_set.all()],
                    'capacities': [{'type_person': cap.idtypecusm.type_customer, 'quantity': cap.quantity} for cap in room.capacity_set.all()],
                    'date_arrive':order.date_arrive,
                    'date_leave':order.date_leave,
                    'status':order.status
                }
            bookings['details'].append(room_info)
            complete.append(bookings)
    for order in cancel_orders:
                bookings = {
                "idbook": order.idbook.idbook,
                "customer": order.idbook.idcustomer.user_id.name,
                "payment": order.idbook.idpayment.payment_name,
                "total_cost":order.idbook.total_cost,
                "state":order.idbook.state,
                "details":[],
                }
                room = order.idroom
                room_info={
                        'iddetail':order.iddetail,
                        'idroom':room.idroom,
                        'type_room':room.idtyperm.type_room,
                        'hotel':room.idtyperm.idhotel.htl_name,
                        'hotel_img':room.idtyperm.idhotel.htl_img,
                        'room_img':room.idtyperm.room_img,
                        'area':room.idtyperm.area,
                        'bed':room.idtyperm.bed,
                        'address':room.idtyperm.idhotel.address,
                        'price': room.price_only_day,
                        'price_total':((order.date_leave - order.date_arrive).days)*room.price_only_day,
                        'utilities': [{'service_name': util.idsv.service} for util in room.utility_set.all()],
                        'capacities': [{'type_person': cap.idtypecusm.type_customer, 'quantity': cap.quantity} for cap in room.capacity_set.all()],
                        'date_arrive':order.date_arrive,
                        'date_leave':order.date_leave,
                        'status':order.status
                    }
                bookings['details'].append(room_info)
                cancel.append(bookings)
    return JsonResponse({'success': True, 'upcoming': upcoming,'complete':complete,'cancel':cancel})
@authenticate_token
@check_role(allowed_roles=['partner'])
def update_status_room(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        book_id = data.get('idbook')
        detail_id = data.get('iddetail')  

        try:
            order = booking.objects.get(idbook=book_id)
        except booking.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Not found order to update'}, status=404)

        if detail_id:
            updated_room = booking_detail.objects.filter(iddetail=detail_id).first() 
            if updated_room:
                status_mapping = {
                    "Booked": "Check in",
                    "Check in": "Check out",
                    "Check out": "Completed",
                }
          
                new_status = status_mapping.get(updated_room.status, updated_room.status)
                if new_status == 'Completed':
                    if  booking_detail.objects.filter(iddetail=detail_id, idbook__idpayment=2).exists():
                        tz = pytz.timezone("Asia/Ho_Chi_Minh")
                        date_payment = datetime.now(tz)
                        updated_rows = booking_detail.objects.filter(iddetail=detail_id).update(status=new_status,date_payment=date_payment)
                    else:
                       updated_rows = booking_detail.objects.filter(iddetail=detail_id).update(status=new_status) 
                else:
                    updated_rows = booking_detail.objects.filter(iddetail=detail_id).update(status=new_status) 
                if updated_rows == 0:
                    return JsonResponse({'success': False, 'error': 'Room not found or already updated'}, status=400)
             
                if booking_detail.objects.filter(idbook=book_id,status="Completed").count() == booking_detail.objects.filter(idbook=book_id).count():
                    order.state = 'Completed'
                    order.iscomplete=True
                    order.save()
                return JsonResponse({'success': True, 'message': 'Update status successful'}, status=200)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@authenticate_token
@check_role(allowed_roles=['partner'])
def get_month_and_hotel(request):
    email = request.user['email']

    partner_info = partner.objects.filter(user_id__email=email).first()
    if not partner_info:
        return JsonResponse({'success': False, 'error': 'Partner not exist'}, status=404)
    
  
    hotels_list = hotels.objects.filter(idpartner=partner_info.idpartner, is_confirm=True)
    if not hotels_list.exists():
        return JsonResponse({'success': False, 'error': 'No hotels found'}, status=404)

    lst_hotel = [{'hotel': ht.htl_name, 'idhotel': ht.idhotel} for ht in hotels_list]
    hotel_ids = hotels_list.values_list('idhotel', flat=True)

    completed_bookings = booking_detail.objects.filter(
        idroom__idtyperm__idhotel__in=hotel_ids, status='Completed'
    ).values_list('date_payment__year', flat=True).distinct().order_by('-date_payment__year')
    
    return JsonResponse({'success': True, 'hotel': lst_hotel, 'year': list(completed_bookings)}, status=200)

@authenticate_token
@check_role(allowed_roles=['partner'])
def revenue_by_month(request, hotel_id, year):
    bookings = booking_detail.objects.filter(
        idroom__idtyperm__idhotel=hotel_id,
        status='Completed',
        date_payment__year=year
    )

    revenue_by_month = defaultdict(int)

    for booking in bookings:
        month = booking.date_payment.month
        stay_days = (booking.date_leave - booking.date_arrive).days  
        total_price = booking.idroom.price_only_day * stay_days 

        revenue_by_month[month] += total_price  

 
    revenue_by_month = dict(revenue_by_month)

    return JsonResponse({'success':True, 'revenue_by_month': revenue_by_month})
