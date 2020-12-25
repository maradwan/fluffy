from flask_sqlalchemy import SQLAlchemy, event
from sqlalchemy import create_engine
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from factory import app

db = SQLAlchemy(app)


class User(db.Model):
  __tablename__ = 'users'
  uid = db.Column(db.Integer, primary_key = True)
  firstname = db.Column(db.String(100))
  lastname = db.Column(db.String(100))
  email = db.Column(db.String(120), unique=True)
  pwdhash = db.Column(db.String(120))
  is_admin = db.Column(db.Boolean, default=False)
  client = db.relationship('Client', backref='client', lazy=True)

  def __repr__(self):
       return "{}".format( self.uid)

  def __init__(self, firstname, lastname, email, password, is_admin):
    self.firstname = firstname.title()
    self.lastname = lastname.title()
    self.email = email.lower()
    self.set_password(password)
    self.is_admin = is_admin

  def set_password(self, password):
    self.pwdhash = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.pwdhash, password)


class Client(db.Model):
  __tablename__ = 'client'
  client_id = db.Column(db.Integer, primary_key = True)
  created_at = db.Column(db.DateTime, index=True, default=datetime.now,nullable=False)
  name = db.Column(db.String(120), nullable=False)
  is_called = db.Column(db.Boolean, default=False)
  phone1 = db.Column(db.String(120),nullable=False)
  phone2 = db.Column(db.String(120))
  email = db.Column(db.String(120))
  city = db.Column(db.String(120), nullable=False)
  comments = db.Column(db.String(120))
  street = db.Column(db.String(120), nullable=False)
  floor = db.Column(db.String(120), nullable=False)
  building = db.Column(db.String(120), nullable=False)
  apartment = db.Column(db.String(120), nullable=False)
  address_directions = db.Column(db.String(120))
  creator_name = db.Column(db.String(120), db.ForeignKey('users.email'))


  def __repr__(self):
        return "{}-{}".format( self.name, self.phone1)


  def __init__(self, name, is_called, phone1, phone2, email, city, comments, creator_name, street,
   floor ,building, apartment, address_directions):

    self.name = name
    self.is_called = is_called
    self.phone1 = phone1
    self.phone2  = phone2
    self.email = email
    self.city = city
    self.comments = comments
    self.creator_name = creator_name
    self.street = street
    self.floor = floor
    self.building = building
    self.apartment = apartment
    self.address_directions = address_directions


class Invoice(db.Model):
  __tablename__ = 'invoice'
  invoice_id = db.Column(db.Integer, primary_key = True)
  client_id = db.Column(db.Integer, db.ForeignKey('client.client_id'), nullable=False)
  created_at = db.Column(db.DateTime, index=True, default=datetime.now,nullable=False)
  is_paid = db.Column(db.Boolean, default=False)
  invoice_date = db.Column(db.Date, index=True, default=datetime.now().date(),nullable=False)
  creator_name = db.Column(db.String(120), db.ForeignKey('users.email'))
  invoice_comments = db.Column(db.String(120))
  price = db.Column(db.Float, nullable=False)
  total_quantity = db.Column(db.Float, nullable=False)
  total = db.Column(db.Float, nullable=False)
  order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
  client = db.relationship("Client", backref=db.backref(
        "invoice", order_by=client_id), lazy=True)

  order = db.relationship("Orders", backref=db.backref(
        "invoice", order_by=order_id), lazy=True)


  def __repr__(self):
       return "{}".format( self.invoice_id)

  def __init__(self, client_id, creator_name, is_paid, invoice_date, invoice_comments, price, total_quantity, total, order_id):
    self.client_id = client_id
    self.creator_name  = creator_name
    self.is_paid = is_paid
    self.invoice_date = invoice_date
    self.invoice_comments = invoice_comments
    self.price = price
    self.total_quantity = total_quantity
    self.total = total
    self.order_id = order_id


class Menu(db.Model):
  __tablename__ = 'menu'
  menu_id = db.Column(db.Integer, primary_key = True)
  created_at = db.Column(db.DateTime, index=True, default=datetime.now,nullable=False)
  creator_name = db.Column(db.String(120), db.ForeignKey('users.email'))
  items = db.Column(db.String(120),nullable=False)
  unit = db.Column(db.Float, nullable=False)
  price = db.Column(db.Float, nullable=False)
  stock = db.Column(db.Float, nullable=False)

  def __repr__(self):
        return "{}".format( self.items)

  def __init__(self, creator_name, items, unit, price, stock ):
    self.creator_name = creator_name
    self.items = items
    self.unit = unit
    self.price  = price
    self.stock  = stock


class Orders(db.Model):
  __tablename__ = 'orders'
  order_id = db.Column(db.Integer, primary_key = True)
  created_at = db.Column(db.DateTime, index=True, default=datetime.now,nullable=False)
  creator_name = db.Column(db.String(120), db.ForeignKey('users.email'))
  client_id = db.Column(db.Integer, db.ForeignKey('client.client_id'), nullable=False)
  start_contract = db.Column(db.Date, index=True, default=datetime.now().date(),nullable=False)
  end_contract = db.Column(db.Date, index=True, default=datetime.now().date(),nullable=False)
  quantity_per_day = db.Column(db.Float, nullable=False)
  total_quantity = db.Column(db.Float, nullable=False)
  menu_id = db.Column(db.Integer, db.ForeignKey('menu.menu_id'), nullable=False)
  sat = db.Column(db.Boolean, default=False)
  sun = db.Column(db.Boolean, default=False)
  mon = db.Column(db.Boolean, default=False)
  tue = db.Column(db.Boolean, default=False)
  wen = db.Column(db.Boolean, default=False)
  thr = db.Column(db.Boolean, default=False)
  fri = db.Column(db.Boolean, default=False)
  comments = db.Column(db.String(120))


  client = db.relationship("Client", backref=db.backref(
        "orders", order_by=client_id), lazy=True)
  item = db.relationship("Menu", backref=db.backref(
        "orders", order_by=menu_id), lazy=True)


  def __repr__(self):
        return "{}-{}".format(self.order_id, self.item)

  def __init__(self, start_contract, end_contract,quantity_per_day, total_quantity, creator_name, client_id, menu_id,
               sat, sun, mon, tue, wen, thr, fri, comments):

    self.start_contract = start_contract
    self.end_contract  = end_contract
    self.quantity_per_day = quantity_per_day
    self.total_quantity = total_quantity
    self.creator_name = creator_name
    self.client_id = client_id
    self.menu_id = menu_id
    self.sat = sat
    self.sun = sun
    self.mon = mon
    self.tue = tue
    self.wen = wen
    self.thr = thr
    self.fri = fri
    self.comments = comments