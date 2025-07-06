#!/usr/bin/env python3
"""
Simplified application runner for Alpha Ultimate Workdesk
"""
import os
from app_fast import app
import routes_minimal

# Ensure admin user exists
def create_admin_if_not_exists():
    with app.app_context():
        from models import User
        from app_fast import db
        
        try:
            admin_user = User.query.filter_by(username='MShaonH').first()
            if not admin_user:
                admin_user = User(
                    username='MShaonH',
                    email='admin@workdesk.com',
                    phone='',
                    is_admin=True
                )
                admin_user.set_password('BadSoul@1989')
                db.session.add(admin_user)
                db.session.commit()
                print("Admin user created successfully")
        except Exception as e:
            db.session.rollback()
            print(f"Admin user setup: {e}")

if __name__ == "__main__":
    create_admin_if_not_exists()
    app.run(host="0.0.0.0", port=5000, debug=False)