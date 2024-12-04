# Uses request.args.get

from flask import Flask, render_template, redirect, request, session
from cs50 import SQL
from datetime import datetime, timezone
from flask_session import Session
from helpers import apology, login_required, usd, is_int
from werkzeug.security import check_password_hash, generate_password_hash
import uuid

application = Flask(__name__)

# Ensure templates are auto-reloaded
application.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
# app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
application.config["SESSION_PERMANENT"] = False
application.config["SESSION_TYPE"] = "filesystem"
Session(application)

db = SQL("sqlite:///social.db")

@application.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
       
        return render_template("index.html")


@application.route("/profile", methods=["GET", "POST"])
@login_required
def profilePage():
    if request.method == "GET":
       
        return render_template("profile.html")
    
@application.route("/friends", methods=["GET", "POST"])
@login_required
def friendPage():
    if request.method == "GET":
       
        return render_template("friends.html")

@application.route("/login", methods=["GET", "POST"])
def signIn():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("handler"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM User WHERE handler = ?",
                          request.form.get("handler"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["ID"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@application.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Validate submission
        name = request.form.get("name")
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Query database for username
        rows = db.execute("SELECT * FROM User WHERE handler = ?", username)

        # Ensure password == confirmation
        if not (password == confirmation):
            return apology("the passwords do not match", 400)

        # Ensure password not blank
        if password == "" or confirmation == "" or username == "":
            return apology("input is blank", 400)

        # Ensure username does not exists already
        if len(rows) == 1:
            return apology("username already exist", 400)
        else:

            hashcode = generate_password_hash(
                password, method='pbkdf2:sha256', salt_length=8)
            db.execute("INSERT INTO User (handler, password, name, email) VALUES(?, ?, ?, ?)",
                       username, hashcode, name, email)

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("register.html")


@application.route("/logout", methods=["GET"])
def logOut():
    session.clear()
    return redirect('/')

# run the application.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production application.
    application.debug = True
    application.run()
