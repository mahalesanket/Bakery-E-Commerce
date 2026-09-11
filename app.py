import os
import sys
import uuid
import random
import string
import logging
import smtplib
import hashlib
import hmac
import re
import pathlib
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
from io import BytesIO
from uuid import uuid4
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import pytz
import razorpay
import mysql.connector
from mysql import connector
from flask import (Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort, send_file, make_response, Blueprint, current_app, get_flashed_messages)
from flask_sqlalchemy import SQLAlchemy
from flask_login import ( LoginManager, login_user, logout_user, login_required, current_user, UserMixin )
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect, generate_csrf, validate_csrf
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import pdfkit

# from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort, send_file, make_response
# from flask_sqlalchemy import SQLAlchemy
# from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
# from flask_bcrypt import Bcrypt
# from flask_mail import Mail, Message
# from flask_wtf.csrf import CSRFProtect, generate_csrf
# import razorpay
# import os
# import uuid
# import logging
# from datetime import datetime
# from werkzeug.utils import secure_filename
# from functools import wraps
# from dotenv import load_dotenv
# import hmac
# import hashlib
# import pdfkit
# from flask_wtf.csrf import validate_csrf
# import random
# import string
# from flask import request, render_template, redirect, url_for, abort, jsonify
# from flask_login import login_required, current_user
# from flask_login import current_user
# import sys
# from flask import render_template, redirect, url_for, request, flash, current_app
# from flask_login import login_user, logout_user, login_required, current_user, LoginManager
# from flask_bcrypt import Bcrypt
# from flask import session
# from mysql import connector
# import mysql.connector
# from flask import abort
# import os
# from werkzeug.utils import secure_filename
# from datetime import datetime, timedelta
# import pytz
# from flask_login import current_user
# from sqlalchemy import func
# from flask_mail import Mail, Message
# from flask import Flask, request, jsonify
# import logging
# from flask import Flask, session, request, redirect, render_template
# from uuid import uuid4
# import uuid
# from flask import make_response
# from flask_login import login_required
# import pathlib
# from flask import send_file
# from reportlab.lib.pagesizes import A4
# from reportlab.pdfgen import canvas
# from io import BytesIO
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from flask import request, redirect, url_for, render_template
# from flask_login import login_required, current_user
# from email.mime.application import MIMEApplication
# from werkzeug.utils import secure_filename
# from flask import Blueprint, render_template, request, flash, redirect, url_for
# from flask_mail import Mail, Message
# import re 
# from flask_login import current_user
# from sqlalchemy.orm import joinedload
# from flask import redirect, url_for
# from flask import request, send_file
# from flask_login import login_required
# from io import BytesIO
# from openpyxl import Workbook
# from datetime import datetime, timedelta
# import pytz
# from flask import request, render_template
# from datetime import datetime, timedelta
# import pytz
# from flask_login import login_required
# from collections import defaultdict
# from flask_login import login_required, current_user
# from flask_login import login_required
# from flask import render_template
# from datetime import datetime
# import pytz
# from flask_login import login_required
# from flask import render_template
# from datetime import datetime
# from flask import request, redirect, url_for, flash
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from flask_login import login_required
# from flask import render_template
# from collections import defaultdict
# from datetime import datetime
# import pytz
# from flask import flash, get_flashed_messages
# from werkzeug.security import generate_password_hash
# import random, smtplib
# from flask import request, session, render_template
# from flask_login import login_required
# from datetime import datetime
# import pytz

# ---------------------------------------------------------------------------
load_dotenv()
app = Flask(__name__)

# ===== CONFIG =====
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key-123')  # or your long random key
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root@localhost/biodata_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions (CSRF first so decorators are available)
csrf = CSRFProtect(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

# Razorpay test credentials (ensure these are correct)
KEY_ID = "rzp_test_Rej2A29kjY96Ty"
KEY_SECRET = "vny9CFp2SeCZzlUqHvIX9HEc"
razorpay_client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))

CSRF_EXEMPT_ROUTES = [
    'thankyou',
    'create_razorpay_order',
    'payment_success',
    'payment_page_static'
    'place_guest_order',
    'guest_payment_success',
    'create_razorpay_guest_order'
]

# Then exempt them
csrf.exempt('place_guest_order')
csrf.exempt('guest_payment_success') 
csrf.exempt('create_razorpay_guest_order')

# After csrf = CSRFProtect(app)
csrf.exempt('payment_success')
csrf.exempt('create_razorpay_order')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # this is app/
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Define allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Initialize Flask-Mail inside this file
mail = Mail()

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'sednainfo5@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'mfzm afcu fwma latu'  # Replace with your app password

mail.init_app(app)  # Initialize Flask-Mail with app

# logging.basicConfig(level=logging.ERROR)
otp_store = {}

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # ✅ Add this line
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    mobile_no = db.Column(db.String(15), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=True)

    def get_id(self):
        return str(self.id)  # Ensure it returns a string

    def set_password(self, password):
        """Hashes the password and stores it."""
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        """Checks the hashed password."""
        return bcrypt.check_password_hash(self.password_hash, password)

class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image1 = db.Column(db.String(200), default='default.jpg')


    offer = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255), nullable=False)
        # Relationship to SubProduct
    sub_products = db.relationship('Sub_Product', backref='product', lazy=True, cascade="all, delete")


class Sub_Product(db.Model):
    __tablename__ = 'sub_product'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)

    name = db.Column(db.String(100), nullable=True)
    price = db.Column(db.Float, nullable=True)
    new_price = db.Column(db.Float, nullable=True)
    image1 = db.Column(db.String(255), nullable=True)
    image2 = db.Column(db.String(255), nullable=True)
    image3 = db.Column(db.String(255), nullable=True)
    image4 = db.Column(db.String(255), nullable=True)
    image5 = db.Column(db.String(255), nullable=True)
    video = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    type = db.Column(db.String(100), nullable=True)
    offer = db.Column(db.Integer, nullable=True)
    youtube = db.Column(db.String(100), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    delivery_cost = db.Column(db.Float, nullable=False)
    packaging_cost = db.Column(db.Float, nullable=False)
    cart_items = db.relationship('CartItem', backref='sub_product', lazy=True)

class Variant(db.Model):
    __tablename__ = 'variant'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    sub_products = db.relationship('SubProductVariant', backref='variant', cascade="all, delete")


# 3. Flavour (global, reusable — e.g., Chocolate, Butterscotch)
class Flavour(db.Model):
    __tablename__ = 'flavour'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    sub_products = db.relationship('SubProductFlavour', backref='flavour', cascade="all, delete")

# 4. SubProductVariant (linking table between SubProduct and Variant)
class SubProductVariant(db.Model):
    __tablename__ = 'subproduct_variant'
    id = db.Column(db.Integer, primary_key=True)
    sub_product_id = db.Column(db.Integer, db.ForeignKey('sub_product.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('variant.id'), nullable=False)

# 5. SubProductFlavour (linking table between SubProduct and Flavour)
class SubProductFlavour(db.Model):
    __tablename__ = 'subproduct_flavour'
    id = db.Column(db.Integer, primary_key=True)
    sub_product_id = db.Column(db.Integer, db.ForeignKey('sub_product.id'), nullable=False)
    flavour_id = db.Column(db.Integer, db.ForeignKey('flavour.id'), nullable=False)

# 6. VariantFlavourPrice (price for a given SubProduct + Variant + Flavour)
class VariantFlavourPrice(db.Model):
    __tablename__ = 'variant_flavour_price'
    id = db.Column(db.Integer, primary_key=True)
    sub_product_id = db.Column(db.Integer, db.ForeignKey('sub_product.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('variant.id'), nullable=False)
    flavour_id = db.Column(db.Integer, db.ForeignKey('flavour.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    # Optional relationships for easier ORM access
    variant = db.relationship('Variant')
    flavour = db.relationship('Flavour')

class BogoOfferItem(db.Model):
    __tablename__ = 'bogo_offer_item'
    id = db.Column(db.Integer, primary_key=True)
    sub_prod_id = db.Column(db.Integer, db.ForeignKey('sub_product.id'), nullable=False)
    free_items_id = db.Column(db.Integer, db.ForeignKey('sub_product.id'), nullable=False)

class ManageAddress(db.Model):
    __tablename__ = 'manage_address'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    pincode = db.Column(db.String(50), nullable=False)
    locality = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    city_district_town = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    landmark = db.Column(db.String(100), nullable=True)
    alternate_mobile = db.Column(db.String(100), nullable=True)
    address_type = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref="addresses", lazy=True)

    def __repr__(self):
        return f"<Address {self.id} - {self.username}, {self.city_district_town}>"

class GuestOrder(db.Model):
    __tablename__ = 'guest_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    guest_name = db.Column(db.String(100), nullable=False)
    guest_email = db.Column(db.String(100), nullable=False)
    guest_mobile = db.Column(db.String(15), nullable=False)
    guest_alternate_mobile = db.Column(db.String(15))
    
    # Address fields
    guest_address = db.Column(db.Text, nullable=False)
    guest_locality = db.Column(db.String(100), nullable=False)
    guest_city = db.Column(db.String(100), nullable=False)
    guest_state = db.Column(db.String(100), nullable=False)
    guest_pincode = db.Column(db.String(10), nullable=False)
    guest_landmark = db.Column(db.String(100))
    
    # Order summary
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    delivery_charges = db.Column(db.Numeric(10, 2), nullable=False)
    packaging_charges = db.Column(db.Numeric(10, 2), nullable=False)
    gst = db.Column(db.Numeric(10, 2), nullable=False)
    grand_total = db.Column(db.Numeric(10, 2), nullable=False)
    
    status = db.Column(db.String(50), default='Pending')
    order_type = db.Column(db.String(20), default='delivery')  # delivery/pickup
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ✅ NEW: Razorpay payment fields
    razorpay_order_id = db.Column(db.String(100))
    razorpay_payment_id = db.Column(db.String(100))
    razorpay_signature = db.Column(db.String(200))
    
    # Relationship with guest order items
    items = db.relationship('GuestOrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

class GuestOrderItem(db.Model):
    __tablename__ = 'guest_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('guest_orders.id'), nullable=False)
    
    sub_productname = db.Column(db.String(255), nullable=True)
    image = db.Column(db.String(255), nullable=True)
    flavour = db.Column(db.String(255), nullable=True)
    variant = db.Column(db.String(100), nullable=True)
    v_cost = db.Column(db.Numeric(10, 2), nullable=True)
    quantity = db.Column(db.Integer, nullable=True)
    
    # Accessories
    acc_1 = db.Column(db.String(255), nullable=True)
    a_cost1 = db.Column(db.Numeric(10, 2), nullable=True)
    a_quantity1 = db.Column(db.Integer, nullable=True)
    
    acc_2 = db.Column(db.String(255), nullable=True)
    a_cost2 = db.Column(db.Numeric(10, 2), nullable=True)
    a_quantity2 = db.Column(db.Integer, nullable=True)
    
    acc_3 = db.Column(db.String(255), nullable=True)
    a_cost3 = db.Column(db.Numeric(10, 2), nullable=True)
    a_quantity3 = db.Column(db.Integer, nullable=True)
    
    acc_4 = db.Column(db.String(255), nullable=True)
    a_cost4 = db.Column(db.Numeric(10, 2), nullable=True)
    a_quantity4 = db.Column(db.Integer, nullable=True)
    
    acc_5 = db.Column(db.String(255), nullable=True)
    a_cost5 = db.Column(db.Numeric(10, 2), nullable=True)
    a_quantity5 = db.Column(db.Integer, nullable=True)
    
    total_price = db.Column(db.Numeric(10, 2), nullable=True)
    message = db.Column(db.String(255), nullable=True)

class Location(db.Model):
    __tablename__ = 'tb_location'
    id = db.Column(db.Integer, primary_key=True)
    mainlocation = db.Column(db.String(255), nullable=False)
    area = db.Column(db.String(255), nullable=False)
    def __repr__(self):
        return f"<Location {self.id}: {self.mainlocation} - {self.area}>"

class Accessories(db.Model):
    __tablename__ = 'tb_accessories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"<Location {self.id}: {self.name} - {self.price}>"

class CartItem(db.Model):
    __tablename__ = 'cartitem'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # <--- NEW FIELD
    sub_product_id = db.Column(db.Integer, db.ForeignKey('sub_product.id'), nullable=False)
    sub_productname = db.Column(db.String(255), nullable=True)
    image = db.Column(db.String(255), nullable=True)
    variant = db.Column(db.String(255), nullable=True)
    v_cost = db.Column(db.Numeric(10, 2), nullable=True)

    acc_1 = db.Column(db.String(255), nullable=True)
    a_cost1 = db.Column(db.Numeric(10, 2), nullable=True)
    acc_2 = db.Column(db.String(255), nullable=True)
    a_cost2 = db.Column(db.Numeric(10, 2), nullable=True)
    acc_3 = db.Column(db.String(255), nullable=True)
    a_cost3 = db.Column(db.Numeric(10, 2), nullable=True)
    acc_4 = db.Column(db.String(255), nullable=True)
    a_cost4 = db.Column(db.Numeric(10, 2), nullable=True)
    acc_5 = db.Column(db.String(255), nullable=True)
    a_cost5 = db.Column(db.Numeric(10, 2), nullable=True)

    total_price = db.Column(db.Numeric(10, 2), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    session_id = db.Column(db.String(100), nullable=False)

    a_quantity1 = db.Column(db.Integer, default=1)
    a_quantity2 = db.Column(db.Integer, default=1)
    a_quantity3 = db.Column(db.Integer, default=1)
    a_quantity4 = db.Column(db.Integer, default=1)
    a_quantity5 = db.Column(db.Integer, default=1)
    delivery_cost = db.Column(db.Numeric(10, 2), nullable=False)
    packaging_cost = db.Column(db.Numeric(10, 2), nullable=False)
    flavour = db.Column(db.String(128),nullable = True)
    message=db.Column(db.String(255),nullable = True)

    def __repr__(self):
        return f'<CartItem {self.sub_productname}>'

class Orders(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    delivery_cost = db.Column(db.Float, nullable=True)
    packaging_charges = db.Column(db.Float, nullable=True)
    gst = db.Column(db.Float, nullable=True)
    grand_total = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    address_id = db.Column(db.Integer, db.ForeignKey('manage_address.id'))
    status = db.Column(db.String(50), default='Pending')
    items = db.relationship('OrderItems', backref='order', lazy=True)
    user = db.relationship('User', backref='orders')  # <--- THIS is important

class OrderItems(db.Model):
    __tablename__ = 'orderitems'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    sub_productname = db.Column(db.String(255), nullable=True)
    flavour = db.Column(db.String(255), nullable = True)
    image = db.Column(db.String(255), nullable = True)
    variant = db.Column(db.String(100), nullable=True)
    v_cost = db.Column(db.Numeric(10, 2), nullable=True)
    quantity = db.Column(db.Integer, nullable=True)
    acc_1 = db.Column(db.String(255), nullable=True)
    a_cost1 = db.Column(db.Numeric(10, 2), nullable=True)
    a_quantity1 = db.Column(db.Integer, nullable=True)
    acc_2 = db.Column(db.String(255), nullable=True)
    a_cost2 = db.Column(db.Numeric(10, 2), nullable=True)
    a_quantity2 = db.Column(db.Integer, nullable=True)
    acc_3 = db.Column(db.String(255), nullable=True)
    a_cost3 = db.Column(db.Numeric(10, 2), nullable=True)
    a_quantity3 = db.Column(db.Integer, nullable=True)
    acc_4 = db.Column(db.String(255), nullable=True)
    a_cost4 = db.Column(db.Numeric(10, 2), nullable=True)
    a_quantity4 = db.Column(db.Integer, nullable=True)
    acc_5 = db.Column(db.String(255), nullable=True)
    a_cost5 = db.Column(db.Numeric(10, 2), nullable=True)
    a_quantity5 = db.Column(db.Integer, nullable=True)
    total_price = db.Column(db.Numeric(10, 2), nullable=True)
    message=db.Column(db.String(255),nullable = True)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    razorpay_order_id = db.Column(db.String(100), nullable=False)
    razorpay_payment_id = db.Column(db.String(100))
    razorpay_signature = db.Column(db.String(200))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='INR')
    status = db.Column(db.String(50), default='created')
    mode = db.Column(db.String(10), default='test')  # Make sure this line exists
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    order = db.relationship('Orders', backref=db.backref('payments', lazy=True))

# Function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif', 'mp4'}

# Initialize Bcrypt for password hashing
@app.before_request
def ensure_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid4())  # Generate a unique session ID

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

def get_db_connection():
   return mysql.connector.connect(
     host="localhost",
        user="root",
        password="",
        database="biodata_db"
    )

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if 'user_id' in session:
        user_id = session['user_id']
        cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
        users = cursor.fetchall()
        return render_template("index.html",users = users)

    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        next_page = request.form.get("next")

        if not email or not password:
            error = "Email and Password are required!"
        else:
            user = User.query.filter_by(email=email).first()

            if user and bcrypt.check_password_hash(user.password, password):
                login_user(user)

                # Merge guest cart to user cart, if any
                session_id = session.get("session_id")
                if session_id:
                    guest_cart = CartItem.query.filter_by(session_id=session_id).all()
                    for item in guest_cart:
                        item.user_id = user.id
                    db.session.commit()
                session['user_id'] = user.id

                # Admin login redirect
                if user.email == "sbpc123@gmail.com":
                    return redirect(url_for("admin_dashboard"))

                # Redirect to next page or cart
                return redirect(next_page) if next_page else redirect(url_for("cart"))
            else:
                error = "Invalid email or password!"

    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        mobile = request.form.get("mobile_no")
        address = request.form.get("address")

        # Enhanced validation patterns
        name_pattern = r"^[a-zA-Z\s]{2,50}$"
        email_pattern = r"^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$"
        password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        mobile_pattern = r"^[6-9]\d{9}$"

        # Validation checks
        if not name or not email or not password or not confirm_password or not mobile:
            error = "All required fields must be filled!"
        elif not re.match(name_pattern, name):
            error = "Name should contain only letters and spaces (2-50 characters)"
        elif not re.match(email_pattern, email):
            error = "Please enter a valid email address"
        elif password != confirm_password:
            error = "Passwords do not match!"
        elif not re.match(password_pattern, password):
            error = "Password must be 8+ characters with uppercase, lowercase, number, and special character (@$!%*?&)"
        elif not re.match(mobile_pattern, mobile):
            error = "Mobile number must be 10 digits starting with 6-9"
        elif User.query.filter_by(email=email).first():
            error = "Email is already registered!"
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            new_user = User(
                name=name,  # ✅ Changed from username to name
                email=email,
                password=hashed_password,
                mobile_no=mobile,
                address=address if address else None
            )
            db.session.add(new_user)
            db.session.commit()

            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('login'))

    return render_template("register.html", error=error)

@app.route('/user_order_history', methods=['GET'])
@login_required
def user_order_history():
    user_id = session['user_id']
    status_filter = request.args.get('status')  # "Delivered,Pending"
    year_filter = request.args.get('year')      # "2024,2025"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    query = '''
        SELECT
            orderitems.*,
            orders.id AS order_id,
            orders.user_id,
            orders.status,
            orders.delivery_cost,
            orders.gst,
            orders.grand_total,
            orders.timestamp,
            orders.address_id,
            manage_address.*
        FROM orderitems
        INNER JOIN orders ON orderitems.order_id = orders.id
        INNER JOIN manage_address ON orders.address_id = manage_address.id
        WHERE orders.user_id = %s
    '''
    params = [user_id]

    # Apply status filter
    if status_filter:
        status_values = status_filter.split(',')
        placeholders = ','.join(['%s'] * len(status_values))
        query += f' AND orders.status IN ({placeholders})'
        params.extend(status_values)

    # Apply year filter
    if year_filter:
        year_values = year_filter.split(',')
        placeholders = ','.join(['%s'] * len(year_values))
        query += f' AND YEAR(orders.timestamp) IN ({placeholders})'
        params.extend(year_values)

    query += ' ORDER BY orders.id DESC'

    cursor.execute(query, params)
    orders = cursor.fetchall()

    # Convert UTC timestamp to IST and format
    ist = pytz.timezone("Asia/Kolkata")
    utc = pytz.utc

    for order in orders:
        timestamp = order['timestamp']
        if isinstance(timestamp, str):
            timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

        localized_utc = utc.localize(timestamp)
        ist_datetime = localized_utc.astimezone(ist)
        order['formatted_time'] = ist_datetime.strftime("%d-%m-%Y %I:%M:%S %p")

        # Parse accessories
        accessories = []
        for i in range(1, 6):
            name = order.get(f'acc_{i}')
            cost = order.get(f'a_cost{i}')
            qty = order.get(f'a_quantity{i}')
            if qty and qty != 0:
                accessories.append({
                    'name': name,
                    'cost': cost,
                    'qty': qty,
                    'total': cost * qty
                })
        order['accessories'] = accessories

    # Fetch filter options again
    cursor.execute('SELECT DISTINCT status FROM orders')
    statuses = [row['status'] for row in cursor.fetchall()]

    cursor.execute('SELECT DISTINCT YEAR(timestamp) AS year FROM orders ORDER BY year DESC')
    years = [row['year'] for row in cursor.fetchall()]

    selected_statuses = status_filter.split(',') if status_filter else []
    selected_years = year_filter.split(',') if year_filter else []

    return render_template(
    'user_orders.html',
    orders=orders,
    statuses=statuses,
    years=years,
    selected_statuses=selected_statuses,
    selected_years=selected_years,
    users=[user]               # ✅ Fixes modal user info
)

@app.route('/logout')
def logout():
    session.clear()
    html = """
    <html>
      <head>
        <script>
          // Clear location tracking flags
          sessionStorage.removeItem("selectedCity");
          sessionStorage.removeItem("selectedOutlet");
          sessionStorage.removeItem("locationAsked");
          // Redirect to homepage
          window.location.href = "/";
        </script>
      </head>
      <body></body>
    </html>
    """
    return make_response(html)

@app.route("/update_password", methods=["GET", "POST"])
def update_password():
    error = None
    success = None

    if request.method == "POST":
        email = request.form.get("email")
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirm_new_password = request.form.get("confirm_new_password")

        # Check if all required fields are filled
        if not email or not old_password or not new_password or not confirm_new_password:
            error = "All fields are required!"
        elif new_password != confirm_new_password:
            error = "New passwords do not match!"
        else:
            user = User.query.filter_by(email=email).first()
            if not user:
                error = "No user found with this email!"
            elif not bcrypt.check_password_hash(user.password, old_password):
                error = "Old password is incorrect!"
            else:
                user.password = bcrypt.generate_password_hash(new_password).decode("utf-8")
                db.session.commit()
                success = "Password updated successfully!"

    return render_template("ad_update_pass.html", error=error, success=success)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            otp = str(random.randint(100000, 999999))
            expires_at = datetime.now() + timedelta(minutes=5)
            # Delete old OTPs for this email
            PasswordReset.query.filter_by(email=email).delete()
            # Save new OTP
            new_otp = PasswordReset(email=email, otp=otp, expires_at=expires_at)
            db.session.add(new_otp)
            db.session.commit()
            send_otp_email(email, otp, user.username)
            session['email'] = email
            flash("OTP sent to your email", "success")
            return redirect(url_for('verify_otp'))
        else:
            flash("Email not registered", "danger")
    return render_template('forgot_password.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    email = session.get('email')
    if not email:
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        entered_otp = request.form['otp']
        record = PasswordReset.query.filter_by(email=email, otp=entered_otp).first()
        if record and record.expires_at > datetime.now():
            session['otp_verified'] = True
            return redirect(url_for('reset_password'))
        else:
            flash("Invalid or expired OTP", "danger")
    return render_template('verify_otp.html', email=email)

def send_otp_email(to_email, otp, username):
    msg_content = f"""
    <p>Hello <strong>{username}</strong>,</p>
    <p>This is to inform you that your password reset process must be confirmed with the following OTP.</p>
    <p>Here is your OTP to verify your password reset:</p>
    <p style="font-size: 18px;">Your One-Time Password (OTP) is: <strong>{otp}</strong></p>
    <br>
    <p>Regards,<br>SS Bakers</p>
    """
    msg = MIMEText(msg_content, "html")
    msg['Subject'] = "Password Reset OTP"
    msg['From'] = "sednainfo5@gmail.com"
    msg['To'] = to_email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login("sednainfo5@gmail.com", "mfzm afcu fwma latu")
            server.send_message(msg)
            print("OTP email sent.")
    except Exception as e:
        print("Failed to send email:", e)


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if not session.get('otp_verified'):
        return redirect(url_for('forgot_password'))
    email = session['email']
    if request.method == 'POST':
        new_password      = request.form['new_password']
        confirm_password  = request.form['confirm_password']
        pattern = r'^[A-Za-z0-9]{6,}$'
        # --- validation ---
        if not re.match(pattern, new_password):
            flash("Password must be at least 6 characters and contain only letters and numbers.", "danger")
            return redirect(url_for('reset_password'))
        if new_password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('reset_password'))
        # -------------------
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.session.commit()
        # clean up OTP records & session
        PasswordReset.query.filter_by(email=email).delete()
        db.session.commit()
        session.pop('otp_verified', None)
        session.pop('email', None)
        flash("Password updated successfully", "success")
        return redirect(url_for('login'))
    return render_template('reset_password.html')

# ---------------------------------------------------------------------------------------- ADMIN DASHBOARD ----
@app.route("/admin_dashboard", methods=["GET", "POST"])
@login_required
def admin_dashboard():
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # === NEW: Get product_id from form ===
            product_id = request.form['product_name']  # Now this is id from tb_products

            # === NEW: Fetch product_name from tb_products using product_id ===
            cursor.execute("SELECT name FROM tb_products WHERE id = %s", (product_id,))
            product_row = cursor.fetchone()
            if not product_row:
                flash("Selected product does not exist.")
                return redirect(url_for('admin_dashboard'))
            product_name = product_row['name']

            # === Existing code, use product_name fetched above ===
            product_category = request.form['product_category']
            product_type = request.form['product_type']
            product_offer = request.form['product_offer']
            product_youtube = request.form['product_youtube']
            product_description = request.form['product_description']
            product_image = request.files.get('product_image1')

            # === Your existing logic checking if product exists in 'product' table by product_name ===
            cursor.execute("SELECT id FROM product WHERE name = %s", (product_name,))
            product = cursor.fetchone()

            if product:
                product_id_main = product['id']
            else:
                cursor.execute("""
                    INSERT INTO product (name, category, type, offer, youtube, description, image1)
                    VALUES (%s, %s, %s, %s, %s, %s, '')
                """, (product_name, product_category, product_type, product_offer, product_youtube, product_description))
                product_id_main = cursor.lastrowid

                if product_image and product_image.filename:
                    ext = os.path.splitext(product_image.filename)[1]
                    filename = f"{product_id_main}_1{ext}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    product_image.save(filepath)
                    cursor.execute("UPDATE product SET image1 = %s WHERE id = %s", (filename, product_id_main))
                flash(f"New product inserted with ID: {product_id_main}")

            # === Then continue with sub-product insertion as before, but use product_id_main ===
            sub_name = request.form['subproduct_name']
            sub_category = request.form['subproduct_category']
            sub_type = request.form['subproduct_type']
            sub_offer = request.form['subproduct_offer']
            sub_youtube = request.form['subproduct_youtube']
            sub_description = request.form['subproduct_description']

            variant1 = request.form.get('variant1')
            cost1 = request.form.get('cost1')
            variant2 = request.form.get('variant2')
            cost2 = request.form.get('cost2')
            variant3 = request.form.get('variant3')
            cost3 = request.form.get('cost3')
            variant4 = request.form.get('variant4')
            cost4 = request.form.get('cost4')
            variant5 = request.form.get('variant5')
            cost5 = request.form.get('cost5')
            delivery_cost = request.form.get('delivery_cost')
            packaging_cost= request.form.get('packaging_cost')

            sub_images = ["", "", "", "", ""]
            sub_video_filename = ""

            cursor.execute("""
                INSERT INTO sub_product (
                    product_id, name,
                    image1, image2, image3, image4, image5,
                    video, category, type, offer, youtube, description,
                    delivery_cost,packaging_cost )
                VALUES (%s, %s,
                        '', '', '', '', '',
                        '', %s, %s, %s, %s, %s,
                        %s,%s)
            """, (
                product_id_main, sub_name,
                sub_category, sub_type, sub_offer, sub_youtube, sub_description,
                delivery_cost,packaging_cost,
            ))

            sub_product_id = cursor.lastrowid

            selected_variant_ids = request.form.getlist('available_variants')
            for variant_id in selected_variant_ids:
                if variant_id:
                    cursor.execute("""
                        INSERT INTO subproduct_variant (sub_product_id, variant_id)
                        VALUES (%s, %s)
                    """, (sub_product_id, variant_id))

            selected_flavour_ids = request.form.getlist('available_flavours')
            for flavour_id in selected_flavour_ids:
                if flavour_id:
                    cursor.execute("""
                        INSERT INTO subproduct_flavour (sub_product_id, flavour_id)
                        VALUES (%s, %s)
                    """, (sub_product_id, flavour_id))

            free_item_ids = request.form.getlist('free_product')
            for free_id in free_item_ids:
                if free_id:
                    cursor.execute("""
                    INSERT INTO bogo_offer_item (sub_prod_id, free_item_ids)
                    VALUES (%s, %s)
                    """, (sub_product_id, free_id))

            for i in range(1, 6):
                file = request.files.get(f'subproduct_image{i}')
                if file and file.filename:
                    ext = os.path.splitext(file.filename)[1]
                    filename = f"{sub_product_id}_{i}{ext}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    sub_images[i - 1] = filename

            sub_video_file = request.files.get('subproduct_video')
            if sub_video_file and sub_video_file.filename:
                ext = os.path.splitext(sub_video_file.filename)[1]
                sub_video_filename = f"{sub_product_id}_svideo{ext}"
                video_path = os.path.join(app.config['UPLOAD_FOLDER'], sub_video_filename)
                sub_video_file.save(video_path)

            cursor.execute("""
                UPDATE sub_product
                SET image1 = %s, image2 = %s, image3 = %s, image4 = %s, image5 = %s,
                    video = %s
                WHERE id = %s
            """, (
                sub_images[0], sub_images[1], sub_images[2], sub_images[3], sub_images[4],
                sub_video_filename, sub_product_id
            ))

            combo_variant_ids = request.form.getlist("combo_variant_ids[]")
            combo_flavour_ids = request.form.getlist("combo_flavour_ids[]")

            for v_id, f_id in zip(combo_variant_ids, combo_flavour_ids):
                price_field = f"combo_price_{v_id}_{f_id}"
                price = request.form.get(price_field)

                if price:
                    cursor.execute("""
                        INSERT INTO variant_flavour_price (sub_product_id, variant_id,     flavour_id, price)
                        VALUES (%s, %s, %s, %s)
                    """, (sub_product_id, v_id, f_id, price))

            conn.commit()
            cursor.close()
            conn.close()

            if product:
                flash(f"Sub-product added with Sub-product ID: {sub_product_id}")
            else:
                flash(f"Product added with ID: {product_id_main}, Sub-product added with Sub-product ID: {sub_product_id}")


            return redirect(url_for('admin_view_product'))

        except Exception as e:
            import traceback
            traceback.print_exc()
            flash(f"Error during upload: {e}")
            return redirect(url_for('admin_dashboard'))

    else:
        # === NEW: Fetch products from tb_products for dropdown ===
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM tb_products ORDER BY name")
        products = cursor.fetchall()
        cursor.execute("""
        SELECT sp.id, sp.name, p.name AS product_name
        FROM sub_product sp
        JOIN product p ON sp.product_id = p.id
        ORDER BY p.name, sp.name
        """)
        subproducts = cursor.fetchall()

        cursor.execute("SELECT id, name FROM variant ORDER BY name")
        variants = cursor.fetchall()

        cursor.execute("SELECT id, name FROM flavour ORDER BY name")
        flavours = cursor.fetchall()

        cursor.close()
        conn.close()

        print("Products fetched for dropdown:")
        print(products)

        return render_template('admin_dashboard.html', products=products, subproducts=subproducts, variants=variants,
        flavours=flavours)

@app.route("/admin-view-product")
@login_required
def admin_view_product():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                p.id AS product_id,
                p.name AS product_name,
                sp.id AS sub_id,
                sp.name AS sub_product_name,
                sp.price AS sub_product_price,
                sp.new_price AS sub_product_new_price
            FROM
                product p
            LEFT JOIN
                sub_product sp ON p.id = sp.product_id
        """)

        products = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template("admin_view_product.html", products=products, user=current_user)

    except Exception as e:
        print("Error:", e)
        flash("Failed to load product data.")
        return render_template("admin_view_product.html", products=[], user=current_user)


@app.route('/add_categories', methods=['GET', 'POST'])
@login_required
def add_categories():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        name = request.form['name'].strip()
        cid = request.form.get('id')
        # Check for duplicate category
        cursor.execute("SELECT id FROM tb_products WHERE name = %s", (name,))
        existing = cursor.fetchone()
        if existing and (cid is None or int(cid) != existing['id']):
            flash(f'Category "{name}" already exists!', 'warning')
            cursor.close()
            conn.close()
            # :exclamation: You must fetch categories again for GET
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM tb_products")
            categories = cursor.fetchall()
            return render_template('ad_add_categories.html', categories=categories)
        # If valid insert/update
        if cid:
            cursor.execute("SELECT name FROM tb_products WHERE id = %s", (cid,))
            row = cursor.fetchone()
            if row:
                old_name = row['name']
                cursor.execute("UPDATE tb_products SET name = %s WHERE id = %s", (name, cid))
                cursor.execute("UPDATE product SET name = %s WHERE name = %s", (name, old_name))
        else:
            cursor.execute("INSERT INTO tb_products (name) VALUES (%s)", (name,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Category saved successfully.", "success")
        return redirect(url_for('add_categories'))  # :white_check_mark: Return here!
    # :white_check_mark: Default GET route logic
    cursor.execute("SELECT * FROM tb_products")
    categories = cursor.fetchall()
    edit_products = None
    if request.args.get('edit_id'):
        cursor.execute("SELECT * FROM tb_products WHERE id = %s", (request.args.get('edit_id'),))
        edit_products = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('ad_add_categories.html', categories=categories, edit_products=edit_products)

@app.route('/edit_category/<int:category_id>')
def edit_category(category_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tb_products WHERE id = %s", (category_id,))
    edit_category = cursor.fetchone()
    cursor.execute("SELECT * FROM tb_products")
    categories = cursor.fetchall()

    cursor.close()
    conn.close()
    # return redirect(url_for('add_categories'))

    return render_template("ad_add_categories.html", edit_category=edit_category, categories=categories)

@app.route('/delete_category/<int:category_id>')
def delete_category(category_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Step 1: Get the name from tb_products using the ID
    cursor.execute("SELECT name FROM tb_products WHERE id = %s", (category_id,))
    product_row = cursor.fetchone()

    if product_row:
        product_name = product_row['name']

        # Step 2: Get the ID from product where name matches
        cursor.execute("SELECT id FROM product WHERE name = %s", (product_name,))
        product_entry = cursor.fetchone()

        if product_entry:
            product_id = product_entry['id']

            # Step 3: Delete from sub_product using product_id
            cursor.execute("DELETE FROM sub_product WHERE product_id = %s", (product_id,))

            # Step 4: Delete from product
            cursor.execute("DELETE FROM product WHERE id = %s", (product_id,))

    # Step 5: Finally delete from tb_products
    cursor.execute("DELETE FROM tb_products WHERE id = %s", (category_id,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('add_categories'))

@app.route('/add_flavour', methods=['GET', 'POST'])
@login_required
def add_flavour():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['flavour'].strip()
        id = request.form.get('id')

        cursor.execute("SELECT id FROM flavour WHERE LOWER(name) = LOWER(%s)", (name,))
        existing = cursor.fetchone()

        if existing and (not id or str(existing['id']) != str(id)):
            flash(f"Flavour '{name}' already exists.", 'error')
            return redirect(url_for('add_flavour'))  # redirect to prevent resubmission

        if id:
            cursor.execute("SELECT name FROM flavour WHERE id = %s", (id,))
            row = cursor.fetchone()
            if row:
                old_name = row['name']
                cursor.execute("UPDATE flavour SET name = %s WHERE id = %s", (name, id))
                cursor.execute("UPDATE orderitems SET flavour = %s WHERE flavour = %s", (name, old_name))
        else:
            cursor.execute("INSERT INTO flavour (name) VALUES (%s)", (name,))
        conn.commit()
        return redirect(url_for('add_flavour'))

    cursor.execute("SELECT * FROM flavour")
    flavours = cursor.fetchall()

    edit_flavour = None
    if request.args.get('edit_id'):
        cursor.execute("SELECT * FROM flavour WHERE id = %s", (request.args.get('edit_id'),))
        edit_flavour = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('ad_add_flavour.html', flavours=flavours, edit_flavour=edit_flavour)

@app.route('/edit_flavour/<int:flavour_id>')
@login_required
def edit_flavour(flavour_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM flavour WHERE id = %s", (flavour_id,))
    edit_category = cursor.fetchone()
    cursor.execute("SELECT * FROM flavour")
    flavours = cursor.fetchall()
    cursor.close()
    conn.close()
    # return redirect(url_for('add_categories'))
    return render_template("ad_add_flavour.html", edit_flavour=edit_flavour, flavours=flavours)

@app.route('/add_variant', methods=['GET', 'POST'])
@login_required
def add_variant():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['variant'].strip()
        variant_id = request.form.get('id')

        # Check for duplicates
        cursor.execute("SELECT id FROM variant WHERE LOWER(name) = LOWER(%s)", (name,))
        existing = cursor.fetchone()

        if existing and (not variant_id or str(existing['id']) != str(variant_id)):
            flash(f"Variant '{name}' already exists.", 'error')
            return redirect(url_for('add_variant'))

        if variant_id:
            cursor.execute("SELECT name FROM variant WHERE id = %s", (variant_id,))
            old_row = cursor.fetchone()
            if old_row:
                old_name = old_row['name']
                cursor.execute("UPDATE variant SET name = %s WHERE id = %s", (name, variant_id))
                cursor.execute("UPDATE orderitems SET variant = %s WHERE variant = %s", (name, old_name))
        else:
            cursor.execute("INSERT INTO variant (name) VALUES (%s)", (name,))

        conn.commit()
        return redirect(url_for('add_variant'))

    # GET
    cursor.execute("SELECT * FROM variant ORDER BY name")
    variants = cursor.fetchall()

    edit_variant = None
    if request.args.get('edit_id'):
        cursor.execute("SELECT * FROM variant WHERE id = %s", (request.args.get('edit_id'),))
        edit_variant = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('ad_add_variant.html', variants=variants, edit_variant=edit_variant)

@app.route('/edit_variant/<int:variant_id>')
@login_required
def edit_variant(variant_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # FIXED: Correct tuple usage
    cursor.execute("SELECT * FROM variant WHERE id = %s", (variant_id,))
    edit_variant = cursor.fetchone()

    cursor.execute("SELECT * FROM variant ORDER BY name")
    variants = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("ad_add_variant.html", edit_variant=edit_variant, variants=variants)

@app.route('/delete_variant/<int:variant_id>')
@login_required
def delete_variant(variant_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM variant WHERE id = %s", (variant_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('add_variant'))

@app.route('/delete_flavour/<int:flavour_id>')
@login_required
def delete_flavour(flavour_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM flavour WHERE id = %s", (flavour_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('add_flavour'))

@app.route('/add_accessory', methods=['GET', 'POST'])
@login_required
def add_accessory():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['accessory'].strip()
        price = request.form['price'].strip()
        id = request.form.get('id')

        # Validate price input
        try:
            price = float(price)
        except ValueError:
            flash("Invalid price entered.", "error")
            return redirect(url_for('add_accessory'))

        # Check if accessory already exists with the same name (case-insensitive)
        cursor.execute("SELECT id FROM tb_accessories WHERE LOWER(name) = LOWER(%s)", (name,))
        existing = cursor.fetchone()

        if existing and (not id or str(existing['id']) != str(id)):
            flash(f"Accessory '{name}' already exists.", 'error')
            return redirect(url_for('add_accessory'))

        if id:
            # Update accessory
            cursor.execute("UPDATE tb_accessories SET name = %s, price = %s WHERE id = %s", (name, price, id))
        else:
            # Insert new accessory
            cursor.execute("INSERT INTO tb_accessories (name, price) VALUES (%s, %s)", (name, price))

        conn.commit()
        return redirect(url_for('add_accessory'))

    # Get all accessories for display
    cursor.execute("SELECT * FROM tb_accessories")
    accessories = cursor.fetchall()

    # If editing, fetch specific accessory
    edit_accessory = None
    if request.args.get('edit_id'):
        cursor.execute("SELECT * FROM tb_accessories WHERE id = %s", (request.args.get('edit_id'),))
        edit_accessory = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('ad_add_access.html', accessories=accessories, edit_accessory=edit_accessory)


@app.route('/edit_accessory/<int:accessory_id>')
@login_required
def edit_accessory(accessory_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch the accessory to edit
    cursor.execute("SELECT * FROM tb_accessories WHERE id = %s", (accessory_id,))
    edit_accessory = cursor.fetchone()

    # Fetch all accessories for listing
    cursor.execute("SELECT * FROM tb_accessories")
    accessories = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("ad_add_access.html", edit_accessory=edit_accessory, accessories=accessories)

@app.route('/delete_accessory/<int:accessory_id>')
@login_required
def delete_accessory(accessory_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tb_accessories WHERE id = %s", (accessory_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('add_accessory'))

#---------------------------------------------------------------------------------- ADMIN ORDER HISTORY ------

@app.route('/order_history')
@login_required
def order_history():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Step 1: Get all orders with user info (Changed u.username to u.name AS username)
    cursor.execute("""
        SELECT
            o.id AS order_id,
            o.user_id,
            u.name AS username,
            o.timestamp,
            o.gst,
            o.grand_total,
            o.status
        FROM orders o
        JOIN user u ON o.user_id = u.id
        ORDER BY o.timestamp DESC
    """)
    order_rows = cursor.fetchall()
    order_columns = [desc[0] for desc in cursor.description]
    orders = [dict(zip(order_columns, row)) for row in order_rows]

    # Convert UTC timestamp to IST and format it
    ist = pytz.timezone("Asia/Kolkata")
    utc = pytz.utc
    for order in orders:
        timestamp = order["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        localized_utc = utc.localize(timestamp)
        ist_datetime = localized_utc.astimezone(ist)
        order["formatted_time"] = ist_datetime.strftime("%d-%m-%Y %I:%M:%S %p")

    # Step 2: Get all order items with image
    cursor.execute("""
        SELECT
            oi.order_id,
            oi.image,
            oi.sub_productname,
            oi.variant,
            oi.v_cost,
            oi.acc_1, oi.a_quantity1, oi.a_cost1,
            oi.acc_2, oi.a_quantity2, oi.a_cost2,
            oi.acc_3, oi.a_quantity3, oi.a_cost3,
            oi.acc_4, oi.a_quantity4, oi.a_cost4,
            oi.acc_5, oi.a_quantity5, oi.a_cost5,
            oi.message
        FROM orderitems oi
    """)
    item_rows = cursor.fetchall()
    item_columns = [desc[0] for desc in cursor.description]
    order_items = [dict(zip(item_columns, row)) for row in item_rows]

    conn.close()

    # Step 3: Group order items by order_id
    grouped_items = defaultdict(list)
    for item in order_items:
        grouped_items[item['order_id']].append(item)

    # Step 4: Combine into final structure
    order_history = []
    for order in orders:
        order['items'] = grouped_items[order['order_id']]
        order_history.append(order)

    return render_template("ad_order_history.html", orders=order_history)


@app.route('/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    new_status = request.form.get('status')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = %s WHERE id = %s", (new_status, order_id))

    # Changed u.username to u.name
    cursor.execute("""
        SELECT u.email, u.name, o.timestamp
        FROM orders o
        JOIN user u ON o.user_id = u.id
        WHERE o.id = %s
    """, (order_id,))
    result = cursor.fetchone()

    if result:
        user_email, username, order_time = result
        send_status_email(user_email, username, new_status, order_id, order_time)

    conn.commit()
    conn.close()

    flash("Order status updated and email sent.", "success")
    return redirect(url_for('order_history'))

def send_status_email(to_email, username, status, order_id, order_time):
    sender_email = "sednainfo5@gmail.com"
    sender_password = "mfzm afcu fwma latu"
    subject = f"Your Order #{order_id} Status Update"

    # Status-specific messages
    status_messages = {
        "Pending": "We've received your order and it's currently pending confirmation.",
        "Confirmed": "Your order has been confirmed and will be processed shortly.",
        "Preparing": "Your delicious cake is being prepared!",
        "Ready": "Your order is ready for pickup or delivery.",
        "Out for Delivery": "Your order is out for delivery!",
        "Delivered": "Your order has been successfully delivered. Enjoy your cake!",
        "Cancelled": "Your order has been cancelled. If this is a mistake, please contact us."
    }

    status_message = status_messages.get(status, "Your order status has been updated.")

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <p>Hello <strong>{username}</strong>,</p>

        <p><strong>Order ID:</strong> {order_id}<br>
           <strong>Order Date:</strong> {order_time}</p>

        <p>{status_message}</p>

        <p>Thank you for choosing our <strong>Cake Store</strong>!<br>
        - <em>S S Bakers</em></p>
      </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.route('/custom_cake_order_history')
@login_required
def custom_cake_order_history():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            cc.id,
            cc.user_id,
            u.name AS username,
            cc.name,
            cc.phone,
            cc.email,
            cc.flavour,
            cc.variant,
            cc.msg,
            cc.img,
            cc.date,
            cc.time,
            cc.address,
            cc.instruction,
            cc.city,
            cc.outlet,
            cc.status
        FROM custom_cake cc
        JOIN user u ON cc.user_id = u.id
        ORDER BY cc.id DESC
    """)

    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    orders = [dict(zip(columns, row)) for row in rows]
    conn.close()

    # Format date + time assuming already in IST
    for order in orders:
        raw_date = order["date"]
        raw_time = order["time"]

        # Parse strings if necessary
        if isinstance(raw_date, str):
            raw_date = datetime.strptime(raw_date, "%Y-%m-%d")
        if isinstance(raw_time, str):
            raw_time = datetime.strptime(raw_time, "%H:%M").time()

        combined_datetime = datetime.combine(raw_date, raw_time)

        # ✅ NO UTC conversion, just formatting
        order["formatted_datetime"] = combined_datetime.strftime("%d-%m-%Y %I:%M:%S %p")

    return render_template(
        'custom_cake_order_history.html',
        orders=orders,
        user_logged_in=True
    )

@app.route('/update_custom_order_status/<int:order_id>', methods=['POST'])
def update_custom_order_status(order_id):
    new_status = request.form.get('status')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE custom_cake SET status = %s WHERE id = %s", (new_status, order_id))

    cursor.execute("""
        SELECT u.email, u.name AS username, CONCAT(cc.date, ' ', cc.time) AS order_time
        FROM custom_cake cc
        JOIN user u ON cc.user_id = u.id
        WHERE cc.id = %s
    """, (order_id,))
    result = cursor.fetchone()

    if result:
        user_email, username, order_time = result
        send_status_email(user_email, username, new_status, order_id, order_time)

    conn.commit()
    conn.close()

    flash("Order status updated and email sent.", "success")
    return redirect(url_for('custom_cake_order_history'))


@app.route('/reports', methods=['GET', 'POST'])
@login_required
def report_page():
    status_filter = request.form.get('status') or 'All'
    date_range = request.form.get('date_filter') or 'All'

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            o.id AS order_id,
            o.user_id,
            u.name AS username,
            o.timestamp,
            o.gst,
            o.grand_total,
            o.status,
            oi.image,
            oi.sub_productname,
            oi.variant,
            oi.v_cost,
    oi.acc_1,  oi.a_cost1,  oi.a_quantity1,
    oi.acc_2,  oi.a_cost2,  oi.a_quantity2,
    oi.acc_3,  oi.a_cost3,  oi.a_quantity3,
    oi.acc_4,  oi.a_cost4,  oi.a_quantity4,
    oi.acc_5,  oi.a_cost5,  oi.a_quantity5,
            oi.message
        FROM orders o
        JOIN user u ON o.user_id = u.id
        JOIN orderitems oi ON o.id = oi.order_id
        WHERE 1=1
    """

    filters = []
    params = []

    # Status filter
    if status_filter and status_filter != 'All':
        filters.append("o.status = %s")
        params.append(status_filter)

    # Date filter
    if date_range and date_range != 'All':
        now = datetime.now()
        if date_range == 'Today':
            filters.append("DATE(o.timestamp) = DATE(%s)")
            params.append(now)
        elif date_range == 'Last Week':
            filters.append("o.timestamp >= %s")
            params.append(now - timedelta(days=7))
        elif date_range == 'Last Month':
            filters.append("o.timestamp >= %s")
            params.append(now - timedelta(days=30))
        elif date_range == 'Last Six Months':
            filters.append("o.timestamp >= %s")
            params.append(now - timedelta(days=182))
        elif date_range == '1 Year':
            filters.append("o.timestamp >= %s")
            params.append(now - timedelta(days=365))

    if filters:
        query += " AND " + " AND ".join(filters)

    query += " ORDER BY o.timestamp DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    entries = [dict(zip(columns, row)) for row in rows]

    conn.close()

    # Convert UTC timestamp to IST and format
    ist = pytz.timezone('Asia/Kolkata')
    utc = pytz.utc

    for entry in entries:
        utc_time = entry['timestamp']
        if isinstance(utc_time, str):
            utc_time = datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S")

        localized_utc = utc.localize(utc_time)
        ist_time = localized_utc.astimezone(ist)
        entry['formatted_time'] = ist_time.strftime('%d-%m-%Y %I:%M:%S %p')

    return render_template(
        "ad_report_page.html",
        entries=entries,
        selected_status=status_filter,
        selected_date=date_range
    )

@app.route("/download_report_excel", methods=["GET"])
@login_required
def download_report_excel():
    # 1️⃣  read query‑string filters
    status      = request.args.get("status", "All")
    date_filter = request.args.get("date_filter", "All")

    # 2️⃣  build SQL
    query = """
        SELECT
            o.id AS order_id,
            u.name AS username,
            o.timestamp,
            o.status,
            oi.sub_productname,
            oi.variant,
            oi.v_cost,
            oi.acc_1, oi.a_quantity1,
            oi.acc_2, oi.a_quantity2,
            oi.acc_3, oi.a_quantity3,
            oi.acc_4, oi.a_quantity4,
            oi.acc_5, oi.a_quantity5
        FROM orders o
        JOIN user       u  ON u.id       = o.user_id
        JOIN orderitems oi ON oi.order_id = o.id
        WHERE 1 = 1
    """
    params, filters = [], []

    # status filter
    if status != "All":
        filters.append("o.status = %s")
        params.append(status)

    # date‑range filter
    if date_filter != "All":
        now = datetime.now()
        ranges = {
            "Today":          ("DATE(o.timestamp) = DATE(%s)",now),
            "Last Week":      ("o.timestamp >= %s", now - timedelta(days=7)),
            "Last Month":     ("o.timestamp >= %s", now - timedelta(days=30)),
            "Last Six Months":("o.timestamp >= %s", now - timedelta(days=182)),
            "1 Year":         ("o.timestamp >= %s", now - timedelta(days=365)),
        }
        clause, value = ranges[date_filter]
        filters.append(clause)
        params.append(value)

    if filters:
        query += " AND " + " AND ".join(filters)

    query += " ORDER BY o.timestamp DESC"

    # 3️⃣  run query
    conn   = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    data    = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()

    # 4️⃣  build Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Order Report"
    ws.append(columns)

    # convert timestamp column (UTC → IST) once per row
    utc = pytz.utc
    ist = pytz.timezone("Asia/Kolkata")
    ts_idx = columns.index("timestamp")

    for row in data:
        row = list(row)                       # make tuple mutable
        ts  = row[ts_idx]

        # parse if returned as string
        if isinstance(ts, str):
            ts = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")

        # localize to UTC then convert to IST
        ist_dt      = utc.localize(ts).astimezone(ist)
        row[ts_idx] = ist_dt.strftime("%d-%m-%Y %I:%M:%S %p")

        ws.append(row)

    # 5️⃣  stream file back to browser
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    filename = f"order_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        stream,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

#------------------------------------------------------------------------------- ADMIN PRODUCT MANAGEMENT ------
@app.route('/view_product/<int:product_id>/<int:subproduct_id>', methods=['GET'])
def view_product(product_id, subproduct_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch main product info
        cursor.execute("""
            SELECT id AS product_id, name AS product_name, image1 AS product_image1,
                   category AS product_category, type AS product_type, offer AS product_offer,
                   youtube AS product_youtube, description AS product_description
            FROM product WHERE id = %s
        """, (product_id,))
        product = cursor.fetchone()
        if not product:
            return "Product not found", 404

        # Fetch sub-product info (simplified)
        cursor.execute("""
            SELECT id AS sub_id, name AS sub_product_name,
                   image1 AS sub_product_image1, image2 AS sub_product_image2,
                   image3 AS sub_product_image3, image4 AS sub_product_image4,
                   image5 AS sub_product_image5, video AS sub_product_video,
                   category AS sub_product_category, type AS sub_product_type,
                   offer AS sub_product_offer, description AS sub_product_description,
                   youtube AS sub_product_youtube, delivery_cost,packaging_cost
            FROM sub_product
            WHERE product_id = %s AND id = %s
        """, (product_id, subproduct_id))
        sub_product = cursor.fetchone()
        if not sub_product:
            return "Sub Product not found", 404

        # Fetch selected variants
        cursor.execute("""
            SELECT v.id, v.name
            FROM variant v
            JOIN subproduct_variant sv ON sv.variant_id = v.id
            WHERE sv.sub_product_id = %s
        """, (subproduct_id,))
        selected_variants = cursor.fetchall()

        # Fetch selected flavours
        cursor.execute("""
            SELECT f.id, f.name
            FROM flavour f
            JOIN subproduct_flavour sf ON sf.flavour_id = f.id
            WHERE sf.sub_product_id = %s
        """, (subproduct_id,))
        selected_flavours = cursor.fetchall()

        # Fetch variant-flavour-price combinations
        cursor.execute("""
            SELECT v.name AS variant_name, f.name AS flavour_name, vfp.price
            FROM variant_flavour_price vfp
            JOIN variant v ON v.id = vfp.variant_id
            JOIN flavour f ON f.id = vfp.flavour_id
            WHERE vfp.sub_product_id = %s
        """, (subproduct_id,))
        combo_prices = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            "ad_view_pdt.html",
            product=product,
            sub_product=sub_product,
            selected_variants=selected_variants,
            selected_flavours=selected_flavours,
            combo_prices=combo_prices
        )

    except Exception as e:
        return f"Error viewing product: {e}"

@app.route('/edit_product/<int:product_id>/<int:subproduct_id>', methods=['GET', 'POST'])
def edit_product(product_id, subproduct_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # upload_folder = 'app/static/uploads/'
        upload_folder = app.config['UPLOAD_FOLDER']

        # Fetch main product details
        cursor.execute("""
            SELECT id AS product_id, name AS product_name, image1 AS product_image1,
                   category AS product_category, type AS product_type,
                   offer AS product_offer, youtube AS product_youtube,
                   description AS product_description
            FROM product
            WHERE id = %s
        """, (product_id,))
        product = cursor.fetchone()
        if not product:
            return "Product not found", 404

        # Fetch sub-product details
        cursor.execute("""
            SELECT id AS sub_id, name AS sub_product_name,
                   image1 AS sub_product_image1, image2 AS sub_product_image2,
                   image3 AS sub_product_image3, image4 AS sub_product_image4,
                   image5 AS sub_product_image5, video AS sub_product_video,
                   category AS sub_product_category, type AS sub_product_type,
                   offer AS sub_product_offer, description AS sub_product_description,
                   youtube AS sub_product_youtube, delivery_cost, packaging_cost
            FROM sub_product
            WHERE product_id = %s AND id = %s
        """, (product_id, subproduct_id))
        sub_product = cursor.fetchone()
        if not sub_product:
            return "Sub Product not found", 404

        if request.method == 'POST':
            # Update main product
            product_id_from_form = request.form.get('product_name')
            cursor.execute("SELECT name FROM product WHERE id = %s", (product_id_from_form,))
            prod_row = cursor.fetchone()
            if not prod_row:
                return "Invalid product selected", 400
            product_name = prod_row['name']

            product_category = request.form.get('category')
            product_type = request.form.get('type')
            product_offer = request.form.get('offer')
            product_description = request.form.get('description')
            product_youtube = request.form.get('youtube')

            product_image1 = request.files.get('product_image1')
            product_image1_filename = product['product_image1']
            if product_image1:
                product_image1_filename = secure_filename(product_image1.filename)
                product_image1.save(os.path.join(upload_folder, product_image1_filename))

            cursor.execute("""
                UPDATE product
                SET name = %s, category = %s, type = %s, offer = %s,
                    description = %s, youtube = %s, image1 = %s
                WHERE id = %s
            """, (
                product_name, product_category, product_type, product_offer,
                product_description, product_youtube, product_image1_filename, product_id
            ))

            # Update sub-product
            sub_product_name = request.form.get('sub_product_name')
            sub_product_category = request.form.get('sub_product_category')
            sub_product_type = request.form.get('sub_product_type')
            sub_product_offer = request.form.get('sub_product_offer')
            sub_product_description = request.form.get('sub_product_description')
            sub_product_youtube = request.form.get('sub_product_youtube')
            delivery_cost = request.form.get('delivery_cost')
            packaging_cost = request.form.get('packaging_cost')
            # Handle images
            sub_images = []
            for i in range(1, 6):
                image_file = request.files.get(f'sub_product_image{i}')
                existing_image = sub_product.get(f'sub_product_image{i}')
                if image_file and image_file.filename:
                    filename = secure_filename(image_file.filename)
                    image_file.save(os.path.join(upload_folder, filename))
                    sub_images.append(filename)
                else:
                    sub_images.append(existing_image)

            # Handle video
            sub_video_file = request.files.get('sub_product_video')
            sub_video_filename = sub_product['sub_product_video']
            if sub_video_file and sub_video_file.filename:
                sub_video_filename = secure_filename(sub_video_file.filename)
                sub_video_file.save(os.path.join(upload_folder, sub_video_filename))

            cursor.execute("""
                UPDATE sub_product
                SET name = %s, category = %s, type = %s, offer = %s,
                    description = %s, youtube = %s,
                    image1 = %s, image2 = %s, image3 = %s, image4 = %s, image5 = %s,
                    video = %s, delivery_cost = %s, packaging_cost = %s
                WHERE id = %s AND product_id = %s
            """, (
                sub_product_name, sub_product_category, sub_product_type, sub_product_offer,
                sub_product_description, sub_product_youtube,
                sub_images[0], sub_images[1], sub_images[2], sub_images[3], sub_images[4],
                sub_video_filename, delivery_cost, packaging_cost,
                subproduct_id, product_id
            ))

            # === Update Variants, Flavours and Prices ===
            selected_variant_ids = request.form.getlist('available_variants')
            selected_flavour_ids = request.form.getlist('available_flavours')

            # Clear old mappings
            cursor.execute("DELETE FROM subproduct_variant WHERE sub_product_id = %s", (subproduct_id,))
            cursor.execute("DELETE FROM subproduct_flavour WHERE sub_product_id = %s", (subproduct_id,))
            cursor.execute("DELETE FROM variant_flavour_price WHERE sub_product_id = %s", (subproduct_id,))

            # Insert new mappings
            for v_id in selected_variant_ids:
                cursor.execute("INSERT INTO subproduct_variant (sub_product_id, variant_id) VALUES (%s, %s)", (subproduct_id, v_id))

            for f_id in selected_flavour_ids:
                cursor.execute("INSERT INTO subproduct_flavour (sub_product_id, flavour_id) VALUES (%s, %s)", (subproduct_id, f_id))

            combo_variant_ids = request.form.getlist("combo_variant_ids[]")
            combo_flavour_ids = request.form.getlist("combo_flavour_ids[]")

            for v_id, f_id in zip(combo_variant_ids, combo_flavour_ids):
                price_field = f"combo_price_{v_id}_{f_id}"
                price = request.form.get(price_field)
                if price:
                    cursor.execute("""
                        INSERT INTO variant_flavour_price (sub_product_id, variant_id, flavour_id, price)
                        VALUES (%s, %s, %s, %s)
                    """, (subproduct_id, v_id, f_id, price))

            conn.commit()
            return redirect(url_for('admin_view_product'))

        # === Render GET view ===
        cursor.execute("SELECT id, name FROM product ORDER BY name")
        product_list = cursor.fetchall()

        cursor.execute("SELECT id, name FROM variant ORDER BY name")
        variants = cursor.fetchall()

        cursor.execute("SELECT id, name FROM flavour ORDER BY name")
        flavours = cursor.fetchall()

        cursor.execute("SELECT variant_id FROM subproduct_variant WHERE sub_product_id = %s", (subproduct_id,))
        selected_variant_ids = [row['variant_id'] for row in cursor.fetchall()]

        cursor.execute("SELECT flavour_id FROM subproduct_flavour WHERE sub_product_id = %s", (subproduct_id,))
        selected_flavour_ids = [row['flavour_id'] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT variant_id, flavour_id, price
            FROM variant_flavour_price
            WHERE sub_product_id = %s
        """, (subproduct_id,))
        combo_prices = { (row['variant_id'], row['flavour_id']): row['price'] for row in cursor.fetchall() }

        return render_template("ad_edit_pdt.html",
            product=product,
            sub_product=sub_product,
            product_list=product_list,
            variants=variants,
            flavours=flavours,
            selected_variant_ids=selected_variant_ids,
            selected_flavour_ids=selected_flavour_ids,
            combo_prices=combo_prices
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error editing product: {e}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# return render_template("ad_edit_pdt.html", product=product, sub_product=sub_product, product_list=product_list)
@app.route('/delete_product/<int:subproduct_id>', methods=['POST'])
def delete_product(subproduct_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete the subproduct by ID
        cursor.execute("DELETE FROM sub_product WHERE id = %s", (subproduct_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('admin_view_product'))  # Redirect back to the main dashboard

    except Exception as e:
        return f"Error deleting sub-product: {e}", 500

#----------------------------------------------------------------------------------- ADMIN MASTER LOCATION ----

@app.route("/master-location", methods=["GET", "POST"])
@login_required
def master_location():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Handle Add New Location
    if request.method == "POST" and 'id' not in request.form:
        mainlocation = request.form['mainlocation']
        area = request.form['area']
        cursor.execute("INSERT INTO tb_location(mainlocation, area) VALUES (%s,%s)", (mainlocation, area))
        conn.commit()
        return redirect(url_for('master_location'))

    # Handle Edit Form Submit
    if request.method == "POST" and 'id' in request.form:
        location_id = request.form['id']
        mainlocation = request.form['mainlocation']
        area = request.form['area']
        cursor.execute("UPDATE tb_location SET mainlocation=%s, area=%s WHERE id=%s",
                       (mainlocation, area, location_id))
        conn.commit()
        return redirect(url_for('master_location'))

    # Fetch all locations
    cursor.execute("SELECT * FROM tb_location ORDER BY mainlocation ASC")
    locations = cursor.fetchall()

    # Check if editing a specific location
    edit_location = None
    if request.args.get('edit'):
        location_id = request.args.get('edit')
        cursor.execute("SELECT * FROM tb_location WHERE id=%s", (location_id,))
        edit_location = cursor.fetchone()

    cursor.close()
    conn.close()
    return render_template("ad_master_location.html", user=current_user, locations=locations, edit_location=edit_location)

@app.route("/delete-location/<int:location_id>", methods=["GET"])
@login_required
def delete_location(location_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tb_location WHERE id=%s", (location_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('master_location'))

# -----------------------------------------------------------------------------------------------------------------
@app.route('/about')
def about():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if 'user_id' in session:
        user_id = session['user_id']
        cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
        users = cursor.fetchall()
        return render_template("about.html", users= users)
    return render_template("about.html")

@app.route('/cake_variety')
def cake_variety():
    user_logged_in = current_user.is_authenticated
    products = Product.query.all()
    
    # Get category from URL parameter
    selected_category = request.args.get('category', None)

    # Fetch user details if logged in
    users = None
    if 'user_id' in session:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        user_id = session['user_id']
        cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
        users = cursor.fetchall()

    # Build a dictionary: product name → subproducts
    subproduct_categories = {}
    for product in products:
        formatted_name = product.name.strip().lower().replace(" ", "_")
        subproducts = Sub_Product.query.filter_by(product_id=product.id).all()
        subproduct_categories[formatted_name] = subproducts

    return render_template(
        'variety.html',
        products=products,
        subproduct_categories=subproduct_categories,
        user_logged_in=user_logged_in,
        users=users,
        selected_category=selected_category  # Pass to template
    )

@app.route('/gallery')  # ✅ Fix: Ensure this route is included
def gallery():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if 'user_id' in session:
        user_id = session['user_id']
        cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
        users = cursor.fetchall()
        return render_template("gallery.html", users= users)

    return render_template("gallery.html")

@app.route('/our_outlet')  # ✅ Fix: Ensure this route is included
def our_outlet():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if 'user_id' in session:
        user_id = session['user_id']
        cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
        users = cursor.fetchall()
        return render_template("outlet.html", users=users)
    return render_template("outlet.html")

@app.route('/enquiry', methods=['POST'])
def enquiry():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        city = request.form.get('city')
        message = request.form.get('message')

        msg = Message(subject="New Franchise Enquiry",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=['sednainfo5@gmail.com'])  # Change if needed

        msg.body = f"""
        Franchise Enquiry Submission:

        Name: {name}
        Phone: {phone}
        Email: {email}
        City: {city}
        Message: {message}
        """

        try:
            mail.send(msg)
            flash("Enquiry sent successfully! We'll contact you soon.", "success")
        except Exception as e:
            flash(f"Enquiry failed to send. Error: {e}", "danger")

        return redirect(url_for('franchise'))  # or whatever route renders your franchise page

@app.route('/contact', methods=['GET', 'POST'])
@csrf.exempt  # ✅ Add this line to disable CSRF for contact form
def contact():
    users = None
    if 'user_id' in session:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        user_id = session['user_id']
        cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
        users = cursor.fetchall()
        cursor.close()
        conn.close()

    if request.method == 'POST':
        name = request.form.get('fname', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        message = request.form.get('message', '').strip()

        # Basic validation (optional)
        if not name or not email or not message:
            flash("Please fill in required fields (Name, Email, Message).", "danger")
            return redirect(url_for('contact'))

        msg = Message(
            subject="New Contact Form Submission",
            sender=app.config['MAIL_USERNAME'],
            recipients=['sednainfo5@gmail.com']  # change if needed
        )

        # Include address in the body
        msg.body = f"""
            Name: {name}
            Phone: {phone}
            Email: {email}
            Address: {address}
            Message:
            {message}
            """

        try:
            mail.send(msg)
            flash("Message sent successfully!", "success")
        except Exception as e:
            # For debugging you can log the exception
            app.logger.error("Contact email send failed: %s", e)
            flash(f"Message failed to send. Error: {e}", "danger")

        return redirect(url_for('contact'))

    return render_template('contact.html', users=users)

@app.route('/franchise')  # ✅ Fix: Ensure this route is included
@csrf.exempt
def franchise():
    return render_template("franchise.html")


@app.route("/get_cities", methods=["GET"])
def get_cities():
    try:
        # Get distinct cities from the Location table
        cities = db.session.query(Location.mainlocation).distinct().all()
        city_list = [city[0] for city in cities]
        return jsonify(city_list)
    except Exception as e:
        logging.error(f"Error fetching cities: {e}")
        return jsonify({'error': 'Failed to fetch cities'}), 500

@app.route("/get_outlets/<string:mainlocation>", methods=["GET"])
def get_outlets(mainlocation):
    try:
        outlets = Location.query.filter_by(mainlocation=mainlocation).all()
        if not outlets:
            return jsonify({'error': 'No outlets found for the specified city'}), 404

        outlet_list = [outlet.area for outlet in outlets]
        return jsonify(outlet_list)
    except Exception as e:
        logging.error(f"Error fetching outlets for {mainlocation}: {e}")
        return jsonify({'error': 'Failed to fetch outlets'}), 500

@app.route('/get_variants', methods=['GET'])
def get_variants():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM variant")
        variants = cursor.fetchall()
        return jsonify(variants)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_flavours', methods=['GET'])
def get_flavours():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM flavour")
        flavours = cursor.fetchall()
        return jsonify(flavours)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_cake_data/<int:sub_product_id>', methods=['GET'])
def get_cake_data(sub_product_id):
    try:
        sub_product = Sub_Product.query.get(sub_product_id)
        if not sub_product:
            return jsonify({'error': 'Cake not found'}), 404

        # Fetch variant and flavour IDs linked to this sub_product
        variant_ids = db.session.query(SubProductVariant.variant_id)\
            .filter_by(sub_product_id=sub_product_id).all()
        variant_ids = [v[0] for v in variant_ids]

        flavour_ids = db.session.query(SubProductFlavour.flavour_id)\
            .filter_by(sub_product_id=sub_product_id).all()
        flavour_ids = [f[0] for f in flavour_ids]

        # Now fetch the actual Variant and Flavour rows
        variants = Variant.query.filter(Variant.id.in_(variant_ids)).all()
        flavours = Flavour.query.filter(Flavour.id.in_(flavour_ids)).all()

        accessories = Accessories.query.all()

        # ✅ Fetch prices only for this sub_product
        price_map = VariantFlavourPrice.query\
            .join(Variant, Variant.id == VariantFlavourPrice.variant_id)\
            .join(Flavour, Flavour.id == VariantFlavourPrice.flavour_id)\
            .filter(VariantFlavourPrice.sub_product_id == sub_product_id)\
            .with_entities(
                Variant.id.label("variant_id"),
                Flavour.id.label("flavour_id"),
                Variant.name.label("variant_name"),
                Flavour.name.label("flavour_name"),
                VariantFlavourPrice.price
            ).all()

        price_data = [
            {
                'variant_id': p.variant_id,
                'variant': p.variant_name,
                'flavour_id': p.flavour_id,
                'flavour': p.flavour_name,
                'price': p.price
            } for p in price_map
        ]

        response_data = {
            'sub_product': {
                'id': sub_product.id,
                'name': sub_product.name,
                'image': sub_product.image1,
                'offer': sub_product.offer,
                'delivery_cost': sub_product.delivery_cost
            },
            'accessories': [
                {'name': acc.name, 'price': acc.price} for acc in accessories
            ],
            'flavours': [
                {'id': f.id, 'name': f.name} for f in flavours
            ],
            'variants': [
                {'id': v.id, 'name': v.name} for v in variants
            ],
            'prices': price_data
        }

        return jsonify(response_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to fetch cake data', 'detail': str(e)}), 500

@app.route('/cart')
def cart():
    session_id = session.get('session_id')
    users = None

    if 'user_id' in session:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        user_id = session['user_id']
        cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
        users = cursor.fetchall()

    if current_user.is_authenticated:
        cartitems = CartItem.query.filter_by(user_id=current_user.id).all()
    elif session_id:
        cartitems = CartItem.query.filter_by(session_id=session_id).all()
    else:
        cartitems = []

    processed_items = []
    for item in cartitems:
        accessories = []
        for i in range(1, 6):
            acc_name = getattr(item, f'acc_{i}', None)
            acc_cost = getattr(item, f'a_cost{i}', 0.0)
            acc_qty = getattr(item, f'a_quantity{i}', 0)
            if acc_name and acc_name.upper() != "NULL":
                accessories.append({
                    'name': acc_name,
                    'cost': acc_cost,
                    'quantity': acc_qty
                })
        processed_items.append({
            'item': item,
            'flavour': item.flavour,  # ✅ include flavour
            'accessories': accessories
        })

    return render_template('cart.html', cartitems=processed_items, session_id=session_id, users=users)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.json
    sub_product_id = data.get('sub_product_id')
    variant = data.get('variant')
    flavour = data.get('flavour')  # ✅ New
    message = data.get("message", "")

    if not sub_product_id:
        return jsonify({'error': 'Sub Product ID is required'}), 400

    if not variant:
        return jsonify({'error': 'Variant is required'}), 400
    if not flavour:
        return jsonify({'error': 'Flavour is required'}), 400

    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id

    user_id = current_user.id if current_user.is_authenticated else None

    existing_item = CartItem.query.filter_by(
        sub_product_id=sub_product_id,
        variant=variant,
        flavour=flavour,  # ✅ Include flavour in uniqueness check
        user_id=user_id,
        session_id=session_id
    ).first()

    if existing_item:
        return jsonify({'message': 'Item is already in the cart'}), 409

    sub_product = Sub_Product.query.get(sub_product_id)
    delivery_cost = sub_product.delivery_cost or 0.0
    packaging_cost= sub_product.packaging_cost or 0.0

    variant_cost = data.get('v_cost', 0.0)
    variant_qty = data.get('quantity', 1)

    accessory_total = sum([
        data.get('a_cost1', 0.0) * data.get('a_quantity1', 0),
        data.get('a_cost2', 0.0) * data.get('a_quantity2', 0),
        data.get('a_cost3', 0.0) * data.get('a_quantity3', 0),
        data.get('a_cost4', 0.0) * data.get('a_quantity4', 0),
        data.get('a_cost5', 0.0) * data.get('a_quantity5', 0)
    ])

    total_price = (variant_cost * variant_qty) + accessory_total + delivery_cost + packaging_cost

    cartitem = CartItem(
        user_id=user_id,
        session_id=session_id,
        sub_product_id=sub_product_id,
        sub_productname=data.get('sub_productname'),
        image=data.get('image'),
        variant=variant,
        flavour=flavour,  # ✅ Add flavour to cart item
        v_cost=variant_cost,
        acc_1=data.get('acc_1'),
        a_cost1=data.get('a_cost1'),
        acc_2=data.get('acc_2'),
        a_cost2=data.get('a_cost2'),
        acc_3=data.get('acc_3'),
        a_cost3=data.get('a_cost3'),
        acc_4=data.get('acc_4'),
        a_cost4=data.get('a_cost4'),
        acc_5=data.get('acc_5'),
        a_cost5=data.get('a_cost5'),
        total_price=total_price,
        quantity=variant_qty,
        a_quantity1=data.get('a_quantity1'),
        a_quantity2=data.get('a_quantity2'),
        a_quantity3=data.get('a_quantity3'),
        a_quantity4=data.get('a_quantity4'),
        a_quantity5=data.get('a_quantity5'),
        delivery_cost=delivery_cost,
        packaging_cost=packaging_cost,
        message=message
    )

    db.session.add(cartitem)
    db.session.commit()

    return jsonify({'message': 'Item added to cart successfully'}), 201

@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    try:
        session_id = session.get('session_id')
        user_id = current_user.id if current_user.is_authenticated else None

        if not session_id and not user_id:
            return jsonify({'error': 'Session expired or not logged in'}), 400

        # Build the base query
        query = CartItem.query.filter(CartItem.id == item_id)

        # Filter based on user or session
        if user_id:
            query = query.filter(CartItem.user_id == user_id)
        else:
            query = query.filter(CartItem.session_id == session_id)

        item = query.first()

        if item:
            db.session.delete(item)
            db.session.commit()
            return jsonify({'success': True}), 200  # ✅ Use JSON for fetch() in frontend
        else:
            return jsonify({'error': 'Item not found'}), 404

    except Exception as e:
        logging.error(f"Error removing item: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/update_cart_item/<int:item_id>', methods=['POST'])
def update_cart_item(item_id):
    data = request.get_json()

    variant_qty = data.get("variant_quantity")
    accessories = data.get("accessories", [])
    new_total = data.get("total_price")

    cart_item = CartItem.query.get(item_id)
    if not cart_item:
        return jsonify({"error": "Cart item not found"}), 404

    # Update variant quantity
    if variant_qty is not None:
        cart_item.quantity = variant_qty

    # Update accessories quantities
    for acc in accessories:
        index = acc["index"]
        qty = acc["quantity"]
        if 0 <= index <= 4:  # For fields a_quantity1 to a_quantity5
            setattr(cart_item, f'a_quantity{index + 1}', qty)

    cart_item.total_price = new_total

    db.session.commit()
    return jsonify({"success": True, "new_total": new_total})

@app.route('/checkout', methods=['GET'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty – please add items before checking out.', 'warning')
        return redirect(url_for('cart'))          # cart view/template
    edit_id = request.args.get('edit', type=int)  # cast to int right away
    edit_address = None
    if edit_id:
        edit_address = ManageAddress.query.get_or_404(edit_id)
        if edit_address.user_id != current_user.id:
            abort(403)
    addresses = ManageAddress.query.filter_by(user_id=current_user.id).all()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user WHERE id = %s", (current_user.id,))
    users = cursor.fetchall()       # one row expected
    cursor.close(); conn.close()    # good housekeeping :white_check_mark:
    return render_template(
        'checkout.html',
        cart_items=cart_items,
        addresses=addresses,
        edit_address=edit_address,
        users=users
    )

@app.route('/manage_user_address')
@login_required
def manage_user_address():
    edit_id = request.args.get('edit')
    edit_address = None

    if edit_id:
        edit_address = ManageAddress.query.get(edit_id)
        if not edit_address or edit_address.user_id != current_user.id:
            abort(403)

    addresses = ManageAddress.query.filter_by(user_id=current_user.id).all()

    return render_template(
        'address.html',
        user=current_user,
        addresses=addresses,
        edit_address=edit_address,
        users=[current_user]        # ✔ badge list

    )

@app.route('/add_address', methods=['GET', 'POST'])
@login_required
def add_address():
    next_page = request.args.get('next', 'checkout')  # default to 'checkout'

    if request.method == 'POST':
        address_id = request.form.get('address_id')

        data = {
            'username': request.form.get('name'),
            'mobile': request.form.get('mobile'),
            'pincode': request.form.get('pincode'),
            'locality': request.form.get('locality'),
            'address': request.form.get('address'),
            'city_district_town': request.form.get('city_district_town'),
            'state': request.form.get('state'),
            'landmark': request.form.get('landmark') or '',
            'alternate_mobile': request.form.get('alternate_mobile') or '',
            'address_type': request.form.get('address_type')
        }

        if address_id:
            address = ManageAddress.query.get(address_id)
            if not address or address.user_id != current_user.id:
                abort(403)

            for key, value in data.items():
                setattr(address, key, value)
        else:
            address = ManageAddress(user_id=current_user.id, email=current_user.email, **data)
            db.session.add(address)

        db.session.commit()

        # AJAX response for JS
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                'success': True,
                'is_edit': bool(address_id),
                'address': {
                    'id': address.id,
                    'username': address.username,
                    'mobile': address.mobile,
                    'pincode': address.pincode,
                    'locality': address.locality,
                    'address': address.address,
                    'city_district_town': address.city_district_town,
                    'state': address.state,
                    'landmark': address.landmark,
                    'alternate_mobile': address.alternate_mobile,
                    'address_type': address.address_type
                }
            })

        return redirect(url_for(next_page))

    # GET request fallback
    return redirect(url_for(next_page))

@app.route('/delete_address/<int:address_id>', methods=['POST'])
@login_required
def delete_address(address_id):
    address = ManageAddress.query.get_or_404(address_id)

    if address.user_id != current_user.id:
        abort(403)

    db.session.delete(address)
    db.session.commit()

    next_page = request.args.get('next', 'checkout')
    return redirect(url_for(next_page))


# ✉️ Function to send email with optional attachment
def send_email(to_email, subject, body, attachment_path=None):
    sender_email = "sednainfo5@gmail.com"
    sender_password = "mfzm afcu fwma latu"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    if attachment_path:
        try:
            with open(attachment_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                msg.attach(part)
        except Exception as e:
            print("⚠️ Failed to attach image:", e)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:

            server.login(sender_email, sender_password)
            server.send_message(msg)
            print("✅ Email sent to:", to_email)
    except Exception as e:
        print("❌ Email failed:", e)


sys.stdout.reconfigure(encoding='utf-8')
@app.route('/custom_order', methods=['GET', 'POST'])
@login_required
def custom_order():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        city = request.form.get('city')
        outlet = request.form.get('outlet')
        flavor = request.form.get('flavour')
        variant = request.form.get('variant')
        message = request.form.get('msg')
        delivery_date = request.form.get('date')
        delivery_time = request.form.get('time')
        address = request.form.get('address')
        instructions = request.form.get('instructions')

        # 🖼️ Handle image upload
        design_image = request.files.get('image')
        image_filename = None
        attachment_path = None

        if design_image and design_image.filename != '':
           filename = secure_filename(design_image.filename)
           upload_folder = os.path.join(app.root_path, 'static/uploads')
           os.makedirs(upload_folder, exist_ok=True)
           upload_path = os.path.join(upload_folder, filename)
           design_image.save(upload_path)  # <-- Saves image to correct path
           image_filename = f"static/uploads/{filename}"  # Save this to DB
        else:
           image_filename = 'static/uploads/placeholder.jpg'  # Default

        # 🗃️ Insert into database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO custom_cake
            (user_id, name, phone, email, flavour, variant, msg, img, date, time, address, instruction, city, outlet)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            current_user.id,
            name,
            phone,
            email,
            flavor,
            variant,
            message,
            image_filename,
            delivery_date,
            delivery_time,
            address,
            instructions,
            city,
            outlet
        ))
        conn.commit()
        conn.close()

        # 📧 Email to user
        user_subject = "🎂 Your Custom Cake Order with SS Bakers!"
        user_body = f"""
        Hi {name},<br><br>
        Thank you for placing your custom cake order with <strong>SS Bakers</strong>!<br><br>
        We will contact you within an hour to confirm the details.<br><br>
        <strong>Order Summary:</strong><br>
        Delivery: {delivery_date} at {delivery_time}<br>
        Flavor: {flavor} | Variant: {variant}<br>
        Outlet: {outlet}, {city}<br><br>
        <em>We appreciate your trust in us!</em><br><br>
        Best Regards,<br>SS Bakers Team 🍰
        """
        print("📧 Sending email to user:")
        print("To:", email)
        print("Subject:", user_subject)
        print("Body:", user_body)

        send_email(email, user_subject, user_body, attachment_path)

        # 📧 Email to admin
        admin_subject = f"📥 New Custom Cake Order from {name}"
        admin_body = f"""
        <b>New Order Details:</b><br><br>
        <b>Name:</b> {name}<br>
        <b>Phone:</b> {phone}<br>
        <b>Email:</b> {email}<br>
        <b>Flavor:</b> {flavor}<br>
        <b>Variant:</b> {variant}<br>
        <b>Message:</b> {message}<br>
        <b>Instructions:</b> {instructions}<br>
        <b>Delivery:</b> {delivery_date} at {delivery_time}<br>
        <b>Address:</b><br>{address}<br>
        <b>Outlet:</b> {outlet}, {city}<br>
        """
        print("📧 Sending email to admin:")
        print("To: sbpc123@gmail.com")
        print("Subject:", admin_subject)
        print("Body:", admin_body)

        send_email("sbpc123@gmail.com", admin_subject, admin_body, attachment_path)

        return redirect(url_for('cake_variety', success='1'))
    return render_template('variety.html')

# Update your place_order route to redirect to payment:
@app.route('/place_order', methods=['POST'])
@login_required
def place_order():
    """Place order and redirect to payment page"""
    user = current_user
    cart_items = CartItem.query.filter_by(user_id=user.id).all()

    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart'))

    address_id = request.form.get('selected_address_id')
    if not address_id:
        flash("Delivery address is required.", "danger")
        return redirect(url_for('checkout'))

    delivery_address = ManageAddress.query.get(address_id)
    if not delivery_address or delivery_address.user_id != user.id:
        abort(403)

    packaging_charges = float(request.form.get('packaging', 0))
    gst = float(request.form.get('gst', 0))
    grand_total = float(request.form.get('grand_total', 0))
    delivery_cost = sum(float(item.delivery_cost) for item in cart_items)

    # Create order with pending status
    new_order = Orders(
        user_id=user.id,
        address_id=address_id,
        delivery_cost=delivery_cost,
        packaging_charges=packaging_charges,
        gst=gst,
        grand_total=grand_total,
        timestamp=datetime.utcnow(),
        status='Pending'
    )
    db.session.add(new_order)
    db.session.flush()

    # Add order items
    for item in cart_items:
        order_item = OrderItems(
            order_id=new_order.id,
            sub_productname=item.sub_productname,
            image=item.image,
            flavour=item.flavour,
            variant=item.variant,
            v_cost=item.v_cost,
            quantity=item.quantity,
            acc_1=item.acc_1,
            a_cost1=item.a_cost1,
            a_quantity1=item.a_quantity1,
            acc_2=item.acc_2,
            a_cost2=item.a_cost2,
            a_quantity2=item.a_quantity2,
            acc_3=item.acc_3,
            a_cost3=item.a_cost3,
            a_quantity3=item.a_quantity3,
            acc_4=item.acc_4,
            a_cost4=item.a_cost4,
            a_quantity4=item.a_quantity4,
            acc_5=item.acc_5,
            a_cost5=item.a_cost5,
            a_quantity5=item.a_quantity5,
            total_price=item.total_price,
            message=item.message,
        )
        db.session.add(order_item)

    # Clear cart
    CartItem.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    # Redirect to payment page
    return redirect(url_for('payment_page_static', order_id=new_order.id))

@app.route('/invoice/<int:order_id>')
@login_required
def invoice(order_id):
    order = Orders.query.get_or_404(order_id)
    order_items = OrderItems.query.filter_by(order_id=order.id).all()
    all_items = []
    for item in order_items:
        accessories = []
        for i in range(1, 6):
            acc = getattr(item, f'acc_{i}', None)
            cost = getattr(item, f'a_cost{i}', 0)
            qty = getattr(item, f'a_quantity{i}', 0)
            if acc and acc.upper() != 'NULL':
                accessories.append({'name': acc, 'cost': cost, 'qty': qty})

        all_items.append({
            'sub_productname': item.sub_productname,
            'variant': item.variant,
            'v_cost': item.v_cost,
            'quantity': item.quantity,
            'total_price': item.total_price,
            'accessories': accessories,
            'flavour': item.flavour
        })

    logo_uri = url_for('static', filename='img/SS_logo.jpg', _external=True)
    html = render_template(
        'invoice_template.html',
        order=order,
        items=all_items,
        name=order.user.name if order.user else "Guest",
        logo_path=logo_uri
    )

    config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
    options = { "enable-local-file-access": "", "page-size": "A4", "encoding": "UTF-8" }
    pdf = pdfkit.from_string(html, False, configuration=config, options=options)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=invoice_{order_id}.pdf'
    return response

@app.route('/download_invoice/<int:order_id>')
@login_required
def download_invoice(order_id):
    order = Orders.query.get_or_404(order_id)
    order_items = OrderItems.query.filter_by(order_id=order.id).all()
    all_items = []
    for item in order_items:
        accessories = []
        for i in range(1, 6):
            acc = getattr(item, f'acc_{i}', None)
            cost = getattr(item, f'a_cost{i}', 0)
            qty = getattr(item, f'a_quantity{i}', 0)
            if acc and acc.upper() != 'NULL':
                accessories.append({'name': acc, 'cost': cost, 'qty': qty})

        all_items.append({
            'sub_productname': item.sub_productname,
            'variant': item.variant,
            'v_cost': item.v_cost,
            'quantity': item.quantity,
            'total_price': item.total_price,
            'accessories': accessories,
            'flavour': item.flavour
        })

    logo_path = url_for('static', filename='img/SS_logo.jpg', _external=True)
    html = render_template(
        'invoice_template.html',
        order=order,
        items=all_items,
        name=order.user.name if order.user else "Guest",
        logo_path=logo_path
    )

    config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
    options = { "enable-local-file-access": "", "page-size": "A4", "encoding": "UTF-8" }
    pdf = pdfkit.from_string(html, False, configuration=config, options=options)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=invoice_{order_id}.pdf'
    return response

@app.route('/dashbord')
def dashbord():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # dictionary=True returns rows as dictionaries
        cursor.execute("""
            SELECT
                p.id AS product_id,
                p.name AS product_name,
                sp.id AS sub_id,  -- Added sub_id from sub_product table
                sp.name AS sub_product_name,
                sp.price AS sub_product_price,
                sp.new_price AS sub_product_new_price
            FROM
                product p
            LEFT JOIN
                sub_product sp ON p.id = sp.product_id
        """)

        products = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template("dashbord.html", products=products)
    except Exception as e:
        return f"Error loading products: {e}"


@app.route('/personal_info', methods=['GET', 'POST'])
@login_required
def personal_info():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        mobile_no = request.form.get('mobile_no')
        gender = request.form.get('gender')
        dob = request.form.get('dob')
        anniversary = request.form.get('anniversary')

        # Update in database
        cursor.execute("""
            UPDATE user
            SET name = %s, email = %s, mobile_no = %s, gender = %s, birthday = %s, anniversary = %s
            WHERE id = %s
        """, (name, email, mobile_no, gender, dob, anniversary, user_id))

        conn.commit()

        flash("Profile updated successfully ✅", "success")
        return redirect(url_for('personal_info'))

    # Fetch user data
    cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    return render_template(
        "profile.html",
        user=user,          
        users=[user]        
    )

@app.route('/cancellationrefunds')
def cancellation_refunds():
    return render_template('cancellationrefunds.html')

@app.route('/termsandconditions')
def terms_and_conditions():
    return render_template('termsandconditions.html')

@app.route('/shipping')
def shipping():
    return render_template('shipping.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/guest_invoice/<order_number>')
def guest_invoice(order_number):
    """Generate invoice PDF for guest orders"""
    guest_order = GuestOrder.query.filter_by(order_number=order_number).first_or_404()
    order_items = GuestOrderItem.query.filter_by(order_id=guest_order.id).all()

    all_items = []
    for item in order_items:
        accessories = []
        for i in range(1, 6):
            acc = getattr(item, f'acc_{i}', None)
            cost = getattr(item, f'a_cost{i}', 0)
            qty = getattr(item, f'a_quantity{i}', 0)
            if acc and acc.upper() != 'NULL':
                accessories.append({'name': acc, 'cost': cost, 'qty': qty})

        all_items.append({
            'sub_productname': item.sub_productname,
            'variant': item.variant,
            'v_cost': item.v_cost,
            'quantity': item.quantity,
            'total_price': item.total_price,
            'accessories': accessories,
            'flavour': item.flavour
        })

    logo_path = url_for('static', filename='img/SS_logo.jpg', _external=True)

    html = render_template(
        'guest_invoice_template.html',
        order=guest_order,
        items=all_items,
        name=guest_order.guest_name,
        logo_path=logo_path
    )

    config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
    options = { "enable-local-file-access": "", "page-size": "A4", "encoding": "UTF-8" }
    pdf = pdfkit.from_string(html, False, configuration=config, options=options)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=invoice_{order_number}.pdf'
    return response

@app.route('/download_guest_invoice/<order_number>')
def download_guest_invoice(order_number):
    """Download invoice PDF for guest orders"""
    guest_order = GuestOrder.query.filter_by(order_number=order_number).first_or_404()
    order_items = GuestOrderItem.query.filter_by(order_id=guest_order.id).all()

    all_items = []
    for item in order_items:
        accessories = []
        for i in range(1, 6):
            acc = getattr(item, f'acc_{i}', None)
            cost = getattr(item, f'a_cost{i}', 0)
            qty = getattr(item, f'a_quantity{i}', 0)
            if acc and acc.upper() != 'NULL':
                accessories.append({'name': acc, 'cost': cost, 'qty': qty})

        all_items.append({
            'sub_productname': item.sub_productname,
            'variant': item.variant,
            'v_cost': item.v_cost,
            'quantity': item.quantity,
            'total_price': item.total_price,
            'accessories': accessories,
            'flavour': item.flavour
        })

    logo_path = url_for('static', filename='img/SS_logo.jpg', _external=True)

    html = render_template(
        'guest_invoice_template.html',
        order=guest_order,
        items=all_items,
        name=guest_order.guest_name,
        logo_path=logo_path
    )

    config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
    options = { "enable-local-file-access": "", "page-size": "A4", "encoding": "UTF-8" }
    pdf = pdfkit.from_string(html, False, configuration=config, options=options)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=invoice_{order_number}.pdf'
    return response

@app.route('/thankyou/<int:order_id>')
@login_required
def thankyou(order_id):
    """Display thank you page"""
    order = Orders.query.get_or_404(order_id)
    
    if order.user_id != current_user.id:
        abort(403)
    
    return render_template('thankyou.html', order_id=order_id, order=order)


@app.route('/payment/<int:order_id>')
@login_required
def payment_page_static(order_id):
    """Display payment page with Razorpay integration"""
    order = Orders.query.get_or_404(order_id)
    
    # Security check - only order owner can view
    if order.user_id != current_user.id:
        abort(403)
    
    # Get user details from database
    user = User.query.get(current_user.id)
    
    return render_template('payment.html', 
                         order_id=order.id,
                         amount=order.grand_total,
                         user_name=user.name,
                         user_email=user.email,
                         user=user)

@app.route('/create_razorpay_order/<int:order_id>', methods=['POST'])
@csrf.exempt  # ✅ CRITICAL: Exempt from CSRF protection
@login_required
def create_razorpay_order(order_id):
    """Create Razorpay order for payment"""
    try:
        print(f"=== Creating Razorpay order for order_id: {order_id} ===")  
        # Get order from database
        order = Orders.query.get_or_404(order_id)
        # Security check - verify user owns this order
        if order.user_id != current_user.id:
            print(f"❌ Unauthorized: Order user_id {order.user_id} != current_user {current_user.id}")
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 403
        
        # Get user details
        user = User.query.get(current_user.id)
        if not user:
            print("❌ User not found")
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Convert amount to paise (Razorpay requires amount in smallest currency unit)
        amount_in_paise = int(float(order.grand_total) * 100)
        
        # Validate minimum amount (Razorpay requires at least ₹1 = 100 paise)
        if amount_in_paise < 100:
            print(f"❌ Amount too low: {amount_in_paise} paise")
            return jsonify({'success': False, 'error': 'Amount must be at least ₹1'}), 400
        
        print(f"✅ Creating Razorpay order:")
        print(f"   - Amount: {amount_in_paise} paise (₹{order.grand_total})")
        print(f"   - User: {user.name} ({user.email})")
        
        # Create Razorpay order
        razorpay_order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'payment_capture': '1',  # Auto capture payment
            'notes': {
                'order_id': order.id,
                'user_id': user.id,
                'user_name': user.name
            }
        }
        
        razorpay_order = razorpay_client.order.create(razorpay_order_data)
        razorpay_order_id = razorpay_order['id']
        
        print(f"✅ Razorpay order created successfully: {razorpay_order_id}")
        
        # Store payment record in database
        payment = Payment(
            order_id=order.id,
            razorpay_order_id=razorpay_order_id,
            amount=order.grand_total,
            currency='INR',
            status='created',
            mode='test'
        )
        db.session.add(payment)
        db.session.commit()
        
        print("✅ Payment record saved to database")        
        response_data = {
            'success': True,
            'razorpay_order_id': razorpay_order_id,
            'amount': amount_in_paise,
            'currency': 'INR',
            'key_id': KEY_ID,
            'name': "SS Bakers",
            'description': f"Order #{order.id}",
            'prefill_name': user.name,
            'prefill_email': user.email,
            'order_id': order.id
        }
        
        print(f"✅ Sending response: {response_data}")
        return jsonify(response_data), 200
        
    except razorpay.errors.BadRequestError as e:
        error_msg = f"Razorpay API error: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 400
        
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/payment_success', methods=['POST'])
@csrf.exempt
def payment_success():
    """Handle successful payment callback"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
            
        payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        signature = data.get('razorpay_signature')
        
        if not all([payment_id, razorpay_order_id, signature]):
            return jsonify({'success': False, 'error': 'Missing payment details'}), 400
        
        print(f"🔄 Processing payment success: {payment_id}, {razorpay_order_id}")
        generated_signature = hmac.new
        (
            bytes(KEY_SECRET, 'utf-8'),
            bytes(razorpay_order_id + "|" + payment_id, 'utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature != signature:
            print("❌ Signature verification failed")
            return jsonify({'success': False, 'error': 'Payment signature verification failed'}), 400
        
        # Update payment record
        payment = Payment.query.filter_by(razorpay_order_id=razorpay_order_id).first()
        if not payment:
            return jsonify({'success': False, 'error': 'Payment record not found'}), 404
            
        payment.razorpay_payment_id = payment_id
        payment.razorpay_signature = signature
        payment.status = 'success'
        payment.updated_at = datetime.utcnow()
        
        # Update order status
        order = Orders.query.get(payment.order_id)
        if order:
            order.status = 'Confirmed'

        db.session.commit()
        print(f"✅ Payment successful for order {order.id}")
        
        # Send confirmation email
        if order and order.user_id:
            user = User.query.get(order.user_id)
            if user:
                send_order_confirmation_email(
                    user.email, 
                    user.name, 
                    order.id, 
                    order.grand_total
                )
        
        return jsonify({
            'success': True,
            'message': 'Payment verified successfully',
            'redirect_url': url_for('thankyou', order_id=order.id, _external=True)
        })
            
    except Exception as e:
        print(f"❌ Error in payment success: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Payment processing failed: {str(e)}'}), 500
# Also add this helper function for better error handling

def send_order_confirmation_email(to_email, name, order_id, total):
    """Send order confirmation email"""
    try:
        subject = f"Order Confirmation - SS Bakers (Order #{order_id})"
        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #b32071;">Thank You for Your Order!</h2>
            <p>Dear {name},</p>
            <p>Your order has been successfully placed with <strong>SS Bakers</strong>.</p>
            
            <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 20px 0;">
              <p><strong>Order Number:</strong> {order_id}</p>
              <p><strong>Total Amount:</strong> ₹{total:.2f}</p>
              <p><strong>Status:</strong> Confirmed</p>
            </div>
            
            <p>We will contact you shortly to confirm delivery details.</p>
            <p>For queries, contact us at +91-8655481522.</p>
            
            <p>Best Regards,<br>
            <strong>SS Bakers Team</strong></p>
          </body>
        </html>
        """
        msg = Message(
            subject=subject, 
            sender=app.config['MAIL_USERNAME'], 
            recipients=[to_email]
        )
        msg.html = body
        mail.send(msg)
        print(f"✅ Confirmation email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send confirmation email: {e}")

# -------------------------------------------------------------------------
# guest_payment
@app.route('/guest_payment/<order_number>')
def guest_payment_page(order_number):
    """Display payment page for guest orders"""
    guest_order = GuestOrder.query.filter_by(order_number=order_number).first_or_404()
    
    return render_template('guest_payment.html', 
                         order_number=guest_order.order_number,
                         amount=float(guest_order.grand_total))

@app.route('/create_razorpay_guest_order/<order_number>', methods=['POST'])
@csrf.exempt
def create_razorpay_guest_order(order_number):
    """Create Razorpay order for guest payment"""
    try:
        print(f"=== Creating Razorpay order for guest order: {order_number} ===")
        
        # Get guest order from database
        guest_order = GuestOrder.query.filter_by(order_number=order_number).first_or_404()
        
        # Convert amount to paise
        amount_in_paise = int(float(guest_order.grand_total) * 100)
        
        # Validate minimum amount
        if amount_in_paise < 100:
            print(f"❌ Amount too low: {amount_in_paise} paise")
            return jsonify({'success': False, 'error': 'Amount must be at least ₹1'}), 400
        
        print(f"✅ Creating Razorpay order:")
        print(f"   - Amount: {amount_in_paise} paise (₹{guest_order.grand_total})")
        print(f"   - Guest: {guest_order.guest_name} ({guest_order.guest_email})")
        
        # Create Razorpay order
        razorpay_order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'payment_capture': '1',
            'notes': {
                'order_number': guest_order.order_number,
                'guest_name': guest_order.guest_name
            }
        }
        
        razorpay_order = razorpay_client.order.create(razorpay_order_data)
        razorpay_order_id = razorpay_order['id']
        
        print(f"✅ Razorpay order created successfully: {razorpay_order_id}")
        
        # ✅ Store Razorpay order ID in guest order
        guest_order.razorpay_order_id = razorpay_order_id
        db.session.commit()
        
        # Return response for frontend
        response_data = {
            'success': True,
            'razorpay_order_id': razorpay_order_id,
            'amount': amount_in_paise,
            'currency': 'INR',
            'key_id': KEY_ID,
            'name': "SS Bakers",
            'description': f"Guest Order #{guest_order.order_number}",
            'prefill_name': guest_order.guest_name,
            'prefill_email': guest_order.guest_email,
            'order_number': guest_order.order_number
        }
        
        print(f"✅ Sending response: {response_data}")
        return jsonify(response_data), 200
        
    except razorpay.errors.BadRequestError as e:
        error_msg = f"Razorpay API error: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 400
        
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/guest_payment_success', methods=['POST'])
@csrf.exempt
def guest_payment_success():
    """Handle successful payment callback for guest orders"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
            
        payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        signature = data.get('razorpay_signature')
        
        if not all([payment_id, razorpay_order_id, signature]):
            return jsonify({'success': False, 'error': 'Missing payment details'}), 400
        
        print(f"🔄 Processing guest payment success: {payment_id}, {razorpay_order_id}")
        
        # Verify signature
        generated_signature = hmac.new(
            bytes(KEY_SECRET, 'utf-8'),
            bytes(razorpay_order_id + "|" + payment_id, 'utf-8'),
            hashlib.sha256
        ).hexdigest()
        


        if generated_signature != signature:
            print("❌ Signature verification failed")
            return jsonify({'success': False, 'error': 'Payment signature verification failed'}), 400
        
        
        guest_order = GuestOrder.query.filter_by(razorpay_order_id=razorpay_order_id).first()
        if not guest_order:
            print(f"❌ Guest order not found for Razorpay order: {razorpay_order_id}")
            return jsonify({'success': False, 'error': 'Order not found'}), 404
            
        # Update guest order status
        guest_order.status = 'Confirmed'
        guest_order.razorpay_payment_id = payment_id
        guest_order.razorpay_signature = signature
        
        db.session.commit()
        
        print(f"✅ Guest payment successful for order {guest_order.order_number}")
        
        # Send confirmation email
        send_guest_order_confirmation_email(
            guest_order.guest_email, 
            guest_order.guest_name, 
            guest_order.order_number, 
            guest_order.grand_total
        )
        
        return jsonify({
            'success': True,
            'message': 'Payment verified successfully',
            'redirect_url': url_for('guest_thankyou', order_number=guest_order.order_number, _external=True)
        })
            
    except Exception as e:
        print(f"❌ Error in guest payment success: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Payment processing failed: {str(e)}'}), 500

def send_guest_order_email(to_email, name, order_number, total):
    """Send order confirmation email to guest"""
    subject = f"Order Confirmation - SS Bakers (Order #{order_number})"
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #b32071;">Thank You for Your Order!</h2>
        <p>Dear {name},</p>
        <p>Your order has been successfully placed with <strong>SS Bakers</strong>.</p>
        
        <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 20px 0;">
          <p><strong>Order Number:</strong> {order_number}</p>
          <p><strong>Total Amount:</strong> ₹{total:.2f}</p>
          <p><strong>Status:</strong> Pending</p>
        </div>
        
        <p>We will contact you shortly to confirm your order details and delivery timing.</p>
        <p>If you have any questions, please contact us at +91-1234567890.</p>
        
        <p>Best Regards,<br>
        <strong>SS Bakers Team</strong></p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #666; font-size: 12px;">
          This is an automated email. Please do not reply to this message.
        </p>
      </body>
    </html>
    """
    
    try:
        msg = Message(
            subject=subject, 
            sender=app.config['MAIL_USERNAME'], 
            recipients=[to_email]
        )
        msg.html = body
        mail.send(msg)
        print(f"✅ Guest order confirmation sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send guest order email: {e}")

def send_guest_order_confirmation_email(to_email, name, order_number, total):
    """Send order confirmation email to guest"""
    try:
        subject = f"Order Confirmation - SS Bakers (Order #{order_number})"
        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #b32071;">Thank You for Your Order!</h2>
            <p>Dear {name},</p>
            <p>Your order has been successfully placed with <strong>SS Bakers</strong>.</p>
            
            <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 20px 0;">
              <p><strong>Order Number:</strong> {order_number}</p>
              <p><strong>Total Amount:</strong> ₹{total:.2f}</p>
              <p><strong>Status:</strong> Confirmed</p>
            </div>
            
            <p>We will contact you shortly to confirm delivery details.</p>
            <p>For queries, contact us at +91-8655481522.</p>
            
            <p>Best Regards,<br>
            <strong>SS Bakers Team</strong></p>
          </body>
        </html>
        """
        
        msg = Message(
            subject=subject, 
            sender=app.config['MAIL_USERNAME'], 
            recipients=[to_email]
        )
        msg.html = body
        mail.send(msg)
        print(f"✅ Guest confirmation email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send guest confirmation email: {e}")

# -------------------------------------------------------------------------

@app.route('/guest_checkout', methods=['GET'])
def guest_checkout():
    """Display guest checkout page"""
    session_id = session.get('session_id')
    
    # Get cart items
    if current_user.is_authenticated:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    elif session_id:
        cart_items = CartItem.query.filter_by(session_id=session_id).all()
    else:
        flash('Your cart is empty. Please add items before checkout.', 'warning')
        return redirect(url_for('cart'))
    
    if not cart_items:
        flash('Your cart is empty. Please add items before checkout.', 'warning')
        return redirect(url_for('cart'))
    
    # Calculate totals
    subtotal = sum(float(item.total_price) for item in cart_items)
    delivery_cost = 50
    packaging_cost = 30
    total_before_tax = subtotal + delivery_cost + packaging_cost
    gst = total_before_tax * 0.18
    grand_total = total_before_tax + gst
    
    return render_template('guest_checkout.html', 
                         cart_items=cart_items,
                         subtotal=subtotal,
                         delivery_cost=delivery_cost,
                         packaging_cost=packaging_cost,
                         gst=gst,
                         grand_total=grand_total)


def generate_order_number():
    """Generate unique order number"""
    timestamp = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.digits, k=6))
    return f"SSB{timestamp}{random_str}"

@app.route('/place_guest_order', methods=['POST'])
def place_guest_order():
    """Process guest order without login"""
    try:
        validate_csrf(request.form.get('csrf_token'))

        # Get form data
        guest_name = request.form.get('guest_name')
        guest_email = request.form.get('guest_email')
        guest_mobile = request.form.get('guest_mobile')
        guest_alternate_mobile = request.form.get('guest_alternate_mobile', '')
        
        # Address fields
        guest_address = request.form.get('guest_address')
        guest_locality = request.form.get('guest_locality')
        guest_city = request.form.get('guest_city')
        guest_state = request.form.get('guest_state')
        guest_pincode = request.form.get('guest_pincode')
        guest_landmark = request.form.get('guest_landmark', '')
        
        # Order totals from hidden fields
        subtotal = float(request.form.get('subtotal', 0))
        delivery_charges = float(request.form.get('delivery_charges', 0))
        packaging_charges = float(request.form.get('packaging_charges', 0))
        gst = float(request.form.get('gst', 0))
        grand_total = float(request.form.get('grand_total', 0))
        
        # Order type (delivery/pickup)
        order_type = request.form.get('order_type', 'delivery')
        
        # Validate required fields
        required_fields = {
            'guest_name': guest_name,
            'guest_email': guest_email,
            'guest_mobile': guest_mobile,
            'guest_address': guest_address,
            'guest_locality': guest_locality,
            'guest_city': guest_city,
            'guest_state': guest_state,
            'guest_pincode': guest_pincode
        }
        
        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            flash(f'Please fill all required fields: {", ".join(missing_fields)}', 'error')
            return redirect(url_for('guest_checkout'))
        
        # Validate mobile number
        if len(guest_mobile) != 10 or not guest_mobile.isdigit():
            flash('Please enter a valid 10-digit mobile number', 'error')
            return redirect(url_for('guest_checkout'))
        
        # Validate pincode
        if len(guest_pincode) != 6 or not guest_pincode.isdigit():
            flash('Please enter a valid 6-digit pincode', 'error')
            return redirect(url_for('guest_checkout'))
        
        # Get cart items
        session_id = session.get('session_id')
        if current_user.is_authenticated:
            cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        elif session_id:
            cart_items = CartItem.query.filter_by(session_id=session_id).all()
        else:
            flash('Your cart is empty', 'warning')
            return redirect(url_for('cart'))
        
        if not cart_items:
            flash('Your cart is empty', 'warning')
            return redirect(url_for('cart'))
        
        # Generate order number
        order_number = generate_order_number()
        
        # Create guest order
        guest_order = GuestOrder(
            order_number=order_number,
            guest_name=guest_name,
            guest_email=guest_email,
            guest_mobile=guest_mobile,
            guest_alternate_mobile=guest_alternate_mobile,
            guest_address=guest_address,
            guest_locality=guest_locality,
            guest_city=guest_city,
            guest_state=guest_state,
            guest_pincode=guest_pincode,
            guest_landmark=guest_landmark,
            subtotal=subtotal,
            delivery_charges=delivery_charges,
            packaging_charges=packaging_charges,
            gst=gst,
            grand_total=grand_total,
            order_type=order_type,
            status='Pending'
        )
        
        db.session.add(guest_order)
        db.session.flush()  # Get the order ID without committing
        
        # Create order items
        for item in cart_items:
            order_item = GuestOrderItem(
                order_id=guest_order.id,
                sub_productname=item.sub_productname,
                image=item.image,
                flavour=item.flavour,
                variant=item.variant,
                v_cost=item.v_cost,
                quantity=item.quantity,
                acc_1=item.acc_1,
                a_cost1=item.a_cost1,
                a_quantity1=item.a_quantity1,
                acc_2=item.acc_2,
                a_cost2=item.a_cost2,
                a_quantity2=item.a_quantity2,
                acc_3=item.acc_3,
                a_cost3=item.a_cost3,
                a_quantity3=item.a_quantity3,
                acc_4=item.acc_4,
                a_cost4=item.a_cost4,
                a_quantity4=item.a_quantity4,
                acc_5=item.acc_5,
                a_cost5=item.a_cost5,
                a_quantity5=item.a_quantity5,
                total_price=item.total_price,
                message=item.message
            )
            db.session.add(order_item)
        
        # Clear cart after successful order
        if current_user.is_authenticated:
            CartItem.query.filter_by(user_id=current_user.id).delete()
        elif session_id:
            CartItem.query.filter_by(session_id=session_id).delete()
        
        db.session.commit()
        
        # Send confirmation email
        send_guest_order_email(guest_email, guest_name, order_number, grand_total)
        
        # ✅ FIX: Redirect to guest payment page instead of thankyou page
        return redirect(url_for('guest_payment_page', order_number=order_number))
       
    except Exception as e:
        db.session.rollback()
        print(f"Error placing guest order: {str(e)}")
        import traceback
        traceback.print_exc()   
        flash('An error occurred while placing your order. Please try again.', 'error')
        return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 400

        

@app.route('/guest_thankyou')
def guest_thankyou():
    """Display thank you page for guest orders"""
    order_number = request.args.get('order_number')
    
    if not order_number:
        flash('Order number not found', 'error')
        return redirect(url_for('home'))
    
    # Get guest order details
    guest_order = GuestOrder.query.filter_by(order_number=order_number).first()
    
    if not guest_order:
        flash('Order not found', 'error')
        return redirect(url_for('home'))
    
    return render_template('guest_thankyou.html', 
                         order_number=order_number,
                         order=guest_order)

@app.route('/debug_payment/<int:order_id>')
@login_required
def debug_payment(order_id):
    """Debug route to check payment setup"""
    order = Orders.query.get_or_404(order_id)
    return jsonify({
        'order_exists': True,
        'order_id': order.id,
        'amount': order.grand_total,
        'user_id': order.user_id,
        'current_user': current_user.id,
        'authorized': order.user_id == current_user.id
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)