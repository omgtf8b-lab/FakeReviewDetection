import argparse
from sqlalchemy.orm import Session
import models
from auth import hash_password
from database import SessionLocal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", default="admin@example.com")
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    db: Session = SessionLocal()
    try:
        existing = db.query(models.User).filter(models.User.email == args.email.lower()).first()
        if existing:
            existing.role = "admin"
            existing.password_hash = hash_password(args.password)
        else:
            db.add(models.User(email=args.email.lower(), password_hash=hash_password(args.password), role="admin"))
        db.commit()
        print(f"Admin ready: {args.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
