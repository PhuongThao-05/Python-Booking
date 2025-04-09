# Create your views here.
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
import requests
from booking import settings
from myapp.authentication import authenticate_token, check_role
from myapp.utils import check_token_validity, generate_jwt_token
from .forms import RegisterForm, UserInfoForm
from .models import account, users, role,hotels,partner,customer
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from .page.page_customer import (set_role,customer_home,
                   customer_hotels,customer_detail_hotel,customer_cart,customer_order,
                    customer_cart_to_order,customer_profile,customer_pay_return,customer_my_order,customer_review)
from .page.page_partner import ( partner_home,partner_hotel,partner_add_hotel,partner_get_typeroom,
                    partner_add_typeroom,partner_get_room, partner_add_room, partner_edit_hotel, partner_profile,partner_order,partner_statistic,
                    partner_edit_typeroom,partner_edit_room,)
from .page.page_admin import (admin_home,admin_login,admin_manage_user,admin_manage_hotel,admin_manage_order,admin_revenue_report,admin_traffic_report,
                              admin_customer_report)
from .partner.partner_features import (get_list_hotel,add_hotel,upload_image,get_list_typeroom,add_typeroom,
                               get_list_room,get_list_utitlity,add_room,edit_hotel,delete_hotel,edit_profile,edit_typeroom,delete_typeroom,edit_room,
                               delete_room,lst_order,update_status_room,get_month_and_hotel,revenue_by_month)
from .customer.customer_features import (list_hotel,detail_hotel,count_item_cart,add_to_cart,list_in_cart,delete_item_cart,item_order,store_cart,clear_cart,
                                show_store_cart,customer_edit_profile,item_booking,order_booking,return_page,success_paypal,success_zalopay,
                                zalo_payment, callback, create_momo_payment, handle_payment_momo_callback,payment_paypal, my_order,cancel_order_or_room,
                                add_review,lst_review,show_review,re_book_order)
from .admin.admin import (admin_login_page,get_list_users,get_list_hotels,confirm_hotel,lock_account,list_order,update_status_order,
                    revenue_report,hotel_traffic_report,get_month_and_year,potential_customers,send_email_to_hotel,
                    )
@authenticate_token
def check_token_acc(request):
    return JsonResponse({'message': 'Bạn đã xác thực thành công!', 'user': request.user})

def google_callback(request):
    code = request.GET.get('code')
    if not code:
        return JsonResponse({'error': 'No code provided'}, status=400)

    # Lấy access token từ Google
    token_url = 'https://oauth2.googleapis.com/token'
    token_data = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': 'http://127.0.0.1:8000/google-callback',
        'grant_type': 'authorization_code',
        'code': code,
    }
    token_response = requests.post(token_url, data=token_data)
    token_json = token_response.json()

    if 'access_token' not in token_json:
        return JsonResponse({'error': 'Failed to retrieve access token'}, status=400)

    access_token = token_json['access_token']

    # Lấy thông tin user từ Google
    userinfo_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
    headers = {'Authorization': f'Bearer {access_token}'}
    userinfo_response = requests.get(userinfo_url, headers=headers)
    userInfo = userinfo_response.json()

    existingUser = account.objects.filter(email=userInfo['email']).first()

    if existingUser is None:
        new_account = account.objects.create(email=userInfo['email'])
        user_new = users.objects.create(email=new_account, name=userInfo['name'])
        customer.objects.create(user_id=user_new)
        return redirect(f'/set-role?email={userInfo["email"]}')
    else:
        role_user = role.objects.get(idrole=existingUser.idrole.idrole)
        user_info = users.objects.get(email=existingUser.email)

        if not existingUser.is_active:
            return JsonResponse({'success': False, 'error': 'Your account is locked!'}, status=405)

        # Kiểm tra token
        if not existingUser.token or not check_token_validity(existingUser.token):
            existingUser.token = generate_jwt_token(existingUser.email, role_user.role_name)
            existingUser.save()

        user_data = {
            'token': existingUser.token,
            'name': user_info.name,
            'role': role_user.role_name,
        }
        return render(request, "user/login-google.html", {"user_info": json.dumps(user_data)})
    
def add_role(request):
    if request.method== 'POST':
        data=json.loads(request.body.decode('utf-8'))
        email=data.get('email')
        idrole=data.get('idrole')
        existingUser = account.objects.filter(email=email).first()
        if existingUser is None:
            return JsonResponse({'success':False,'error':'Not found account'},status=404)
        role_instance = role.objects.filter(idrole=idrole).first()
        if role_instance:
            existingUser.idrole = role_instance 
            existingUser.token = generate_jwt_token(existingUser.email, role_instance.role_name)
            existingUser.save()
        updated_user = account.objects.get(email=existingUser.email) 
        user_info = users.objects.get(email=email)
        print(role_instance)
        user_data = {
            'token': updated_user.token,
            'name': user_info.name,
            'role': role_instance.role_name,
        }
        message = 'Welcome! Login successful!' if role_instance.role_name == 'partner' else 'Login successful!'

        return JsonResponse({'success': True, 'message': message, 'user_info': user_data}, status=200)
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            idrole = form.cleaned_data['idrole']

            role_user = role.objects.get(idrole=idrole.idrole) 
            token = generate_jwt_token(email,role_user.role_name)
            hashed_password = make_password(password)
            account.objects.create(
                email=email,
                password= hashed_password,
                idrole=idrole,
                token=token
            )
            messages.success(request, "Account registered successfully!")
            user = account.objects.get(email=email)
            request.session['email'] = user.email
            return redirect('userinfo')
    else:
        form = RegisterForm()
    roles=role.objects.filter(idrole__gt=1)
    return render(request, 'user/register.html', {'form': form,'roles':roles})

def user_info(request):
    email = request.session.get('email')  
    if not email:
         messages.error(request, "Account does not exist")
    user_account = account.objects.get(email=email)
    user = users.objects.filter(email=user_account).first()
    if request.method == "POST":
        if not user:
            user = users(email=user_account)   
        form = UserInfoForm(request.POST, instance=user, initial_email=email)
        if form.is_valid():
            form.save()
            if user_account.idrole.role_name == 'customer':
                if not customer.objects.filter(user_id=user).exists():
                    customer.objects.create(user_id=user)
            elif user_account.idrole.role_name == 'partner': 
                if not partner.objects.filter(user_id=user).exists():
                    partner.objects.create(user_id=user)
            return redirect('login')
    else:
        form = UserInfoForm(instance=user, initial_email=email)

    return render(request, 'user/userinfo.html', {'form': form})

def login_user(request):
    if request.method == "POST":
        data=json.loads(request.body.decode('utf-8'))
        email = data.get('email')
        password = data.get('password')
        
        try:
            user = account.objects.get(email=email)
        except account.DoesNotExist:
            return JsonResponse({'success':False,'error': 'Account does not exist'},status=404)

        if check_password(password, user.password):
            messages.success(request, "Login successful!")
            user = account.objects.get(email=email)
            userinfo = users.objects.get(email=user.email) 
            role_user = role.objects.get(idrole=user.idrole.idrole) 
            
            if user.is_active == False:
                return JsonResponse({'success':False,'error': 'Your account is locked!'},status=405)   

            if user.token and check_token_validity(user.token):
                messages.success(request, "Token is valid.")
            else:
                access_token = generate_jwt_token(user.email,role_user.role_name)
                user.token = access_token  
                user.save() 
            user_data=[]  
            if role_user.role_name == 'customer':
                user_data = {
                    'token': user.token,
                    'name': userinfo.name,
                    'role': role_user.role_name,
                }
                return JsonResponse({'success':True,'message': 'Login successful!','user_info':user_data},status=200)
            elif role_user.role_name == 'partner':
                user_data = {
                    'token': user.token,
                    'name': userinfo.name,
                    'role': role_user.role_name,
                }
                return JsonResponse({'success':True,'message': 'Wellcome! Login successful!','user_info':user_data},status=200)
            else:
                return JsonResponse({'success':False,'error': 'Invalid role!'},status=405)       
        else:
           return JsonResponse({'success':False,'error': 'Invalid password!'},status=405)  
def login(request):
    return render(request, 'user/login.html')
 
