"""Local restaurant order manager. Run: python3 app.py"""
import json
import sqlite3
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'restaurant.db'


def connection():
    db = sqlite3.connect(DB, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db


def initialize():
    with connection() as db:
        db.executescript((ROOT / 'schema.sql').read_text(encoding='utf-8'))
        if db.execute('SELECT count(*) FROM employees').fetchone()[0] == 0:
            db.executescript((ROOT / 'seed.sql').read_text(encoding='utf-8'))


def rows(db, sql, params=()):
    return [dict(r) for r in db.execute(sql, params)]


class Handler(BaseHTTPRequestHandler):
    def send_json(self, value, status=200):
        raw = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/':
            raw = (ROOT / 'index.html').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if path != '/api/data':
            self.send_json({'error': 'ไม่พบหน้า'}, 404)
            return
        with connection() as db:
            self.send_json({
                'customers': rows(db, 'SELECT * FROM customers ORDER BY customer_id DESC'),
                'employees': rows(db, 'SELECT * FROM employees ORDER BY employee_id'),
                'categories': rows(db, 'SELECT * FROM categories ORDER BY category_id'),
                'menus': rows(db, '''SELECT m.*, c.category_name FROM menu_items m
                                      JOIN categories c ON c.category_id=m.category_id ORDER BY m.menu_id DESC'''),
                'orders': rows(db, '''SELECT o.*, c.customer_name, e.employee_name,
                           COALESCE(SUM(i.quantity*i.unit_price),0) AS total
                           FROM orders o LEFT JOIN customers c ON c.customer_id=o.customer_id
                           JOIN employees e ON e.employee_id=o.employee_id
                           LEFT JOIN order_items i ON i.order_id=o.order_id
                           GROUP BY o.order_id ORDER BY o.order_id DESC'''),
                'items': rows(db, '''SELECT i.*,m.menu_name FROM order_items i
                                    JOIN menu_items m ON m.menu_id=i.menu_id ORDER BY i.order_item_id''')
            })

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in ('/api/customers', '/api/menus', '/api/orders', '/api/order-status'):
            self.send_json({'error': 'ไม่พบคำสั่ง'}, 404)
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size < 1 or size > 100000:
                raise ValueError('ขนาดข้อมูลไม่ถูกต้อง')
            data = json.loads(self.rfile.read(size))
            with connection() as db:
                if path == '/api/customers':
                    name = str(data['customer_name']).strip()
                    phone = str(data.get('phone') or '').strip() or None
                    if not name: raise ValueError('กรุณากรอกชื่อลูกค้า')
                    if data.get('customer_id'):
                        cur = db.execute('UPDATE customers SET customer_name=?,phone=? WHERE customer_id=?',
                                         (name, phone, int(data['customer_id'])))
                        if not cur.rowcount: raise ValueError('ไม่พบลูกค้า')
                    else:
                        db.execute('INSERT INTO customers(customer_name,phone) VALUES (?,?)', (name, phone))
                elif path == '/api/menus':
                    name = str(data['menu_name']).strip()
                    price = Decimal(str(data['price']))
                    if not name or not price.is_finite() or price < 0: raise ValueError('ชื่อหรือราคาไม่ถูกต้อง')
                    category_id = int(data['category_id'])
                    available = int(bool(data.get('is_available', True)))
                    if data.get('menu_id'):
                        cur = db.execute('''UPDATE menu_items SET menu_name=?,price=?,category_id=?,is_available=?
                                            WHERE menu_id=?''', (name, str(price), category_id, available, int(data['menu_id'])))
                        if not cur.rowcount: raise ValueError('ไม่พบเมนู')
                    else:
                        db.execute('INSERT INTO menu_items(menu_name,price,category_id,is_available) VALUES (?,?,?,?)',
                                   (name, str(price), category_id, available))
                elif path == '/api/orders':
                    items = data['items']
                    if not isinstance(items, list) or not items: raise ValueError('ออเดอร์ต้องมีอาหารอย่างน้อยหนึ่งรายการ')
                    order_type = data['order_type']
                    if order_type not in ('ทานที่ร้าน', 'กลับบ้าน'): raise ValueError('ประเภทออเดอร์ไม่ถูกต้อง')
                    customer_id = int(data['customer_id']) if data.get('customer_id') else None
                    employee_id = int(data['employee_id'])
                    cur = db.execute('INSERT INTO orders(customer_id,employee_id,order_type,note) VALUES (?,?,?,?)',
                                     (customer_id, employee_id, order_type, str(data.get('note') or '').strip()))
                    for item in items:
                        menu_id, qty = int(item['menu_id']), int(item['quantity'])
                        if qty < 1: raise ValueError('จำนวนอาหารต้องมากกว่า 0')
                        menu = db.execute('SELECT price FROM menu_items WHERE menu_id=? AND is_available=1', (menu_id,)).fetchone()
                        if menu is None: raise ValueError('เมนูไม่พร้อมจำหน่าย')
                        db.execute('INSERT INTO order_items(order_id,menu_id,quantity,unit_price,item_note) VALUES (?,?,?,?,?)',
                                   (cur.lastrowid, menu_id, qty, menu['price'], str(item.get('item_note') or '').strip()))
                else:
                    if data.get('status') not in ('รับออเดอร์','กำลังทำ','เสร็จแล้ว','ยกเลิก'):
                        raise ValueError('สถานะไม่ถูกต้อง')
                    cur = db.execute('UPDATE orders SET status=? WHERE order_id=?', (data['status'], int(data['order_id'])))
                    if not cur.rowcount: raise ValueError('ไม่พบออเดอร์')
            self.send_json({'ok': True})
        except (ValueError, KeyError, TypeError, json.JSONDecodeError, sqlite3.IntegrityError) as exc:
            self.send_json({'error': str(exc)}, 400)


if __name__ == '__main__':
    initialize()
    print('เปิดเว็บที่ http://127.0.0.1:8000')
    ThreadingHTTPServer(('127.0.0.1', 8000), Handler).serve_forever()
