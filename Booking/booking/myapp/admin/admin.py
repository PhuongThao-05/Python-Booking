from collections import defaultdict
from datetime import date, datetime
from django.contrib import admin
from django.db.models import Q
# Register your models here.
import json
from django.contrib import messages
from django.contrib import admin
from django.http import JsonResponse
import pytz
from django.core.paginator import Paginator
from myapp.authentication import authenticate_token, check_role
from myapp.models import account, booking, booking_detail, hotels, role,users
from myapp.shared_features import send_notification_email
from myapp.utils import check_token_validity, generate_jwt_token
from django.db.models import Exists, OuterRef, Max,Count,Sum
from datetime import date
import pandas as pd
def admin_login_page(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON format'}, status=400)

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return JsonResponse({'success': False, 'error': 'Email and password are required'}, status=400)

        try:
            user = account.objects.get(email=email)
        except account.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Account does not exist'}, status=404)
        try:
            role_user = role.objects.get(idrole=user.idrole.idrole)
        except role.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Role not found'}, status=404)
  
        if role_user.role_name == 'admin':
            if user.password == password:
                if user.token and check_token_validity(user.token):
                    messages.success(request, "Token is valid.")
                else:
                    access_token = generate_jwt_token(user.email, role_user.role_name)
                    user.token = access_token
                    user.save()
                return JsonResponse({'success': True, 'message': 'Login admin page successful!','token':user.token}, status=200)
            else:
                return JsonResponse({'success': False, 'error': 'Password invalid'}, status=400) 
        else:
            return JsonResponse({'success': False, 'error': 'Account unauthorized'}, status=403)

@authenticate_token
@check_role(allowed_roles=['admin'])   
def get_list_users(request):
    search_query = request.GET.get('search', '').strip()
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 5)) 

    acc = account.objects.filter(idrole__idrole__gt=1).select_related('idrole').prefetch_related('users').order_by('-users__user_id')
    if search_query:
        acc = acc.filter(Q(email__icontains=search_query)|Q(users__name__icontains=search_query))
    if not acc.exists():
        return JsonResponse({'success': True,'total_pages': 1,'current_page': page, 'list_user': []}, status=200)
    
    paginator = Paginator(acc, limit)
    accs_page = paginator.get_page(page)

    if not accs_page:
        return JsonResponse({'success': False, 'message': 'Users not found!'}, status=404)

    list_user = []
    for a in accs_page:
        account_info = {
            'email': a.email,
            'is_active':a.is_active,
            'role': {
                'role_name': a.idrole.role_name if a.idrole else None,
                'profession': a.idrole.profession if a.idrole else None,
            },
            'user': {}
        }

        if hasattr(a, 'users'):
            user_info = {
                'name': a.users.name,
                'phonenumber': a.users.phonenumber,
            }
            account_info['user'] = user_info

        list_user.append(account_info)
    return JsonResponse({'success': True,'total_pages': paginator.num_pages,
        'current_page': page, 'list_user': list_user}, status=200)


@authenticate_token
@check_role(allowed_roles=['admin'])   
def get_list_hotels(request):
    search_query = request.GET.get('search', '').strip()
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 3)) 

    hotels_list = hotels.objects.filter(is_delete=False).select_related('idpartner').prefetch_related(
        'type_room_set__room_detail_set__utility_set',
        'type_room_set__room_detail_set__capacity_set'
    ).order_by('-idhotel')
    
    if not hotels_list.exists():
        return JsonResponse({'success': False, 'message': 'Hotels not found!'}, status=404)
    
    if search_query:
        hotels_list = hotels_list.filter(htl_name__icontains=search_query)
  
    paginator = Paginator(hotels_list, limit)
    hotels_page = paginator.get_page(page)

    if not hotels_page:
        return JsonResponse({'success': False, 'message': 'Hotels not found!'}, status=404)

    hotel_data = []
    for hotel in hotels_page:
        owner = hotel.idpartner.user_id if hotel.idpartner and hotel.idpartner.user_id else None
        owner_name = owner.name if owner else 'N/A'
        hotel_info = {
            'idhotel':hotel.idhotel,
            'hotel_name': hotel.htl_name,
            'hotel_image':hotel.htl_img,
            'hotel_address':hotel.address,
            'begin_price':hotel.begin_price,
            'is_confirm':hotel.is_confirm,
            'owner':owner_name,
            'type_rooms': []
        }
        for typeroom in hotel.type_room_set.all():
            type_room_info = {
                'type_name': typeroom.type_room,
                'area':typeroom.area,
                'room_img':typeroom.room_img,
                'bed':typeroom.bed,
                'rooms': []
            }
            for room in typeroom.room_detail_set.all():
                room_info = {
                    'idroom':room.idroom,
                    'price': room.price_only_day,
                    'utilities': [{'service_name': utility.idsv.service} for utility in room.utility_set.all()],
                    'capacities': [{'type_person': cap.idtypecusm.type_customer, 'quantity': cap.quantity} for cap in room.capacity_set.all()]
                }
                type_room_info['rooms'].append(room_info)
            hotel_info['type_rooms'].append(type_room_info)
        hotel_data.append(hotel_info)

    return JsonResponse({'success': True, 'total_pages': paginator.num_pages,
        'current_page': page, 'hotels': hotel_data}, status=200)

@authenticate_token
@check_role(allowed_roles=['admin'])
def confirm_hotel(request, id):
        try:
            hotel = hotels.objects.filter(idhotel=id).first()
            if not hotel:
                return JsonResponse({'success': False, 'error': 'Hotel does not exist.'}, status=404)
            if request.method == 'POST':
                if hotel.is_confirm==False:
                    hotel.is_confirm=True
                    hotel.save()
                else:
                    hotel.is_confirm=False
                    hotel.save()
                return JsonResponse({'success': True, 'message': 'Hotel confirmed successfully!'}, status=200)
            if request.method == 'GET':
                return JsonResponse({'success': True, 'confirm': hotel.is_confirm}, status=200)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@authenticate_token
@check_role(allowed_roles=['admin'])
def lock_account(request, email):
        try:
            acc = account.objects.filter(email=email).first()
            if not acc:
                return JsonResponse({'success': False, 'error': 'Account does not exist.'}, status=404)
            if request.method == 'POST':
                if acc.is_active==True:
                    acc.is_active=False
                    acc.save()
                else:
                    acc.is_active=True
                    acc.save()
                return JsonResponse({'success': True, 'message': 'Account is locked!'}, status=200)
            if request.method == 'GET':
                return JsonResponse({'success': True, 'is_active': acc.is_active}, status=200)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
@authenticate_token
@check_role(allowed_roles=['admin'])
def list_order(request):
    search_query = request.GET.get('search', '').strip()
    date_arrive=request.GET.get('arrive','').strip()
    date_leave=request.GET.get('leave','').strip()
    status=request.GET.get('status','').strip()
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 3)) 
    orders=booking_detail.objects.order_by('-iddetail')
    if search_query:
        orders = orders.filter( Q(idbook__idcustomer__user_id__name__icontains=search_query) |
    Q(idroom__idtyperm__idhotel__htl_name__icontains=search_query))
    
    if date_arrive and date_leave:
        date_arrive = datetime.strptime(date_arrive, "%Y-%m-%d").date()
        date_leave = datetime.strptime(date_leave, "%Y-%m-%d").date()
        orders = orders.filter(date_arrive=date_arrive, date_leave=date_leave)
    elif date_arrive:
        date_arrive = datetime.strptime(date_arrive, "%Y-%m-%d").date()
        orders = orders.filter(date_arrive=date_arrive)
    elif date_leave:
        date_leave = datetime.strptime(date_leave, "%Y-%m-%d").date()
        orders = orders.filter(date_leave=date_leave)

    if status:
        orders = orders.filter(status=status)

    paginator = Paginator(orders, limit)
    orders_page = paginator.get_page(page)

    lst_order=[]
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    for order in orders_page:
        bookings = {
            "idbook": order.idbook.idbook,
            'idpayment':order.idbook.idpayment.idpayment,
            "customer": order.idbook.idcustomer.user_id.name,
            "payment": order.idbook.idpayment.payment_name,
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
                'date_payment':order.date_payment.astimezone(tz).strftime("%Y-%m-%d %H:%M") if order.date_payment else None,
                'status':order.status
            }
        bookings['details'].append(room_info)
        lst_order.append(bookings)
    
    return JsonResponse({'success': True,'total_pages': paginator.num_pages,
        'current_page': page, 'order':lst_order})
@authenticate_token
@check_role(allowed_roles=['admin'])
def update_status_order(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        book_id = data.get('idbook')
        detail_id = data.get('iddetail')  
        status=data.get('new_status')
        datepayment=data.get('datepayment')
        try:
            order = booking.objects.get(idbook=book_id)
        except booking.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Not found order to update'}, status=404)

        if detail_id:
            updated_room = booking_detail.objects.filter(iddetail=detail_id).first() 
            if updated_room:
                if status == 'Completed':
                    if  booking_detail.objects.filter(iddetail=detail_id, idbook__idpayment=2).exists():
                        if datepayment:
                            tz = pytz.timezone("Asia/Ho_Chi_Minh")
                            date_payment = tz.localize(datetime.strptime(datepayment, "%Y-%m-%d %H:%M:%S"))
                            updated_rows = booking_detail.objects.filter(iddetail=detail_id).update(status=status,date_payment=date_payment)
                        else:
                            tz = pytz.timezone("Asia/Ho_Chi_Minh")
                            date_payment = datetime.now(tz)
                            updated_rows = booking_detail.objects.filter(iddetail=detail_id).update(status=status,date_payment=date_payment)
                    else:
                       updated_rows = booking_detail.objects.filter(iddetail=detail_id).update(status=status) 
                if status == 'Canceled':
                    updated_rows = booking_detail.objects.filter(iddetail=detail_id).update(status=status, iscancel=True) 
                if updated_rows == 0:
                    return JsonResponse({'success': False, 'error': 'Room not found or already updated'}, status=400)
             
                if booking_detail.objects.filter(idbook=book_id,status="Completed").count() == booking_detail.objects.filter(idbook=book_id).count():
                    order.state = 'Completed'
                    order.iscomplete=True
                    order.save()
                if booking_detail.objects.filter(idbook=book_id,status="Canceled", iscancel=True).count() == booking_detail.objects.filter(idbook=book_id).count():
                    order.state = 'Canceled'
                    order.iscancel=True
                    order.save()
            return JsonResponse({'success': True, 'message': 'Update status successful'}, status=200)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@authenticate_token
@check_role(allowed_roles=['admin'])
def revenue_report(request):
    now = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
    data = json.loads(request.body.decode('utf-8'))
    month = data.get("month")  
    year = data.get("year", now.year) 

    try:
        year = int(year)
        month = int(month) if month else None 
        print('year',year)
        print('month',month)
    except ValueError:
        return JsonResponse({"success": False, "error": "Invalid month or year"}, status=400)

    all_hotels = hotels.objects.filter(is_confirm=True).values_list("htl_name", flat=True)
    hotels_revenue = {hotel: 0 for hotel in all_hotels}

    bookings = booking_detail.objects.filter(status='Completed', date_payment__year=year)
    if month:
        bookings = bookings.filter(date_payment__month=month)  

    for booking in bookings:
        hotel_name = booking.idroom.idtyperm.idhotel.htl_name  
        stay_days = (booking.date_leave - booking.date_arrive).days
        total_price = booking.idroom.price_only_day * stay_days  

        hotels_revenue[hotel_name] += total_price 

    revenue_ranges = {
        "Dưới 100 triệu":[],
        "100 - 500 triệu":[],
        "Dưới 1 tỷ": [],
        "1 - 5 tỷ": [],
        "5 - 10 tỷ": [],
        "Trên 10 tỷ": []
    }

    for hotel_name, revenue in hotels_revenue.items():  
        hotel_info = {"name": hotel_name, "revenue": revenue}
        if revenue < 100_000_000:
            revenue_ranges["Dưới 100 triệu"].append(hotel_info)
        elif revenue < 500_000_000:
            revenue_ranges["100 - 500 triệu"].append(hotel_info)
        elif revenue < 1_000_000_000:
            revenue_ranges["Dưới 1 tỷ"].append(hotel_info)
        elif revenue < 5_000_000_000:
            revenue_ranges["1 - 5 tỷ"].append(hotel_info)
        elif revenue < 10_000_000_000:
            revenue_ranges["5 - 10 tỷ"].append(hotel_info)
        else:
            revenue_ranges["Trên 10 tỷ"].append(hotel_info)

    return JsonResponse({ "success": True,"month": month,"year": year,"data": revenue_ranges}, status=200)
@authenticate_token
@check_role(allowed_roles=['admin'])
def hotel_traffic_report(request):
    now = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
    data = json.loads(request.body.decode('utf-8'))
    month = data.get("month")  
    year = data.get("year", now.year) 

    try:
        year = int(year)
        month = int(month) if month else None 
    except ValueError:
        return JsonResponse({"success": False, "error": "Invalid month or year"}, status=400)


    bookings = booking_detail.objects.filter(date_payment__year=year)
    if month:
        bookings = bookings.filter(date_payment__month=month)  

    hotel_traffic = defaultdict(lambda: {"completed": 0, "canceled": 0})
    for booking in bookings:
        hotel_name = booking.idroom.idtyperm.idhotel.htl_name  
        if booking.status == 'Completed':
            hotel_traffic[hotel_name]["completed"] += 1
        elif booking.status == 'Canceled':
            hotel_traffic[hotel_name]["canceled"] += 1


    top_completed = sorted(hotel_traffic.items(), key=lambda x: x[1]["completed"], reverse=True)[:10]
    top_canceled = sorted(hotel_traffic.items(), key=lambda x: x[1]["canceled"], reverse=True)[:10]

    return JsonResponse({
        "success": True,
        "month": month,  
        "year": year,
        "top_completed": dict(top_completed),
        "top_canceled": dict(top_canceled)
    }, status=200)

@authenticate_token
@check_role(allowed_roles=['admin'])
def get_month_and_year(request):
    bookings_year = booking_detail.objects.values_list('date_payment__year', flat=True).exclude(date_payment__isnull=True).distinct().order_by('-date_payment__year')
    bookings_month = booking_detail.objects.values_list('date_payment__month', flat=True).exclude(date_payment__isnull=True).distinct().order_by('-date_payment__month')
    
    return JsonResponse({'success': True, 'month':list(bookings_month) , 'year': list(bookings_year)}, status=200)

@authenticate_token
@check_role(allowed_roles=['admin'])
def potential_customers(request):
    today = date.today()
    list_order = booking.objects.filter(
        Exists(
            booking_detail.objects.filter(
                idbook=OuterRef('idbook'),
                iscancel=False,
                status='Completed'
            )
        ),
        iscomplete=True
    ).select_related('idcustomer')
    rfm_data = list_order.values('idcustomer__user_id__email','idcustomer__user_id__name').annotate(
    recency=Max('created_at'),  # Ngày đặt đơn gần nhất
    frequency=Count('idbook', distinct=True),  # Số đơn hàng hoàn thành
    monetary=Sum(
        booking_detail.objects.filter(
            idbook=OuterRef('idbook'),
            iscancel=False,
            status='Completed'
        ).values('idbook').annotate(total=Sum('idroom__price_only_day')).values('total')  # Lấy tổng tiền từ chi tiết đã hoàn thành
    )
    )
    
    # Chuyển dữ liệu thành DataFrame để xử lý RFM Score
    df_rfm = pd.DataFrame(list(rfm_data))
    df_rfm.rename(columns={'idcustomer__user_id__email': 'customer_email'}, inplace=True)
    df_rfm.rename(columns={'idcustomer__user_id__name': 'customer_name'}, inplace=True)
    df_rfm['recency'] = df_rfm['recency'].apply(lambda x: (today - x.date()).days)  # Đổi thành số ngày

    # Tính điểm RFM (xếp hạng)
    df_rfm['r_rank'] = df_rfm['recency'].rank(ascending=True)  # Gần nhất -> điểm cao
    df_rfm['f_rank'] = df_rfm['frequency'].rank(ascending=False)  # Mua nhiều -> điểm cao
    df_rfm['m_rank'] = df_rfm['monetary'].rank(ascending=False)  # Chi tiêu nhiều -> điểm cao

    df_rfm['rfm_score'] = df_rfm['r_rank'] + df_rfm['f_rank'] + df_rfm['m_rank']

    top_customers = df_rfm[df_rfm['recency'] <= df_rfm['recency'].median()].nsmallest(len(df_rfm) // 2, 'rfm_score')

    inactive_customers = df_rfm.nlargest(len(df_rfm) // 2, 'recency')
    inactive_customers = inactive_customers.loc[~inactive_customers['customer_email'].isin(top_customers['customer_email'])]

    print(top_customers.to_dict(orient='records'))
    print(inactive_customers.to_dict(orient='records'))
    return JsonResponse({
        'success': True,
        'top_customers': top_customers.to_dict(orient='records'),
        'inactive_customers': inactive_customers.to_dict(orient='records')
    }, status=200)

@authenticate_token
@check_role(allowed_roles=['admin'])
def send_email_to_hotel(request):
    data=json.loads(request.body.decode('utf-8'))
    title=data.get('title')
    message=data.get('message')
    emails=data.get('emails',[])
    for email in emails:
        send_notification_email(title,message,email)
    return JsonResponse({'success': True, 'message': 'Send email successfully!'},status=200)



