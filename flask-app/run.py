from app import create_app
import os

app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], port=int(os.getenv("PORT", 5000)), use_reloader=False)
