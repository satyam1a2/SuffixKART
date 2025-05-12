from flask import Flask, render_template, request, redirect, url_for, flash, session
import time
from pymongo import MongoClient
import os
import subprocess
import json
from bson import ObjectId, json_util
from datetime import datetime
import hashlib
import secrets
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Template filters
@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    """Convert a Unix timestamp or datetime to a formatted date string."""
    if isinstance(timestamp, datetime):
        # If it's already a datetime object, just format it
        return timestamp.strftime('%B %d, %Y at %H:%M')
    # Otherwise, convert the timestamp to a datetime
    return datetime.fromtimestamp(timestamp).strftime('%B %d, %Y at %H:%M')

# MongoDB connection setup
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['suffixKART_db']
    seller_profiles = db['seller_profiles']
    items_collection = db['items']
    orders_collection = db['orders']
    # Add user_credentials collection for authentication
    user_credentials = db['user_credentials']
    # Add cart collection for shopping cart
    cart_collection = db['cart']
    # Add buyer_profiles collection
    buyer_profiles = db['buyer_profiles']
    print("MongoDB connection successful")
except Exception as e:
    print(f"MongoDB connection error: {e}")

# Helper function to hash passwords
def hash_password(password, salt=None):
    """Hash a password with a salt for secure storage."""
    if salt is None:
        salt = secrets.token_hex(16)
    # Combine password and salt and hash
    pw_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return pw_hash, salt

# Authentication middleware
@app.before_request
def require_login():
    """Check if user is logged in for protected routes."""
    # List of routes that require authentication
    seller_routes = [
        'seller_dashboard', 
        'add_item', 
        'edit_item',
        'delete_item'
    ]
    
    buyer_routes = [
        'buyer_dashboard',
        'checkout',
        'view_orders'
    ]
    
    # Check if current route requires authentication
    if request.endpoint in seller_routes:
        # Allow access to seller_dashboard with seller_id if not logged in (for viewing only)
        if request.endpoint == 'seller_dashboard' and request.method == 'GET':
            return None
            
        # Check if user is logged in
        if 'user_id' not in session:
            flash('Please log in to access this page')
            return redirect(url_for('login'))
        
        # Check if user is a seller
        if not session.get('is_seller', False) and not session.get('is_admin', False):
            flash('You do not have permission to access this page')
            return redirect(url_for('index'))
        
        # For routes that use seller_id, check if it matches the logged-in user
        if 'seller_id' in request.view_args:
            seller_id = request.view_args['seller_id']
            if str(session['user_id']) != seller_id and not session.get('is_admin', False):
                flash('You do not have permission to access this page')
                return redirect(url_for('seller_dashboard', seller_id=session['user_id']))
    
    elif request.endpoint in buyer_routes:
        # Check if user is logged in
        if 'user_id' not in session:
            flash('Please log in to access this page')
            return redirect(url_for('login'))

# Determine which backend executable to use
def get_backend_executable():
    """Check if new_backend.exe exists, otherwise use backend.exe."""
    if os.path.exists("new_backend.exe"):
        return "new_backend.exe"
    return "backend.exe"

# Function to execute C++ backend with direct data access
def execute_cpp_algorithm(algorithm_type, data):
    """
    Execute C++ algorithm with data passed directly as JSON
    
    algorithm_type: "bloom", "bktree", or "suffixtree"
    data: Dictionary containing data to be processed
    """
    # Convert data to JSON string
    json_data = json.dumps(data, default=json_util.default)
    
    # Get the appropriate backend executable
    backend_exe = get_backend_executable()
    
    # Execute the appropriate C++ executable with the data as argument
    try:
        # Call the appropriate algorithm
        if algorithm_type == "bloom":
            # Check if item exists using bloom filter
            result = subprocess.run([f'./{backend_exe}', 'bloom', json_data], 
                                   capture_output=True, text=True, check=True)
        elif algorithm_type == "bktree":
            # Search using BK-Tree for fuzzy matching
            result = subprocess.run([f'./{backend_exe}', 'bktree', json_data], 
                                   capture_output=True, text=True, check=True)
        elif algorithm_type == "suffixtree":
            # Use suffix tree for order history
            result = subprocess.run([f'./{backend_exe}', 'suffixtree', json_data], 
                                   capture_output=True, text=True, check=True)
        else:
            return {"error": "Invalid algorithm type"}
        
        # Parse the output
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing C++ algorithm: {e}")
        return {"error": str(e), "output": e.stdout, "stderr": e.stderr}
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON output: {e}")
        return {"error": "Invalid JSON output from C++ algorithm"}

@app.route('/')
def index():
    # Get some sample items from the database to display
    sample_items = list(items_collection.find().limit(5))
    return render_template('index.html', items=sample_items, seller_profiles=seller_profiles)

@app.route('/register', methods=['GET', 'POST'])
def register_seller():
    if request.method == 'POST':
        # Get seller details from form
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form.get('confirm_password', '')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register_seller'))
        
        # Check if email already exists
        if user_credentials.find_one({'email': email}):
            flash('Email already registered')
            return redirect(url_for('register_seller'))
        
        # Hash the password
        password_hash, salt = hash_password(password)
        
        # Create seller profile
        seller_data = {
            'name': request.form['name'],
            'email': email,
            'phone': request.form['phone'],
            'address': request.form['address'],
            'description': request.form['description'],
            'date_registered': datetime.now()
        }
        
        # Insert seller profile into MongoDB
        seller_id = seller_profiles.insert_one(seller_data).inserted_id
        
        # Create user credentials
        user_data = {
            'email': email,
            'password_hash': password_hash,
            'salt': salt,
            'seller_id': seller_id,
            'user_type': 'seller',
            'is_admin': False
        }
        
        # Insert user credentials into MongoDB
        user_credentials.insert_one(user_data)
        
        flash('Seller profile created successfully! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html', user_type='seller')

@app.route('/register/buyer', methods=['GET', 'POST'])
def register_buyer():
    if request.method == 'POST':
        # Get buyer details from form
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form.get('confirm_password', '')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register_buyer'))
        
        # Check if email already exists
        if user_credentials.find_one({'email': email}):
            flash('Email already registered')
            return redirect(url_for('register_buyer'))
        
        # Hash the password
        password_hash, salt = hash_password(password)
        
        # Create buyer profile
        buyer_data = {
            'name': request.form['name'],
            'email': email,
            'phone': request.form['phone'],
            'address': request.form['address'],
            'date_registered': datetime.now()
        }
        
        # Insert buyer profile into MongoDB
        buyer_id = buyer_profiles.insert_one(buyer_data).inserted_id
        
        # Create user credentials
        user_data = {
            'email': email,
            'password_hash': password_hash,
            'salt': salt,
            'buyer_id': buyer_id,
            'user_type': 'buyer',
            'is_admin': False
        }
        
        # Insert user credentials into MongoDB
        user_credentials.insert_one(user_data)
        
        flash('Buyer account created successfully! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html', user_type='buyer')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Find user by email
        user = user_credentials.find_one({'email': email})
        
        if user:
            # Verify password
            stored_hash = user['password_hash']
            salt = user['salt']
            new_hash, _ = hash_password(password, salt)
            
            if new_hash == stored_hash:
                # Set session variables
                session['email'] = email
                
                # Check user type and set appropriate session variables
                if user.get('user_type') == 'seller' or 'seller_id' in user:
                    session['user_id'] = str(user.get('seller_id'))
                    session['is_seller'] = True
                    session['is_admin'] = user.get('is_admin', False)
                    flash('Login successful!')
                    return redirect(url_for('seller_dashboard', seller_id=user['seller_id']))
                elif user.get('user_type') == 'buyer' or 'buyer_id' in user:
                    session['user_id'] = str(user.get('buyer_id'))
                    session['is_buyer'] = True
                    flash('Login successful!')
                    return redirect(url_for('buyer_dashboard'))
                else:
                    # Fallback to admin or other role
                    session['user_id'] = str(user.get('_id'))
                    session['is_admin'] = user.get('is_admin', False)
                    flash('Login successful!')
                    return redirect(url_for('index'))
        
        flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear session
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.route('/seller/<seller_id>')
def seller_dashboard(seller_id):
    # Get seller profile from MongoDB
    seller = seller_profiles.find_one({'_id': ObjectId(seller_id)})
    
    if not seller:
        flash('Seller not found!')
        return redirect(url_for('index'))
    
    # Get items added by this seller
    seller_items = list(items_collection.find({'seller_id': ObjectId(seller_id)}))
    
    # Check if logged in and seller owns this dashboard
    is_owner = 'user_id' in session and str(session['user_id']) == str(seller_id)
    
    return render_template('seller_dashboard.html', 
                          seller=seller, 
                          items=seller_items, 
                          is_owner=is_owner)

@app.route('/add_item/<seller_id>', methods=['GET', 'POST'])
def add_item(seller_id):
    if request.method == 'POST':
        # Get item details from form
        item_name = request.form['name']
        
        # First, use the Bloom Filter to check if item exists (via C++ backend)
        # Get all existing items for bloom filter
        all_items = list(items_collection.find({}, {'name': 1}))
        item_names = [item['name'] for item in all_items]
        
        bloom_data = {
            'operation': 'check',
            'item_name': item_name,
            'existing_items': item_names
        }
        
        bloom_response = execute_cpp_algorithm('bloom', bloom_data)
        
        # Check if the item was successfully added (not a duplicate)
        if bloom_response.get('is_unique', False):
            # Item is unique according to Bloom Filter, now store in MongoDB
            item_data = {
                'name': item_name,
                'price': float(request.form['price']),
                'description': request.form['description'],
                'quantity': int(request.form['quantity']),
                'category': request.form['category'],
                'seller_id': ObjectId(seller_id),
                'date_added': datetime.now()
            }
            
            # Insert item into MongoDB
            item_id = items_collection.insert_one(item_data).inserted_id
            
            # Update bloom filter with new item
            update_bloom_data = {
                'operation': 'insert',
                'item_name': item_name
            }
            execute_cpp_algorithm('bloom', update_bloom_data)
            
            flash('Item added successfully!')
        else:
            # Item was probably already present
            flash('This item might already exist in the system.')
        
        return redirect(url_for('seller_dashboard', seller_id=seller_id))
    
    # Get categories for the dropdown
    categories = [
        'Fruits & Vegetables',
        'Dairy & Eggs',
        'Meat & Seafood',
        'Bakery',
        'Pantry Staples',
        'Frozen Foods',
        'Snacks',
        'Beverages',
        'Household Items',
        'Health & Personal Care',
        'Other'
    ]
    
    return render_template('add_item.html', seller_id=seller_id, categories=categories)

@app.route('/edit_item/<item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    # Get item details
    item = items_collection.find_one({'_id': ObjectId(item_id)})
    
    if not item:
        flash('Item not found!')
        return redirect(url_for('index'))
    
    # Check if user owns this item
    if str(session['user_id']) != str(item['seller_id']) and not session.get('is_admin', False):
        flash('You do not have permission to edit this item')
        return redirect(url_for('seller_dashboard', seller_id=session['user_id']))
    
    if request.method == 'POST':
        # Update item details
        updated_item = {
            'name': request.form['name'],
            'price': float(request.form['price']),
            'description': request.form['description'],
            'quantity': int(request.form['quantity']),
            'category': request.form['category'],
            'date_updated': datetime.now()
        }
        
        # Update item in MongoDB
        items_collection.update_one(
            {'_id': ObjectId(item_id)},
            {'$set': updated_item}
        )
        
        flash('Item updated successfully!')
        return redirect(url_for('seller_dashboard', seller_id=item['seller_id']))
    
    # Get categories for the dropdown
    categories = [
        'Fruits & Vegetables',
        'Dairy & Eggs',
        'Meat & Seafood',
        'Bakery',
        'Pantry Staples',
        'Frozen Foods',
        'Snacks',
        'Beverages',
        'Household Items',
        'Health & Personal Care',
        'Other'
    ]
    
    return render_template('edit_item.html', item=item, categories=categories)

@app.route('/delete_item/<item_id>')
def delete_item(item_id):
    # Get item details
    item = items_collection.find_one({'_id': ObjectId(item_id)})
    
    if not item:
        flash('Item not found!')
        return redirect(url_for('index'))
    
    # Check if user owns this item
    if str(session['user_id']) != str(item['seller_id']) and not session.get('is_admin', False):
        flash('You do not have permission to delete this item')
        return redirect(url_for('seller_dashboard', seller_id=session['user_id']))
    
    # Delete item from MongoDB
    items_collection.delete_one({'_id': ObjectId(item_id)})
    
    flash('Item deleted successfully!')
    return redirect(url_for('seller_dashboard', seller_id=item['seller_id']))

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/search_results')
def search_results():
    query = request.args.get('query', '')
    
    if not query:
        return render_template('search_results.html', items=[], query='')
    
    # Use BK-Tree for fuzzy matching via C++ backend
    # Get all existing items for BK-Tree
    all_items = list(items_collection.find({}, {'name': 1}))
    item_names = [item['name'] for item in all_items]
    
    bktree_data = {
        'query': query,
        'items': item_names,
        'tolerance': 2  # Tolerance for fuzzy matching
    }
    
    bktree_response = execute_cpp_algorithm('bktree', bktree_data)
    
    # Get matched items from MongoDB
    matched_items = []
    item_ids_seen = set()  # Track item IDs we've already added
    
    if 'matches' in bktree_response:
        # Look up the matched items in MongoDB using a single query for all matches
        match_names = bktree_response.get('matches', [])
        if match_names:
            db_items = list(items_collection.find({'name': {'$in': match_names}}))
            
            # Process each item and add it only once
            for item in db_items:
                item_id_str = str(item['_id'])
                if item_id_str not in item_ids_seen:
                    # Get seller details
                    seller = seller_profiles.find_one({'_id': item['seller_id']})
                    item['seller'] = seller
                    matched_items.append(item)
                    item_ids_seen.add(item_id_str)
    
    return render_template('search_results.html', items=matched_items, query=query)

@app.route('/buy_item/<item_id>')
def buy_item(item_id):
    # Get item details
    item = items_collection.find_one({'_id': ObjectId(item_id)})
    
    if not item:
        flash('Item not found!')
        return redirect(url_for('index'))
    
    # Add item to cart with quantity 1
    # Get the user's ID from session
    user_id = session.get('user_id', None)
    
    # If no user is logged in, use a temporary cart ID stored in the session
    if not user_id:
        # Create a temporary cart ID if it doesn't exist
        if 'temp_cart_id' not in session:
            session['temp_cart_id'] = str(uuid.uuid4())
        cart_id = session['temp_cart_id']
    else:
        cart_id = user_id
    
    # Check if there's enough stock
    if 1 > item['quantity']:
        flash('Not enough stock available!')
        return redirect(url_for('index'))
    
    # Check if item is already in cart
    existing_item = cart_collection.find_one({
        'cart_id': cart_id,
        'item_id': str(item_id)
    })
    
    if existing_item:
        # Update quantity
        new_quantity = existing_item['quantity'] + 1
        cart_collection.update_one(
            {'_id': existing_item['_id']},
            {'$set': {'quantity': new_quantity}}
        )
    else:
        # Add item to cart
        cart_item = {
            'cart_id': cart_id,
            'item_id': str(item_id),
            'quantity': 1,
            'date_added': datetime.now()
        }
        cart_collection.insert_one(cart_item)
    
    flash(f"{item['name']} added to your cart!")
    return redirect(url_for('view_cart'))

@app.route('/order_history/<item_name>')
def order_history(item_name):
    # Use Suffix Tree to find order history
    suffix_data = {
        'operation': 'search',
        'item': item_name
    }
    
    suffix_response = execute_cpp_algorithm('suffixtree', suffix_data)
    
    # Get orders from MongoDB based on the search results
    orders = []
    
    if 'buyers' in suffix_response:
        for buyer in suffix_response['buyers']:
            # Find orders by this buyer for this item
            item_ids = [item['_id'] for item in items_collection.find({'name': item_name})]
            buyer_orders = list(orders_collection.find({
                'buyer_name': buyer,
                'item_id': {'$in': item_ids}
            }))
            
            for order in buyer_orders:
                # Get item and seller details
                item = items_collection.find_one({'_id': order['item_id']})
                seller = seller_profiles.find_one({'_id': order['seller_id']})
                order['item'] = item
                order['seller'] = seller
                orders.append(order)
    
    return render_template('order_history.html', orders=orders, item_name=item_name)

@app.route('/view_seller/<seller_id>')
def view_seller(seller_id):
    # Get seller profile from MongoDB
    seller = seller_profiles.find_one({'_id': ObjectId(seller_id)})
    
    if not seller:
        flash('Seller not found!')
        return redirect(url_for('index'))
    
    # Get all items from this seller
    seller_items = list(items_collection.find({'seller_id': ObjectId(seller_id)}))
    
    return render_template('view_seller.html', seller=seller, items=seller_items)

@app.route('/cart')
def view_cart():
    # Get the user's ID from session
    user_id = session.get('user_id', None)
    
    # If no user is logged in, use a temporary cart ID stored in the session
    if not user_id:
        # Create a temporary cart ID if it doesn't exist
        if 'temp_cart_id' not in session:
            session['temp_cart_id'] = str(uuid.uuid4())
        cart_id = session['temp_cart_id']
    else:
        cart_id = user_id
    
    # Get cart items from MongoDB
    cart_items = list(cart_collection.find({'cart_id': cart_id}))
    
    # Fetch the actual item details for each item in the cart
    items_with_details = []
    total_price = 0
    
    for cart_item in cart_items:
        item = items_collection.find_one({'_id': ObjectId(cart_item['item_id'])})
        if item:
            # Add quantity from cart to the item
            item['cart_quantity'] = cart_item['quantity']
            # Calculate the subtotal for this item
            item['subtotal'] = item['price'] * cart_item['quantity']
            # Add to the total price
            total_price += item['subtotal']
            # Get seller info
            seller = seller_profiles.find_one({'_id': item['seller_id']})
            item['seller'] = seller
            # Add to the list
            items_with_details.append(item)
    
    return render_template('cart.html', 
                           cart_items=items_with_details, 
                           total_price=total_price)

@app.route('/add_to_cart/<item_id>', methods=['POST'])
def add_to_cart(item_id):
    # Get the quantity from the form
    quantity = int(request.form.get('quantity', 1))
    
    # Get the user's ID from session
    user_id = session.get('user_id', None)
    
    # If no user is logged in, use a temporary cart ID stored in the session
    if not user_id:
        # Create a temporary cart ID if it doesn't exist
        if 'temp_cart_id' not in session:
            session['temp_cart_id'] = str(uuid.uuid4())
        cart_id = session['temp_cart_id']
    else:
        cart_id = user_id
    
    # Check if the item exists
    item = items_collection.find_one({'_id': ObjectId(item_id)})
    if not item:
        flash('Item not found!')
        return redirect(url_for('index'))
    
    # Check if there's enough stock
    if quantity > item['quantity']:
        flash('Not enough stock available!')
        return redirect(url_for('index'))
    
    # Check if item is already in cart
    existing_item = cart_collection.find_one({
        'cart_id': cart_id,
        'item_id': item_id
    })
    
    if existing_item:
        # Update quantity
        new_quantity = existing_item['quantity'] + quantity
        cart_collection.update_one(
            {'_id': existing_item['_id']},
            {'$set': {'quantity': new_quantity}}
        )
    else:
        # Add item to cart
        cart_item = {
            'cart_id': cart_id,
            'item_id': item_id,
            'quantity': quantity,
            'date_added': datetime.now()
        }
        cart_collection.insert_one(cart_item)
    
    flash(f"{quantity} {item['name']} added to your cart!")
    return redirect(url_for('view_cart'))

@app.route('/update_cart/<item_id>', methods=['POST'])
def update_cart(item_id):
    # Get the quantity from the form
    quantity = int(request.form.get('quantity', 1))
    
    # Get the user's ID from session
    user_id = session.get('user_id', None)
    
    # If no user is logged in, use a temporary cart ID stored in the session
    if not user_id:
        cart_id = session.get('temp_cart_id', '')
    else:
        cart_id = user_id
    
    # Update quantity in cart
    if quantity <= 0:
        # Remove item from cart if quantity is 0 or less
        cart_collection.delete_one({
            'cart_id': cart_id,
            'item_id': item_id
        })
        flash('Item removed from cart!')
    else:
        # Check if there's enough stock
        item = items_collection.find_one({'_id': ObjectId(item_id)})
        if item and quantity > item['quantity']:
            flash('Not enough stock available!')
            return redirect(url_for('view_cart'))
        
        # Update quantity
        cart_collection.update_one(
            {
                'cart_id': cart_id,
                'item_id': item_id
            },
            {'$set': {'quantity': quantity}}
        )
        flash('Cart updated!')
    
    return redirect(url_for('view_cart'))

@app.route('/remove_from_cart/<item_id>')
def remove_from_cart(item_id):
    # Get the user's ID from session
    user_id = session.get('user_id', None)
    
    # If no user is logged in, use a temporary cart ID stored in the session
    if not user_id:
        cart_id = session.get('temp_cart_id', '')
    else:
        cart_id = user_id
    
    # Remove item from cart
    cart_collection.delete_one({
        'cart_id': cart_id,
        'item_id': item_id
    })
    
    flash('Item removed from cart!')
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    # Get the user's ID from session
    user_id = session.get('user_id', None)
    
    # If no user is logged in, use a temporary cart ID
    if not user_id:
        cart_id = session.get('temp_cart_id', '')
    else:
        cart_id = user_id
    
    # Get cart items
    if user_id:
        cart_items = list(cart_collection.find({'cart_id': user_id}))
    else:
        cart_items = list(cart_collection.find({'cart_id': cart_id}))
    
    if not cart_items:
        flash('Your cart is empty!')
        return redirect(url_for('view_cart'))
    
    # Clear the cart
    if user_id:
        cart_collection.delete_many({'cart_id': user_id})
    else:
        cart_collection.delete_many({'cart_id': cart_id})
        # Clear the temporary cart ID from session if guest checkout
        if 'temp_cart_id' in session:
            session.pop('temp_cart_id')
    
    # Show thank you page
    flash('Your order has been placed successfully!')
    return render_template('thank_you.html')

@app.route('/buyer/dashboard')
def buyer_dashboard():
    # Get the user's ID from session
    user_id = session.get('user_id', None)
    
    if not user_id:
        flash('Please log in to view your dashboard')
        return redirect(url_for('login'))
    
    # Get buyer profile
    user = user_credentials.find_one({'buyer_id': ObjectId(user_id)})
    
    if not user:
        flash('Buyer profile not found')
        return redirect(url_for('index'))
    
    # Get buyer's orders
    orders = list(orders_collection.find({'buyer_id': user_id}))
    
    # Enrich orders with item and seller details
    for order in orders:
        item = items_collection.find_one({'_id': order['item_id']})
        seller = seller_profiles.find_one({'_id': order['seller_id']})
        order['item'] = item
        order['seller'] = seller
    
    # Get buyer profile
    buyer = buyer_profiles.find_one({'_id': ObjectId(user_id)})
    
    return render_template('buyer_dashboard.html', 
                          orders=orders, 
                          buyer=buyer)

@app.route('/buyer/orders')
def view_orders():
    # Get the user's ID from session
    user_id = session.get('user_id', None)
    
    if not user_id:
        flash('Please log in to view your orders')
        return redirect(url_for('login'))
    
    # Get buyer's orders
    orders = list(orders_collection.find({'buyer_id': user_id}).sort('date', -1))
    
    # Enrich orders with item and seller details
    for order in orders:
        item = items_collection.find_one({'_id': order['item_id']})
        seller = seller_profiles.find_one({'_id': order['seller_id']})
        order['item'] = item
        order['seller'] = seller
    
    return render_template('buyer_orders.html', orders=orders)

@app.route('/categories')
def browse_categories():
    # Get all categories
    categories = [
        'Fruits & Vegetables',
        'Dairy & Eggs',
        'Meat & Seafood',
        'Bakery',
        'Pantry Staples',
        'Frozen Foods',
        'Snacks',
        'Beverages',
        'Household Items',
        'Health & Personal Care',
        'Other'
    ]
    
    return render_template('categories.html', categories=categories)

@app.route('/category/<category_name>')
def browse_category(category_name):
    # Find items in this category
    category_items = list(items_collection.find({'category': category_name}))
    
    # Enrich items with seller details
    for item in category_items:
        seller = seller_profiles.find_one({'_id': item['seller_id']})
        item['seller'] = seller
    
    return render_template('category_items.html', 
                          items=category_items, 
                          category=category_name)

@app.route('/shopping_list', methods=['GET', 'POST'])
def shopping_list():
    # Initialize or retrieve shopping list from session
    if 'shopping_list' not in session:
        session['shopping_list'] = []
    
    if request.method == 'POST':
        if 'add_item' in request.form and request.form['add_item']:
            # Add new item to the list
            new_item = request.form['add_item'].strip()
            if new_item:
                session['shopping_list'].append(new_item)
                session.modified = True  # Ensure session is saved
        
        elif 'remove_item' in request.form:
            # Remove item from the list
            try:
                index = int(request.form['remove_item'])
                if 0 <= index < len(session['shopping_list']):
                    removed_item = session['shopping_list'].pop(index)
                    flash(f'Removed "{removed_item}" from your list')
                    session.modified = True
            except (ValueError, IndexError):
                flash('Error removing item from list')
        
        elif 'end_list' in request.form:
            # Process the completed shopping list
            return redirect(url_for('process_shopping_list'))
        
        elif 'clear_list' in request.form:
            # Clear the shopping list
            session['shopping_list'] = []
            flash('Shopping list cleared')
            session.modified = True
    
    return render_template('shopping_list.html', items=session['shopping_list'])

@app.route('/process_shopping_list')
def process_shopping_list():
    # Get the shopping list from session
    shopping_list = session.get('shopping_list', [])
    
    if not shopping_list:
        flash('Your shopping list is empty!')
        return redirect(url_for('shopping_list'))
    
    # Get all available items for BK-Tree
    all_items = list(items_collection.find({}, {'name': 1}))
    all_item_names = [item['name'] for item in all_items]
    
    # Initialize results hashmap to store matches
    results = {}
    
    # Process each item in the shopping list
    for list_item in shopping_list:
        # Use BK-Tree for fuzzy matching
        bktree_data = {
            'query': list_item,
            'items': all_item_names,
            'tolerance': 2  # Tolerance for fuzzy matching
        }
        
        bktree_response = execute_cpp_algorithm('bktree', bktree_data)
        
        # Store matches in results
        item_matches = []
        
        if 'matches' in bktree_response and bktree_response['matches']:
            # For each matched name, find all items and their sellers
            for match_name in bktree_response['matches']:
                matched_items = list(items_collection.find({'name': match_name}))
                
                for item in matched_items:
                    seller = seller_profiles.find_one({'_id': item['seller_id']})
                    item_with_seller = {
                        'item': item,
                        'seller': seller
                    }
                    item_matches.append(item_with_seller)
            
            results[list_item] = item_matches
        else:
            # No matches found
            results[list_item] = []
    
    # Clear the shopping list after processing
    session['shopping_list'] = []
    session.modified = True
    
    return render_template('shopping_list_results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
