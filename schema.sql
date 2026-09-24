PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
  customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_name TEXT NOT NULL,
  phone TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS employees (
  employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_name TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('เจ้าของร้าน','พ่อครัว','พนักงาน'))
);
CREATE TABLE IF NOT EXISTS categories (
  category_id INTEGER PRIMARY KEY AUTOINCREMENT,
  category_name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS menu_items (
  menu_id INTEGER PRIMARY KEY AUTOINCREMENT,
  category_id INTEGER NOT NULL REFERENCES categories(category_id) ON DELETE RESTRICT,
  menu_name TEXT NOT NULL UNIQUE,
  price NUMERIC NOT NULL CHECK (price >= 0),
  is_available INTEGER NOT NULL DEFAULT 1 CHECK (is_available IN (0,1))
);
CREATE TABLE IF NOT EXISTS orders (
  order_id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id INTEGER REFERENCES customers(customer_id) ON DELETE SET NULL,
  employee_id INTEGER NOT NULL REFERENCES employees(employee_id) ON DELETE RESTRICT,
  ordered_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  order_type TEXT NOT NULL CHECK (order_type IN ('ทานที่ร้าน','กลับบ้าน')),
  status TEXT NOT NULL DEFAULT 'รับออเดอร์' CHECK (status IN ('รับออเดอร์','กำลังทำ','เสร็จแล้ว','ยกเลิก')),
  note TEXT
);
CREATE TABLE IF NOT EXISTS order_items (
  order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
  menu_id INTEGER NOT NULL REFERENCES menu_items(menu_id) ON DELETE RESTRICT,
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  unit_price NUMERIC NOT NULL CHECK (unit_price >= 0),
  item_note TEXT
);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_employee ON orders(employee_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
