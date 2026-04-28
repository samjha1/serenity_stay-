from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Room, Booking, FoodOrder, ServiceRequest, User, Invoice, ActivityBooking, MenuItem
from datetime import datetime
import json

staff_bp = Blueprint("staff", __name__)
STAFF_ROLES = {"admin", "frontdesk", "kitchen", "housekeeping"}

def staff_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in STAFF_ROLES:
            flash("Staff access required.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in STAFF_ROLES:
                flash("Access denied.", "error")
                return redirect(url_for("auth.login"))
            if current_user.role not in roles:
                flash("You do not have permission for this area.", "error")
                return redirect(url_for("staff.dashboard"))
            return f(*args, **kwargs)
        return decorated
    return decorator

@staff_bp.route("/dashboard")
@login_required
@staff_required
def dashboard():
    role = current_user.role
    stats = {}
    if role in ("admin", "frontdesk"):
        stats["total_rooms"] = Room.query.count()
        stats["available_rooms"] = Room.query.filter_by(status="available").count()
        stats["occupied_rooms"] = Room.query.filter_by(status="occupied").count()
        stats["total_bookings"] = Booking.query.count()
        stats["pending_bookings"] = Booking.query.filter_by(status="pending").count()
        stats["confirmed_bookings"] = Booking.query.filter_by(status="confirmed").count()
        stats["checked_in"] = Booking.query.filter_by(status="checked_in").count()
        stats["recent_bookings"] = Booking.query.order_by(Booking.created_at.desc()).limit(8).all()
        stats["pending_activities"] = ActivityBooking.query.filter_by(status="pending").count()
        stats["activities"] = ActivityBooking.query.order_by(ActivityBooking.created_at.desc()).limit(8).all()
    if role in ("admin", "kitchen"):
        stats["pending_orders"] = FoodOrder.query.filter_by(status="pending").count()
        stats["preparing_orders"] = FoodOrder.query.filter_by(status="preparing").count()
        stats["food_orders"] = FoodOrder.query.order_by(FoodOrder.created_at.desc()).limit(8).all()
    if role in ("admin", "housekeeping"):
        stats["pending_requests"] = ServiceRequest.query.filter_by(status="pending").count()
        stats["inprogress_requests"] = ServiceRequest.query.filter_by(status="in_progress").count()
        stats["service_requests"] = ServiceRequest.query.order_by(ServiceRequest.created_at.desc()).limit(8).all()
    if role == "admin":
        from sqlalchemy import func
        total_revenue = db.session.query(func.sum(Invoice.total_amount)).filter_by(status="paid").scalar() or 0
        stats["total_revenue"] = round(float(total_revenue), 2)
        stats["total_guests"] = User.query.count()
        stats["cleaning_rooms"] = Room.query.filter_by(status="cleaning").count()
        stats["maintenance_rooms"] = Room.query.filter_by(status="maintenance").count()
    return render_template("pages/staff/dashboard.html", stats=stats, role=role)

@staff_bp.route("/bookings")
@login_required
@role_required("admin", "frontdesk")
def bookings():
    status_filter = request.args.get("status", "")
    q = Booking.query
    if status_filter:
        q = q.filter_by(status=status_filter)
    bookings = q.order_by(Booking.created_at.desc()).all()
    return render_template("pages/staff/bookings.html", bookings=bookings, status_filter=status_filter, role=current_user.role)

@staff_bp.route("/bookings/<int:booking_id>/update", methods=["POST"])
@login_required
@role_required("admin", "frontdesk")
def update_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    new_status = request.form.get("status")
    if new_status:
        booking.status = new_status
        if new_status == "checked_in":
            booking.room.status = "occupied"
        elif new_status == "checked_out":
            booking.room.status = "cleaning"
            inv = Invoice.query.filter_by(booking_id=booking.id).first()
            if inv:
                inv.status = "paid"
                inv.paid_at = datetime.utcnow()
        elif new_status == "cancelled":
            booking.room.status = "available"
        db.session.commit()
        flash(f"Booking #{booking_id} updated to {new_status}.", "success")
    return redirect(url_for("staff.bookings"))

@staff_bp.route("/rooms")
@login_required
@role_required("admin", "frontdesk")
def rooms():
    rooms = Room.query.order_by(Room.room_number).all()
    return render_template("pages/staff/rooms.html", rooms=rooms, role=current_user.role)


@staff_bp.route("/rooms/add", methods=["POST"])
@login_required
@role_required("admin")
def add_room():
    room_number = request.form.get("room_number", "").strip()
    room_type = request.form.get("room_type", "").strip().lower()
    floor_raw = request.form.get("floor", "1").strip()
    capacity_raw = request.form.get("capacity", "2").strip()
    price_raw = request.form.get("price_per_night", "0").strip()
    description = request.form.get("description", "").strip()
    amenities = request.form.get("amenities", "").strip()
    image_path = request.form.get("image_path", "images/room1.jpg").strip()
    valid_types = {"standard", "deluxe", "suite", "villa"}

    if not room_number or room_type not in valid_types:
        flash("Room number and valid room type are required.", "error")
        return redirect(url_for("staff.rooms"))
    if Room.query.filter_by(room_number=room_number).first():
        flash("Room number already exists.", "error")
        return redirect(url_for("staff.rooms"))
    try:
        floor = int(floor_raw)
        capacity = int(capacity_raw)
        price_per_night = float(price_raw)
    except ValueError:
        flash("Floor, capacity, and price must be valid numbers.", "error")
        return redirect(url_for("staff.rooms"))
    if floor < 1 or capacity < 1 or price_per_night <= 0:
        flash("Floor/capacity must be positive and price must be greater than 0.", "error")
        return redirect(url_for("staff.rooms"))

    room = Room(
        room_number=room_number,
        room_type=room_type,
        floor=floor,
        capacity=capacity,
        price_per_night=price_per_night,
        status="available",
        description=description,
        amenities=amenities,
        image_path=image_path,
    )
    db.session.add(room)
    db.session.commit()
    flash(f"Room {room_number} added successfully.", "success")
    return redirect(url_for("staff.rooms"))

@staff_bp.route("/rooms/<int:room_id>/update", methods=["POST"])
@login_required
@role_required("admin", "frontdesk")
def update_room(room_id):
    room = Room.query.get_or_404(room_id)
    new_status = request.form.get("status")
    if new_status:
        room.status = new_status
        db.session.commit()
        flash(f"Room {room.room_number} status updated.", "success")
    return redirect(url_for("staff.rooms"))


@staff_bp.route("/rooms/<int:room_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    active_booking = Booking.query.filter(
        Booking.room_id == room.id,
        Booking.status.in_(["pending", "confirmed", "checked_in"]),
    ).first()
    if active_booking:
        flash("Cannot delete room with active bookings.", "error")
        return redirect(url_for("staff.rooms"))
    db.session.delete(room)
    db.session.commit()
    flash(f"Room {room.room_number} removed.", "success")
    return redirect(url_for("staff.rooms"))


@staff_bp.route("/activities")
@login_required
@role_required("admin", "frontdesk")
def activities():
    status_filter = request.args.get("status", "")
    q = ActivityBooking.query
    if status_filter:
        q = q.filter_by(status=status_filter)
    activities = q.order_by(ActivityBooking.created_at.desc()).all()
    return render_template("pages/staff/activities.html", activities=activities, status_filter=status_filter, role=current_user.role)


@staff_bp.route("/activities/<int:activity_id>/update", methods=["POST"])
@login_required
@role_required("admin", "frontdesk")
def update_activity(activity_id):
    activity = ActivityBooking.query.get_or_404(activity_id)
    new_status = request.form.get("status")
    if new_status in {"pending", "confirmed", "completed", "cancelled"}:
        activity.status = new_status
        if not activity.assigned_to:
            activity.assigned_to = current_user.id
        activity.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f"Activity booking #{activity.id} updated.", "success")
    return redirect(url_for("staff.activities"))

@staff_bp.route("/food-orders")
@login_required
@role_required("admin", "kitchen")
def food_orders():
    status_filter = request.args.get("status", "")
    q = FoodOrder.query
    if status_filter:
        q = q.filter_by(status=status_filter)
    orders = q.order_by(FoodOrder.created_at.desc()).all()
    orders_data = []
    for o in orders:
        try:
            items = json.loads(o.items_json)
        except:
            items = []
        orders_data.append({"order": o, "items": items})
    menu_items = MenuItem.query.order_by(MenuItem.category.asc(), MenuItem.name.asc()).all()
    return render_template(
        "pages/staff/food_orders.html",
        orders_data=orders_data,
        status_filter=status_filter,
        menu_items=menu_items,
        role=current_user.role,
    )


@staff_bp.route("/menu-items/add", methods=["POST"])
@login_required
@role_required("admin", "kitchen")
def add_menu_item():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "").strip().lower()
    price_raw = request.form.get("price", "").strip()
    is_veg = request.form.get("is_veg") == "on"
    valid_categories = {"starters", "main_course", "desserts", "beverages", "buffet", "special_event_menu"}

    if not name or category not in valid_categories:
        flash("Dish name and valid category are required.", "error")
        return redirect(url_for("staff.food_orders"))
    try:
        price = float(price_raw)
    except ValueError:
        flash("Price must be a valid number.", "error")
        return redirect(url_for("staff.food_orders"))
    if price <= 0:
        flash("Price must be greater than zero.", "error")
        return redirect(url_for("staff.food_orders"))

    item = MenuItem(
        name=name,
        description=description,
        category=category,
        price=price,
        is_available=True,
        is_veg=is_veg,
    )
    db.session.add(item)
    db.session.commit()
    flash(f"Menu item '{name}' added.", "success")
    return redirect(url_for("staff.food_orders"))


@staff_bp.route("/menu-items/<int:item_id>/toggle", methods=["POST"])
@login_required
@role_required("admin", "kitchen")
def toggle_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.is_available = not item.is_available
    db.session.commit()
    flash(f"Menu item '{item.name}' availability updated.", "success")
    return redirect(url_for("staff.food_orders"))

@staff_bp.route("/menu-items/<int:item_id>/delete", methods=["POST"])
@login_required
@role_required("admin", "kitchen")
def delete_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item_name = item.name
    db.session.delete(item)
    db.session.commit()
    flash(f"Menu item '{item_name}' deleted.", "success")
    return redirect(url_for("staff.food_orders"))

@staff_bp.route("/food-orders/<int:order_id>/update", methods=["POST"])
@login_required
@role_required("admin", "kitchen")
def update_food_order(order_id):
    order = FoodOrder.query.get_or_404(order_id)
    new_status = request.form.get("status")
    if new_status:
        order.status = new_status
        db.session.commit()
        flash(f"Order #{order_id} updated to {new_status}.", "success")
    return redirect(url_for("staff.food_orders"))

@staff_bp.route("/service-requests")
@login_required
@role_required("admin", "housekeeping")
def service_requests():
    status_filter = request.args.get("status", "")
    service_filter = request.args.get("type", "")
    q = ServiceRequest.query
    if status_filter:
        q = q.filter_by(status=status_filter)
    if service_filter:
        q = q.filter_by(service_type=service_filter)
    reqs = q.order_by(ServiceRequest.created_at.desc()).all()
    return render_template("pages/staff/service_requests.html", requests=reqs, status_filter=status_filter, service_filter=service_filter, role=current_user.role)

@staff_bp.route("/service-requests/<int:req_id>/update", methods=["POST"])
@login_required
@role_required("admin", "housekeeping")
def update_service_request(req_id):
    sr = ServiceRequest.query.get_or_404(req_id)
    new_status = request.form.get("status")
    if new_status:
        sr.status = new_status
        sr.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f"Service request #{req_id} updated.", "success")
    return redirect(url_for("staff.service_requests"))

@staff_bp.route("/api/stats")
@login_required
@staff_required
def api_stats():
    return jsonify({
        "available": Room.query.filter_by(status="available").count(),
        "occupied": Room.query.filter_by(status="occupied").count(),
        "cleaning": Room.query.filter_by(status="cleaning").count(),
        "maintenance": Room.query.filter_by(status="maintenance").count(),
        "pending_orders": FoodOrder.query.filter_by(status="pending").count(),
        "pending_requests": ServiceRequest.query.filter_by(status="pending").count(),
    })
