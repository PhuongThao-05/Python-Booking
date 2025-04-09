from datetime import datetime, timedelta
import threading
import time
import hashlib
import hmac
import json
import random
from django.http import JsonResponse
import paypalrestsdk
import pytz
import requests
from booking import settings
from myapp.authentication import authenticate_token, check_role
from myapp.models import cart, hotels,booking,booking_detail,customer, rating,room_detail, type_payment, users, type_room
from django.utils.timezone import now
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
from pyngrok import ngrok
from django.core.cache import cache
from django.db.models import Q,F
from django.db.models import Prefetch
from django.core.paginator import Paginator

from myapp.shared_features import can_book_room, send_notification_email
@authenticate_token
@check_role(allowed_roles=['customer'])
def customer_edit_profile(request):
    email_user = request.user['email']
    userinfo = users.objects.filter(email=email_user).first()
    
    if not userinfo:
        return JsonResponse({'error': 'Customer personal infomation does not exist.'}, status=403)
    
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

            return JsonResponse({'success': True, 'message': 'Customer information updated successfully!','name':str(userinfo.name)}, status=200)
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid method. Use GET to view and POST to update profile.'}, status=405)


def list_hotel(request):
    search_query = request.GET.get('search', '').strip()
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 3)) 
    hotels_list = hotels.objects.filter(is_delete=False,is_confirm=True).order_by('-idhotel')
    if not hotels_list.exists():
        return JsonResponse({'success': False, 'message': 'Hotels not found!'}, status=404)
    if search_query:
        hotels_list=hotels_list.filter(Q(htl_name__icontains=search_query)|Q(address__icontains=search_query))
    
    paginator = Paginator(hotels_list, limit)
    hotels_page = paginator.get_page(page)
    hotel_data = []
    for hotel in hotels_page:
        hotel_info = {
            'hotel_id':hotel.idhotel,
            'hotel_name': hotel.htl_name,
            'hotel_image':hotel.htl_img,
            'hotel_address':hotel.address,
            'begin_price':hotel.begin_price,
        }
        hotel_data.append(hotel_info)

    return JsonResponse({'success': True,'total_pages': paginator.num_pages,
        'current_page': page, 'hotels': hotel_data}, status=200)

def detail_hotel(request,id,start_date,end_date):
    hotels_list = hotels.objects.filter(idhotel=id,is_delete=False).prefetch_related(
         Prefetch(
        'type_room_set',
        queryset=type_room.objects.filter(is_delete=False),
        to_attr='filtered_type_rooms'
    ),
        'type_room_set__room_detail_set__utility_set',
        'type_room_set__room_detail_set__capacity_set'
    )
    if not hotels_list.exists():
        return JsonResponse({'success': False, 'message': 'Hotels not found!'}, status=404)
    try:
        check_date_start = start_date
        check_date_end = end_date
    except (json.JSONDecodeError, AttributeError):
        check_date_start = now().date()
        check_date_end= check_date_start + timedelta(days=1)

    check_date_start = datetime.strptime(check_date_start, "%Y-%m-%d")
    check_date_end = datetime.strptime(check_date_end, "%Y-%m-%d")
  
    hotel_data = []
    for hotel in hotels_list:
        hotel_info = {
            'hotel_name': hotel.htl_name,
            'hotel_image':hotel.htl_img,
            'hotel_address':hotel.address,
            'partner_email':str(hotel.idpartner.user_id.email.email),
            'partner_phone':hotel.idpartner.user_id.phonenumber,
            'begin_price':hotel.begin_price,
            'description':hotel.description,
            'type_rooms': []
        }
        for typeroom in hotel.filtered_type_rooms:
            type_room_info = {
                'type_name': typeroom.type_room,
                'area':typeroom.area,
                'room_img':typeroom.room_img,
                'bed':typeroom.bed,
                'rooms': []
            }
            for room in typeroom.room_detail_set.order_by('price_only_day'):
                room_info = {
                    'idroom':room.idroom,
                    'price': room.price_only_day,
                    'utilities': [{'service_name': utility.idsv.service} for utility in room.utility_set.all()],
                    'capacities': [{'type_person': cap.idtypecusm.type_customer, 'quantity': cap.quantity} for cap in room.capacity_set.all()]
                }
                if can_book_room(room.idroom, check_date_start, check_date_end):    
                    type_room_info['rooms'].append(room_info)
            hotel_info['type_rooms'].append(type_room_info)
        hotel_data.append(hotel_info)

    return JsonResponse({'success': True, 'hotels': hotel_data}, status=200)

@authenticate_token
@check_role(allowed_roles=['customer'])
def add_to_cart(request):
    email_user=request.user['email']
    customer_info=customer.objects.filter(user_id__email=email_user).first()
    if not customer_info:
        return JsonResponse({'success':False, 'error':'Customer not found'},status=404)
    if(request.method == 'POST'):
        data=json.loads(request.body.decode('utf-8'))
        idroom=data.get('idroom')
        check_in_date=data.get('datestart')
        check_out_date=data.get('dateend')
        room=room_detail.objects.filter(idroom=idroom).first()
        try:
            cart.objects.create(
                idroom=room,
                idcustomer=customer_info,
                check_in_date=check_in_date,
                check_out_date=check_out_date
            )
            return JsonResponse({'success':True,'message':'Add room to cart successful!'},status=201)
        except Exception as e:
            return JsonResponse({'success':False,'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

@authenticate_token
@check_role(allowed_roles=['customer'])
def count_item_cart(request):
    email_user=request.user['email']
    customer_info=customer.objects.filter(user_id__email=email_user).first()
    if not customer_info:
        return JsonResponse({'success':False, 'error':'Customer not found'},status=404)
    count_item=cart.objects.filter(idcustomer=customer_info.idcustomer).count()
    return JsonResponse({'success':True, 'count':count_item},status=200)

@authenticate_token
@check_role(allowed_roles=['customer'])
def list_in_cart(request):
    email_user=request.user['email']
    customer_info=customer.objects.filter(user_id__email=email_user).first()
    if not customer_info:
        return JsonResponse({'success':False, 'error':'Customer not found'},status=404)
    list_item=cart.objects.filter(idcustomer=customer_info.idcustomer).prefetch_related(
    'idroom__idtyperm__idhotel',
    'idroom__utility_set',     
    'idroom__capacity_set')
    carts = []
    for item in list_item:
        cart_info = {
            'idcart':item.idcart,
            'datestart': item.check_in_date,
            'dateend': item.check_out_date,
            'days': (item.check_out_date - item.check_in_date).days,
            'room': []
        }

        room = item.idroom 
        room_info = {
            'idroom':room.idroom,
            'price': room.price_only_day,
            'utilities': [{'service_name': util.idsv.service} for util in room.utility_set.all()],
            'capacities': [{'type_person': cap.idtypecusm.type_customer, 'quantity': cap.quantity} for cap in room.capacity_set.all()],
            'type_room': []
        }

        type_room = room.idtyperm  
        type_info = {
            'type_room': type_room.type_room,
            'hotel': []
        }

        hotel=type_room.idhotel
        hotel_info = {
                'hotel_name': hotel.htl_name,
                'address': hotel.address,
                'hotel_image':hotel.htl_img,
            }
        type_info['hotel'].append(hotel_info)

        room_info['type_room'].append(type_info)
        cart_info['room'].append(room_info)
        carts.append(cart_info)
    return JsonResponse({'success':True, 'list_cart':carts},status=200)

@authenticate_token
@check_role(allowed_roles=['customer'])
def delete_item_cart(request, id):
    if request.method == 'DELETE':
        try:
            cart_item = cart.objects.filter(idcart=id).first()
            if not cart_item:
                return JsonResponse({'success': False, 'error': 'Item does not exist in cart.'}, status=404)
            cart_item.delete()
            return JsonResponse({'success': True, 'message': 'Item deleted from cart successfully!'}, status=200)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid method. Use DELETE to delete cart item.'}, status=405)
    

@authenticate_token
@check_role(allowed_roles=['customer'])
def item_order(request, id):
    if request.method=='POST':
        data=json.loads(request.body.decode('utf-8'))
        date_in=data.get('datestart')
        date_out=data.get('dateend')
        order_type=data.get('order_type')
        request.session[f"date_in_{request.user['email']}"] = date_in
        request.session[f"date_out_{request.user['email']}"] = date_out
        request.session[f"order_type_{request.user['email']}"]=order_type
        return JsonResponse({'success': True, 'message': 'Dates saved to session'}, status=200)

    if request.method=='GET':
        email_user=request.user['email']
        customer_info=users.objects.filter(email=email_user).first()
        if not customer_info:
            return JsonResponse({'success':False, 'error':'Customer not found'},status=404)
        id_customer=customer.objects.get(user_id=customer_info.user_id).idcustomer
        item_info=room_detail.objects.filter(idroom=id).prefetch_related(
        'idroom__idtyperm__idhotel',
        'idroom__utility_set',     
        'idroom__capacity_set')
        date_in = request.session.get(f"date_in_{request.user['email']}")
        date_out = request.session.get(f"date_out_{request.user['email']}")

        date_in_obj = datetime.strptime(date_in, "%Y-%m-%d").date()
        date_out_obj = datetime.strptime(date_out, "%Y-%m-%d").date()
        days = (date_out_obj - date_in_obj).days
        order = []
        customer_info={
                    'name': str(customer_info.name),
                    'email': str(customer_info.email),
                    'idcustomer':id_customer,
                    'date_in':date_in,
                    'date_out':date_out,
                    'days':days
                } 
        for item in item_info:       

            room_info = {
                'idroom':item.idroom,
                'price': item.price_only_day,
                'utilities': [{'service_name': util.idsv.service} for util in item.utility_set.all()],
                'capacities': [{'type_person': cap.idtypecusm.type_customer, 'quantity': cap.quantity} for cap in item.capacity_set.all()],
                'type_room': [],
            }           

            type_room = item.idtyperm  
            type_info = {
                'type_room': type_room.type_room,
                'area': type_room.area,
                'hotel': []
            }

            hotel=type_room.idhotel
            hotel_info = {
                    'hotel_name': hotel.htl_name,
                    'address': hotel.address,
                    'hotel_image':hotel.htl_img,
                }
            type_info['hotel'].append(hotel_info)
            room_info['type_room'].append(type_info)
            order.append(room_info)
        return JsonResponse({'success':True, 'order_info':order,'customer':customer_info},status=200)

@authenticate_token
@check_role(allowed_roles=['customer'])
def store_cart(request):
    if request.method=='POST':
        data=json.loads(request.body.decode('utf-8'))
        items=data.get('selectedItems', [])
        order_type=data.get('order_type')
        request.session[f"order_type_{request.user['email']}"]=order_type
        order=[]
        for selected_item in items:
            list_items = cart.objects.filter(idcart=selected_item['idcart']).prefetch_related(
                'idroom__idtyperm__idhotel',
                'idroom__utility_set',     
                'idroom__capacity_set'
            )
            
            for cart_item in list_items:
                cart_info = {
                    'idcart': cart_item.idcart,
                    'datestart': cart_item.check_in_date.strftime('%Y-%m-%d'),  
                    'dateend': cart_item.check_out_date.strftime('%Y-%m-%d'), 
                    'days': (cart_item.check_out_date - cart_item.check_in_date).days,
                    'room': []
                }

                room = cart_item.idroom
                room_info = {
                    'idroom': room.idroom,
                    'price': room.price_only_day,
                    'utilities': [{'service_name': util.idsv.service} for util in room.utility_set.all()],
                    'capacities': [{'type_person': cap.idtypecusm.type_customer, 'quantity': cap.quantity} for cap in room.capacity_set.all()],
                    'type_room': []
                }

                type_room = room.idtyperm
                type_info = {
                    'type_room': type_room.type_room,
                    'hotel': []
                }

                hotel = type_room.idhotel
                hotel_info = {
                    'hotel_name': hotel.htl_name,
                    'address': hotel.address,
                    'hotel_image': hotel.htl_img,
                }
                type_info['hotel'].append(hotel_info)

                room_info['type_room'].append(type_info)
                cart_info['room'].append(room_info)
                order.append(cart_info)
        request.session[f"store_cart_{request.user['email']}"]=order
        return JsonResponse({'success': True, 'list_order': order}, status=200)

@authenticate_token
@check_role(allowed_roles=['customer'])
def show_store_cart(request):
    if request.method=='GET':
        data=request.session.get(f"store_cart_{request.user['email']}") 
        if not data:
            return JsonResponse({'success':False, 'error':'Data not available'}, status=404)
        email_user=request.user['email']
        customer_info=users.objects.filter(email=email_user).first()
        id_customer=customer.objects.get(user_id=customer_info.user_id).idcustomer
        if not customer_info:
            return JsonResponse({'success':False, 'error':'Customer not found'},status=404)
        customer_info={
                    'name': str(customer_info.name),
                    'email': str(customer_info.email),
                    'idcustomer':id_customer
        }
        return JsonResponse({'success': True, 'order_info':data,'customer':customer_info}, status=200)

@authenticate_token
@check_role(allowed_roles=['customer'])
def item_booking(request):
    if request.method=='POST':
        data=json.loads(request.body.decode('utf-8'))
        id_customer=data.get('id_customer')
        id_payment=data.get('id_payment')
        items=data.get('item_booking', [])  
        total_price=data.get('total_price')
        order_type=request.session.get(f"order_type_{request.user['email']}")
        cache.set(f"booking_info_{request.user['email']}",{
            'id_customer': id_customer,
            'id_payment': id_payment,
            'items': items,
            'total_price': total_price,
            'order_type':order_type
        })
        booking_info = cache.get(f"booking_info_{request.user['email']}")
        print(booking_info)
        return JsonResponse({'success': True, 'data':booking_info}, status=200)

@csrf_exempt
def order_booking(request,email):
    print(email)
    global payment_result
    try:
        booking_info = cache.get(f"booking_info_{email}")
        if not booking_info:
            return JsonResponse({'success': False, 'message': 'No booking info found in cache'}, status=400)
        
        print("Booking info from cache:", booking_info)
        id_payment = booking_info.get('id_payment')
        if id_payment == 2:
            payment_result=-1
        tz = pytz.timezone("Asia/Ho_Chi_Minh")
        date_payment = datetime.now(tz) if id_payment == 1 else None
        booking_obj = booking.objects.create(
            idcustomer=customer.objects.get(pk=booking_info.get('id_customer')),
            idpayment=type_payment.objects.get(pk=booking_info.get('id_payment')),
            total_cost=float(booking_info.get('total_price')),
            state='Đặt chỗ thành công'
        )
        print("Booking created:", booking_obj)

        items = booking_info.get('items', [])
        for item in items:
            print("Creating booking detail for:", item)
            booking_detail.objects.create(
                idbook=booking_obj,
                idroom=room_detail.objects.get(pk=item.get('idroom')),
                date_arrive=datetime.strptime(item.get('date_arrive'), '%Y-%m-%d').date(),
                date_leave=datetime.strptime(item.get('date_leave'), '%Y-%m-%d').date(),
                status='Booked',
                date_payment=date_payment,
            )

        if booking_info.get('order_type') == 'cart':
            print("Deleted in cart")
            cart.objects.filter(idroom__in=[item['idroom'] for item in booking_info['items']]).delete()
        cache.clear() 
        print("All booking details created successfully")
        return JsonResponse({'success': True, 'message':'Placed order successfully!'}, status=200)

    except Exception as e:
        print("Error occurred:", str(e))
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
#------------------Thanh toán-----------------------------------------------------------------
ZALOPAY_CONFIG = {
    'app_id': '2554',
    'key1': 'sdngKKJmqEMzvh5QQcdD2A9XBSKUNaYn',
    'key2': 'trMrHtvjo6myautxDUiAcYsVtaeQ8nhf',
    'endpoint': 'https://sb-openapi.zalopay.vn/v2/create',
}
ngrok_url=None
ngrok_start=False
lock = threading.Lock()  # Tạo một khóa để đồng bộ hóa
payment_result=0

def start_ngrok():
    global ngrok_url, ngrok_start

    with lock:  # Đảm bảo chỉ một luồng chạy đoạn mã bên trong
        if not ngrok_start:
            try:
                ngrok.set_auth_token(settings.AUTH_TOKEN)
                tunnel = ngrok.connect(8000)
                ngrok_url = tunnel.public_url 
                ngrok_start = True
                print('NGrok', ngrok_url)
            except Exception as e:
                print("Failed to start NGrok:", e)
                raise
    return ngrok_url

@authenticate_token
@check_role(allowed_roles=['customer'])
def zalo_payment(request):
    if request.method == 'POST':
        if not ngrok_url:
            return JsonResponse({'success': False, 'error': 'Ngrok URL not available'}, status=500)
        data = json.loads(request.body)
        email = request.user['email']
        amount = data.get('amount')
        trans_id = random.randint(100000, 999999)
        ReturnUrl = "http://127.0.0.1:8000/return-payment/"; 
        embed_data = {
        'redirecturl': ReturnUrl,
        }
        items = []
        order = {
            'app_id': ZALOPAY_CONFIG['app_id'],
            'app_trans_id': f"{datetime.now().strftime('%y%m%d')}{trans_id}",
            'app_user': str(email),
            'app_time': int(datetime.now().timestamp() * 1000),
            'item': json.dumps(items), 
            'embed_data': json.dumps(embed_data),
            'amount': int(amount),
            'callback_url': f"{ngrok_url}/callback/",
            'description': f"Payment for order #{trans_id}",
            'bank_code': '',
        }
        data = '|'.join([
            str(order['app_id']),
            str(order['app_trans_id']),
            str(order['app_user']),
            str(order['amount']),
            str(order['app_time']),
            order['embed_data'],
            order['item']
        ])
        mac = hmac.new(ZALOPAY_CONFIG['key1'].encode(), data.encode(), hashlib.sha256).hexdigest()
        order['mac'] = mac

        try:
            response = requests.post(ZALOPAY_CONFIG['endpoint'], params=order)
            result = response.json()
            print("Zalopay Response:", result) 
            print(result.get('return_code'))
            if result.get('return_code') == 1:
                return JsonResponse({'success': True, 'url': result.get('order_url')})
            else:
                return JsonResponse({'success': False, 'error': result.get('return_message')}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def callback(request):
    global payment_result
    payment_result=0
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            data_str = data['data']
            req_mac = data['mac']
            mac = hmac.new(ZALOPAY_CONFIG['key2'].encode(), data_str.encode(), hashlib.sha256).hexdigest()

            if req_mac != mac:
                return JsonResponse({'return_code': -1, 'return_message': 'mac not equal'})

            data_json = json.loads(data_str)
            app_trans_id = data_json['app_trans_id']
            email= data_json['app_user']
            status_response = check_status_order(app_trans_id)

            if status_response.get('return_code') == 1:
                response = order_booking(request,email)
                if response.status_code == 200:  
                    print('Thêm thành công')
                    payment_result=1
                else:
                    payment_result=0
                    print('Không thêm được')
                return JsonResponse({'return_code': 1, 'return_message': 'success'})
            else:
                print('Thanh toán thất bại!')
                payment_result=0
                return JsonResponse({'return_code': 0, 'return_message': 'Payment failed or processing'})

        except Exception as e:
            return JsonResponse({'return_code': 0, 'return_message': str(e)})


def check_status_order(app_trans_id):
    post_data = {
        'app_id': ZALOPAY_CONFIG['app_id'],
        'app_trans_id': app_trans_id,
    }
    data_str = f"{post_data['app_id']}|{post_data['app_trans_id']}|{ZALOPAY_CONFIG['key1']}"
    post_data['mac'] = hmac.new(ZALOPAY_CONFIG['key1'].encode(), data_str.encode(), hashlib.sha256).hexdigest()

    response = requests.post('https://sb-openapi.zalopay.vn/v2/query', data=post_data)
    return response.json()

def return_page(request):
    global payment_result
    if  payment_result == 1:
        message = {
            "title": "Congratulations, your order has been successfully placed!",
            "message": "Please follow your order!",
            "status":1
        }
    elif payment_result == -1:
        message = {
            "title": "Your order place successfully!",
            "message": "Please follow your order!",
            "status":-1
        }
    else:
        message = {
            "title": "Unfortunately, your order has failed!",
            "message": "Please try again!",
            "status":0
        }
    return JsonResponse({'success': True, 'data': message})

if ngrok_url is None:
    ngrok_url = start_ngrok()

@authenticate_token
@check_role(allowed_roles=['customer'])
def create_momo_payment(request):
    if request.method == 'POST':
        if not ngrok_url:
            return JsonResponse({'success': False, 'error': 'Ngrok URL not available'}, status=500)
        try:
            data = json.loads(request.body)
            email=request.user['email']
            amount = data.get('amount')

            config = {
            'accessKey': 'F8BBA842ECF85',
            'secretKey': 'K951B6PE1waDMi640xX08PD3vg6EkVlz',
            'orderInfo': 'pay with MoMo',
            'partnerCode': 'MOMO',
            'redirectUrl': 'http://127.0.0.1:8000/return-payment/',
            'ipnUrl': f"{ngrok_url}/handle_payment_momo_callback/", 
            'requestType': 'payWithMethod',
            'extraData': email,
            'orderGroupId': '',
            'autoCapture': True,
            'lang': 'vi',
            }
            
            accessKey = config['accessKey']
            secretKey = config['secretKey']
            orderInfo = config['orderInfo']
            partnerCode = config['partnerCode']
            redirectUrl = config['redirectUrl']
            ipnUrl = config['ipnUrl']
            requestType = config['requestType']
            extraData = config['extraData']
            orderGroupId = config['orderGroupId']
            autoCapture = config['autoCapture']
            lang = config['lang']

            # Generate orderId and requestId
            amount = amount
            orderId = f"{partnerCode}{int(time.time() * 1000)}"
            requestId = orderId

        
            # Create raw signature
            raw_signature = (
                f"accessKey={accessKey}&amount={amount}&extraData={extraData}"
                f"&ipnUrl={ipnUrl}&orderId={orderId}&orderInfo={orderInfo}"
                f"&partnerCode={partnerCode}&redirectUrl={redirectUrl}"
                f"&requestId={requestId}&requestType={requestType}"
            )

            # Generate HMAC SHA256 signature
            signature = hmac.new(
                bytes(secretKey, 'utf-8'),
                msg=bytes(raw_signature, 'utf-8'),
                digestmod=hashlib.sha256
            ).hexdigest()

            # Request body
            request_body = {
                "partnerCode": partnerCode,
                "partnerName": "Test",
                "storeId": "MomoTestStore",
                "requestId": requestId,
                "amount": amount,
                "orderId": orderId,
                "orderInfo": orderInfo,
                "redirectUrl": redirectUrl,
                "ipnUrl": ipnUrl,
                "lang": lang,
                "requestType": requestType,
                "autoCapture": autoCapture,
                "extraData": extraData,
                "orderGroupId": orderGroupId,
                "signature": signature,
            }

            # Send request to MoMo
            url = "https://test-payment.momo.vn/v2/gateway/api/create"
            headers = {
                "Content-Type": "application/json",
            }

            try:
                response = requests.post(url, data=json.dumps(request_body), headers=headers)
                response_data = response.json()

                # Kiểm tra phản hồi từ MoMo
                if response_data.get("resultCode") == 0:
                    pay_url = response_data.get("payUrl")
                    return JsonResponse({'success':True,"payUrl": pay_url}, status=200)
                else:
                    return JsonResponse({'success':False,"error": response_data.get("message")}, status=400)

            except requests.RequestException as e:
                return JsonResponse({'success':False, "error": str(e)}, status=500)

        except Exception as e:
            return JsonResponse({'success':False,'error': str(e)}, status=500)


@csrf_exempt
def handle_payment_momo_callback(request):
    global payment_result
    payment_result=0
    if request.method == "POST":
        try:
            body = json.loads(request.body.decode('utf-8'))
            print("callback:",body)
            email = body.get("extraData", "{}")
            result_code = body.get('resultCode')
            if result_code == 0: 
                print("Thanh toán thành công!")
                response = order_booking(request,email)
                if response.status_code == 200:  
                    print('Thêm thành công')
                    payment_result=1
                else:
                    print('Không thêm được')
                return JsonResponse({'status': 'success', 'message': 'Payment successful.'})
            else: 
                print("Thanh toán thất bại!")
                payment_result=0
                return JsonResponse({'status': 'failure', 'message': 'Payment failed.'})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format.'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

@authenticate_token
@check_role(allowed_roles=['customer'])
def payment_paypal(request):
    if request.method=='POST':
        data = json.loads(request.body)
        email=request.user['email']
        amount = data.get('amount')
        transform_usd = round(amount * 0.00003940, 2)
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            
            },
            "redirect_urls": {
                "return_url": "http://127.0.0.1:8000/return-payment/",
                "cancel_url": "http://127.0.0.1:8000/return-payment/"
            },
            "transactions": [{
                "amount": {
                    "total": str(transform_usd),
                    "currency": "USD"
                },
                  "custom": email,
            }]
        })
    
        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    return JsonResponse({'success':True,'paypal_url':link.href},status=200)
        else:
            print(payment.error)
            return JsonResponse({'success':True,'error': payment.error},status=400)


def success_paypal(request):
    global payment_result
    payment_result=0
    if request.method == 'POST':
        data = json.loads(request.body)
        payment_id = data.get('paymentId')
        payer_id = data.get('payerId')
        
        if not payment_id or not payer_id:
            return JsonResponse({'success': False, 'message': 'Missing payment details'},status=404)

        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            if payment.execute({"payer_id": payer_id}):
                print("Payment executed successfully!")
                email = payment.transactions[0].custom
                response = order_booking(request,email)
                if response.status_code == 200:  
                    print('Thêm thành công')
                    payment_result=1
                else:
                    print('Không thêm được')
                return JsonResponse({'success': True, 'message': 'Payment completed'},status=200)
            else:
                print(payment.error)
                return JsonResponse({'success': False, 'message': payment.error}, status=400)
        except Exception as e:
            print(e)
            return JsonResponse({'success': False, 'message': 'Error occurred'},status=500)

def success_zalopay(request):
    global payment_result
    payment_result=0
    if request.method == 'POST':
        data = json.loads(request.body)
        status = data.get('status')
        
        if not status:
            return JsonResponse({'success': False, 'message': 'Missing payment details'},status=404)

        if status is not None and int(status) == 1:
            payment_result=1
        else:
             payment_result=0
        return JsonResponse({'success': True, 'message': 'Payment completed'},status=200)
#-------------------------------------------------------------------------------------
@authenticate_token
@check_role(allowed_roles=['customer'])
def clear_cart(request):
    email_user=request.user['email']
    customer_info=customer.objects.filter(user_id__email=email_user).first()
    if not customer_info:
        return JsonResponse({'success':False, 'error':'Customer not found'},status=404)
    current_date = now().date()
    expired_items = cart.objects.filter(idcustomer=customer_info.idcustomer).filter(Q(check_in_date__lt=current_date) | Q(check_out_date__lt=current_date))
    deleted_count, _ = expired_items.delete()
 
    lst_cart=cart.objects.filter(idcustomer=customer_info.idcustomer)

    for order in lst_cart:
        if not can_book_room(order.idroom.idroom, order.check_in_date, order.check_out_date):
            order.delete()            
    return JsonResponse({'success': True, 'message': 'Delete exprired items successful!','delete_count':deleted_count})

@authenticate_token
@check_role(allowed_roles=['customer'])
def my_order(request):
    email_user=request.user['email']
    customer_info=customer.objects.filter(user_id__email=email_user).first()
    if not customer_info:
        return JsonResponse({'success':False, 'error':'Customer not found'},status=404)
    orders=booking.objects.filter(idcustomer=customer_info.idcustomer).select_related('idcustomer')
    upcoming_orders=orders.filter(iscomplete=False,iscancel=False).prefetch_related(Prefetch(
                                'booking_detail_set', 
                                queryset=booking_detail.objects.filter(iscancel=False).select_related('idroom')
                        .prefetch_related('idroom__utility_set','idroom__capacity_set').order_by('-iddetail') 
            )).order_by('-idbook')
    complete_orders=orders.filter(iscomplete=True).prefetch_related(Prefetch(
                                'booking_detail_set', 
                                queryset=booking_detail.objects.filter(iscancel=False).select_related('idroom')
                        .prefetch_related('idroom__utility_set','idroom__capacity_set').order_by('-iddetail') 
            )).order_by('-idbook')
    cancel_orders=orders.filter(iscancel=True).prefetch_related(Prefetch(
                                'booking_detail_set', 
                                queryset=booking_detail.objects.filter(iscancel=True).select_related('idroom')
                        .prefetch_related('idroom__utility_set','idroom__capacity_set').order_by('-iddetail') 
            )).order_by('-idbook')
    upcoming=[]
    complete=[]
    cancel=[]
    for order in upcoming_orders:
        bookings = {
            "idbook": order.idbook,
            "customer": order.idcustomer.user_id.name,
            "payment": order.idpayment.payment_name,
            "total_cost":order.total_cost,
            "state":order.state,
            "details":[],
            }
        for detail in order.booking_detail_set.all():
            room = detail.idroom
            room_info={
                'iddetail':detail.iddetail,
                'idroom':room.idroom,
                'type_room':room.idtyperm.type_room,
                'hotel':room.idtyperm.idhotel.htl_name,
                'hotel_img':room.idtyperm.idhotel.htl_img,
               'partner_email':str(room.idtyperm.idhotel.idpartner.user_id.email.email),
                 'partner_phone':room.idtyperm.idhotel.idpartner.user_id.phonenumber,
                'room_img':room.idtyperm.room_img,
                'area':room.idtyperm.area,
                'bed':room.idtyperm.bed,
                'address':room.idtyperm.idhotel.address,
                'price': room.price_only_day,
                'price_total':((detail.date_leave - detail.date_arrive).days)*room.price_only_day,
                'utilities': [{'service_name': util.idsv.service} for util in room.utility_set.all()],
                'capacities': [{'type_person': cap.idtypecusm.type_customer, 'quantity': cap.quantity} for cap in room.capacity_set.all()],
                'date_arrive':detail.date_arrive,
                'date_leave':detail.date_leave,
                'status':detail.status,
            }
            bookings['details'].append(room_info)
        upcoming.append(bookings)
    for order in complete_orders:
            bookings = {
                "idbook": order.idbook,
                "customer": order.idcustomer.user_id.name,
                "payment": order.idpayment.payment_name,
                "total_cost":order.total_cost,
                "state":order.state,
                "details":[],
                }
            for detail in order.booking_detail_set.all():
                room = detail.idroom
                room_info={
                    'iddetail':detail.iddetail,
                    'is_review':detail.is_review,
                    'idroom':room.idroom,
                    'type_room':room.idtyperm.type_room,
                    'hotel':room.idtyperm.idhotel.htl_name,
                    'hotel_img':room.idtyperm.idhotel.htl_img,
                    'partner_email':str(room.idtyperm.idhotel.idpartner.user_id.email.email),
                    'partner_phone':room.idtyperm.idhotel.idpartner.user_id.phonenumber,
                    'room_img':room.idtyperm.room_img,
                    'area':room.idtyperm.area,
                    'bed':room.idtyperm.bed,
                    'address':room.idtyperm.idhotel.address,
                    'price': room.price_only_day,
                    'price_total':((detail.date_leave - detail.date_arrive).days)*room.price_only_day,
                    'utilities': [{'service_name': util.idsv.service} for util in room.utility_set.all()],
                    'capacities': [{'type_person': cap.idtypecusm.type_customer, 'quantity': cap.quantity} for cap in room.capacity_set.all()],
                    'date_arrive':detail.date_arrive,
                    'date_leave':detail.date_leave,
                    'status':detail.status,
                }
                bookings['details'].append(room_info)
            complete.append(bookings)
    for order in cancel_orders:
                bookings = {
                    "idbook": order.idbook,
                    "customer": order.idcustomer.user_id.name,
                    "payment": order.idpayment.payment_name,
                    "total_cost":order.total_cost,
                    "state":order.state,
                    "details":[],
                    }
                for detail in order.booking_detail_set.all():
                    room = detail.idroom
                    room_info={
                        'iddetail':detail.iddetail,
                        'idroom':room.idroom,
                        'type_room':room.idtyperm.type_room,
                        'hotel':room.idtyperm.idhotel.htl_name,
                        'hotel_img':room.idtyperm.idhotel.htl_img,
                        'partner_email':str(room.idtyperm.idhotel.idpartner.user_id.email.email),
                        'partner_phone':room.idtyperm.idhotel.idpartner.user_id.phonenumber,
                        'room_img':room.idtyperm.room_img,
                        'area':room.idtyperm.area,
                        'bed':room.idtyperm.bed,
                        'address':room.idtyperm.idhotel.address,
                        'price': room.price_only_day,
                        'price_total':((detail.date_leave - detail.date_arrive).days)*room.price_only_day,
                        'utilities': [{'service_name': util.idsv.service} for util in room.utility_set.all()],
                        'capacities': [{'type_person': cap.idtypecusm.type_customer, 'quantity': cap.quantity} for cap in room.capacity_set.all()],
                        'date_arrive':detail.date_arrive,
                        'date_leave':detail.date_leave,
                        'status':detail.status,
                    }
                    bookings['details'].append(room_info)
                cancel.append(bookings)
    return JsonResponse({'success': True, 'upcoming': upcoming,'complete':complete,'cancel':cancel})
@authenticate_token
@check_role(allowed_roles=['customer','partner'])
def cancel_order_or_room(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        book_id = data.get('idbook')
        detail_id = data.get('iddetail')  

        try:
            order = booking.objects.get(idbook=book_id)
        except booking.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Not found order to cancel'}, status=404)

        if detail_id:
            canceled_room = booking_detail.objects.filter(iddetail=detail_id).first() 
            if canceled_room:
                room_price = canceled_room.idroom.price_only_day
                updated_rows = booking_detail.objects.filter(iddetail=detail_id, iscancel=False).update(iscancel=True,status='Canceled')

                if updated_rows == 0:
                    return JsonResponse({'success': False, 'error': 'Room not found or already canceled'}, status=400)

                remaining_rooms = booking_detail.objects.filter(idbook=book_id, iscancel=False).count()
                if remaining_rooms == 0:
                    order.iscancel = True
                    order.state='Canceled'
                else:
                    order.total_cost = max(order.total_cost - room_price, 0)
                order.save()
        else:
            order.iscancel = True
            order.state='Canceled'
            order.save()
            booking_detail.objects.filter(idbook=book_id, iscancel=False).update(iscancel=True,status='Canceled')

        return JsonResponse({'success': True, 'message': 'Cancellation successful'}, status=200)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
@authenticate_token
@check_role(allowed_roles=['customer'])
def add_review(request):
    if request.method == 'POST':
        email_user=request.user['email']
        customer_info=customer.objects.filter(user_id__email=email_user).first()
        if not customer_info:
            return JsonResponse({'success': False, 'error': 'Not found account'}, status=404)
        data = json.loads(request.body.decode('utf-8'))
        score_clean = data.get('clean')
        score_utility = data.get('utility')  
        score_location = data.get('location')
        score_service=data.get('service')
        score_cost=data.get('satisfy')
        title=data.get('title')
        commend=data.get('commend')
        detail_id = data.get('iddetail') 
        detail_instance = booking_detail.objects.get(iddetail=detail_id) 
        rating.objects.create(
                iddetail= detail_instance,
                score_clean = score_clean,
                score_utility = score_utility ,
                score_location = score_location,
                score_service=score_service,
                score_cost=score_cost,
                title=title,
                commend=commend,
                rate = round((float(score_clean) + float(score_utility) + float(score_location) +
                float(score_service) + float(score_cost)) / 5, 1)
        )
        detail_instance.is_review=True
        detail_instance.save()
        return JsonResponse({'success': True, 'message': 'Thank you for leave your review!'}, status=200)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
@authenticate_token
@check_role(allowed_roles=['customer'])
def lst_review(request):
        email_user=request.user['email']
        customer_info=customer.objects.filter(user_id__email=email_user).first()
        if not customer_info:
            return JsonResponse({'success': False, 'error': 'Not found account'}, status=404)
        reviews=rating.objects.filter(iddetail__idbook__idcustomer=customer_info.idcustomer).order_by('-idrate')
        show_review=[]
        for review in reviews:
               rate = {
                        "customer": review.iddetail.idbook.idcustomer.user_id.name,
                        'email':review.iddetail.idbook.idcustomer.user_id.email.email,
                        'type_room':review.iddetail.idroom.idtyperm.type_room,
                        'hotel':review.iddetail.idroom.idtyperm.idhotel.htl_name,
                        'hotel_img':review.iddetail.idroom.idtyperm.idhotel.htl_img,
                        'room_img':review.iddetail.idroom.idtyperm.room_img,
                        'area':review.iddetail.idroom.idtyperm.area,
                        'bed':review.iddetail.idroom.idtyperm.bed,
                        'address':review.iddetail.idroom.idtyperm.idhotel.address,
                        'price':review.iddetail.idroom.price_only_day,
                        'price_total': (review.iddetail.date_leave - review.iddetail.date_arrive).days*review.iddetail.idroom.price_only_day,
                        'utilities': [{'service_name': util.idsv.service} for util in review.iddetail.idroom.utility_set.all()],
                        'capacities': [{'type_person': cap.idtypecusm.type_customer, 'quantity': cap.quantity} for cap in review.iddetail.idroom.capacity_set.all()],
                        'date_arrive':review.iddetail.date_arrive,
                        'date_leave':review.iddetail.date_leave,
                        'score_clean':review.score_clean,
                        'score_utility': review.score_utility ,
                        'score_location': review.score_location,
                        'score_service': review.score_service,
                        'score_cost': review.score_cost,
                        'title':review.title,
                        'commend':review.commend,
                        'rate':review.rate,
                        'created_at':review.created_at,
                    }
               show_review.append(rate)
        return JsonResponse({'success': True,'review':show_review}, status=200)

def show_review(request,id):
        reviews=rating.objects.filter(iddetail__idroom__idtyperm__idhotel=id)
        show_review=[]
        for review in reviews:
               rate = {
                        "customer": review.iddetail.idbook.idcustomer.user_id.name,
                        'email':review.iddetail.idbook.idcustomer.user_id.email.email,
                        'type_room':review.iddetail.idroom.idtyperm.type_room,
                        'hotel':review.iddetail.idroom.idtyperm.idhotel.htl_name,
                        'hotel_img':review.iddetail.idroom.idtyperm.idhotel.htl_img,
                        'room_img':review.iddetail.idroom.idtyperm.room_img,
                        'area':review.iddetail.idroom.idtyperm.area,
                        'bed':review.iddetail.idroom.idtyperm.bed,
                        'address':review.iddetail.idroom.idtyperm.idhotel.address,
                        'price': review.iddetail.idroom.price_only_day,
                        'utilities': [{'service_name': util.idsv.service} for util in review.iddetail.idroom.utility_set.all()],
                        'capacities': [{'type_person': cap.idtypecusm.type_customer, 'quantity': cap.quantity} for cap in review.iddetail.idroom.capacity_set.all()],
                        'date_arrive':review.iddetail.date_arrive,
                        'date_leave':review.iddetail.date_leave,
                        'days': (review.iddetail.date_leave - review.iddetail.date_arrive).days,
                        'score_clean':review.score_clean,
                        'score_utility': review.score_utility ,
                        'score_location': review.score_location,
                        'score_service': review.score_service,
                        'score_cost': review.score_cost,
                        'title':review.title,
                        'commend':review.commend,
                        'rate':review.rate,
                        'created_date':review.created_at
                    }
               show_review.append(rate)
        return JsonResponse({'success': True,'review':show_review}, status=200)

@authenticate_token
@check_role(allowed_roles=['customer'])
def re_book_order(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        items = data.get('bookingData', [])
        email_user = request.user['email']
        customer_info = customer.objects.filter(user_id__email=email_user).first()

        if not customer_info:
            return JsonResponse({'success': False, 'error': 'Customer not found'}, status=404)

        errors = []
        for selected_item in items:
            room = room_detail.objects.filter(idroom=selected_item['room_id']).first()
            check_date_start = datetime.strptime(selected_item['date_arrive'], "%Y-%m-%d").date()
            check_date_end = datetime.strptime(selected_item['date_leave'], "%Y-%m-%d").date()
            print(can_book_room(selected_item['room_id'],check_date_start,check_date_end))
            if not room:
                errors.append(f"Phòng ID {selected_item['room_id']} không tồn tại.")
            elif not can_book_room(selected_item['room_id'],check_date_start,check_date_end):
                errors.append(f"{room.idtyperm.type_room} không thể đặt vào {selected_item['date_arrive']} - {selected_item['date_leave']}")

        if errors:
            print(errors)
            return JsonResponse({'success': False, 'errors': errors}, status=400)

        for selected_item in items:
            room = room_detail.objects.filter(idroom=selected_item['room_id']).first()
            try:
                cart.objects.create(
                    idroom=room,
                    idcustomer=customer_info,
                    check_in_date=selected_item['date_arrive'],
                    check_out_date=selected_item['date_leave']
                )
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)

        return JsonResponse({'success': True, 'message': 'Re add room to cart successful!'}, status=201)

    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
