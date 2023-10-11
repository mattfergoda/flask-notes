"""Flask app for Cupcakes"""
import os

from flask import Flask, redirect, render_template, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.exceptions import Unauthorized

from forms import CSRFProtectForm, RegisterForm, LoginForm, AddNoteForm
from models import db, connect_db, User, Note

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "postgresql:///notes"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

connect_db(app)

app.config["SECRET_KEY"] = "I'LL NEVER TELL!!"
debug = DebugToolbarExtension(app)

USERNAME_KEY = "username"


@app.get("/")
def render_home_page():
    """Redirect to register page"""

    return redirect("/register")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user: produce form & handle form submission."""

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        # Check if username is already taken.
        if User.query.filter(User.username == username).all():
            flash(f"Username {username} already taken.")
            return render_template("register.html", form=form)

        user = User.register(username, password, email, first_name, last_name)

        db.session.add(user)
        db.session.commit()

        session[USERNAME_KEY] = user.username

        # on successful login, redirect to secret page
        return redirect(f"/users/{username}")

    else:
        return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Produce login form or handle login."""

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # authenticate will return a user or False
        user = User.authenticate(username, password)

        if user:
            session[USERNAME_KEY] = user.username
            return redirect(f"/users/{user.username}")

        else:
            flash("Incorrect name or password", "danger")

    return render_template("login.html", form=form)


@app.get("/users/<username>")
def display_user_page(username):
    """Displays specific page for a user"""

    user = User.query.get_or_404(username)

    if USERNAME_KEY not in session:
        flash("You must be logged in to view profile!", "danger")

        return redirect("/login")
    if username != session[USERNAME_KEY]:
        flash("This is not your profile", "danger")

        return redirect(f"/users/{session['username']}")

    form = CSRFProtectForm()

    return render_template("user.html", user=user, form=form)


@app.post("/logout")
def logout_user():
    """Logs user out and redirects to homepage."""

    form = CSRFProtectForm()

    if form.validate_on_submit():
        session.pop(USERNAME_KEY, None)
        flash("You are logged out.", "success")

    return redirect("/")


@app.post("/users/<username>/delete")
def handle_deleting_user(username):
    """Deletes user from database and logs user out."""

    if username != session.get(USERNAME_KEY):
        raise Unauthorized

    form = CSRFProtectForm()

    if form.validate_on_submit():
        session.pop(USERNAME_KEY, None)

        user = User.query.get_or_404(username)
        db.session.delete(user)
        db.session.commit()

        flash("User has been deleted.", "success")

    return redirect("/")


@app.route("/users/<username>/notes/add", methods=["GET", "POST"])
def add_note(username):
    """Display new note form or handle new note submit."""

    if USERNAME_KEY not in session:
        flash("You must be logged in to view profile!", "danger")

        return redirect("/login")
    if username != session[USERNAME_KEY]:
        raise Unauthorized
    # User.query.get_or_404(username)

    form = AddNoteForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        note = Note(title=title, content=content, owner_username=username)

        db.session.add(note)
        db.session.commit()

        flash("Note added successfully", "success")

        return redirect(f"/users/{username}")

    return render_template("add_note.html", form=form)


@app.route("/notes/<int:note_id>/update", methods=["GET", "POST"])
def update_note(note_id):
    """Display update note form or handle update note submit."""

    note = Note.query.get_or_404(note_id)

    if note.user.username != session.get(USERNAME_KEY):
        raise Unauthorized

    form = AddNoteForm(obj=note)

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        note.title = title or note.title
        note.content = content or note.content

        db.session.commit()

        flash("Note updated successfully", "success")

        return redirect(f"/users/{note.user.username}")

    return render_template("add_note.html", form=form)
