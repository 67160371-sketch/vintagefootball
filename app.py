import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = 'vintage_football_key_67160371_wisarut'

# Ensure DB initialized
init_db()

def get_current_user():
    if 'user_id' in session:
        conn = get_db()
        user = conn.execute('SELECT * FROM Users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        return user
    return None

@app.context_processor
def inject_user_and_counts():
    user = get_current_user()
    low_stock_count = 0
    pending_orders_count = 0
    if user and user['role'] == 'admin':
        conn = get_db()
        low_stock_count = conn.execute('SELECT COUNT(*) FROM Products WHERE stock_quantity < 3').fetchone()[0]
        pending_orders_count = conn.execute("SELECT COUNT(*) FROM Orders WHERE status = 'Pending'").fetchone()[0]
        conn.close()
    return {
        'current_user': user,
        'low_stock_count': low_stock_count,
        'pending_orders_count': pending_orders_count
    }

# ==================== PUBLIC & CUSTOMER ROUTES ====================

@app.route('/')
def catalog():
    search_query = request.args.get('q', '').strip()
    size_filter = request.args.get('size', '').strip()
    condition_filter = request.args.get('condition', '').strip()
    sort_by = request.args.get('sort', 'newest')

    conn = get_db()
    query = 'SELECT * FROM Products WHERE 1=1'
    params = []

    if search_query:
        query += ' AND (team_name LIKE ? OR season LIKE ?)'
        params.extend([f'%{search_query}%', f'%{search_query}%'])

    if size_filter:
        query += ' AND size = ?'
        params.append(size_filter)

    if condition_filter:
        query += ' AND condition LIKE ?'
        params.append(f'%{condition_filter}%')

    if sort_by == 'price_asc':
        query += ' ORDER BY price ASC'
    elif sort_by == 'price_desc':
        query += ' ORDER BY price DESC'
    elif sort_by == 'team':
        query += ' ORDER BY team_name ASC'
    else:
        query += ' ORDER BY id DESC'

    products = conn.execute(query, params).fetchall()

    # Get distinct sizes for filter dropdown
    sizes = conn.execute('SELECT DISTINCT size FROM Products ORDER BY size').fetchall()
    conn.close()

    return render_template('catalog.html', 
                           products=products, 
                           search_query=search_query, 
                           size_filter=size_filter,
                           sizes=[s['size'] for s in sizes],
                           sort_by=sort_by)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db()
    product = conn.execute('SELECT * FROM Products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    if not product:
        flash('ไม่พบข้อมูลสินค้านี้', 'danger')
        return redirect(url_for('catalog'))
    return render_template('product_detail.html', product=product)

@app.route('/cart')
def cart():
    user = get_current_user()
    return render_template('cart.html', user=user)

@app.route('/api/products')
def api_products():
    conn = get_db()
    products = conn.execute('SELECT * FROM Products').fetchall()
    conn.close()
    return jsonify([dict(p) for p in products])

@app.route('/api/checkout', methods=['POST'])
def checkout():
    user = get_current_user()
    data = request.get_json() or {}

    items = data.get('items', [])
    shipping_address = data.get('shipping_address', '').strip()

    if not items:
        return jsonify({'success': False, 'message': 'ไม่มีสินค้าในตะกร้า'}), 400

    if not shipping_address:
        return jsonify({'success': False, 'message': 'กรุณากรอกที่อยู่จัดส่งให้ครบถ้วน'}), 400

    user_id = user['id'] if user else None

    # If guest checked out, create or assign a guest customer id
    conn = get_db()
    cursor = conn.cursor()

    if not user_id:
        guest_email = data.get('email', 'guest@vintagefootball.com')
        guest_name = data.get('name', 'ลูกค้าทั่วไป (Guest)')
        # Find or create guest user
        cursor.execute("SELECT id FROM Users WHERE email = ?", (guest_email,))
        existing_user = cursor.fetchone()
        if existing_user:
            user_id = existing_user['id']
        else:
            cursor.execute('''
                INSERT INTO Users (name, email, password, role, address)
                VALUES (?, ?, 'guest123', 'customer', ?)
            ''', (guest_name, guest_email, shipping_address))
            user_id = cursor.lastrowid

    # Verify inventory and compute total
    total_amount = 0.0
    items_to_process = []

    for item in items:
        prod_id = int(item['id'])
        qty = int(item['quantity'])

        product = cursor.execute('SELECT * FROM Products WHERE id = ?', (prod_id,)).fetchone()
        if not product:
            conn.close()
            return jsonify({'success': False, 'message': f'ไม่พบสินค้า ID {prod_id}'}), 400

        if product['stock_quantity'] < qty:
            conn.close()
            return jsonify({
                'success': False, 
                'message': f"เสื้อ {product['team_name']} ({product['season']}) มีสต็อกคงเหลือเพียง {product['stock_quantity']} ตัว ไม่พอสำหรับการสั่งซื้อ {qty} ตัว"
            }), 400

        price = float(product['price'])
        total_amount += price * qty
        items_to_process.append({
            'product_id': prod_id,
            'quantity': qty,
            'price': price,
            'current_stock': product['stock_quantity']
        })

    # Begin order creation & stock deduction
    try:
        # Insert Order
        cursor.execute('''
            INSERT INTO Orders (user_id, total_amount, status, shipping_address)
            VALUES (?, ?, 'Pending', ?)
        ''', (user_id, total_amount, shipping_address))
        order_id = cursor.lastrowid

        # Insert Order Items & Deduct Stock
        for item in items_to_process:
            cursor.execute('''
                INSERT INTO Order_Items (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item['product_id'], item['quantity'], item['price']))

            cursor.execute('''
                UPDATE Products 
                SET stock_quantity = stock_quantity - ? 
                WHERE id = ?
            ''', (item['quantity'], item['product_id']))

        conn.commit()
        conn.close()
        return jsonify({
            'success': True, 
            'order_id': order_id, 
            'total_amount': total_amount,
            'message': 'บันทึกคำสั่งซื้อเรียบร้อย และระบบได้ตัดสต็อกสินค้าทันที!'
        })
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาดในการสั่งซื้อ: {str(e)}'}), 500

@app.route('/order-success/<int:order_id>')
def order_success(order_id):
    conn = get_db()
    order = conn.execute('''
        SELECT o.*, u.name as customer_name, u.email as customer_email
        FROM Orders o
        LEFT JOIN Users u ON o.user_id = u.id
        WHERE o.id = ?
    ''', (order_id,)).fetchone()

    if not order:
        flash('ไม่พบข้อมูลคำสั่งซื้อ', 'danger')
        conn.close()
        return redirect(url_for('catalog'))

    items = conn.execute('''
        SELECT oi.*, p.team_name, p.season, p.size, p.condition, p.image_url
        FROM Order_Items oi
        JOIN Products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    ''', (order_id,)).fetchall()
    conn.close()

    return render_template('order_success.html', order=order, items=items)

# ==================== CUSTOMER ACCOUNTS ====================

@app.route('/my-orders')
def my_orders():
    user = get_current_user()
    if not user:
        flash('กรุณาเข้าสู่ระบบเพื่อดูประวัติการสั่งซื้อของคุณ', 'info')
        return redirect(url_for('login', next=request.path))

    conn = get_db()
    orders = conn.execute('''
        SELECT * FROM Orders 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (user['id'],)).fetchall()

    orders_with_items = []
    for order in orders:
        items = conn.execute('''
            SELECT oi.*, p.team_name, p.season, p.size, p.image_url
            FROM Order_Items oi
            JOIN Products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order['id'],)).fetchall()
        orders_with_items.append({
            'order': order,
            'items': items
        })

    conn.close()
    return render_template('my_orders.html', orders_with_items=orders_with_items, user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db()
        user = conn.execute('SELECT * FROM Users WHERE email = ? AND password = ?', (email, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            flash(f"ยินดีต้อนรับคุณ {user['name']} เข้าสู่ระบบสำเร็จ!", 'success')

            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('catalog'))
        else:
            flash('อีเมลหรือรหัสผ่านไม่ถูกต้อง โปรดตรวจสอบอีกครั้ง', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        address = request.form.get('address', '').strip()

        if not name or not email or not password:
            flash('กรุณากรอกข้อมูลให้ครบทุกช่องที่มีเครื่องหมายดอกจัน (*)', 'danger')
            return render_template('register.html')

        conn = get_db()
        cursor = conn.cursor()
        existing = cursor.execute('SELECT id FROM Users WHERE email = ?', (email,)).fetchone()
        if existing:
            conn.close()
            flash('อีเมลนี้ถูกใช้งานแล้ว โปรดใช้อีเมลอื่น หรือเข้าสู่ระบบ', 'warning')
            return render_template('register.html')

        cursor.execute('''
            INSERT INTO Users (name, email, password, role, address)
            VALUES (?, ?, ?, 'customer', ?)
        ''', (name, email, password, address))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()

        session['user_id'] = new_id
        session['user_name'] = name
        session['user_role'] = 'customer'
        flash('สมัครสมาชิกเรียบร้อยแล้ว ยินดีต้อนรับสู่ครอบครัว Vintage Football Shirts!', 'success')
        return redirect(url_for('catalog'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('ออกจากระบบเรียบร้อยแล้ว', 'info')
    return redirect(url_for('catalog'))

@app.route('/quick-login/<role>')
def quick_login(role):
    """1-Click switch for demonstration and testing purposes"""
    conn = get_db()
    if role == 'admin':
        user = conn.execute("SELECT * FROM Users WHERE role = 'admin' LIMIT 1").fetchone()
    else:
        user = conn.execute("SELECT * FROM Users WHERE role = 'customer' LIMIT 1").fetchone()
    conn.close()

    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_role'] = user['role']
        flash(f"⚡ สลับโหมดใช้งานเป็น: {user['name']} ({user['role'].upper()})", 'info')
        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('catalog'))
    
    flash('ไม่พบบัญชีผู้ใช้สำหรับโหมดนี้', 'danger')
    return redirect(url_for('catalog'))

# ==================== ADMIN SIDE ====================

def admin_required(func):
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user['role'] != 'admin':
            flash('หน้านี้สงวนสิทธิ์เฉพาะผู้ดูแลระบบ (Admin) เท่านั้น กรุณาเข้าสู่ระบบด้วยบัญชีแอดมิน', 'danger')
            return redirect(url_for('login', next=request.path))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db()

    # 1. Total Revenue: SUM(total_amount)
    revenue_res = conn.execute('SELECT SUM(total_amount) FROM Orders WHERE status != "Cancelled"').fetchone()[0]
    total_revenue = revenue_res if revenue_res else 0.0

    # 2. Orders awaiting processing (Pending)
    pending_orders_count = conn.execute("SELECT COUNT(*) FROM Orders WHERE status = 'Pending'").fetchone()[0]

    # 3. Total Orders
    total_orders_count = conn.execute("SELECT COUNT(*) FROM Orders").fetchone()[0]

    # 4. Total Products
    total_products_count = conn.execute("SELECT COUNT(*) FROM Products").fetchone()[0]

    # 5. Low-Stock Alert: stock_quantity < 3 (Required by Page 3 Phase 2)
    low_stock_products = conn.execute('''
        SELECT * FROM Products 
        WHERE stock_quantity < 3 
        ORDER BY stock_quantity ASC
    ''').fetchall()

    # 6. Recent Orders
    recent_orders = conn.execute('''
        SELECT o.*, u.name as customer_name, u.email as customer_email
        FROM Orders o
        LEFT JOIN Users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
        LIMIT 6
    ''').fetchall()

    conn.close()

    return render_template('admin/dashboard.html',
                           total_revenue=total_revenue,
                           pending_orders_count=pending_orders_count,
                           total_orders_count=total_orders_count,
                           total_products_count=total_products_count,
                           low_stock_products=low_stock_products,
                           recent_orders=recent_orders)

@app.route('/admin/inventory')
@admin_required
def admin_inventory():
    conn = get_db()
    products = conn.execute('SELECT * FROM Products ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin/inventory.html', products=products)

@app.route('/admin/product/add', methods=['POST'])
@admin_required
def admin_add_product():
    team_name = request.form.get('team_name', '').strip()
    season = request.form.get('season', '').strip()
    size = request.form.get('size', 'M').strip()
    condition = request.form.get('condition', '').strip()
    price = float(request.form.get('price', 0))
    stock_quantity = int(request.form.get('stock_quantity', 0))
    image_url = request.form.get('image_url', '').strip()

    if not image_url:
        image_url = 'https://images.unsplash.com/photo-1577223625816-7546f13df25d?w=800&auto=format&fit=crop&q=80'

    conn = get_db()
    conn.execute('''
        INSERT INTO Products (team_name, season, size, condition, price, stock_quantity, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (team_name, season, size, condition, price, stock_quantity, image_url))
    conn.commit()
    conn.close()

    flash(f"เพิ่มเสื้อฟุตบอล '{team_name} ({season})' เข้าสู่คลังสินค้าสำเร็จ!", 'success')
    return redirect(url_for('admin_inventory'))

@app.route('/admin/product/edit/<int:product_id>', methods=['POST'])
@admin_required
def admin_edit_product(product_id):
    team_name = request.form.get('team_name', '').strip()
    season = request.form.get('season', '').strip()
    size = request.form.get('size', 'M').strip()
    condition = request.form.get('condition', '').strip()
    price = float(request.form.get('price', 0))
    stock_quantity = int(request.form.get('stock_quantity', 0))
    image_url = request.form.get('image_url', '').strip()

    conn = get_db()
    conn.execute('''
        UPDATE Products
        SET team_name = ?, season = ?, size = ?, condition = ?, price = ?, stock_quantity = ?, image_url = ?
        WHERE id = ?
    ''', (team_name, season, size, condition, price, stock_quantity, image_url, product_id))
    conn.commit()
    conn.close()

    flash(f"อัปเดตข้อมูลเสื้อ '{team_name}' สำเร็จ!", 'success')
    return redirect(url_for('admin_inventory'))

@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    conn = get_db()
    conn.execute('DELETE FROM Products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()

    flash('ลบข้อมูลสินค้าออกจากระบบเรียบร้อยแล้ว', 'info')
    return redirect(url_for('admin_inventory'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    conn = get_db()
    orders = conn.execute('''
        SELECT o.*, u.name as customer_name, u.email as customer_email, u.address as user_saved_address
        FROM Orders o
        LEFT JOIN Users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    ''').fetchall()

    orders_full = []
    for order in orders:
        items = conn.execute('''
            SELECT oi.*, p.team_name, p.season, p.size, p.image_url
            FROM Order_Items oi
            JOIN Products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order['id'],)).fetchall()
        orders_full.append({
            'order': order,
            'items': items
        })

    conn.close()
    return render_template('admin/orders.html', orders=orders_full)

@app.route('/admin/order/status/<int:order_id>', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    new_status = request.form.get('status', 'Pending').strip()
    valid_statuses = ['Pending', 'Paid', 'Shipped', 'Cancelled']

    if new_status not in valid_statuses:
        flash('สถานะไม่ถูกต้อง', 'danger')
        return redirect(url_for('admin_orders'))

    conn = get_db()
    conn.execute('UPDATE Orders SET status = ? WHERE id = ?', (new_status, order_id))
    conn.commit()
    conn.close()

    flash(f"อัปเดตสถานะคำสั่งซื้อ #{order_id} เป็น '{new_status}' สำเร็จ!", 'success')
    
    # Return to referring page or orders page
    referrer = request.referrer
    if referrer and ('admin' in referrer):
        return redirect(referrer)
    return redirect(url_for('admin_orders'))

if __name__ == '__main__':
    # host='0.0.0.0' allows other devices on the same Wi-Fi/LAN to access the website
    app.run(debug=True, host='0.0.0.0', port=5000)
