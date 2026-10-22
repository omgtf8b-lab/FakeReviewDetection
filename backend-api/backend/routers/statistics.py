from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user,require_roles
from services.labels import current_label
import models,schemas

router=APIRouter(prefix='/api/statistics',tags=['Thống kê'])


def counts(query):
    total=query.count()
    fake=query.filter(current_label()=='fake').count()
    real=query.filter(current_label()=='real').count()
    return total,fake,real,total-fake-real,round(fake/total*100,2) if total else 0


@router.get('/overview',response_model=schemas.StatisticsOverview)
def overview(db:Session=Depends(get_db),user=Depends(require_roles('admin','engineer'))):
    total,fake,real,pending,ratio=counts(db.query(models.Review))
    return dict(total_users=db.query(models.User).count(),total_products=db.query(models.Product).count(),total_reviews=total,
        total_predictions=db.query(models.Prediction).count(),fake_reviews=fake,real_reviews=real,pending_reviews=pending,fake_percentage=ratio)


@router.get('/me',response_model=schemas.MyStatisticsOverview)
def mine(db:Session=Depends(get_db),user=Depends(get_current_user)):
    total,fake,real,pending,ratio=counts(db.query(models.Review).filter_by(user_id=user.id))
    predictions=db.query(models.Prediction).join(models.Review).filter(models.Review.user_id==user.id).count()
    return dict(total_products=db.query(models.Product).count(),my_reviews=total,my_predictions=predictions,my_fake_reviews=fake,
        my_real_reviews=real,my_pending_reviews=pending,my_fake_percentage=ratio)


@router.get('/products/{pid}',response_model=schemas.ProductStatistics)
def product(pid:int,db:Session=Depends(get_db)):
    if not db.get(models.Product,pid):raise HTTPException(404,'Không tìm thấy sản phẩm')
    total,fake,real,pending,ratio=counts(db.query(models.Review).filter_by(product_id=pid))
    rating=db.query(func.avg(models.Review.rating)).filter_by(product_id=pid).scalar() or 0
    return dict(product_id=pid,total_reviews=total,fake_reviews=fake,real_reviews=real,average_rating=round(float(rating),2),fake_percentage=ratio)
