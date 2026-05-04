from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ratings = db.relationship('Rating', backref='user', lazy=True)
    watchlist = db.relationship('Watchlist', backref='user', lazy=True)
    history = db.relationship('History', backref='user', lazy=True)

class Movie(db.Model):
    __tablename__ = 'movies'
    movie_id = db.Column(db.Integer, primary_key=True)
    tmdb_id = db.Column(db.Integer, unique=True, nullable=True)
    title = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(200), nullable=False)
    language = db.Column(db.String(50), default='en')
    release_year = db.Column(db.Integer)
    tmdb_rating = db.Column(db.Float, default=0.0)
    poster_url = db.Column(db.String(500))
    synopsis = db.Column(db.Text)
    cast = db.Column(db.Text)
    director = db.Column(db.String(200))
    streaming_platforms = db.Column(db.String(300))
    mood_tags = db.Column(db.String(200))

    ratings = db.relationship('Rating', backref='movie', lazy=True)
    watchlist_entries = db.relationship('Watchlist', backref='movie', lazy=True)
    history_entries = db.relationship('History', backref='movie', lazy=True)

class Rating(db.Model):
    __tablename__ = 'ratings'
    rating_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.movie_id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_flagged = db.Column(db.Boolean, default=False)

class Watchlist(db.Model):
    __tablename__ = 'watchlist'
    watchlist_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.movie_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class History(db.Model):
    __tablename__ = 'history'
    history_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.movie_id'), nullable=False)
    watched_at = db.Column(db.DateTime, default=datetime.utcnow)

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    rec_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.movie_id'), nullable=False)
    algorithm = db.Column(db.String(100), default='genre-based')
    score = db.Column(db.Float, default=0.0)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
