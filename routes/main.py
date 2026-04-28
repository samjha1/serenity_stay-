from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import (
    db,
    Room,
    Booking,
    MenuItem,
    FoodOrder,
    ServiceRequest,
    Invoice,
    ActivityBooking,
    User,
    ContactMessage,
)
from datetime import datetime, date
import json

main_bp = Blueprint("main", __name__)


def guest_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "guest":
            flash("Access denied.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated


def _ensure_default_menu_items():
    """Create a starter menu so Food order is usable on fresh databases."""
    if MenuItem.query.count() > 0:
        return
    defaults = [
        {"name": "Margherita Pizza", "description": "Classic pizza with mozzarella and basil.", "category": "main_course", "price": 420, "is_veg": True},
        {"name": "Paneer Tikka", "description": "Char-grilled cottage cheese cubes with spices.", "category": "starters", "price": 320, "is_veg": True},
        {"name": "Chicken Burger", "description": "Grilled chicken patty burger with fries.", "category": "main_course", "price": 390, "is_veg": False},
        {"name": "Pasta Alfredo", "description": "Creamy alfredo pasta with herbs.", "category": "main_course", "price": 360, "is_veg": True},
        {"name": "Chocolate Brownie", "description": "Warm brownie served with vanilla scoop.", "category": "desserts", "price": 240, "is_veg": True},
        {"name": "Fresh Lime Soda", "description": "Refreshing sweet and salted lime soda.", "category": "beverages", "price": 120, "is_veg": True},
    ]
    for item in defaults:
        db.session.add(MenuItem(is_available=True, **item))
    db.session.commit()


@main_bp.route("/")
def index():
    return render_template("pages/public/index.html")


@main_bp.route("/contact", methods=["POST"])
def submit_contact():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    subject = request.form.get("subject", "").strip()
    message = request.form.get("message", "").strip()
    if not name or not email or len(message) < 10:
        return jsonify({"success": False, "message": "Please complete all required fields."}), 400

    contact = ContactMessage(name=name, email=email, subject=subject, message=message)
    db.session.add(contact)
    db.session.commit()
    return jsonify({"success": True, "message": "Message sent successfully. We will contact you soon."})


@main_bp.route("/dashboard")
@login_required
@guest_required
def dashboard():
    bookings = (
        Booking.query.filter_by(user_id=current_user.id)
        .order_by(Booking.created_at.desc())
        .limit(5)
        .all()
    )
    food_orders = (
        FoodOrder.query.filter_by(user_id=current_user.id)
        .order_by(FoodOrder.created_at.desc())
        .limit(5)
        .all()
    )
    service_requests = (
        ServiceRequest.query.filter_by(user_id=current_user.id)
        .order_by(ServiceRequest.created_at.desc())
        .limit(5)
        .all()
    )
    activity_bookings = (
        ActivityBooking.query.filter_by(user_id=current_user.id)
        .order_by(ActivityBooking.created_at.desc())
        .limit(5)
        .all()
    )
    active_booking = Booking.query.filter_by(user_id=current_user.id, status="checked_in").first()
    return render_template(
        "pages/guest/dashboard.html",
        bookings=bookings,
        food_orders=food_orders,
        service_requests=service_requests,
        activity_bookings=activity_bookings,
        active_booking=active_booking,
    )


@main_bp.route("/rooms")
@login_required
@guest_required
def rooms():
    room_type = request.args.get("room_type", "")
    check_in = request.args.get("check_in", "")
    check_out = request.args.get("check_out", "")
    q = Room.query.filter_by(status="available")
    if room_type:
        q = q.filter_by(room_type=room_type)
    rooms = q.all()
    return render_template(
        "pages/guest/rooms.html", rooms=rooms, check_in=check_in, check_out=check_out, room_type=room_type
    )


@main_bp.route("/book/<int:room_id>", methods=["GET", "POST"])
@login_required
@guest_required
def book_room(room_id):
    room = Room.query.get_or_404(room_id)
    if room.status != "available":
        flash("This room is currently not available for booking.", "error")
        return redirect(url_for("main.rooms"))

    if request.method == "POST":
        ci = request.form.get("check_in")
        co = request.form.get("check_out")
        try:
            guests = int(request.form.get("guests", 1))
        except ValueError:
            flash("Invalid guest count.", "error")
            return render_template("pages/guest/booking.html", room=room, today=date.today().isoformat())

        special = request.form.get("special_requests", "")
        try:
            check_in = datetime.strptime(ci, "%Y-%m-%d").date()
            check_out = datetime.strptime(co, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid dates.", "error")
            return render_template("pages/guest/booking.html", room=room, today=date.today().isoformat())

        if check_in >= check_out:
            flash("Check-out must be after check-in.", "error")
            return render_template("pages/guest/booking.html", room=room, today=date.today().isoformat())
        if check_in < date.today():
            flash("Check-in cannot be in the past.", "error")
            return render_template("pages/guest/booking.html", room=room, today=date.today().isoformat())
        if guests < 1 or guests > room.capacity:
            flash(f"Guest count must be between 1 and {room.capacity}.", "error")
            return render_template("pages/guest/booking.html", room=room, today=date.today().isoformat())

        nights = (check_out - check_in).days
        total = nights * room.price_per_night
        booking = Booking(
            user_id=current_user.id,
            room_id=room_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            special_requests=special,
            total_amount=total,
            status="confirmed",
        )
        db.session.add(booking)
        db.session.flush()

        tax = round(total * 0.12, 2)
        invoice = Invoice(
            booking_id=booking.id,
            user_id=current_user.id,
            room_charges=total,
            food_charges=0,
            service_charges=0,
            tax_amount=tax,
            total_amount=round(total + tax, 2),
            status="unpaid",
        )
        db.session.add(invoice)
        db.session.commit()

        flash(f"Booking confirmed! Room {room.room_number} for {nights} night(s).", "success")
        return redirect(url_for("main.dashboard"))

    return render_template(
        "pages/guest/booking.html",
        room=room,
        today=date.today().isoformat(),
        check_in=request.args.get("check_in", ""),
        check_out=request.args.get("check_out", ""),
    )


@main_bp.route("/food")
@login_required
@guest_required
def food():
    _ensure_default_menu_items()
    menu_items = MenuItem.query.filter_by(is_available=True).all()
    active_booking = Booking.query.filter_by(user_id=current_user.id, status="checked_in").first()
    menu_by_category = {}
    for item in menu_items:
        menu_by_category.setdefault(item.category, []).append(item)
    orders = (
        FoodOrder.query.filter_by(user_id=current_user.id)
        .order_by(FoodOrder.created_at.desc())
        .limit(10)
        .all()
    )
    return render_template(
        "pages/guest/food.html", menu_by_category=menu_by_category, active_booking=active_booking, orders=orders
    )


@main_bp.route("/food/order", methods=["POST"])
@login_required
@guest_required
def place_order():
    data = request.get_json() or {}
    items = data.get("items", [])
    instructions = data.get("instructions", "")
    booking_id = data.get("booking_id")
    if not items:
        return jsonify({"success": False, "message": "No items selected"}), 400

    total = 0
    for item in items:
        mi = MenuItem.query.get(item["id"])
        if mi:
            total += mi.price * item["qty"]

    order = FoodOrder(
        user_id=current_user.id,
        booking_id=booking_id,
        items_json=json.dumps(items),
        total_amount=round(total, 2),
        special_instructions=instructions,
        status="pending",
    )
    db.session.add(order)

    if booking_id:
        inv = Invoice.query.filter_by(booking_id=booking_id, user_id=current_user.id).first()
        if inv:
            inv.food_charges += round(total, 2)
            subtotal = inv.room_charges + inv.food_charges + inv.service_charges
            inv.tax_amount = round(subtotal * 0.12, 2)
            inv.total_amount = round(subtotal + inv.tax_amount, 2)

    db.session.commit()
    return jsonify({"success": True, "message": "Order placed!", "order_id": order.id})


@main_bp.route("/services")
@login_required
@guest_required
def services():
    active_booking = Booking.query.filter_by(user_id=current_user.id, status="checked_in").first()
    requests = (
        ServiceRequest.query.filter_by(user_id=current_user.id)
        .order_by(ServiceRequest.created_at.desc())
        .all()
    )
    return render_template("pages/guest/services.html", active_booking=active_booking, requests=requests)


@main_bp.route("/services/request", methods=["POST"])
@login_required
@guest_required
def request_service():
    service_type = request.form.get("service_type")
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "normal")
    booking_id = request.form.get("booking_id")
    if not service_type or not description:
        flash("Service type and description are required.", "error")
        return redirect(url_for("main.services"))
    sr = ServiceRequest(
        user_id=current_user.id,
        booking_id=booking_id or None,
        service_type=service_type,
        description=description,
        priority=priority,
        status="pending",
    )
    db.session.add(sr)
    db.session.commit()
    flash("Service request submitted successfully.", "success")
    return redirect(url_for("main.services"))


@main_bp.route("/activities")
@login_required
@guest_required
def activities():
    bookings = (
        ActivityBooking.query.filter_by(user_id=current_user.id)
        .order_by(ActivityBooking.created_at.desc())
        .all()
    )
    return render_template("pages/guest/activities.html", bookings=bookings, today=date.today().isoformat())


@main_bp.route("/activities/book", methods=["POST"])
@login_required
@guest_required
def book_activity():
    activity_type = request.form.get("activity_type", "").strip()
    preferred_date_raw = request.form.get("preferred_date", "").strip()
    preferred_time = request.form.get("preferred_time", "").strip()
    guests_count_raw = request.form.get("guests_count", "1").strip()
    notes = request.form.get("notes", "").strip()
    if not activity_type or not preferred_date_raw or not preferred_time:
        flash("Activity type, date, and time are required.", "error")
        return redirect(url_for("main.activities"))
    try:
        preferred_date = datetime.strptime(preferred_date_raw, "%Y-%m-%d").date()
        guests_count = int(guests_count_raw)
    except ValueError:
        flash("Invalid activity date or guest count.", "error")
        return redirect(url_for("main.activities"))
    if preferred_date < date.today():
        flash("Preferred date cannot be in the past.", "error")
        return redirect(url_for("main.activities"))
    if guests_count < 1 or guests_count > 10:
        flash("Guests count must be between 1 and 10.", "error")
        return redirect(url_for("main.activities"))

    frontdesk = User.query.filter_by(role="frontdesk").first()
    booking = ActivityBooking(
        user_id=current_user.id,
        activity_type=activity_type,
        preferred_date=preferred_date,
        preferred_time=preferred_time,
        guests_count=guests_count,
        notes=notes,
        status="pending",
        assigned_to=frontdesk.id if frontdesk else None,
    )
    db.session.add(booking)
    db.session.commit()
    flash("Activity booking submitted. Frontdesk will confirm shortly.", "success")
    return redirect(url_for("main.activities"))


@main_bp.route("/invoice/<int:booking_id>")
@login_required
@guest_required
def invoice(booking_id):
    booking = Booking.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    inv = Invoice.query.filter_by(booking_id=booking_id).first()
    food_orders = FoodOrder.query.filter_by(booking_id=booking_id).all()
    service_reqs = ServiceRequest.query.filter_by(booking_id=booking_id).all()
    return render_template(
        "pages/guest/invoice.html", booking=booking, invoice=inv, food_orders=food_orders, service_reqs=service_reqs
    )


@main_bp.route("/api/order-status")
@login_required
@guest_required
def order_status():
    orders = (
        FoodOrder.query.filter_by(user_id=current_user.id)
        .order_by(FoodOrder.created_at.desc())
        .limit(5)
        .all()
    )
    return jsonify(
        [{"id": o.id, "status": o.status, "total": o.total_amount, "created": o.created_at.strftime("%H:%M")} for o in orders]
    )


@main_bp.route("/api/service-status")
@login_required
@guest_required
def service_status_api():
    reqs = (
        ServiceRequest.query.filter_by(user_id=current_user.id)
        .order_by(ServiceRequest.created_at.desc())
        .limit(5)
        .all()
    )
    return jsonify(
        [{"id": r.id, "type": r.service_type, "status": r.status, "created": r.created_at.strftime("%d %b %H:%M")} for r in reqs]
    )

