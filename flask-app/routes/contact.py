from flask import Blueprint, request, jsonify
from extensions import db
from models.models import Contact

contact_bp = Blueprint("contact", __name__, url_prefix="/api/contact")


@contact_bp.route("/", methods=["POST"])
def send_message():
    data = request.get_json()
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    subject = (data.get("subject") or "").strip()
    message = (data.get("message") or "").strip()

    if not all([name, email, subject, message]):
        return jsonify({"error": "All fields are required"}), 400

    contact = Contact(name=name, email=email, subject=subject, message=message)
    db.session.add(contact)
    db.session.commit()
    return jsonify({"message": "Message sent successfully"}), 200
