from flask import Blueprint, request, jsonify, make_response, redirect, url_for, current_app
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity,
    unset_jwt_cookies, set_access_cookies
)
from extensions import db, bcrypt, oauth
from models.models import User, Notification
import re
import secrets

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _add_notification(user_id, title, message, ntype="info"):
    n = Notification(user_id=user_id, type=ntype, title=title, message=message)
    db.session.add(n)
    db.session.commit()


def _google_oauth_error(message):
    return redirect(url_for("pages.login", oauth_error=message))


def _split_google_name(userinfo):
    fname = (userinfo.get("given_name") or "").strip()
    lname = (userinfo.get("family_name") or "").strip()
    full_name = (userinfo.get("name") or "").strip()

    if not fname and full_name:
        parts = full_name.split(" ", 1)
        fname = parts[0]
        if len(parts) > 1:
            lname = parts[1]

    email = (userinfo.get("email") or "").strip()
    if not fname and email:
        fname = email.split("@", 1)[0]
    if not lname:
        lname = "Google"

    return fname or "Google", lname


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    fname = (data.get("fname") or "").strip()
    lname = (data.get("lname") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    profile_img = data.get("profile_img", "")

    if not all([fname, lname, email, password]):
        return jsonify({"error": "All fields are required"}), 400
    if len(fname) < 3 or len(lname) < 3:
        return jsonify({"error": "Name must be at least 3 characters"}), 400
    if "@" not in email:
        return jsonify({"error": "Invalid email address"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    hashed = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(fname=fname, lname=lname, email=email, password=hashed,
                profile_img=profile_img, signup_method="form")
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=str(user.id))
    _add_notification(user.id, "Login", f"Welcome back, {user.fname}!", "login")

    response = make_response(jsonify({"message": "Login successful", "user": user.to_dict()}))
    set_access_cookies(response, token)
    return response, 200


@auth_bp.route("/google/login", methods=["GET"])
def google_login():
    google = oauth.create_client("google")
    if google is None:
        return _google_oauth_error("Google login is not configured yet.")

    redirect_uri = (
        current_app.config.get("GOOGLE_REDIRECT_URI")
        or url_for("auth.google_callback", _external=True)
    )
    return google.authorize_redirect(redirect_uri)


@auth_bp.route("/google/callback", methods=["GET"])
def google_callback():
    if request.args.get("error"):
        return _google_oauth_error("Google sign-in was cancelled or denied.")

    google = oauth.create_client("google")
    if google is None:
        return _google_oauth_error("Google login is not configured yet.")

    try:
        token = google.authorize_access_token()
    except Exception:
        return _google_oauth_error("Google sign-in could not be verified.")

    userinfo = token.get("userinfo")
    if not userinfo:
        try:
            userinfo = google.get("https://openidconnect.googleapis.com/v1/userinfo").json()
        except Exception:
            return _google_oauth_error("Google profile could not be loaded.")

    email = (userinfo.get("email") or "").strip().lower()
    if not email:
        return _google_oauth_error("Google did not return an email address.")
    if userinfo.get("email_verified") in (False, "false", "False", "0", 0):
        return _google_oauth_error("Please verify your Google email before signing in.")

    user = User.query.filter_by(email=email).first()
    if not user:
        fname, lname = _split_google_name(userinfo)
        random_password = secrets.token_urlsafe(32)
        user = User(
            fname=fname,
            lname=lname,
            email=email,
            password=bcrypt.generate_password_hash(random_password).decode("utf-8"),
            profile_img=userinfo.get("picture", ""),
            signup_method="google",
        )
        db.session.add(user)
        db.session.commit()
        _add_notification(user.id, "Account Created", f"Welcome, {user.fname}!", "success")
    else:
        if not user.profile_img and userinfo.get("picture"):
            user.profile_img = userinfo["picture"]
            db.session.commit()
        _add_notification(user.id, "Login", f"Welcome back, {user.fname}!", "login")

    access_token = create_access_token(identity=str(user.id))
    response = make_response(redirect(url_for("pages.dashboard")))
    set_access_cookies(response, access_token)
    return response


@auth_bp.route("/logout", methods=["POST"])
def logout():
    response = make_response(jsonify({"message": "Logged out"}))
    unset_jwt_cookies(response)
    response.delete_cookie("access_token_cookie")
    return response, 200


@auth_bp.route("/delete", methods=["DELETE"])
@jwt_required()
def delete_account():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    db.session.delete(user)
    db.session.commit()
    response = make_response(jsonify({"message": "Account deleted successfully"}))
    unset_jwt_cookies(response)
    response.delete_cookie("access_token_cookie")
    return response, 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200
