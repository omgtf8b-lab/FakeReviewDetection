import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, require_roles, create_access_token, hash_password
from services.providers import verify_firebase
import models
import schemas
import extended_models as ex

router=APIRouter(prefix='/api/integrations',tags=['Tích hợp dịch vụ'])


class ExternalInput(BaseModel):
    id_token:str=Field(min_length=20,max_length=10000)


@router.post('/firebase/login',response_model=schemas.TokenResponse)
def external_login(body:ExternalInput,db:Session=Depends(get_db)):
    claims=verify_firebase(body.id_token)
    uid=claims['uid'];identity=db.get(ex.ExternalIdentity,uid)
    if identity:user=db.get(models.User,identity.user_id)
    else:
        email=claims.get('email') if claims.get('email_verified') else None
        phone=claims.get('phone_number')
        if not email and not phone:raise HTTPException(400,'Cần email đã xác minh hoặc số điện thoại đã xác minh.')
        user=db.query(models.User).filter_by(email=email.lower()).first() if email else None
        if not user:
            address=email.lower() if email else f"phone-{hashlib.sha256(uid.encode()).hexdigest()[:24]}@phone.example.com"
            user=models.User(email=address,role='buyer',password_hash=hash_password(secrets.token_urlsafe(40)))
            db.add(user);db.flush()
        db.add(ex.ExternalIdentity(uid=uid,user_id=user.id))
        profile=db.get(ex.Profile,user.id) or ex.Profile(user_id=user.id)
        if phone:profile.phone=phone
        db.add(profile);db.commit();db.refresh(user)
    if not user or not user.is_active:raise HTTPException(403,'Tài khoản đã bị khóa')
    return {'access_token':create_access_token(user),'token_type':'bearer','expires_in':3600,'user':user}


class DeviceInput(BaseModel):
    token:str=Field(min_length=20,max_length=1024)


@router.put('/device')
def device(body:DeviceInput,db:Session=Depends(get_db),user=Depends(get_current_user)):
    row=db.get(ex.Device,body.token)
    if row and row.user_id!=user.id:raise HTTPException(409,'Thiết bị đang gắn với một tài khoản khác')
    if not row:db.add(ex.Device(token=body.token,user_id=user.id));db.commit()
    return {'message':'Đã đăng ký thiết bị'}


class PreferenceInput(BaseModel):
    email_enabled:bool=False
    sms_enabled:bool=False
    push_enabled:bool=False


@router.get('/preferences')
def preferences(db:Session=Depends(get_db),user=Depends(get_current_user)):
    row=db.get(ex.Preference,user.id)
    return {'email_enabled':bool(row and row.email_enabled),'sms_enabled':bool(row and row.sms_enabled),'push_enabled':bool(row and row.push_enabled)}


@router.put('/preferences')
def set_preferences(body:PreferenceInput,db:Session=Depends(get_db),user=Depends(get_current_user)):
    row=db.get(ex.Preference,user.id) or ex.Preference(user_id=user.id)
    for key,value in body.model_dump().items():setattr(row,key,value)
    db.add(row);db.commit();return body


@router.get('/outbox')
def outbox(db:Session=Depends(get_db),user=Depends(require_roles('admin'))):
    # Do not expose reset tokens or full device tokens through the dashboard.
    return [{'id':r.id,'channel':r.channel,'status':r.status,'created_at':r.created_at} for r in db.query(ex.Outbox).order_by(ex.Outbox.id.desc()).limit(100)]
