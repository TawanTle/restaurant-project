INSERT INTO employees(employee_name,role) VALUES ('คุณดาว','เจ้าของร้าน'),('คุณบอย','พ่อครัว');
INSERT INTO categories(category_name) VALUES ('ข้าว'),('เส้น'),('กับข้าว');
INSERT INTO customers(customer_name,phone) VALUES ('สมชาย ใจดี','0812345678'),('มาลี สดใส','0898765432');
INSERT INTO menu_items(category_id,menu_name,price) VALUES
 (1,'ข้าวกะเพราหมูสับ',55),(1,'ข้าวผัดหมู',50),(2,'ผัดซีอิ๊ว',60),(3,'ไข่เจียวหมูสับ',45);
INSERT INTO orders(customer_id,employee_id,order_type,status,note) VALUES (1,1,'กลับบ้าน','รับออเดอร์','ไม่เผ็ด');
INSERT INTO order_items(order_id,menu_id,quantity,unit_price,item_note) VALUES (1,1,2,55,'ไม่เผ็ด'),(1,4,1,45,NULL);
