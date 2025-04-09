SHOW TIMEZONE;
SET TIMEZONE = 'Asia/Ho_Chi_Minh';

CREATE TABLE role
( 
  idrole int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  role_name text,
  profession text
 )

CREATE TABLE account
( 
  email VARCHAR(320) PRIMARY KEY,
  password VARCHAR(128),
  idrole int,
  token text,
  is_active boolean default true,
  foreign key (idrole) references role(idrole)
 )

 CREATE TABLE users
( 
  user_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email VARCHAR(320),
  name text,
  phonenumber varchar(10),
  foreign key (email) references account(email),
  unique(email)
 )
 CREATE TABLE partner
( 
  idpartner int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id int,
 foreign key (user_id) references users(user_id)
 )
 CREATE TABLE hotels
( 
  idhotel int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  htl_name text,
  htl_img text,
  address text,
  description text,
  begin_price int,
  is_confirm boolean default false,
  idpartner int,
   is_delete boolean default false,
  foreign key (idpartner) references partner(idpartner)
 )

 CREATE TABLE type_room
( 
  idtyperm int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  idhotel int,
  type_room text,
  area FLOAT,
  room_img text,
  bed text,
  is_delete boolean default false,
 foreign key (idhotel) references hotels(idhotel)
 )

  CREATE TABLE room_detail
( 
  idroom int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  idtyperm int,
  price_only_day int,
  quantity int,
  foreign key (idtyperm) references type_room(idtyperm)
 )

  CREATE TABLE type_bed
( 
  idtypebd int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  type_bed text
 )
  CREATE TABLE bed
( 
  idbed int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  idtyperm int,
  idtypebd int,
  quantity int,
  foreign key (idtypebd) references type_bed(idtypebd),
  foreign key (idtyperm) references type_room(idtyperm)
 )
  CREATE TABLE service
( 
  idsv int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  service text
 )
  CREATE TABLE utility
( 
  idulty int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  idroom int,
  idsv int,
  foreign key (idsv) references service(idsv),
  foreign key (idroom) references room_detail(idroom)
 )
  CREATE TABLE type_customer
( 
  idtypecusm int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  type_customer text
 )
  CREATE TABLE capacity
( 
  idcap int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  idroom int,
  idtypecusm int,
  quantity int,
  foreign key (idtypecusm) references type_customer(idtypecusm),
  foreign key (idroom) references room_detail(idroom)
 )
  CREATE TABLE customer
( 
  idcustomer int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id int,
  foreign key (user_id) references users(user_id)
 )
  CREATE TABLE type_payment
( 
  idpayment int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  payment_name text
 )
  CREATE TABLE booking
( 
  idbook int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  idcustomer int,
  idpayment int,
  iscancel boolean default false,
  iscomplete boolean default false,
  created_at TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE,
  total_cost float,
  state text,
  foreign key (idcustomer) references customer(idcustomer),
  foreign key (idpayment) references type_payment(idpayment)
 )

CREATE TABLE booking_detail
( 
  iddetail int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  idbook int,
  idroom int,
  date_arrive date,
  date_leave date,
  iscancel boolean default false,
  is_review boolean default false,
  status text,
  date_payment TIMESTAMP WITH TIME ZONE,
  unique(idbook,idroom),
  FOREIGN KEY (idbook) REFERENCES booking(idbook), 
  FOREIGN KEY (idroom) REFERENCES room_detail(idroom)     
 ) 

CREATE TABLE cart
( 
  idcart int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  idcustomer int,
  idroom int,
  check_in_date date,
  check_out_date date,
  foreign key (idcustomer) references customer(idcustomer),
  foreign key (idroom) references room_detail(idroom)
 )
  CREATE TABLE rating
( 
  idrate int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  iddetail INT, 
  score_clean float,
  score_utility float,
  score_service float,
  score_location float,
  score_cost float,
  rate float,
  title text,
  commend text,
  created_at date,
 CONSTRAINT fk_rate_booking_detail FOREIGN KEY (iddetail) REFERENCES booking_detail(iddetail)
 )





