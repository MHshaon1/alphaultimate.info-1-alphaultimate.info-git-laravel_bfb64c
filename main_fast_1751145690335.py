from app_fast import app
import routes_minimal as routes  # Import routes after app creation

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)