import random
from django_seed import Seed

from myapp.utils import generate_jwt_token
from .models import account, users, partner, hotels, type_room, room_detail,role
from django.contrib.auth.hashers import make_password
def seed_acount():
    seeder = Seed.seeder()
    roles = list(role.objects.all())
    seeder.add_entity(account, 5, { 
       'email': lambda x: seeder.faker.email(),  # Tạo email giả lập
       'password': lambda x: make_password(seeder.faker.password(length=6)), 
       'idrole': lambda x: random.choice(roles),  # Chọn ngẫu nhiên một Role
        'token': lambda x: generate_jwt_token(
            email=seeder.faker.email(),  # Email giả lập
            role=random.choice(roles).role_name  # Lấy role_name từ Role ngẫu nhiên
        ),
    })
    seeder.execute()
    print("Acount seeded.")
def seed_users():
    seeder = Seed.seeder()

    # Lấy tất cả các account instances
    accounts = list(account.objects.all())

    # Danh sách các account chưa được sử dụng
    unused_accounts = accounts.copy()

    def generate_unique_account():
        """Lấy một account ngẫu nhiên từ danh sách chưa sử dụng."""
        if not unused_accounts:
            raise ValueError("Không còn account nào chưa được sử dụng.")
        account = random.choice(unused_accounts)
        unused_accounts.remove(account)  
        return account

    seeder.add_entity(users, len(accounts), {  # Tạo users với số lượng bằng số account
        'email': lambda x: generate_unique_account(),  # Gán account instance
        'name': lambda x: seeder.faker.name(),
        'phonenumber': lambda x: seeder.faker.random_number(digits=10, fix_len=True),  # Số điện thoại ngẫu nhiên
    })

    seeder.execute()
    print("Users seeded with unique emails.")

def seed_partner():
    seeder = Seed.seeder()

    # Lấy danh sách users có role là "partner"
    userslist = list(users.objects.filter(email__idrole__role_name="partner"))
    if not userslist:
        print("Không có user nào với role là 'partner'.")
        return

    # Copy danh sách users chưa được sử dụng
    unused_userslist = userslist[:]

    def generate_unique_partner():
        if not unused_userslist:
            raise ValueError("Không còn partner nào chưa được sử dụng.")
        user = random.choice(unused_userslist)
        unused_userslist.remove(user)
        return user

    # Thêm dữ liệu vào bảng partner
    seeder.add_entity(partner, len(userslist), { 
        'user_id': lambda x: generate_unique_partner()
    })

    seeder.execute()
    print("Partner seeded.")

def seed_hotel():
    seeder = Seed.seeder()

    partners = list(partner.objects.all())

    seeder.add_entity(hotels, 5, { 
        'htl_name': lambda x: seeder.faker.word(),  
        'htl_img': lambda x: "partner/upload/a17da9dba758f7f9fcbca15dceab565a.jpg", 
        'address': lambda x: seeder.faker.address(), 
        'description': lambda x: seeder.faker.text(max_nb_chars=100), 
        'idpartner': lambda x: random.choice(partners),  
    })

    seeder.execute()
    print("Hotels seeded.")


