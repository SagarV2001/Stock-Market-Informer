import os
import time
import mongo
import otpModule
from flask import Flask, request, session, render_template, redirect
import smtplib
import dotenv
import user
import threading

def update():
    while(True):
        try:
            members_to_alert = mongo.updateAndreturnUsersToNotify()
            with smtplib.SMTP("smtp.gmail.com") as connection:
                SENDER_EMAIL = os.getenv("SENDER_EMAIL")
                SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
                connection.starttls()
                connection.login(user=SENDER_EMAIL, password=SENDER_PASSWORD)
                for tup in members_to_alert:  #tup = (email,stock_name,change)
                    connection.sendmail(from_addr=SENDER_EMAIL, to_addrs=tup[0],
                                    msg=f"Subject:SMI Stock sudden surge/fall \n\n Your stock {tup[1]} recently had {tup[2]} of over 4 percent.")
            print("Update done!")
            time.sleep(14400)  # run every 4 hours
        except Exception:
            print("Update Failed!")
            time.sleep(3600)  # run every 1 hour if update failed


if __name__=="__main__":
    update_thread = threading.Thread(target=update)
    update_thread.start()
    #loading constants

    #server initialization and cookie creation
    app = Flask(__name__, static_url_path='/static')
    app.secret_key = os.getenv("SESSION_KEY")
    app.config["SESSION_COOKIE_SECURE"] = True

    #default user initialization
    authorized_user=None
    registration_attempt = 5  #otp attempts

    @app.route("/")
    def home():
        if isLoggedIn():
            return redirect("/logged-in")
        return render_template("index.html")

    @app.post("/register")
    @app.get("/register")
    def register():
        if isLoggedIn():
            return redirect("/logged-in")
        else:
            return render_template("register.html")

    @app.get("/login")
    @app.post("/login")
    def login():
        if isLoggedIn():
            return redirect("/logged-in")
        else:
            return render_template("login.html")

    @app.post("/login-user")
    def loginUser():
        global authorized_user
        #return username if email is entered
        session["username"] = mongo.getUserName(request.form["username"])
        session["password"] = request.form["password"]
        if isLoggedIn():
            return redirect("/logged-in")
        else:
            return redirect("/login-error")

    @app.route("/login-<error>")
    def retryLogin(error):
        msg="Wrong username or password"
        return render_template("login.html",error=msg)
    @app.get("/logged-in")
    def loggedInUser():
        if isLoggedIn():
            msg=None
            if session.get("error"):
                msg = session.get("error")
                print(msg)
                session.pop("error")
            global authorized_user
            authorized_user.updateData()
            return render_template("loggedIn.html",data = authorized_user.data,msg=msg)
        else:
            return redirect("/login")

    @app.post("/register-user")
    def registerUser():
        email=request.form["email"]
        session["username"] = request.form["username"]
        session["email"] = email
        session["password"] = request.form["password"]
        session["genotp"] = otpModule.generateOTP(6)

        #todo encrypt password

        with smtplib.SMTP("smtp.gmail.com") as connection:
            SENDER_EMAIL = os.getenv("SENDER_EMAIL")
            SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
            connection.starttls()
            connection.login(user=SENDER_EMAIL, password=SENDER_PASSWORD)
            connection.sendmail(from_addr=SENDER_EMAIL, to_addrs=email,
                                msg=f"Subject:SMI verification email \n\n verify email by Otp-> {session['genotp']}")
        return render_template("verifyEmail.html")


    @app.post("/verified-user")
    def verifyEmailAndCreateAccount():
        global authorized_user
        if request.form["otp"]==session.get("genotp"):
            username = session.get("username")
            email = session.get("email")
            password = session.get("password")
            authorized_user = user.User(user_id=username,password=password,email=email)
            session.pop("email")
            session.pop("genotp")
            print(authorized_user.getUserInfo())
            return redirect("/logged-in")
        else:
            global registration_attempt
            registration_attempt-=1
            if registration_attempt>0:
                return render_template("verifyEmail.html",error_message=f"OTP entered is wrong! {registration_attempt} attempts left. Then try again in new session")
            else:
                session.clear()
                return redirect("/")

    @app.post("/log-out")
    def logOut():
        try:
            session.pop("username")
            session.pop("password")
        except Exception:
            pass
        return redirect("/")
    #check cookie for user and password
    def isLoggedIn():
        global authorized_user
        authorized_user = user.getUser(user_id=session.get("username"),password=session.get("password"))
        if authorized_user:
            return True
        else:
            try:
                session.pop("username")
                session.pop("password")
            except Exception:
                pass
            return False
    @app.post("/add-data")
    def addData():
        try:
            if isLoggedIn():
                global authorized_user
                authorized_user.addData(request.form["data"])
                return redirect("/logged-in")
        except Exception:
            session["error"] = "Failed to add Data! Please retry."
            return redirect("/logged-in")
    @app.post("/delete-stock-<stock_name>")
    def deleteStock(stock_name):
        if isLoggedIn():
            try:
                global authorized_user
                authorized_user.deleteData(stock_name)
                return redirect("/logged-in")
            except Exception:
                return redirect("/logged-in")
        else:
            return redirect("/")
    app.run()