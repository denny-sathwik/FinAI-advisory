from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.models import Account, Transaction
from datetime import datetime
from sqlalchemy import func

transaction_bp = Blueprint("transactions", __name__, url_prefix="/api/transactions")

VALID_CATEGORIES = [
    "groceries", "housing", "entertainment", "transportation",
    "healthcare", "education", "shopping", "food",
    "personal", "utilities", "other-expense",
]


def _parse_positive_amount(value):
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None
    return amount if amount > 0 else None


@transaction_bp.route("/add", methods=["POST"])
@jwt_required()
def add_transaction():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    required = ["merchant_name", "amount", "date", "category"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    if data["category"] not in VALID_CATEGORIES:
        return jsonify({"error": "Invalid category"}), 400

    amount = _parse_positive_amount(data["amount"])
    if amount is None:
        return jsonify({"error": "Amount must be greater than 0"}), 400

    account = Account.query.filter_by(user_id=user_id).first()
    if not account:
        return jsonify({"error": "Set up account details before adding transactions"}), 404

    try:
        # Accept "YYYY-MM-DD", "YYYY-MM-DDTHH:MM:SS", or full ISO with Z / offset
        raw_date = data["date"].replace("Z", "+00:00").replace("z", "+00:00")
        tx_date = datetime.fromisoformat(raw_date)
    except (ValueError, AttributeError):
        return jsonify({"error": "Invalid date format. Use ISO 8601."}), 400

    tx = Transaction(
        user_id=user_id,
        amount=amount,
        merchant_name=data["merchant_name"],
        date=tx_date,
        category=data["category"],
        description=data.get("description", ""),
    )
    account.total_balance = (account.total_balance or 0) - amount
    db.session.add(tx)
    db.session.commit()
    return jsonify({
        "message": "Transaction added successfully",
        "transaction": tx.to_dict(),
        "account": account.to_dict(),
    }), 200


@transaction_bp.route("/", methods=["GET"])
@jwt_required()
def get_transactions():
    user_id = int(get_jwt_identity())
    txs = (
        Transaction.query
        .filter_by(user_id=user_id)
        .order_by(Transaction.created_at.desc())
        .all()
    )
    return jsonify({"transactions": [t.to_dict() for t in txs]}), 200


@transaction_bp.route("/total", methods=["GET"])
@jwt_required()
def get_total():
    user_id = int(get_jwt_identity())
    total = db.session.query(func.sum(Transaction.amount)).filter_by(user_id=user_id).scalar() or 0
    return jsonify({"total_amount": total}), 200


@transaction_bp.route("/<int:tx_id>", methods=["DELETE"])
@jwt_required()
def delete_transaction(tx_id):
    user_id = int(get_jwt_identity())
    tx = Transaction.query.filter_by(id=tx_id, user_id=user_id).first()
    if not tx:
        return jsonify({"error": "Transaction not found"}), 404
    account = Account.query.filter_by(user_id=user_id).first()
    if account:
        account.total_balance = (account.total_balance or 0) + tx.amount
    db.session.delete(tx)
    db.session.commit()
    return jsonify({
        "message": "Deleted",
        "account": account.to_dict() if account else None,
    }), 200


@transaction_bp.route("/<int:tx_id>", methods=["PATCH"])
@jwt_required()
def edit_transaction(tx_id):
    user_id = int(get_jwt_identity())
    tx = Transaction.query.filter_by(id=tx_id, user_id=user_id).first()
    if not tx:
        return jsonify({"error": "Transaction not found"}), 404
    data = request.get_json()
    account = Account.query.filter_by(user_id=user_id).first()
    old_amount = tx.amount
    if "merchant_name" in data:
        tx.merchant_name = data["merchant_name"]
    if "amount" in data:
        amount = _parse_positive_amount(data["amount"])
        if amount is None:
            return jsonify({"error": "Amount must be greater than 0"}), 400
        tx.amount = amount
    if "category" in data:
        if data["category"] not in VALID_CATEGORIES:
            return jsonify({"error": "Invalid category"}), 400
        tx.category = data["category"]
    if "description" in data:
        tx.description = data["description"]
    if "date" in data:
        try:
            raw = data["date"].replace("Z", "+00:00")
            tx.date = datetime.fromisoformat(raw)
        except (ValueError, AttributeError):
            return jsonify({"error": "Invalid date format"}), 400
    if account:
        account.total_balance = (account.total_balance or 0) + old_amount - tx.amount
    db.session.commit()
    return jsonify({
        "message": "Updated",
        "transaction": tx.to_dict(),
        "account": account.to_dict() if account else None,
    }), 200


@transaction_bp.route("/statistics", methods=["GET"])
@jwt_required()
def get_statistics():
    user_id = int(get_jwt_identity())
    rows = (
        db.session.query(Transaction.category, func.sum(Transaction.amount))
        .filter_by(user_id=user_id)
        .group_by(Transaction.category)
        .all()
    )
    stats = [{"category": row[0], "total_amount": float(row[1])} for row in rows]
    return jsonify({"spending_by_category": stats}), 200
