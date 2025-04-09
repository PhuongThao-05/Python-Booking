from datetime import timedelta
from celery import shared_task
from django.core.mail import send_mail
import json
from django.db.models import Q,F
from booking import settings
from myapp.models import booking_detail, room_detail

@shared_task
def send_notification_email(title,message,user_email):
    subject = title
    message = message
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user_email]

    send_mail(subject, message, from_email, recipient_list)

#Kiểm tra phòng được đặt trong khoảng thời gian này hay không
def can_book_room(room_id, check_date_start, check_date_end):
        try:
            room = room_detail.objects.get(idroom=room_id)
            total_quantity = room.quantity

            for day in range((check_date_end - check_date_start).days + 1):
                check_date = check_date_start + timedelta(days=day)

                booked_count = booking_detail.objects.filter(
                    idroom=room_id,
                    iscancel=False,
                    idbook__iscomplete=False,
                    idbook__iscancel=False,
                    date_arrive__lte=check_date,
                    date_leave__gt=check_date
                ).exclude(Q(status="Completed") | Q(status="Canceled")).count()
                if booked_count >= total_quantity:
                    return False 
            return True  
        except room_detail.DoesNotExist:
            return False  