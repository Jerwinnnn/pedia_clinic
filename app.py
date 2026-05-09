from flask import Flask
from extensions import db, login_manager
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'
    login_manager.login_message = 'Please log in to access the admin panel.'

    from routes.client import client_bp
    from routes.admin import admin_bp
    app.register_blueprint(client_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    with app.app_context():
        from models import User  # import AFTER app context is pushed
        db.create_all()

        if not User.query.first():
            from werkzeug.security import generate_password_hash
            default_admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                full_name='Clinic Assistant'
            )
            db.session.add(default_admin)
            db.session.commit()
            print("Default admin created — username: admin / password: admin123")

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)