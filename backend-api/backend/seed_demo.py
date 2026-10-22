"""Idempotent synthetic demonstration data, not research ground truth."""
import os
from datetime import datetime, timedelta
from database import Base, engine, SessionLocal
import models
import extended_models as ex
from auth import hash_password
from services.prediction_service import predict_for_review

PASSWORD=os.environ.get('DEMO_PASSWORD', '')


def main():
    if len(PASSWORD)<8:
        raise RuntimeError("Set DEMO_PASSWORD locally (at least 8 characters) before creating synthetic accounts.")
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        users={}
        for name,role in [('admin','admin'),('seller','seller'),('buyer','buyer'),('engineer','engineer'),('demo_account_a','buyer'),('demo_account_b','buyer')]:
            email=f'{name}@example.com'
            user=db.query(models.User).filter_by(email=email).first()
            if not user:
                user=models.User(email=email,role=role,password_hash=hash_password(PASSWORD));db.add(user);db.flush()
            users[name]=user
            if not db.get(ex.Profile,user.id):db.add(ex.Profile(user_id=user.id,display_name=name,shop_name='Demo Electronics' if role=='seller' else ''))
        db.commit()
        products=[]
        for i,name in enumerate(['USB-C Cable','Wireless Headphones','Laptop Stand'],1):
            code=f'DEMO-SIMULATED-{i}'
            product=db.query(models.Product).filter_by(product_code=code).first()
            if not product:
                product=models.Product(product_code=code,name=name,price=150000*i,category='Electronics',description='Synthetic demonstration product.',shop_id=users['seller'].id)
                db.add(product);db.flush();db.add(ex.ProductExtra(product_id=product.id,stock=30,canonical_key=f'demo-{i}'))
            products.append(product)
        if not db.query(ex.Category).filter_by(name='Electronics').first():db.add(ex.Category(name='Electronics'))
        db.commit()
        for product in products:
            for name in ['buyer','demo_account_a','demo_account_b']:
                user=users[name]
                if db.query(models.Review).filter_by(product_id=product.id,user_id=user.id).first():continue
                content='Amazing product buy it now amazing product' if name.startswith('demo_account') else f'I used this {product.name.lower()} for two months. The package included a manual and one adapter.'
                review=models.Review(product_id=product.id,user_id=user.id,rating=5 if name.startswith('demo_account') else 3,content=content,created_at=datetime(2026,10,1,10,products.index(product)))
                db.add(ex.Purchase(user_id=user.id,product_id=product.id,status='completed',quantity=1))
                db.add(review);db.commit();db.refresh(review);predict_for_review(db,review)
        if not db.query(ex.Content).first():
            db.add(ex.Content(kind='faq',title='Điểm đáng ngờ có ý nghĩa gì?',body='Đây là kết quả mô hình và các tín hiệu để kiểm tra, không chứng minh chắc chắn gian lận. Dữ liệu demo được mô phỏng.'))
        db.commit()
    print('Created synthetic demo data. Password supplied via DEMO_PASSWORD; it is not printed.')


if __name__=='__main__':main()
