from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Room, Booking, MenuItem, FoodOrder, ServiceRequest, Invoice, ActivityBooking, User
from datetime import datetime, date
import json

guest_bp = Blueprint("guest", __name__)

def guest_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "guest":
            flash("Access denied.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

@guest_bp.route("/dashboard")
@login_required
@guest_required
def dashboard():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).limit(5).all()
    food_orders = FoodOrder.query.filter_by(user_id=current_user.id).order_by(FoodOrder.created_at.desc()).limit(5).all()
    service_requests = ServiceRequest.query.filter_by(user_id=current_user.id).order_by(ServiceRequest.created_at.desc()).limit(5).all()
    activity_bookings = ActivityBooking.query.filter_by(user_id=current_user.id).order_by(ActivityBooking.created_at.desc()).limit(5).all()
    active_booking = Booking.query.filter_by(user_id=current_user.id, status="checked_in").first()
    return render_template("pages/guest/dashboard.html", bookings=bookings, food_orders=food_orders,
        service_requests=service_requests, activity_bookings=activity_bookings, active_booking=active_booking)

@guest_bp.route("/rooms")
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
    return render_template("pages/guest/rooms.html", rooms=rooms, check_in=check_in, check_out=check_out, room_type=room_type)

@guest_bp.route("/book/<int:room_id>", methods=["GET", "POST"])
@login_required
@guest_required
def book_room(room_id):
    room = Room.query.get_or_404(room_id)
    if room.status != "available":
        flash("This room is currently not available for booking.", "error")
        return redirect(url_for("guest.rooms"))
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
        except:
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
        booking = Booking(user_id=current_user.id, room_id=room_id, check_in=check_in,
            check_out=check_out, guests=guests, special_requests=special,
            total_amount=total, status="confirmed")
        db.session.add(booking)
        db.session.flush()
        tax = round(total * 0.12, 2)
        invoice = Invoice(booking_id=booking.id, user_id=current_user.id,
            room_charges=total, food_charges=0, service_charges=0,
            tax_amount=tax, total_amount=round(total + tax, 2), status="unpaid")
        db.session.add(invoice)
        db.session.commit()
        flash(f"Booking confirmed! Room {room.room_number} for {nights} night(s).", "success")
        return redirect(url_for("guest.dashboard"))
    return render_template(
        "pages/guest/booking.html",
        room=room,
        today=date.today().isoformat(),
        check_in=request.args.get("check_in", ""),
        check_out=request.args.get("check_out", ""),
    )

@guest_bp.route("/food")
@login_required
@guest_required
def food():
    menu_items = MenuItem.query.filter_by(is_available=True).all()
    active_booking = Booking.query.filter_by(user_id=current_user.id, status="checked_in").first()
    menu_by_category = {}
    for item in menu_items:
        menu_by_category.setdefault(item.category, []).append(item)
    orders = FoodOrder.query.filter_by(user_id=current_user.id).order_by(FoodOrder.created_at.desc()).limit(10).all()
    return render_template("pages/guest/food.html", menu_by_category=menu_by_category,
        active_booking=active_booking, orders=orders)

@guest_bp.route("/food/order", methods=["POST"])
@login_required
@guest_required
def place_order():
    data = request.get_json()
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
    order = FoodOrder(user_id=current_user.id, booking_id=booking_id,
        items_json=json.dumps(items), total_amount=round(total, 2),
        special_instructions=instructions, status="pending")
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

@guest_bp.route("/services")
@login_required
@guest_required
def services():
    active_booking = Booking.query.filter_by(user_id=current_user.id, status="checked_in").first()
    requests = ServiceRequest.query.filter_by(user_id=current_user.id).order_by(ServiceRequest.created_at.desc()).all()
    return render_template("pages/guest/services.html", active_booking=active_booking, requests=requests)


@guest_bp.route("/activities")
@login_required
@guest_required
def activities():
    bookings = ActivityBooking.query.filter_by(user_id=current_user.id).order_by(ActivityBooking.created_at.desc()).all()
    return render_template("pages/guest/activities.html", bookings=bookings, today=date.today().isoformat())


@guest_bp.route("/activities/book", methods=["POST"])
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
        return redirect(url_for("guest.activities"))
    try:
        preferred_date = datetime.strptime(preferred_date_raw, "%Y-%m-%d").date()
        guests_count = int(guests_count_raw)
    except ValueError:
        flash("Invalid activity date or guest count.", "error")
        return redirect(url_for("guest.activities"))
    if preferred_date < date.today():
        flash("Preferred date cannot be in the past.", "error")
        return redirect(url_for("guest.activities"))
    if guests_count < 1 or guests_count > 10:
        flash("Guests count must be between 1 and 10.", "error")
        return redirect(url_for("guest.activities"))

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
    return redirect(url_for("guest.activities"))

@guest_bp.route("/services/request", methods=["POST"])
@login_required
@guest_required
def request_service():
    service_type = request.form.get("service_type")
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "normal")
    booking_id = request.form.get("booking_id")
    if not service_type or not description:
        flash("Service type and description are required.", "error")
        return redirect(url_for("guest.services"))
    sr = ServiceRequest(user_id=current_user.id, booking_id=booking_id or None,
        service_type=service_type, description=description, priority=priority, status="pending")
    db.session.add(sr)
    db.session.commit()
    flash("Service request submitted successfully.", "success")
    return redirect(url_for("guest.services"))

@guest_bp.route("/invoice/<int:booking_id>")
@login_required
@guest_required
def invoice(booking_id):
    booking = Booking.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    inv = Invoice.query.filter_by(booking_id=booking_id).first()
    food_orders = FoodOrder.query.filter_by(booking_id=booking_id).all()
    service_reqs = ServiceRequest.query.filter_by(booking_id=booking_id).all()
    return render_template("pages/guest/invoice.html", booking=booking, invoice=inv,
        food_orders=food_orders, service_reqs=service_reqs)

@guest_bp.route("/api/order-status")
@login_required
@guest_required
def order_status():
    orders = FoodOrder.query.filter_by(user_id=current_user.id).order_by(FoodOrder.created_at.desc()).limit(5).all()
    return jsonify([{"id": o.id, "status": o.status, "total": o.total_amount,
        "created": o.created_at.strftime("%H:%M")} for o in orders])

@guest_bp.route("/api/service-status")
@login_required
@guest_required
def service_status_api():
    reqs = ServiceRequest.query.filter_by(user_id=current_user.id).order_by(ServiceRequest.created_at.desc()).limit(5).all()
    return jsonify([{"id": r.id, "type": r.service_type, "status": r.status,
        "created": r.created_at.strftime("%d %b %H:%M")} for r in reqs])
