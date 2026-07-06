from flask import Blueprint, render_template, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError
from jwt.exceptions import ExpiredSignatureError

pages_bp = Blueprint("pages", __name__)


def is_authenticated():
    try:
        verify_jwt_in_request()
        return True
    except Exception:
        return False


@pages_bp.route("/")
def home():
    return render_template("home.html")


@pages_bp.route("/login")
def login():
    if is_authenticated():
        return redirect(url_for("pages.dashboard"))
    return render_template("login.html")


@pages_bp.route("/register")
def register():
    if is_authenticated():
        return redirect(url_for("pages.dashboard"))
    return render_template("register.html")


@pages_bp.route("/dashboard")
def dashboard():
    if not is_authenticated():
        return redirect(url_for("pages.login"))
    return render_template("dashboard.html")


@pages_bp.route("/ai-assistant")
def ai_assistant():
    if not is_authenticated():
        return redirect(url_for("pages.login"))
    return render_template("ai_assistant.html")


@pages_bp.route("/risk-assessment")
def risk_assessment():
    if not is_authenticated():
        return redirect(url_for("pages.login"))
    return render_template("risk_assessment.html")


@pages_bp.route("/goal-planning")
def goal_planning():
    if not is_authenticated():
        return redirect(url_for("pages.login"))
    return render_template("goal_planning.html")


@pages_bp.route("/financial-health")
def financial_health():
    if not is_authenticated():
        return redirect(url_for("pages.login"))
    return render_template("financial_health.html")


@pages_bp.route("/spendings")
def spendings():
    if not is_authenticated():
        return redirect(url_for("pages.login"))
    return render_template("spendings.html")


@pages_bp.route("/transactions")
def transactions():
    if not is_authenticated():
        return redirect(url_for("pages.login"))
    return render_template("transactions.html")


@pages_bp.route("/news")
def news():
    if not is_authenticated():
        return redirect(url_for("pages.login"))
    return render_template("news.html")


@pages_bp.route("/profile")
def profile():
    if not is_authenticated():
        return redirect(url_for("pages.login"))
    return render_template("profile.html")


@pages_bp.route("/account")
def account():
    if not is_authenticated():
        return redirect(url_for("pages.login"))
    return render_template("account.html")


@pages_bp.route("/billing")
def billing():
    if not is_authenticated():
        return redirect(url_for("pages.login"))
    return render_template("billing.html")


@pages_bp.route("/notifications")
def notifications():
    if not is_authenticated():
        return redirect(url_for("pages.login"))
    return render_template("notifications.html")


@pages_bp.route("/contact")
def contact():
    return render_template("contact.html")
