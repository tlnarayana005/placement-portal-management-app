import os

from app import create_app
from app.extensions import db
from seed_admin import seed_admin


def main():
    # Ensure DB tables exist before starting API.
    app = create_app()
    with app.app_context():
        db.create_all()

        # Create the single admin user (no admin registration allowed).
        seed_admin()

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    app.run(host=host, port=port, debug=True)


if __name__ == "__main__":
    main()

