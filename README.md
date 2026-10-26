# ⚽ Vintage Football Shirts E-Commerce System
## ระบบร้านขายเสื้อฟุตบอลมือสองวินเทจหายาก

> **จัดทำโดย:** นายวิศรุต พุกพะยา  
> **รหัสนิสิต:** 67160371  
> **โครงงาน:** Web Application พัฒนาระบบร้านขายเสื้อฟุตบอลมือสองวินเทจหายาก

---

## 📖 ภาพรวมของระบบ (System Overview)
ระบบถูกออกแบบและพัฒนาขึ้นตามแผนงานและโครงสร้างการพัฒนา Web Application โดยรองรับ 2 มุมมองหลัก ได้แก่:
1. **มุมมองลูกค้า (Customers):** ค้นหาและเลือกซื้อเสื้อฟุตบอลวินเทจแท้, ตรวจสอบสภาพและไซส์, สั่งซื้อสินค้าพร้อมระบุที่อยู่จัดส่ง, ตรวจสอบประวัติการสั่งซื้อ
2. **มุมมองผู้ดูแลระบบ (Admin):** ติดตามยอดขายรวมแบบสรุปสถิติ, ตรวจจับแจ้งเตือนสต็อกสินค้าต่ำ (Low-Stock Alert < 3 ชิ้น), จัดการคำสั่งซื้อและเปลี่ยนสถานะจัดส่ง, จัดการคลังสินค้า (CRUD: เพิ่ม แก้ไข ลบ เสื้อฟุตบอล)

---

## 🌟 6 โมดูลหลักตามแผนงาน (Core Modules)

| โมดูล | ฟังก์ชันการทำงาน | รายละเอียดทางเทคนิค |
|---|---|---|
| **1. Product Catalog** | แสดงรายการเสื้อฟุตบอลแบบ Grid Card | ค้นหาชื่อทีม/ปีฤดูกาล, กรองตามไซส์ (S, M, L, XL), กรองตามระดับสภาพ (Condition Tag เช่น 9.5/10, ป้ายห้อย BNWT), ป้ายเตือนสต็อกต่ำ |
| **2. Shopping Cart & Checkout** | ตะกร้าสินค้าและการชำระเงิน | เก็บข้อมูลชั่วคราวฝั่ง Client (localStorage), คำนวณราคาสุทธิ, ฟอร์มกรอกที่อยู่จัดส่ง, บันทึกลงตาราง Orders & Order_Items พร้อมตัดสต็อกทันที `(stock = stock - qty)` |
| **3. Order Management** | จัดการคำสั่งซื้อสำหรับ Admin | ตารางรายการสั่งซื้อทั้งหมด, รายละเอียดเสื้อที่สั่ง, ปุ่มเปลี่ยนสถานะสั่งซื้อ (Pending &rarr; Paid &rarr; Shipped &rarr; Cancelled) |
| **4. Customer Accounts** | บัญชีผู้ใช้งานลูกค้า | ระบบ Login / Register, บันทึก Session ผู้ใช้, Customer Dashboard แสดงประวัติการสั่งซื้อ (Order History) |
| **5. Admin Dashboard** | สรุปสถิติและแจ้งเตือน | Stat Cards: ยอดขายรวมสุทธิ `SUM(total_amount)`, จำนวนออเดอร์ที่รอจัดการ (Pending), ป้ายเตือนสต็อกต่ำสีแดงกะพริบ `stock_quantity < 3` |
| **6. Inventory Management** | จัดการคลังเสื้อฟุตบอล (CRUD) | ฟอร์มเพิ่มเสื้อใหม่, ฟอร์มแก้ไขข้อมูล, ปุ่มลบสินค้า, ตารางแสดงข้อมูลพร้อมไฮไลต์แถบสีแดงเมื่อสต็อกเหลือน้อยกว่า 3 ชิ้น |

---

## 🗄️ โครงสร้างฐานข้อมูล (Database Schema)
ระบบใช้ฐานข้อมูล **SQLite3** ตามโครงสร้าง 4 ตารางหลัก:

1. **Users**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `name`: TEXT (ชื่อ-นามสกุล)
   - `email`: TEXT UNIQUE (อีเมลเข้าสู่ระบบ)
   - `password`: TEXT (รหัสผ่าน)
   - `role`: TEXT ('customer' หรือ 'admin')
   - `address`: TEXT (ที่อยู่จัดส่งเริ่มต้น)

2. **Products**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `team_name`: TEXT (ชื่อทีม/สโมสร เช่น Manchester United, Arsenal)
   - `season`: TEXT (ปีฤดูกาล/รุ่น เช่น 1998-1999 Treble Home)
   - `size`: TEXT (ขนาดไซส์ S, M, L, XL, XXL)
   - `condition`: TEXT (ระดับสภาพเสื้อ เช่น 9.5/10 สภาพสะสม, ป้ายห้อย BNWT)
   - `price`: REAL (ราคาจำหน่าย)
   - `stock_quantity`: INTEGER (จำนวนสต็อกคงเหลือ)
   - `image_url`: TEXT (ลิงก์รูปภาพเสื้อฟุตบอล)

3. **Orders**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `user_id`: INTEGER (รหัสลูกค้าที่สั่งซื้อ)
   - `total_amount`: REAL (ยอดรวมสุทธิ)
   - `status`: TEXT ('Pending', 'Paid', 'Shipped', 'Cancelled')
   - `shipping_address`: TEXT (ที่อยู่จัดส่งพัสดุ)
   - `created_at`: TIMESTAMP (วันเวลาที่ทำรายการ)

4. **Order_Items**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `order_id`: INTEGER (รหัสออเดอร์ที่ผูก)
   - `product_id`: INTEGER (รหัสเสื้อฟุตบอล)
   - `quantity`: INTEGER (จำนวนที่สั่ง)
   - `price`: REAL (ราคาต่อชิ้น ณ เวลาที่สั่งซื้อ)

---

## 🚀 วิธีการติดตั้งและรันระบบ (How to Run)

### วิธีที่ 1: รันผ่านไฟล์ Bat (ง่ายที่สุด)
- **เปิดใช้งานเฉพาะในเครื่อง / Wi-Fi เดียวกัน:** ดับเบิลคลิกไฟล์ **`run.bat`** (เข้าผ่าน `http://127.0.0.1:5000` หรือ `http://192.168.44.2:5000`)
- **เปิดออนไลน์ให้คนภายนอกเข้าได้ทั่วโลก (Public Link):** ดับเบิลคลิกไฟล์ **`start_public_tunnel.bat`**

### วิธีที่ 2: รันผ่าน Command Line / Terminal
```bash
cd C:\Users\User\.gemini\antigravity\scratch\vintage_football_store
python app.py
```
เปิดเว็บบราวเซอร์ไปที่: **`http://127.0.0.1:5000`**

### วิธีทดสอบระบบแบบ End-to-End อัตโนมัติ:
```bash
python test_e2e.py
```

---

## 🔑 ข้อมูลบัญชีผู้ใช้สำหรับทดสอบ (Demo Accounts)

| บทบาท (Role) | อีเมล (Email) | รหัสผ่าน (Password) | วัตถุประสงค์การใช้งาน |
|---|---|---|---|
| **ผู้ดูแลระบบ (Admin)** | `admin@vintagefootball.com` | `admin123` | เข้าถึง Admin Dashboard, จัดการคลังเสื้อ (CRUD), เปลี่ยนสถานะออเดอร์ |
| **ลูกค้า (Customer)** | `customer@gmail.com` | `123456` | เลือกซื้อเสื้อใส่ตะกร้า, Checkout ตัดสต็อก, ดูประวัติการสั่งซื้อ |

*(หมายเหตุ: บนหน้าเว็บมีแถบ **Quick Demo Switcher** ด้านบนสุด สามารถคลิกสลับโหมดได้ทันทีในคลิกเดียวเพื่อความสะดวกในการพรีเซนต์)*
