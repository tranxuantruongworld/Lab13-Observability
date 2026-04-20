import json
from sqlmodel import Session, create_engine, select
from app.models import Order, OrderStatus, SQLModel

sqlite_file_name = 'database.db'
sqlite_url = f'sqlite:///{sqlite_file_name}'
engine = create_engine(sqlite_url)

def seed_orders():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        with open('data/sample_queries.jsonl', 'r') as f:
            lines = f.readlines()
        
        emails_seen = set()
        order_counter = 100
        
        for line in lines:
            query = json.loads(line)
            email = query['customer_email']
            category = query['category']
            content = query['content'].lower()
            
            if email in emails_seen:
                continue
            emails_seen.add(email)
            
            # Skip spam for orders
            if category == 'spam':
                continue
            
            order_id = f'ORD-{order_counter}'
            order_counter += 1
            
            # Determine items based on content
            if 'rtx 3050' in content:
                items = 'NVIDIA RTX 3050'
                amount = 299.99
            elif 'webcam' in content:
                items = 'Logitech HD Webcam'
                amount = 69.99
            elif 'arduino' in content:
                items = 'Arduino Nano'
                amount = 15.00
            elif 'esp32' in content:
                items = 'ESP32-S3-CAM'
                amount = 25.00
            elif 'color' in content:
                items = 'T-Shirt (Red)'
                amount = 19.99
            elif 'delivery' in content:
                items = 'Mechanical Keyboard'
                amount = 89.00
            else:
                items = 'Technical Support Subscription'
                amount = 49.00
            
            # Check if order already exists
            existing = session.exec(select(Order).where(Order.customer_email == email)).first()
            if not existing:
                order = Order(
                    id=order_id,
                    customer_email=email,
                    total_amount=amount,
                    status=OrderStatus.DELIVERED if category != 'refund' else OrderStatus.SHIPPED,
                    items=items
                )
                session.add(order)
                print(f"Adding order {order_id} for {email}")
        
        session.commit()

if __name__ == '__main__':
    seed_orders()
