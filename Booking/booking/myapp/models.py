from django.db import models

# Create your models here.
class role(models.Model):
    idrole = models.IntegerField(primary_key=True)
    role_name = models.TextField()
    profession = models.TextField()

    class Meta:
        db_table='role'
    def __str__(self):
        return self.role_name

class account(models.Model):
    email = models.CharField(max_length=320, primary_key=True)
    password = models.CharField(max_length=128)
    idrole = models.ForeignKey(role, on_delete=models.DO_NOTHING, null=True)
    token = models.TextField()
    is_active= models.BooleanField(default=True)
    class Meta:
        db_table='account'
    def __str__(self):
        return self.email
class users(models.Model):
    user_id = models.AutoField(primary_key=True)
    email = models.OneToOneField(account, on_delete=models.DO_NOTHING, null=True)
    name = models.TextField()
    phonenumber = models.CharField()
    class Meta:
      
        db_table='users'
    def __str__(self):
        return self.name
class partner(models.Model):
    idpartner = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(users, on_delete=models.DO_NOTHING, null=True)
    class Meta:
      
        db_table='partner'
    def __str__(self):
        return str(self.idpartner)
class hotels(models.Model):
    idhotel = models.AutoField(primary_key=True)
    htl_name = models.TextField()
    htl_img = models.TextField()
    address = models.TextField()
    description = models.TextField()
    begin_price = models.IntegerField()
    is_confirm = models.BooleanField(default=False)
    is_delete = models.BooleanField(default=False)
    idpartner = models.ForeignKey(partner, on_delete=models.DO_NOTHING, null=True)
    class Meta:
      
        db_table='hotels'
    def __str__(self):
        return self.htl_name
class type_room(models.Model):
    idtyperm = models.AutoField(primary_key=True)
    idhotel = models.ForeignKey(hotels,on_delete=models.DO_NOTHING, null=True)
    type_room=models.TextField(null=True)
    bed=models.TextField(null=True)
    area=models.FloatField(null=True)
    room_img = models.TextField()
    is_delete = models.BooleanField(default=False)
    class Meta:
      
        db_table='type_room'
    def __str__(self):
        return str(self.type_room)
class room_detail(models.Model):
    idroom = models.AutoField(primary_key=True)
    idtyperm = models.ForeignKey(type_room, on_delete=models.DO_NOTHING, null=True)
    price_only_day = models.IntegerField()
    quantity= models.IntegerField(null=True)
    class Meta:
      
        db_table='room_detail'
    def __str__(self):
        return str(self.idroom)

class service(models.Model):
    idsv = models.IntegerField(primary_key=True)
    service = models.TextField()
    class Meta:
      
        db_table='service'
    def __str__(self):
        return self.service
class utility(models.Model):
    idulty = models.AutoField(primary_key=True)
    idroom = models.ForeignKey(room_detail, on_delete=models.CASCADE, null=True)
    idsv = models.ForeignKey(service, on_delete=models.DO_NOTHING, null=True)
    class Meta:
      
        db_table='utility'
    def __str__(self):
        return str(self.idulty)
class type_customer(models.Model):
    idtypecusm = models.IntegerField(primary_key=True)
    type_customer = models.TextField()
    class Meta:
      
        db_table='type_customer'
    def __str__(self):
        return self.type_customer
class capacity(models.Model):
    idcap = models.AutoField(primary_key=True)
    idroom = models.ForeignKey(room_detail, on_delete=models.CASCADE, null=True)
    idtypecusm = models.ForeignKey(type_customer, on_delete=models.DO_NOTHING, null=True)
    quantity = models.IntegerField()
    class Meta:
      
        db_table='capacity'
    def __str__(self):
        return str(self.idcap)
class customer(models.Model):
    idcustomer = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(users, on_delete=models.DO_NOTHING, null=True)
    class Meta:
      
        db_table='customer'
    def __str__(self):
        return str(self.idcustomer)
class type_payment(models.Model):
    idpayment = models.IntegerField(primary_key=True)
    payment_name = models.TextField()
    class Meta:
      
        db_table='type_payment'
    def __str__(self):
        return self.payment_name
class booking(models.Model):
    idbook = models.AutoField(primary_key=True)
    idcustomer = models.ForeignKey(customer, on_delete=models.DO_NOTHING, null=True)
    idpayment = models.ForeignKey(type_payment, on_delete=models.DO_NOTHING, null=True)
    iscancel = models.BooleanField(default=False)
    iscomplete = models.BooleanField(default=False)
    total_cost = models.FloatField(null=True)
    state = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
      
        db_table='booking'
    def __str__(self):
        return str(self.idbook)
class booking_detail(models.Model):
    iddetail = models.AutoField(primary_key=True)
    idbook = models.ForeignKey(booking, on_delete=models.DO_NOTHING, null=True,db_column='idbook')
    idroom = models.ForeignKey(room_detail, on_delete=models.DO_NOTHING, null=True,db_column='idroom')
    date_arrive = models.DateField()
    date_leave = models.DateField()
    iscancel = models.BooleanField(default=False)
    is_review = models.BooleanField(default=False)
    status=models.TextField()
    date_payment = models.DateTimeField(null=True)
    class Meta:
        unique_together=('idbook','idroom')
        db_table='booking_detail'
    def __str__(self):
        return str(self.iddetail)
class cart(models.Model):
    idcart = models.AutoField(primary_key=True)
    idcustomer = models.ForeignKey(customer,on_delete=models.DO_NOTHING, null=True)
    idroom = models.ForeignKey(room_detail, on_delete=models.DO_NOTHING, null=True)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    class Meta:
      
        db_table='cart'
    def __str__(self):
        return str(self.idcart)
class rating(models.Model):
    idrate = models.AutoField(primary_key=True)
    iddetail = models.ForeignKey(booking_detail, on_delete=models.DO_NOTHING, null=True,db_column='iddetail')
    score_clean = models.FloatField()
    score_utility = models.FloatField()
    score_service = models.FloatField()
    score_location = models.FloatField()
    score_cost = models.FloatField()
    rate = models.FloatField()
    title=models.TextField()
    commend=models.TextField()
    created_at = models.DateField(auto_now_add=True)  
    class Meta:
      
        db_table='rating'
    def __str__(self):
        return str(self.idrate)