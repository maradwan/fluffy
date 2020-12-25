from factory import app
from flask import render_template, request, flash, session, url_for, redirect, Response
from .forms import SignupForm, SigninForm, Delivery
from .models import db, User, Client, Invoice, Menu, Orders
from functools import wraps
from datetime import timedelta
from datetime import datetime
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from os import environ as env
from sqlalchemy import between
from decimal import Decimal
from prometheus_flask_exporter import PrometheusMetrics
from sqlalchemy.sql import text

metrics = PrometheusMetrics(app)

app.config['RECAPTCHA_PUBLIC_KEY'] = env.get("RECAPTCHA_PUBLIC_KEY")
app.config['RECAPTCHA_PRIVATE_KEY'] = env.get("RECAPTCHA_PRIVATE_KEY")
metrics.info('Fluffy', 'Application info', version='1.0.0')

is_paid = 0
is_called = 0
is_admin = 1
default_stock = 10


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)

def login_required(f):
   @wraps(f)
   def wrap(*args, **kwargs):
       if 'email' in session:
           return f(*args, **kwargs)
       else:
           return redirect(url_for('signin'))
   return wrap


class ModelView(ModelView):
    def is_accessible(self):
        try:
          if 'email' in session:
            user = User.query.filter_by(email = session['email']).first()
            if user.is_admin:
              return True
        except:
          return False


class SignupView(BaseView):
    @login_required
    @expose('/', methods=['POST', 'GET'])
    def index(self):
      form = SignupForm()
      user = User.query.filter_by(email=session['email']).first()

      if not user.is_admin:
        return redirect(url_for('profile'))

      if request.method == 'POST':
        if form.validate() == False:
          return self.render('admin/signup.html', form=form)
        else:
          newuser = User(form.firstname.data, form.lastname.data, form.email.data, form.password.data, is_admin)
          db.session.add(newuser)
          db.session.commit()
          flash('Record was successfully added', 'success')
          return redirect('/admin/')

      elif request.method == 'GET':
        return self.render('admin/signup.html', form=form)


class SignoutView(BaseView):
    @login_required
    @expose('/')
    def signout(self):
      return redirect(url_for('signout'))

class DeliveryView(BaseView):
  @login_required
  @expose('/', methods=['POST', 'GET'])
  def delivery(self):
    form = Delivery()

    if request.method == 'POST':
      if form.validate() == False:
        return self.render('admin/delivery.html', form=form)
      else:
        data = db.session.query(Orders).filter((between(form.get_date.data,Orders.start_contract,
        Orders.end_contract))).filter(getattr(Orders, form.day.data) == True).order_by(Orders.client_id.asc()).all()
        return self.render('admin/showdelivery.html', data=data, form=form)

    elif request.method == 'GET':
      return self.render('admin/delivery.html', form=form)

class DashboardView(AdminIndexView):
    @login_required
    @expose('/')
    def index(self):
        not_called = len(Client.query.filter_by(is_called=is_called).all())
        not_paid = len(Invoice.query.filter_by(is_paid=is_paid).all())
        new_orders = len(Orders.query.filter(Orders.created_at.like('{}%'.format(datetime.now().date()))).all())
        new_client = len(Client.query.filter(Client.created_at.like('{}%'.format(datetime.now().date()))).all())
        stock = len(Menu.query.filter(Menu.stock < '{}'.format(default_stock) ).all())

        return self.render('admin/index.html', not_called=not_called, not_paid=not_paid, new_orders=new_orders, new_client=new_client, stock=stock)

class OrdersView(ModelView):
  def on_model_change(self, form, model, is_created):
    if is_created:
            user = User.query.filter_by(email=session['email']).first()
            model.creator_name = user.email
            item = Menu.query.filter_by(menu_id=model.menu_id).first()
            newinvoice = Invoice(model.client_id, model.creator_name, is_paid, datetime.now().date(),
            '', item.price, model.total_quantity, Decimal(model.total_quantity) * Decimal(item.price),
            model.order_id )
            db.session.add(newinvoice)
            db.session.commit()

            new_stock = Decimal(item.stock) - Decimal(model.total_quantity)
            item.stock = new_stock
            db.session.commit()


  can_export = True
  column_display_pk = True
  column_hide_backrefs = True
  can_view_details = True
  create_modal = True
  edit_modal = True
  column_exclude_list = ['' ]
  column_list = ['created_at', 'order_id','client_id', 'client', 'item', 'quantity_per_day', 'total_quantity', 'start_contract', 'end_contract', 'sat', 'sun', 'mon', 'tue', 'wen', 'thr', 'fri', 'comments']
  form_excluded_columns = ['created_at', 'invoice']
  column_searchable_list = ['client_id', 'start_contract']

class MenuView(ModelView):
  def on_model_change(self, form, model, is_created):
    if is_created:
            user = User.query.filter_by(email=session['email']).first()
            model.creator_name = user.email

  can_export = True
  column_display_pk = True
  column_hide_backrefs = True
  can_view_details = True
  create_modal = True
  edit_modal = True
  form_columns = ['items', 'price', 'unit', 'stock']
  column_searchable_list = ['menu_id','items']


class InvoiceView(ModelView):
  @login_required
  def on_model_change(self, form, model, is_created):
    if is_created:
            user = User.query.filter_by(email=session['email']).first()
            model.creator_name = user.email

  can_export = True
  column_display_pk = True
  column_hide_backrefs = True
  can_view_details = True
  create_modal = True
  edit_modal = True 
  column_exclude_list = ['created_at' ]
  column_list = ['created_at', 'invoice_id','order_id','client_id', 'client', 'is_paid', 'invoice_date', 'invoice_comments', 'price', 'total_quantity', 'total', 'order']
  form_excluded_columns = ['created_at']
  column_searchable_list = [ 'client_id', 'invoice_id','order_id']


class ClientView(ModelView):
  @login_required
  def on_model_change(self, form, model, is_created):
    if is_created:
            user = User.query.filter_by(email=session['email']).first()
            model.creator_name = user.email

  can_export = True
  column_display_pk = True
  column_hide_backrefs = True
  can_view_details = True
  create_modal = True
  edit_modal = True
  form_excluded_columns = ['created_at', 'client', 'order', 'invoice', 'orders']
  column_exclude_list = ['client']
  column_searchable_list = ['phone1', 'name', 'phone2', 'client_id']


class UserView(ModelView):
  can_export = True
  can_create = False
  column_display_pk = True
  column_hide_backrefs = True
  can_view_details = True
  create_modal = True
  edit_modal = True
  column_searchable_list = ['email','uid']
  column_exclude_list = ['pwdhash' ]
  form_excluded_columns = ['pwdhash']


admin = Admin(app,name='Fluffy', template_mode='bootstrap3', index_view= DashboardView())
admin.add_view(ClientView(Client, db.session))
admin.add_view(MenuView(Menu, db.session))
admin.add_view(OrdersView(Orders, db.session))
admin.add_view(InvoiceView(Invoice, db.session))

admin.add_view(DeliveryView(name='Delivery', menu_icon_type='glyph'))
admin.add_view(SignoutView(name='Log Out', menu_icon_type='glyph'))

admin.add_view(SignupView(name='New User', category='Settings'))
admin.add_view(UserView(User, db.session,name='Users', endpoint='user', category='Settings'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/')
def home():
  return redirect(url_for('signin'))

@app.route('/testdb')
@login_required
def testdb():
  if db.session.query("1").from_statement(text("SELECT 1")).all():
    return 'It works.'
  else:
    return 'Something is broken.'

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
  user = User.query.filter_by(email = session['email']).first()
  if 'email' in session and user.is_admin:
      return redirect('/admin/')
  return render_template('profile.html')

@app.route('/signout')
@login_required
def signout():
  session.pop('email', None)
  return redirect(url_for('signin'))

@app.route('/signin', methods=['GET', 'POST'])
def signin():
  form = SigninForm()

  if 'email' in session:
     return redirect(url_for('profile'))

  if request.method == 'POST':
    if form.validate() == False:
      return render_template('signin.html', form=form)
    else:
      session['email'] = form.email.data
      return redirect(url_for('profile'))

  elif request.method == 'GET':
    return render_template('signin.html', form=form)