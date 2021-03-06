from flask import Flask, render_template, request, redirect, session, flash
import database as db
import authentication
import logging
import ordermanagement as om
from bson.json_util import loads, dumps
from flask import make_response

app = Flask(__name__)

app.secret_key = 'bs@g@d@c0ff33!'

logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.INFO)

@app.route('/')
def index():
    return render_template('index.html', page="Index")

@app.route('/login', methods=['GET', 'POST'])
def login():
    session.pop("user",None)
    session.pop("cart",None)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop("user",None)
    session.pop("cart",None)
    return redirect('/')


@app.route('/auth', methods = ['GET', 'POST'])
def auth():
    username = request.form.get('username')
    password = request.form.get('password')

    is_successful, user = authentication.login(username, password)
    app.logger.info('%s', is_successful)
    if(is_successful):
        session["user"] = user
        return redirect('/')
    else:
        flash("Invalid username or password. Please try again.")
        return redirect('/login')

@app.route('/products')
def products():
    product_list = db.get_products()
    return render_template('products.html', page="Products", product_list=product_list)

@app.route('/api/products/<int:code>',methods=['GET'])
def api_get_products():
    resp = make_response(dumps(db.get_products()))
    resp.mimetype = 'application/json'
    return resp

@app.route('/productdetails')
def productdetails():
    code = request.args.get('code', '')
    product = db.get_product(int(code))

    return render_template('productdetails.html', code=code, product=product)

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/addtocart')
def addtocart():
    code = request.args.get('code', '')
    product = db.get_product(int(code))
    item=dict()
    # A click to add a product translates to a 
    # quantity of 1 for now

    item["code"] = code
    item["qty"] = 1
    item["name"] = product["name"]
    item["subtotal"] = int(product["price"])*int(item["qty"])

    if(session.get("cart") is None):
        session["cart"]={}

    cart = session["cart"]
    cart[code]=item
    session["cart"]=cart
    return redirect('/cart')

@app.route('/updatecart', methods=['POST'])
def updatecart():
    code = request.form.getlist("code")
    qty = request.form.getlist("qty")

    cart = session["cart"]

    for item in range(len(code)):
        product = db.get_product(int(code[item]))
        cart[code[item]]["qty"] = int(qty[item])
        cart[code[item]]["subtotal"] = int(qty[item]) * int(product["price"])

    session["cart"] = cart
    
    return redirect('/cart')

@app.route('/deleteitem')
def deleteitem():
    code = request.args.get('code', '')
    cart = session["cart"]
    cart.pop(code, None)
    session["cart"]=cart

    return redirect('/cart')

@app.route('/deleteall')
def deleteall():
    session.pop('cart', None)
    return redirect('/cart')

@app.route('/branches')
def branches():
    branch_list = db.get_branches()
    return render_template('branches.html', page="Branches", branch_list=branch_list)

@app.route('/branchdetails')
def branchdetails():
    code = request.args.get('code', '')
    branch = db.get_branch(code)

    return render_template('branchdetails.html', code=code, branch=branch)

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html', page="About Us")

@app.route('/checkout')
def checkout():
    # clear cart in session memory upon checkout
    om.create_order_from_cart()
    session.pop("cart",None)
    return redirect('/ordercomplete')

@app.route('/ordercomplete')
def ordercomplete():
    return render_template('ordercomplete.html')

@app.route('/orderhistory')
def orderhistory():
    orders = db.get_orders()
    order_list = []
    for item in orders:
        for order in item['details']:
            order_list.append(order)


    return render_template('orderhistory.html', order_list=order_list)

@app.route('/password')
def changepassword():
    return render_template('changepassword.html')

@app.route('/password-auth', methods = ['POST'])
def passwordauth():
    old = request.form.get('old-password')
    new = request.form.get('new-password')
    confirm = request.form.get('confirm-password')

    is_successful, is_correct_old, is_same_new = authentication.change_password_verification(old, new, confirm)
    app.logger.info('%s', is_successful)
    if(is_successful):
        db.change_pass(session['user']['username'], new)
        return redirect('/login')
    else:
        if not is_correct_old:
            flash("Old password is not correct.")
        if not is_same_new:
            flash("Passwords do not match.")

        return redirect('/password')