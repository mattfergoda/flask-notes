"""Flask app for Cupcakes"""
import os

from flask import Flask, request, redirect, render_template, jsonify, session
from flask_debugtoolbar import DebugToolbarExtension

from forms import CSRFProtectForm, RegisterForm
from models import db, connect_db, User

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "postgresql:///notes"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

connect_db(app)

app.config["SECRET_KEY"] = "I'LL NEVER TELL!!"
debug = DebugToolbarExtension(app)


@app.get("/")
def render_home_page():
    """Redirect to register page"""

    return redirect("/register")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user: produce form & handle form submission."""

    form = RegisterForm()

    if form.validate_on_submit():
        user_name = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        user = User.register(user_name, password, email, first_name, last_name)
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id

        # on successful login, redirect to secret page
        return redirect("/users/username")

    else:
        return render_template("register.html", form=form)
