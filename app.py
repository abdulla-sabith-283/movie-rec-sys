from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from database import db
import os

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'movie-rec-secret-key-2024')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-movie-rec-secret-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///moviedb.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
jwt = JWTManager(app)

from routes.auth import auth_bp
from routes.movies import movies_bp
from routes.watchlist import watchlist_bp
from routes.ratings import ratings_bp
from routes.recommendations import recommendations_bp
from routes.history import history_bp
from routes.admin import admin_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(movies_bp, url_prefix='/api/movies')
app.register_blueprint(watchlist_bp, url_prefix='/api/watchlist')
app.register_blueprint(ratings_bp, url_prefix='/api/ratings')
app.register_blueprint(recommendations_bp, url_prefix='/api/recommendations')
app.register_blueprint(history_bp, url_prefix='/api/history')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

with app.app_context():
    db.create_all()
    from seed import seed_data
    seed_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
