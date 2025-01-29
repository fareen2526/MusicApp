# Fareen Alam - Header Comment
# application.py is Python code that connects the back end databases to the html page (exchanging information between the two).

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


def time_ago(diff):
    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif seconds < 2419200:  # roughly 4 weeks
        weeks = int(seconds // 604800)
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    else:
        # If it's beyond weeks, you can decide whether to return months/years
        months = int(seconds // 2419200)
        return f"{months} month{'s' if months > 1 else ''} ago"


@application.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        # Fetch all posts with associated comments (if any), regardless of the user who posted them
        posts_with_comments = db.execute(
            """
            SELECT 
                Post.ID as postID, 
                Post.title as postDescription,
                Post.imageUrl as imageUrl, 
                Post.createdDate as postDate, 
                Post.likes as likes,
                User.ID as userID, 
                User.handler, 
                Song.songName, 
                Song.songUrl, 
                Comment.userID as commentUserID, 
                Comment.content as commentContent, 
                Comment.createdDate as commentCreatedDate,
                U.name as commentUserName,
                U.imageUrl as commentAvatar
            FROM Post 
            JOIN Song ON Post.songID = Song.ID 
            JOIN User ON Post.userID = User.ID
            LEFT JOIN Comment ON Post.ID = Comment.postID
            LEFT JOIN User U ON Comment.userID = U.ID
            """
        )

        posts = []
        comments_by_post = {}

        # Process the results into a structured dictionary
        for row in posts_with_comments:
            # Prepare the post details
            if not any(p["postID"] == row["postID"] for p in posts):
                originalTime = datetime.now(timezone.utc) - datetime.strptime(
                        row["postDate"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                posts.append({
                    "postID": row["postID"],
                    "imageUrl": row["imageUrl"],
                    "userID": row["userID"],
                    "handler": row["handler"],
                    "postDescription": row["postDescription"],
                    "songName": row["songName"],
                    "songUrl": row["songUrl"],
                    "postDate": row["postDate"],
                    "likes": row["likes"],
                    "timeElapse": time_ago(datetime.now(timezone.utc) - datetime.strptime(
                        row["postDate"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)),
                    "originalTime": originalTime
                })

            # If the post has comments, add them to a dictionary based on postID
            # Ensuring the comment exists (non-null content)
            if row["commentContent"]:
                comment = {
                    "commentUserID": row["commentUserID"],
                    "content": row["commentContent"],
                    "createdDate": row["commentCreatedDate"],
                    "userName": row["commentUserName"],
                    "avatar": row["commentAvatar"],
                    "timeElapse": time_ago(datetime.now(timezone.utc) - datetime.strptime(
                        row["commentCreatedDate"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc))
                }

                # Collect the comments by postID
                if row["postID"] not in comments_by_post:
                    comments_by_post[row["postID"]] = []
                comments_by_post[row["postID"]].append(comment)
        
        for post in posts:
            print("PostID: ", post["postID"])
            print(post["originalTime"], type(post["originalTime"]))
            print("------------")
        posts.sort(key=lambda post: post['originalTime'], reverse=False)

        print("After the sort: ******")
        for post in posts:
            print("PostID: ", post["postID"])
            print(post["originalTime"], type(post["originalTime"]))
            print("------------")

        # Pass comments grouped by post
        return render_template("index.html", posts=posts, comments=comments_by_post)

    if request.method == "POST":
        # Handle comment submission
        comment_content = request.form.get("commentInput")
        post_id = request.form.get("postID")  # postID hidden field from form

        print(comment_content + " ----- " + post_id)
        if comment_content and post_id:
            # Assuming user is logged in and user_id is in session
            user_id = session["user_id"]

            # Insert the new comment into the database
            db.execute(
                "INSERT INTO Comment (postID, userID, content, createdDate) VALUES (?, ?, ?, ?)",
                post_id, user_id, comment_content, datetime.now(
                    timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            )

        # After posting the comment, redirect to the home page (or the current page)
        return redirect("/")
# Midway path
@application.route("/search_profile", methods=["POST"])
def search_profile():
    # Capture the username from the form
    username = request.form.get("username")
    
    # Redirect to the dynamic profile URL
    return redirect(f"/profile/{username}")

@application.route("/profile", methods=["GET", "POST"])
def mainProfile():
    user_info = db.execute(
                "SELECT ID, name, email, handler, imageUrl FROM User WHERE ID = ?", session["user_id"])
    if request.method == "GET":
        return redirect(f'/profile/{user_info[0]["handler"]}')
    else:
        # Handle user form creation
        imageUrl = request.form.get("post-imageUrl")
        songName = request.form.get("post-songName")
        songLink = request.form.get("post-songLink")
        postDescription = request.form.get("post-description")

        # Add the song to DB to get the songID
        songId = db.execute("INSERT INTO Song (songName, songUrl) VALUES (?, ?)",
                            songName, songLink)
        
        # Insert the new comment into the database
        db.execute(
                "INSERT INTO Post (imageUrl, title, songID, userID) VALUES (?, ?, ?, ?)",
                imageUrl, postDescription, songId, session["user_id"])
        
        return redirect(f'/profile/{user_info[0]["handler"]}')


@application.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    if request.method == "GET":
        current_logged_in_user = db.execute(
            "SELECT ID, name, email, handler, imageUrl FROM User WHERE ID = ?", session["user_id"])

        # Fetch user info based on the username provided in the URL
        user_info = db.execute(
            "SELECT ID, name, email, handler, imageUrl FROM User WHERE handler = ?", username)

        # Check if the user exists
        if not user_info:
            return "User not found", 404

        user_info = user_info[0]  # Assuming 'handler' is unique
        user_id = user_info["ID"]
        image_url = user_info["imageUrl"]

        if not image_url:
            image_url = "../static/avatar.jpeg"

        # Fetch all posts with associated comments for the specified user
        posts_with_comments = db.execute(
            """
            SELECT 
                Post.ID as postID, 
                Post.imageUrl as imageUrl, 
                Post.createdDate as postDate, 
                User.ID as userID, 
                User.handler, 
                Song.songName, 
                Song.songUrl, 
                Comment.userID as commentUserID, 
                Comment.content as commentContent, 
                Comment.createdDate as commentCreatedDate,
                U.name as commentUserName,
                U.imageUrl as commentAvatar
            FROM Post 
            JOIN Song ON Post.songID = Song.ID 
            JOIN User ON Post.userID = User.ID
            LEFT JOIN Comment ON Post.ID = Comment.postID
            LEFT JOIN User U ON Comment.userID = U.ID
            WHERE User.ID = ?
            """, user_id
        )

        # Processing posts and comments remains the same
        posts = []
        comments_by_post = {}

        for row in posts_with_comments:
            if not any(p["postID"] == row["postID"] for p in posts):
                posts.append({
                    "postID": row["postID"],
                    "imageUrl": row["imageUrl"],
                    "userID": row["userID"],
                    "handler": row["handler"],
                    "songName": row["songName"],
                    "songUrl": row["songUrl"],
                    "postDate": row["postDate"],
                    "timeElapse": time_ago(datetime.now(timezone.utc) - datetime.strptime(
                        row["postDate"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc))
                })

            if row["commentContent"]:
                comment = {
                    "commentUserID": row["commentUserID"],
                    "content": row["commentContent"],
                    "createdDate": row["commentCreatedDate"],
                    "userName": row["commentUserName"],
                    "avatar": row["commentAvatar"],
                    "timeElapse": time_ago(datetime.now(timezone.utc) - datetime.strptime(
                        row["commentCreatedDate"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc))
                }

                if row["postID"] not in comments_by_post:
                    comments_by_post[row["postID"]] = []
                comments_by_post[row["postID"]].append(comment)

        return render_template("profile.html", current_logged_in_user=current_logged_in_user, user_info=user_info, username=username, image_url=image_url, posts=posts, comments=comments_by_post)


@application.route("/likes", methods=["POST"])
def likeAction():
    post_id = request.form.get("postID")  # postID hidden field from form
    print("Posst ID: ", post_id)
    currentLike = db.execute("SELECT likes FROM Post WHERE ID = ?", post_id)[0]
    # print("Current Like: ", currentLike["likes"])
    # Insert the follow relationship into the database
    try:
        db.execute("UPDATE Post SET likes = ? WHERE ID = ?", currentLike["likes"] + 1, post_id)
        # flash("You are now following the user!", "success")
    except Exception as e:
        # flash("An error occurred while trying to follow the user.", "danger")
        print(e)

    return redirect("/")  # Redirect as needed


@application.route("/follow", methods=["POST"])
def follow():
    user_id_to_follow = request.form.get("user_id_to_follow")

    # Insert the follow relationship into the database
    try:
        db.execute("INSERT INTO Followers (ID, FollowingID, FollowerID) VALUES (?, ?, ?)",
                   str(uuid.uuid4()), session["user_id"], user_id_to_follow)
        # flash("You are now following the user!", "success")
    except Exception as e:
        # flash("An error occurred while trying to follow the user.", "danger")
        print(e)

    return redirect("/")  # Redirect as needed


@application.route("/friends", methods=["GET", "POST"])
def friendPage():
    if request.method == "GET":
        userInfo = db.execute("SELECT handler FROM User WHERE ID = ?", session["user_id"])

        followingUsers = db.execute(
            "SELECT * FROM Followers JOIN Profile ON Followers.FollowerID = Profile.UserID WHERE FollowingID =  ?", session["user_id"])
        # print(followingUsers)

        followerUsers = db.execute(
            "SELECT * FROM Followers JOIN Profile ON Followers.FollowingID = Profile.UserID WHERE FollowerID =  ?", session["user_id"])
        print(followerUsers)
    return render_template("friends.html", followingUsers=followingUsers, followerUsers=followerUsers, user=userInfo[0])

# Changing profile picture
@application.route("/changeProfilePicture", methods=["GET", "POST"])
def changeProfilePicture():
    if request.method == "POST":
        imageUrl = request.form.get("post-imageUrl")
        db.execute("UPDATE User SET imageUrl = ? WHERE ID = ?", imageUrl, session["user_id"])
        return redirect("/")

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

# Register Page
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
