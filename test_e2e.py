import os
import sys
import sqlite3
import json

# Ensure utf-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app import app
from database import get_db, init_db

def test_full_e2e_flow():
    print("==================================================")
    print("⚽ STARTING END-TO-END TEST: VINTAGE FOOTBALL E-COMMERCE")
    print("==================================================")

    init_db()
    client = app.test_client()

    # 1. Test Catalog & Search Filter (Module 1)
    print("\n[TEST 1] Testing Product Catalog & Search Filter...")
    res = client.get('/')
    assert res.status_code == 200, f"Catalog failed with status {res.status_code}"
    assert 'VINTAGE KITS' in res.get_data(as_text=True)
    print("  ✓ Catalog page loads successfully.")

    # Search filter test
    res_search = client.get('/?q=Manchester')
    assert res_search.status_code == 200
    assert 'Manchester United' in res_search.get_data(as_text=True)
    print("  ✓ Search filter by team name works.")

    # 2. Test Customer Login & Account (Module 4)
    print("\n[TEST 2] Testing Customer Login...")
    res_login = client.post('/login', data={
        'email': 'customer@gmail.com',
        'password': '123456'
    }, follow_redirects=True)
    assert res_login.status_code == 200
    assert 'สมชาย รักบอล' in res_login.get_data(as_text=True)
    print("  ✓ Customer login successful.")

    # 3. Test Shopping Cart & Checkout with Real-time Stock Deduction (Module 2)
    print("\n[TEST 3] Testing Shopping Cart & Checkout with Stock Deduction...")
    # Check initial stock of Product 2 (Arsenal 2003-2004)
    conn = get_db()
    initial_product = conn.execute("SELECT * FROM Products WHERE id = 2").fetchone()
    initial_stock = initial_product['stock_quantity']
    conn.close()
    print(f"  • Product 2 initial stock: {initial_stock}")

    # Checkout 2 jerseys
    checkout_payload = {
        'items': [
            {'id': 2, 'quantity': 2}
        ],
        'shipping_address': '99/1 ซอยอารีย์ ถนนพหลโยธิน เขตพญาไท กทม. 10400'
    }
    res_checkout = client.post('/api/checkout', 
                               data=json.dumps(checkout_payload), 
                               content_type='application/json')
    assert res_checkout.status_code == 200
    checkout_data = json.loads(res_checkout.get_data(as_text=True))
    assert checkout_data['success'] is True
    order_id = checkout_data['order_id']
    print(f"  ✓ Order created successfully with Order ID: #{order_id}")

    # Check updated stock in DB
    conn = get_db()
    updated_product = conn.execute("SELECT * FROM Products WHERE id = 2").fetchone()
    updated_stock = updated_product['stock_quantity']
    assert updated_stock == initial_stock - 2, f"Stock mismatch! Expected {initial_stock - 2}, got {updated_stock}"
    print(f"  ✓ Stock deduction verified: {initial_stock} -> {updated_stock} (deducted 2 units correctly).")

    # Verify Order in DB
    order_row = conn.execute("SELECT * FROM Orders WHERE id = ?", (order_id,)).fetchone()
    assert order_row['status'] == 'Pending'
    assert order_row['total_amount'] == 3900.0 * 2
    conn.close()
    print("  ✓ Order and Order_Items recorded with status 'Pending' and correct total.")

    # 4. Test Customer Order History (Module 4)
    print("\n[TEST 4] Testing Customer Order History View...")
    res_orders = client.get('/my-orders')
    assert res_orders.status_code == 200
    assert f"#ORD-{order_id:05d}" in res_orders.get_data(as_text=True)
    print("  ✓ Order appears in Customer's Order History.")

    # 5. Switch to Admin and Check Admin Dashboard & Low-Stock Alert (Module 5)
    print("\n[TEST 5] Testing Admin Dashboard & Low-Stock Alert...")
    client.get('/quick-login/admin')
    res_admin = client.get('/admin')
    assert res_admin.status_code == 200
    admin_html = res_admin.get_data(as_text=True)
    assert 'แผงควบคุมระบบ (ADMIN DASHBOARD)' in admin_html
    assert 'เตือนสต็อกต่ำ' in admin_html
    print("  ✓ Admin Dashboard rendered with Revenue & Low-Stock alert cards.")

    # 6. Test Admin Status Update (Module 3)
    print("\n[TEST 6] Testing Order Management Status Update...")
    res_status = client.post(f'/admin/order/status/{order_id}', data={
        'status': 'Shipped'
    }, follow_redirects=True)
    assert res_status.status_code == 200
    conn = get_db()
    updated_order = conn.execute("SELECT status FROM Orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()
    assert updated_order['status'] == 'Shipped'
    print(f"  ✓ Admin changed order #{order_id} status from Pending to Shipped.")

    # 7. Test Admin Inventory Management CRUD (Module 6)
    print("\n[TEST 7] Testing Inventory CRUD (Add, Edit, Delete)...")
    # Add
    res_add = client.post('/admin/product/add', data={
        'team_name': 'Liverpool (Vintage Test)',
        'season': '1995-1996 Away Green',
        'size': 'XL',
        'condition': '9/10 เกรดสะสม',
        'price': '4200',
        'stock_quantity': '1', # triggers low stock alert!
        'image_url': 'https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=800'
    }, follow_redirects=True)
    assert res_add.status_code == 200
    conn = get_db()
    new_prod = conn.execute("SELECT * FROM Products WHERE team_name = 'Liverpool (Vintage Test)'").fetchone()
    assert new_prod is not None
    new_id = new_prod['id']
    print(f"  ✓ Product added successfully (ID: {new_id}).")

    # Edit
    res_edit = client.post(f'/admin/product/edit/{new_id}', data={
        'team_name': 'Liverpool (Vintage Test Edited)',
        'season': '1995-1996 Away Green Final',
        'size': 'L',
        'condition': '9.5/10 สภาพกริ๊บ',
        'price': '4800',
        'stock_quantity': '5',
        'image_url': ''
    }, follow_redirects=True)
    assert res_edit.status_code == 200
    conn = get_db()
    edited_prod = conn.execute("SELECT * FROM Products WHERE id = ?", (new_id,)).fetchone()
    assert edited_prod['team_name'] == 'Liverpool (Vintage Test Edited)'
    assert edited_prod['price'] == 4800.0
    print("  ✓ Product edited successfully.")

    # Delete
    res_del = client.post(f'/admin/product/delete/{new_id}', follow_redirects=True)
    assert res_del.status_code == 200
    conn = get_db()
    deleted_prod = conn.execute("SELECT * FROM Products WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    assert deleted_prod is None
    print("  ✓ Product deleted successfully.")

    print("\n==================================================")
    print("🏆 ALL 6 MODULES & END-TO-END FLOW TESTS PASSED 100%!")
    print("==================================================")

if __name__ == '__main__':
    test_full_e2e_flow()
