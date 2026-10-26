import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'vintage_football.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Table 1: Users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer',
            address TEXT
        )
    ''')

    # Table 2: Products
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT NOT NULL,
            season TEXT NOT NULL,
            size TEXT NOT NULL,
            condition TEXT NOT NULL,
            price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL DEFAULT 0,
            image_url TEXT
        )
    ''')

    # Table 3: Orders
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            shipping_address TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users(id)
        )
    ''')

    # Table 4: Order_Items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Order_Items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES Orders(id),
            FOREIGN KEY (product_id) REFERENCES Products(id)
        )
    ''')

    # Seed Sample Users if empty
    cursor.execute('SELECT COUNT(*) FROM Users')
    if cursor.fetchone()[0] == 0:
        sample_users = [
            ('วิศรุต พุกพะยา (Admin)', 'admin@vintagefootball.com', 'admin123', 'admin', 'สำนักงานใหญ่ Vintage Football Kits ถ.สุขุมวิท กทม.'),
            ('สมชาย รักบอล (Customer)', 'customer@gmail.com', '123456', 'customer', '128/9 หมู่ 4 แขวงลาดพร้าว เขตลาดพร้าว กรุงเทพฯ 10230')
        ]
        cursor.executemany('''
            INSERT INTO Users (name, email, password, role, address)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_users)

    # Seed Sample Products if empty
    cursor.execute('SELECT COUNT(*) FROM Products')
    if cursor.fetchone()[0] == 0:
        sample_products = [
            (
                'Manchester United',
                '1998-1999 Treble Home (Final Camp Nou)',
                'L',
                '9.5/10 สภาพสะสม ไร้ตำหนิ',
                4500.0,
                2,  # Low stock < 3 for alert testing!
                '/static/images/manchester_united.png'
            ),
            (
                'Arsenal',
                '2003-2004 Invincibles Home (Henry 14)',
                'M',
                '9/10 สภาพนางฟ้า ป้ายคอคมชัด',
                3900.0,
                5,
                '/static/images/arsenal.png'
            ),
            (
                'AC Milan',
                '2006-2007 UCL Final Athens (Kaka 22)',
                'XL',
                '8.5/10 สกรีนสวย มีรอยขุยเล็กน้อย',
                3200.0,
                1,  # Low stock < 3 for alert testing!
                '/static/images/acmilan.jpg'
            ),
            (
                'Barcelona',
                '2008-2009 Sextuple Home (Messi 10)',
                'L',
                '9/10 สภาพสมบูรณ์ สปอนเซอร์ UNICEF แน่น',
                4200.0,
                6,
                '/static/images/barcelona.png'
            ),
            (
                'Real Madrid',
                '2001-2002 Centenary Home (Zidane 5)',
                'M',
                '9.5/10 รุ่นฉลอง 100 ปี หายากมาก',
                5500.0,
                2,  # Low stock < 3 for alert testing!
                '/static/images/realmadrid.png'
            ),
            (
                'Brazil National Team',
                '2002 World Cup Winners (Ronaldo 9)',
                'L',
                '10/10 ป้ายห้อย (BNWT) แท้ดั้งเดิม',
                6200.0,
                1,  # Low stock < 3 for alert testing!
                '/static/images/brazil.png'
            ),
            (
                'Juventus',
                '1997-1998 Del Piero 10 (Sony)',
                'XL',
                '8/10 สกรีนแตกวินเทจตามกาลเวลา คลาสสิก',
                2800.0,
                4,
                '/static/images/juventus.png'
            ),
            (
                'Liverpool',
                '2004-2005 Istanbul UCL Final (Gerrard 8)',
                'M',
                '9/10 แมตช์ปาฏิหาริย์อิสตันบูล ป้ายครบ',
                3800.0,
                2,  # Low stock < 3 for alert testing!
                '/static/images/liverpool.png'
            )
        ]
        cursor.executemany('''
            INSERT INTO Products (team_name, season, size, condition, price, stock_quantity, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_products)

    # Seed Sample Orders if empty
    cursor.execute('SELECT COUNT(*) FROM Orders')
    if cursor.fetchone()[0] == 0:
        # Get customer id
        cursor.execute("SELECT id FROM Users WHERE role = 'customer' LIMIT 1")
        customer = cursor.fetchone()
        customer_id = customer['id'] if customer else 2

        # Order 1: Delivered / Shipped
        cursor.execute('''
            INSERT INTO Orders (user_id, total_amount, status, shipping_address, created_at)
            VALUES (?, ?, ?, ?, datetime('now', '-2 days'))
        ''', (customer_id, 3900.0, 'Shipped', '128/9 หมู่ 4 แขวงลาดพร้าว เขตลาดพร้าว กรุงเทพฯ 10230'))
        order_1_id = cursor.lastrowid

        cursor.execute('''
            INSERT INTO Order_Items (order_id, product_id, quantity, price)
            VALUES (?, 2, 1, 3900.0)
        ''', (order_1_id,))

        # Order 2: Pending (for admin pending counter and action demonstration!)
        cursor.execute('''
            INSERT INTO Orders (user_id, total_amount, status, shipping_address, created_at)
            VALUES (?, ?, ?, ?, datetime('now', '-1 hours'))
        ''', (customer_id, 4500.0, 'Pending', '128/9 หมู่ 4 แขวงลาดพร้าว เขตลาดพร้าว กรุงเทพฯ 10230'))
        order_2_id = cursor.lastrowid

        cursor.execute('''
            INSERT INTO Order_Items (order_id, product_id, quantity, price)
            VALUES (?, 1, 1, 4500.0)
        ''', (order_2_id,))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
