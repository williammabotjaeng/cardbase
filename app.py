import datetime
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from flask_wtf import FlaskForm
from flask_mail import Message, Mail
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, FloatField
from wtforms.validators import InputRequired, Length, DataRequired, Email
from dotenv import load_dotenv

from openai import OpenAI

import argparse


import moment
import os

app = Flask(__name__)

load_dotenv()

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'QPEunVzlmptwr73MfPz44w=='
api_token = os.getenv("API_TOKEN")
log_config_id = os.getenv("CONFIG_ID")

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")  # Replace with your email address
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD") # Replace with your email password


mail = Mail(app)

client = OpenAI()

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=True)
    first_name = db.Column(db.String(20), nullable=True)
    last_name = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
     
    flash_card_sets = db.relationship('FlashCardSet', backref='user', lazy=True)


class FlashCardSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    set_title = db.Column(db.String(255), nullable=False)
    set_description = db.Column(db.String(255), nullable=False)
    set_creation_date = db.Column(db.Date, nullable=False, default=moment.now().date)
    set_modified_date = db.Column(db.Date, nullable=False, default=moment.now().date, onupdate=moment.now().date)

    entries = db.relationship('FlashCardEntry', backref='flashcard_set', lazy=True)

class FlashCardEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(255), nullable=False)
    definition = db.Column(db.String(255), nullable=False)

    flashcard_set_id = db.Column(db.Integer, db.ForeignKey('flash_card_set.id'), nullable=False)


with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Length(min=4, max=100)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=64)])

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Length(min=4, max=100)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=64)])

class FlashCardSetForm(FlaskForm):
    set_title = StringField('Set Title', validators=[InputRequired()])
    set_description = StringField('Set Description', validators=[InputRequired()])
    submit = SubmitField('Create Set')

class FlashCardEntryForm(FlaskForm):
    flashcard_set_id = StringField('FlashCardSet ID', validators=[InputRequired()])
    term = StringField('Term', validators=[InputRequired()])
    definition = StringField('Definition', validators=[InputRequired()])
    submit = SubmitField('Save Entry')

class ContactUsForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    message = TextAreaField("Message", validators=[DataRequired()])
    submit = SubmitField("Send")

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    return render_template("index.html", form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            user = User.query.filter_by(email=email).first()
            
            if not user or not check_password_hash(user.password, password):
                flash('Please check your login details and try again.')
                return redirect(url_for('login'))

            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", form=form)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
   
    if request.method == 'POST':
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            user = User.query.filter_by(email=email).first()
            if user:
                flash('Username already exists. Please choose a different one.')
                return redirect(url_for('login'))

            new_user = User(email=email, password=generate_password_hash(password, method='sha256'))
            db.session.add(new_user)
            db.session.commit()

            message_body = """We are excited to introduce you to CardBase, the innovative flashcard platform that will revolutionize the way you learn. With CardBase, you can tap into the vast resources of YouTube, web pages, and social media to generate personalized flashcards that cover any subject matter you desire.

By leveraging the power of AI, CardBase seamlessly combines the wisdom of centuries with state-of-the-art technology to simplify your learning experience. Our platform empowers you to effortlessly create and manage flashcards using your voice, allowing you to learn on the go and make the most of your valuable time.
\n
Whether you're a student, a professional, or simply someone passionate about continuous learning, CardBase is designed to cater to your needs. With our platform, you can access a wealth of knowledge from various sources and compile it into engaging flashcards, all at the convenience of a few simple voice commands.

We invite you to embrace the efficiency and convenience of CardBase today. Experience a new level of productivity as you explore any subject matter with ease and simplicity. 
\n
To get started, simply visit our user-friendly website and follow our quick and hassle-free registration process. Once you're in, you'll gain access to a range of powerful features and tools designed to enhance your learning experience.

If you have any questions or need assistance, our dedicated support team is here to help. Feel free to reach out to us at **CardBase@gmail.com**, and we'll be delighted to assist you.
\n
Thank you for choosing CardBase as your go-to flashcard platform. We are thrilled to have you on board and cannot wait to witness the positive impact CardBase will have on your learning journey.

Wishing you success and fulfillment as you embark on your quest for knowledge!
\n
Best regards,
\n
CardBase Team"""
          
            # Send email to the new user
            msg = Message(
                subject="Welcome to CardBase - Simply Learning! Amplify Knowledge!",
                sender=app.config["MAIL_USERNAME"],
                recipients=[email],
                body=f"Hi {email},\n\n{message_body}"
            )
            mail.send(msg)

            flash('Registration successful! An email has been sent to your email address.')
            user = User.query.filter_by(email=email).first()
            login_user(user)
            return redirect(url_for('home'))
    return render_template("register.html", form=form)

@login_required
@app.route("/home")
def home():
    user_id = current_user.id 
    flashcard_sets = FlashCardSet.query.filter_by(user_id=user_id).all()
    return render_template("home.html", current_user=current_user, flashcard_sets=flashcard_sets)

@app.route("/create_set", methods=["GET", "POST"])
@login_required
def create_set():
    current_user.session_engaged = True
    print(current_user.session_engaged)
    if request.method == "POST":
        user_id = current_user.id
        set_title = request.form.get("set_title")
        set_description = request.form.get("set_description")
        set_creation_date = moment.now().date()
        set_modified_date = moment.now().date()

        new_set = FlashCardSet(
            user_id=user_id,
            set_title=set_title,
            set_description=set_description,
            set_creation_date=set_creation_date,
            set_modified_date=set_modified_date
        )

        db.session.add(new_set)
        db.session.commit()

        print(FlashCardSet.query.filter_by(user_id=user_id).all())

        return redirect(url_for("flash_card_sets"))
    
    return render_template("create_set.html", current_user=current_user)

@app.route("/create_product", methods=["GET", "POST"])
@login_required
def create_product():
    current_user.session_engaged = True
    print(current_user.session_engaged)
    form = ProductForm()
    print("Form Validation", form.validate_on_submit())
    print("Form Errors", form.errors)
    if form.validate_on_submit():
        name = form.name.data
        price = form.price.data
        description = form.description.data
        category = form.category.data
        image_url = form.image_url.data
        sku_code = form.sku_code.data
        user_id = form.user_id.data

        new_product = Product(
            name=name,
            price=price,
            description=description,
            category=category,
            image_url=image_url,
            sku_code=sku_code,
            user_id=user_id
        )

        db.session.add(new_product)
        db.session.commit()

        print(Product.query.filter_by(user_id=user_id).all())

        return redirect(url_for("products"))
    
    return render_template("create_product.html", form=form, current_user=current_user)


@app.route("/start_invoice", methods=["GET", "POST"])
def start_invoice():
    audio_file = request.files["file"]
    print("Audio File", type(audio_file))

    audio_file.save('temp.wav')
    
    transcribe_streaming_v2(str(app.config["PROJECT_ID"]), "temp.wav")
    redirect(url_for("customers"))
    return "Success", 200

@app.route("/what")
def what():
    return render_template("what.html")

@app.route("/getintouch", methods=["GET", "POST"])
def contact():
    form = ContactUsForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        message = form.message.data

        msg = Message(
            subject="New Message from Contact Form",
            sender=app.config["MAIL_USERNAME"],
            recipients=["CardBaseapp@gmail.com"],
            body=f"Name: {name}\nEmail: {email}\nMessage: {message}"
        )

        mail.send(msg)

        flash("Your message has been sent successfully!", "success")
        return redirect(url_for("home"))

    return render_template("getintouch.html", form=form, current_user=current_user)

@app.route("/customers")
@login_required
def customers():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template("customers.html", current_user=current_user, customers=customers)

@app.route("/invoices")
@login_required
def invoices():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    invoices = []
    for customer in customers:
        print(customer)
        invoices.extend(customer.invoices)
    return render_template("invoices.html", current_user=current_user, invoices=invoices)

@app.route("/products")
@login_required
def products():
    products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template("products.html", current_user=current_user, products=products)

@app.route("/create_customer", methods=["GET", "POST"])
@login_required
def create_customer():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        phone_number = request.form.get("phone_number")
        address = request.form.get("address")

        new_customer = Customer(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            address=address,
            user_id=current_user.id  
        )

        db.session.add(new_customer)
        db.session.commit()

        print(Customer.query.filter_by(user_id=current_user.id).all())

        return redirect(url_for("customers"))
    
    return render_template("create_customer.html", current_user=current_user)


@app.route("/customers/delete/<int:customer_id>", methods=["POST"])
@login_required
def delete_customer(customer_id):

    customer = Customer.query.filter_by(user_id=current_user.id, id=customer_id).first()

    if customer:
        db.session.delete(customer)
        db.session.commit()

    db.session.commit()

    return redirect(url_for("customers"))

@app.route("/customers/edit/<int:customer_id>", methods=["GET", "POST"])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.filter_by(user_id=current_user.id, id=customer_id).first()
    if not customer:
        return redirect(url_for("customers"))

    if request.method == "POST":
        # Update the customer object with the new data from the form
        print(request.form)
        customer.first_name = request.form.get("first_name")
        customer.last_name = request.form.get("last_name")
        customer.email = request.form.get("email")
        customer.phone_number = request.form.get("phone_number")
        customer.address = request.form.get("address")

        db.session.commit()


        return redirect(url_for("customers"))
    else:
        return render_template("edit_customer.html", current_user=current_user, customer=customer)
    
@app.route("/assign/<int:customer_id>", methods=["GET"])
@login_required
def verify_contact(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return render_template("create_invoice.html", customer=customer)

@app.route("/docs")
def docs():
    return render_template("docs.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))