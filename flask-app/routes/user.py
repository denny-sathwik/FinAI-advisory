from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db, bcrypt
from models.models import User, Account, Card, Notification

user_bp = Blueprint("user", __name__, url_prefix="/api/user")


def _notify(user_id, title, message, ntype="info"):
    n = Notification(user_id=user_id, type=ntype, title=title, message=message)
    db.session.add(n)


# ── Profile ────────────────────────────────────────────────────────────────────

@user_bp.route("/update/<int:user_id>", methods=["PATCH"])
@jwt_required()
def update_user(user_id):
    current = int(get_jwt_identity())
    if current != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if "fname" in data:
        user.fname = data["fname"].strip()
    if "lname" in data:
        user.lname = data["lname"].strip()
    if "email" in data:
        user.email = data["email"].strip().lower()
    if "profile_img" in data:
        user.profile_img = data["profile_img"]
    if "password" in data:
        pw = data["password"]
        if len(pw) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400
        user.password = bcrypt.generate_password_hash(pw).decode("utf-8")

    _notify(user_id, "Profile Updated", "Your profile information was updated.", "update")
    db.session.commit()
    return jsonify({"message": "Profile updated", "user": user.to_dict()}), 200


# ── Account Details ────────────────────────────────────────────────────────────

@user_bp.route("/account", methods=["GET"])
@jwt_required()
def get_account():
    user_id = int(get_jwt_identity())
    account = Account.query.filter_by(user_id=user_id).first()
    if not account:
        return jsonify({"error": "No account found"}), 404
    return jsonify({"account": account.to_dict()}), 200


@user_bp.route("/account-details", methods=["POST"])
@jwt_required()
def save_account_details():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    # Validate required fields
    required = ["total_balance", "amount_invested", "monthly_income", "monthly_budget",
                "account_type", "card_number", "card_holder", "card_cvc"]
    for field in required:
        if data.get(field) is None:
            return jsonify({"error": f"{field} is required"}), 400

    if len(str(data["card_number"])) != 16:
        return jsonify({"error": "Card number must be 16 digits"}), 400
    if len(str(data["card_cvc"])) != 3:
        return jsonify({"error": "CVC must be 3 digits"}), 400
    if len(str(data["card_holder"])) < 3:
        return jsonify({"error": "Card holder name must be at least 3 characters"}), 400

    # Upsert account
    account = Account.query.filter_by(user_id=user_id).first()
    if account:
        account.total_balance = data["total_balance"]
        account.amount_invested = data["amount_invested"]
        account.monthly_income = data["monthly_income"]
        account.monthly_budget = data["monthly_budget"]
        account.account_type = data["account_type"]
        _notify(user_id, "Account Updated", "Your account details have been updated.", "update")
    else:
        account = Account(
            user_id=user_id,
            total_balance=data["total_balance"],
            amount_invested=data["amount_invested"],
            monthly_income=data["monthly_income"],
            monthly_budget=data["monthly_budget"],
            account_type=data["account_type"],
        )
        db.session.add(account)
        _notify(user_id, "Account Created", "Your account has been set up successfully!", "success")

    # Upsert card (one card per user for simplicity)
    card = Card.query.filter_by(user_id=user_id).first()
    if card:
        card.card_number = str(data["card_number"])
        card.card_holder = data["card_holder"]
        card.card_cvc = str(data["card_cvc"])
    else:
        card = Card(
            user_id=user_id,
            card_number=str(data["card_number"]),
            card_holder=data["card_holder"],
            card_cvc=str(data["card_cvc"]),
        )
        db.session.add(card)

    db.session.commit()
    return jsonify({"message": "Account and card saved successfully"}), 201


@user_bp.route("/update-account", methods=["PATCH"])
@jwt_required()
def update_account():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    account = Account.query.filter_by(user_id=user_id).first()
    if not account:
        return jsonify({"error": "Account not found"}), 404
    if "monthly_budget" in data:
        account.monthly_budget = data["monthly_budget"]
    db.session.commit()
    return jsonify({"message": "Account updated"}), 200


@user_bp.route("/card", methods=["GET"])
@jwt_required()
def get_cards():
    user_id = int(get_jwt_identity())
    cards = Card.query.filter_by(user_id=user_id).all()
    if not cards:
        return jsonify({"error": "No cards found"}), 404
    return jsonify({"cards": [c.to_dict() for c in cards], "count": len(cards)}), 200


# ── Notifications ──────────────────────────────────────────────────────────────

@user_bp.route("/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    user_id = int(get_jwt_identity())
    notifications = (
        Notification.query
        .filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return jsonify({"notifications": [n.to_dict() for n in notifications]}), 200
