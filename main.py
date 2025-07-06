import logging
from app import app, db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def init_database():
    """Initialize database tables and admin user"""
    with app.app_context():
        try:
            # Import models to ensure tables are created
            import models  # noqa: F401
            db.create_all()
            
            # Create admin user if it doesn't exist
            from models import User
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User()
                admin_user.username = 'admin'
                admin_user.email = 'admin@workdesk.com'
                admin_user.phone = ''
                admin_user.is_admin = True
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                logging.info("Admin user created: username=admin, password=admin123")
                
            # Check service status
            from api_key_manager import APIKeyManager
            missing_keys = APIKeyManager.get_missing_keys()
            if missing_keys:
                for key in missing_keys:
                    logging.warning(f"{key} not found. Related functionality disabled.")
            else:
                logging.info("All external services configured and ready.")
                
        except Exception as e:
            db.session.rollback()
            logging.error(f"Database initialization error: {e}")

# Initialize database and import routes
init_database()
import routes  # Import routes after app and database setup

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
