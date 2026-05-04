from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db, User, Movie, Rating
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

def require_admin():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    return user and user.is_admin, user

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    is_admin, user = require_admin()
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    total_users = User.query.count()
    total_movies = Movie.query.count()
    total_ratings = Rating.query.count()
    flagged_reviews = Rating.query.filter_by(is_flagged=True).count()
    avg_rating = db.session.query(func.avg(Rating.score)).scalar()

    return jsonify({
        'total_users': total_users,
        'total_movies': total_movies,
        'total_ratings': total_ratings,
        'flagged_reviews': flagged_reviews,
        'avg_rating': round(avg_rating, 2) if avg_rating else 0
    })

@admin_bp.route('/reviews', methods=['GET'])
@jwt_required()
def get_all_reviews():
    is_admin, _ = require_admin()
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    reviews = Rating.query.order_by(Rating.created_at.desc()).limit(50).all()
    return jsonify([{
        'id': r.rating_id,
        'user_name': r.user.name,
        'movie_title': r.movie.title,
        'score': r.score,
        'review': r.review,
        'is_flagged': r.is_flagged,
        'created_at': r.created_at.isoformat()
    } for r in reviews])

@admin_bp.route('/reviews/<int:rating_id>/flag', methods=['POST'])
@jwt_required()
def flag_review(rating_id):
    is_admin, _ = require_admin()
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    rating = Rating.query.get_or_404(rating_id)
    rating.is_flagged = not rating.is_flagged
    db.session.commit()
    return jsonify({'message': 'Review flag toggled', 'is_flagged': rating.is_flagged})

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    is_admin, _ = require_admin()
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([{
        'id': u.user_id,
        'name': u.name,
        'email': u.email,
        'is_admin': u.is_admin,
        'created_at': u.created_at.isoformat()
    } for u in users])

@admin_bp.route('/movies', methods=['POST'])
@jwt_required()
def add_movie():
    is_admin, _ = require_admin()
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    movie = Movie(
        title=data.get('title'),
        genre=data.get('genre', ''),
        language=data.get('language', 'en'),
        release_year=data.get('release_year'),
        tmdb_rating=data.get('tmdb_rating', 0.0),
        poster_url=data.get('poster_url', ''),
        synopsis=data.get('synopsis', ''),
        cast=data.get('cast', ''),
        director=data.get('director', ''),
        streaming_platforms=data.get('streaming_platforms', ''),
        mood_tags=data.get('mood_tags', '')
    )
    db.session.add(movie)
    db.session.commit()
    return jsonify({'message': 'Movie added', 'movie_id': movie.movie_id}), 201
