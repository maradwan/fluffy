# -*- coding: utf-8 -*-
from os import environ as env
from flask import Flask

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = env.get("SQLALCHEMY_DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = env.get("SQLALCHEMY_TRACK_MODIFICATIONS")
app.secret_key = env.get("APP_SECRET_KEY")

from .models import db, User
db.init_app(app)
db.create_all()

# Admin User
if not User.query.filter_by(email = env.get("ADMIN_USER") + '@' + env.get("ADMIN_USER") + '.com').first():
   newuser = User(env.get("ADMIN_USER"), env.get("ADMIN_USER"), env.get("ADMIN_USER") + '@' + env.get("ADMIN_USER") + '.com',
   env.get("ADMIN_PASSWORD"), 1)

   db.session.add(newuser)
   db.session.commit()

   demouser = User(env.get("DEMO_USER"), env.get("DEMO_USER"), env.get("DEMO_USER") + '@' + env.get("DEMO_USER") + '.com',
   env.get("DEMO_PASSWORD"), 1)
   db.session.add(demouser)
   db.session.commit()

import factory.routes
