# SuffixKART - Advanced Grocery Store System

SuffixKART is a modern grocery store system that integrates MongoDB with advanced C++ algorithms to provide a robust shopping experience. The system is built on a Flask web application that communicates with a C++ backend for specialized algorithmic operations.

## Key Features

- **User Authentication**
  - Secure registration and login for both buyers and sellers
  - Session-based authentication with access control
  - Password hashing with salting for security

- **Advanced C++ Algorithms**
  - **Bloom Filter**: Used for item uniqueness verification
  - **BK-Tree**: Powers fuzzy search capabilities for product search
  - **Suffix Tree**: Efficiently tracks and searches order history

- **Seller Features**
  - Seller dashboard to manage products
  - Add, edit, and delete product listings
  - View sales history for products

- **Buyer Features**
  - Browse products by category
  - Search for products with fuzzy matching
  - Shopping cart for collecting items before purchase
  - Checkout process with shipping and payment details
  - Order history and tracking

- **Product Management**
  - Product categorization with 11 different categories
  - Inventory tracking with stock status indicators
  - Product descriptions, pricing, and seller information

- **Shopping Cart**
  - Add items to cart (even when not logged in)
  - Adjust quantities for items in cart
  - Cart persistence between sessions
  - Automatic merging of guest cart with user cart on login

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript with Bootstrap 5
- **Backend**: Flask (Python)
- **Database**: MongoDB
- **Algorithms**: C++ implementations of Bloom Filter, BK-Tree, and Suffix Tree
- **Authentication**: Custom secure authentication system

## Installation and Setup

### Prerequisites

- Python 3.6+
- MongoDB
- C++ compiler (GCC, Clang, or MSVC)
- nlohmann/json library for C++

### Steps

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/suffixKART.git
   cd suffixKART
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Build the C++ backend:
   ```
   ./build.bat    # On Windows
   ./build.sh     # On Linux/Mac
   ```

4. Ensure MongoDB is running:
   ```
   mongod --dbpath /path/to/data/directory
   ```

5. Run the Flask application:
   ```
   python app.py
   ```

6. Access the application in your browser at `http://localhost:5000`

## Database Structure

- **seller_profiles**: Stores seller information
- **buyer_profiles**: Stores buyer information
- **user_credentials**: Stores authentication information for both sellers and buyers
- **items_collection**: Stores product listings
- **orders_collection**: Stores order information
- **cart_collection**: Stores shopping cart contents

## System Architecture

The system works through a Flask web application that handles user requests and communicates with a MongoDB database for data storage. For specialized algorithmic operations, the system uses a C++ backend that is called via subprocess. The C++ backend implements three key algorithms:

1. **Bloom Filter** for efficient membership testing (used when adding new items)
2. **BK-Tree** for fuzzy string matching (used in product search)
3. **Suffix Tree** for pattern matching in order histories

Data is exchanged between the Flask app and C++ backend using JSON.

```
+------------------+      +------------------+      +------------------+
|                  |      |                  |      |                  |
|  Flask Web App   |<---->|   MongoDB DB    |<---->|   C++ Algorithms |
|                  |      |                  |      |                  |
+------------------+      +------------------+      +------------------+
        ^                                                   ^
        |                                                   |
        v                                                   v
+------------------+                              +------------------+
|                  |                              |                  |
|   Web Browser    |                              |   JSON Data      |
|                  |                              |                  |
+------------------+                              +------------------+
```

## Warnings

Please take note of the following warnings while using the system:

- When adding items, ensure their names are unique to avoid confusion
- Ensure MongoDB is running before starting the application
- The C++ backend must be compiled for the system to function correctly

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
