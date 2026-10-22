"""External adapters are inactive until the owner configures credentials."""
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from fastapi import HTTPException
import httpx
import extended_models as ex


def firebase_app():
    project=os.getenv('FIREBASE_PROJECT_ID')
    if not project:raise HTTPException(503,'Chưa cấu hình Firebase cho đăng nhập ngoài hoặc thông báo đẩy.')
    try:
        import firebase_admin
        try:return firebase_admin.get_app()
        except ValueError:return firebase_admin.initialize_app(options={'projectId':project})
    except ImportError as exc:
        raise HTTPException(503,'Cài requirements-integrations.txt để dùng Firebase.') from exc


def verify_firebase(token):
    app=firebase_app()
    from firebase_admin import auth
    try:return auth.verify_id_token(token,app=app,check_revoked=True)
    except Exception as exc:raise HTTPException(401,'Không xác minh được danh tính bên ngoài.') from exc


def queue_alert(db,user_id,message):
    import models
    preference=db.get(ex.Preference,user_id)
    if not preference:return
    user=db.get(models.User,user_id);profile=db.get(ex.Profile,user_id)
    if preference.email_enabled:
        db.add(ex.Outbox(channel='email',recipient=user.email,payload=json.dumps({'message':message})))
    if preference.sms_enabled and profile and profile.phone:
        db.add(ex.Outbox(channel='sms',recipient=profile.phone,payload=json.dumps({'message':message})))
    if preference.push_enabled:
        for device in db.query(ex.Device).filter_by(user_id=user_id):
            db.add(ex.Outbox(channel='push',recipient=device.token,payload=json.dumps({'message':message})))


def deliver(row):
    payload=json.loads(row.payload)
    message=payload.get('message','')
    if payload.get('kind')=='password_reset':
        base=os.getenv('FRONTEND_URL','http://127.0.0.1:5173')
        message=f"Khôi phục mật khẩu (hết hạn sau 15 phút): {base}/reset-password?token={payload['token']}"
    if row.channel=='email':
        host=os.environ['SMTP_HOST'];port=int(os.getenv('SMTP_PORT','587'))
        mail=EmailMessage();mail['From']=os.environ['SMTP_FROM'];mail['To']=row.recipient;mail['Subject']='Fake Review Detection';mail.set_content(message)
        with smtplib.SMTP(host,port,timeout=15) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            if os.getenv('SMTP_USER'):smtp.login(os.environ['SMTP_USER'],os.environ['SMTP_PASSWORD'])
            smtp.send_message(mail)
    elif row.channel=='push':
        from firebase_admin import messaging
        messaging.send(messaging.Message(token=row.recipient,notification=messaging.Notification(title='Cảnh báo review',body=message)),app=firebase_app())
    elif row.channel=='sms':
        sid=os.environ['TWILIO_ACCOUNT_SID']
        response=httpx.post(f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json',auth=(sid,os.environ['TWILIO_AUTH_TOKEN']),
            data={'From':os.environ['TWILIO_FROM'],'To':row.recipient,'Body':message},timeout=15)
        response.raise_for_status()
    else:raise ValueError('Unsupported channel')
