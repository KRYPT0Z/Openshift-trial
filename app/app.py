import re
from datetime import datetime

from flask import Flask, render_template, request, session, redirect, url_for, jsonify, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, Product, User, Order, OrderItem

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shop.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "change-this-later"

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def get_basket_count():
    basket = session.get("basket", {})
    return sum(basket.values())


def get_basket_items_and_total():
    basket = session.get("basket", {})
    items = []
    total = 0

    for product_id, quantity in basket.items():
        product = Product.query.get(int(product_id))
        if product is not None:
            item_total = product.price * quantity
            total += item_total

            items.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "item_total": item_total
                }
            )

    return items, total


def validate_expiry_date(expiry_date):
    expiry_date = expiry_date.strip()

    if not re.fullmatch(r"\d{2}/\d{2}", expiry_date):
        return False, "Expiry date must be in MM/YY format."

    month = int(expiry_date[:2])
    year = int(expiry_date[3:5])

    if month < 1 or month > 12:
        return False, "Expiry month must be between 01 and 12."

    current_date = datetime.now()
    current_year = current_date.year % 100
    current_month = current_date.month

    if year < current_year or (year == current_year and month < current_month):
        return False, "Card expiry date cannot be in the past."

    return True, ""


@app.route("/")
def home():
    sort_option = request.args.get("sort", "default")
    added_product_id = request.args.get("added")
    search_query = request.args.get("search", "").strip()

    products = Product.query.all()

    if search_query:
        search_text = search_query.lower()
        products = [
            product for product in products
            if search_text in product.name.lower()
        ]

    if sort_option == "name":
        products = sorted(products, key=lambda product: product.name.lower())
    elif sort_option == "price":
        products = sorted(products, key=lambda product: product.price)
    elif sort_option == "impact":
        products = sorted(products, key=lambda product: product.impact)

    added_product = None
    if added_product_id:
        added_product = Product.query.get(int(added_product_id))

    return render_template(
        "index.html",
        products=products,
        current_sort=sort_option,
        basket_count=get_basket_count(),
        added_product=added_product,
        search_query=search_query
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    errors = {}
    form_data = {
        "full_name": "",
        "username": "",
        "email": ""
    }

    if request.method == "POST":
        form_data["full_name"] = request.form.get("full_name", "").strip()
        form_data["username"] = request.form.get("username", "").strip()
        form_data["email"] = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not form_data["full_name"]:
            errors["full_name"] = "Please enter your full name."

        if not form_data["username"]:
            errors["username"] = "Please enter a username."
        elif len(form_data["username"]) < 3:
            errors["username"] = "Username must be at least 3 characters long."
        elif User.query.filter_by(username=form_data["username"]).first():
            errors["username"] = "That username is already taken."

        if not form_data["email"]:
            errors["email"] = "Please enter your email address."
        elif "@" not in form_data["email"] or "." not in form_data["email"]:
            errors["email"] = "Please enter a valid email address."
        elif User.query.filter_by(email=form_data["email"]).first():
            errors["email"] = "That email address is already in use."

        if not password:
            errors["password"] = "Please enter a password."
        elif len(password) < 6:
            errors["password"] = "Password must be at least 6 characters long."

        if not confirm_password:
            errors["confirm_password"] = "Please confirm your password."
        elif password != confirm_password:
            errors["confirm_password"] = "Passwords do not match."

        if not errors:
            user = User(
                full_name=form_data["full_name"],
                username=form_data["username"],
                email=form_data["email"],
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()

            return redirect(url_for("login", registered=1))

    return render_template(
        "register.html",
        errors=errors,
        form_data=form_data,
        basket_count=get_basket_count()
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    errors = {}
    form_data = {
        "username_or_email": ""
    }

    registered = request.args.get("registered")

    if request.method == "POST":
        form_data["username_or_email"] = request.form.get("username_or_email", "").strip()
        password = request.form.get("password", "")

        if not form_data["username_or_email"]:
            errors["username_or_email"] = "Please enter your username or email address."

        if not password:
            errors["password"] = "Please enter your password."

        if not errors:
            user = User.query.filter(
                db.or_(
                    User.username == form_data["username_or_email"],
                    User.email == form_data["username_or_email"]
                )
            ).first()

            if user is None or not check_password_hash(user.password_hash, password):
                errors["general"] = "Invalid login details."
            else:
                login_user(user)
                next_page = request.args.get("next")
                if next_page:
                    return redirect(next_page)
                return redirect(url_for("home"))

    return render_template(
        "login.html",
        errors=errors,
        form_data=form_data,
        registered=registered,
        basket_count=get_basket_count()
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/product/<int:product_id>")
def product_page(product_id):
    product = Product.query.get_or_404(product_id)

    return render_template(
        "product.html",
        product=product,
        basket_count=get_basket_count()
    )


@app.route("/product/<int:product_id>/hover_details")
def product_hover_details(product_id):
    product = Product.query.get_or_404(product_id)

    return jsonify(
        {
            "name": product.name,
            "description": product.description,
            "price": f"£{product.price:.2f}",
            "impact": f"{product.impact:.1f} kg CO2e"
        }
    )


@app.route("/add_to_basket/<int:product_id>")
def add_to_basket(product_id):
    product = Product.query.get_or_404(product_id)

    basket = session.get("basket", {})
    product_id_str = str(product.id)

    if product_id_str in basket:
        basket[product_id_str] += 1
    else:
        basket[product_id_str] = 1

    session["basket"] = basket

    source = request.args.get("source", "home")

    if source == "product":
        return redirect(url_for("product_page", product_id=product.id, added=1))

    current_sort = request.args.get("sort", "default")
    current_search = request.args.get("search", "")

    return redirect(
        url_for(
            "home",
            added=product.id,
            sort=current_sort,
            search=current_search
        )
    )


@app.route("/basket")
def basket():
    items, total = get_basket_items_and_total()

    return render_template(
        "basket.html",
        items=items,
        total=total,
        basket_count=get_basket_count()
    )


@app.route("/increase_item/<int:product_id>")
def increase_item(product_id):
    basket = session.get("basket", {})
    product_id_str = str(product_id)

    if product_id_str in basket:
        basket[product_id_str] += 1
    else:
        basket[product_id_str] = 1

    session["basket"] = basket

    return redirect(url_for("basket"))


@app.route("/decrease_item/<int:product_id>")
def decrease_item(product_id):
    basket = session.get("basket", {})
    product_id_str = str(product_id)

    if product_id_str in basket:
        basket[product_id_str] -= 1

        if basket[product_id_str] <= 0:
            del basket[product_id_str]

    session["basket"] = basket

    return redirect(url_for("basket"))


@app.route("/remove_item/<int:product_id>")
def remove_item(product_id):
    basket = session.get("basket", {})
    product_id_str = str(product_id)

    if product_id_str in basket:
        del basket[product_id_str]

    session["basket"] = basket

    return redirect(url_for("basket"))


@app.route("/clear_basket")
def clear_basket():
    session["basket"] = {}
    return redirect(url_for("basket"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, total = get_basket_items_and_total()

    if not items:
        return redirect(url_for("basket"))

    form_data = {
        "full_name": current_user.full_name if current_user.is_authenticated else "",
        "email": current_user.email if current_user.is_authenticated else "",
        "address": "",
        "card_number": "",
        "expiry_date": "",
        "cvv": ""
    }
    errors = {}

    if request.method == "POST":
        form_data["full_name"] = request.form.get("full_name", "").strip()
        form_data["email"] = request.form.get("email", "").strip()
        form_data["address"] = request.form.get("address", "").strip()
        form_data["card_number"] = request.form.get("card_number", "").strip()
        form_data["expiry_date"] = request.form.get("expiry_date", "").strip()
        form_data["cvv"] = request.form.get("cvv", "").strip()

        if not form_data["full_name"]:
            errors["full_name"] = "Please enter your full name."

        if not form_data["email"]:
            errors["email"] = "Please enter your email address."
        elif "@" not in form_data["email"] or "." not in form_data["email"]:
            errors["email"] = "Please enter a valid email address."

        if not form_data["address"]:
            errors["address"] = "Please enter your billing address."

        if not form_data["card_number"]:
            errors["card_number"] = "Please enter your card number."
        else:
            cleaned_card_number = re.sub(r"[\s-]", "", form_data["card_number"])
            if not cleaned_card_number.isdigit() or len(cleaned_card_number) != 16:
                errors["card_number"] = "Card number must contain exactly 16 digits. Spaces and dashes are allowed."

        if not form_data["expiry_date"]:
            errors["expiry_date"] = "Please enter the expiry date."
        else:
            is_valid_expiry, expiry_error = validate_expiry_date(form_data["expiry_date"])
            if not is_valid_expiry:
                errors["expiry_date"] = expiry_error

        if not form_data["cvv"]:
            errors["cvv"] = "Please enter the CVV."
        elif not form_data["cvv"].isdigit() or len(form_data["cvv"]) not in (3, 4):
            errors["cvv"] = "CVV must be 3 or 4 digits."

        if not errors:
            new_order = Order(
                customer_name=form_data["full_name"],
                customer_email=form_data["email"],
                billing_address=form_data["address"],
                total_amount=total,
                created_at=datetime.utcnow(),
                user_id=current_user.id if current_user.is_authenticated else None
            )
            db.session.add(new_order)
            db.session.flush()

            for item in items:
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_name=item["product"].name,
                    quantity=item["quantity"],
                    unit_price=item["product"].price,
                    line_total=item["item_total"]
                )
                db.session.add(order_item)

            db.session.commit()

            session["last_order_id"] = new_order.id
            session["basket"] = {}

            return redirect(url_for("success"))

    return render_template(
        "checkout.html",
        items=items,
        total=total,
        errors=errors,
        form_data=form_data,
        basket_count=get_basket_count()
    )


@app.route("/success")
def success():
    order_id = session.pop("last_order_id", None)

    if order_id is None:
        return redirect(url_for("home"))

    order = Order.query.get(order_id)
    if order is None:
        return redirect(url_for("home"))

    return render_template(
        "success.html",
        order=order,
        basket_count=get_basket_count()
    )


@app.route("/invoice/<int:order_id>")
def invoice(order_id):
    order = Order.query.get_or_404(order_id)

    if order.user_id is not None:
        if not current_user.is_authenticated or current_user.id != order.user_id:
            abort(403)

    return render_template(
        "invoice.html",
        order=order,
        basket_count=get_basket_count()
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)