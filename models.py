from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(20), default="guest")
    bookings = db.relationship("Booking", backref="guest", lazy=True)
    food_orders = db.relationship("FoodOrder", backref="guest", lazy=True)
    service_requests = db.relationship(
        "ServiceRequest",
        foreign_keys="ServiceRequest.user_id",
        backref="guest",
        lazy=True,
    )
    assigned_requests = db.relationship(
        "ServiceRequest",
        foreign_keys="ServiceRequest.assigned_to",
        backref="assigned_staff",
        lazy=True,
    )
    activity_bookings = db.relationship(
        "ActivityBooking",
        foreign_keys="ActivityBooking.user_id",
        backref="guest",
        lazy=True,
    )
    assigned_activities = db.relationship(
        "ActivityBooking",
        foreign_keys="ActivityBooking.assigned_to",
        backref="assigned_staff",
        lazy=True,
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_staff(self):
        return self.role in {"admin", "frontdesk", "kitchen", "housekeeping"}

    @property
    def is_guest(self):
        return self.role == "guest"

class Room(db.Model):
    __tablename__ = "rooms"
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    floor = db.Column(db.Integer, default=1)
    capacity = db.Column(db.Integer, default=2)
    price_per_night = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="available")
    image_path = db.Column(db.String(255), default="images/room1.jpg")
    description = db.Column(db.Text)
    amenities = db.Column(db.Text)
    bookings = db.relationship("Booking", backref="room", lazy=True)

class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    guests = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default="pending")
    special_requests = db.Column(db.Text)
    total_amount = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MenuItem(db.Model):
    __tablename__ = "menu_items"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    is_veg = db.Column(db.Boolean, default=False)

class FoodOrder(db.Model):
    __tablename__ = "food_orders"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=True)
    items_json = db.Column(db.Text, nullable=False)
    total_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default="pending")
    special_instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ServiceRequest(db.Model):
    __tablename__ = "service_requests"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=True)
    service_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default="normal")
    status = db.Column(db.String(20), default="pending")
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Invoice(db.Model):
    __tablename__ = "invoices"
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    room_charges = db.Column(db.Float, default=0.0)
    food_charges = db.Column(db.Float, default=0.0)
    service_charges = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default="unpaid")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)
    booking = db.relationship("Booking", backref="invoice", uselist=False)
    guest = db.relationship("User", backref="invoices")


class ActivityBooking(db.Model):
    __tablename__ = "activity_bookings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    activity_type = db.Column(db.String(80), nullable=False)
    preferred_date = db.Column(db.Date, nullable=False)
    preferred_time = db.Column(db.String(20), nullable=False)
    guests_count = db.Column(db.Integer, default=1)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
