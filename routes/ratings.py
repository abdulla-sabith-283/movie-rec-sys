from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db, Rating, Movie

ratings_bp = Blueprint('ratings', __name__)

@ratings_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_rating():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    movie_id = data.get('movie_id')
    score = data.get('score')
    review = data.get('review', '')

    if not movie_id or score is None:
        return jsonify({'error': 'movie_id and score required'}), 400
    if not (1 <= int(score) <= 5):
        return jsonify({'error': 'Score must be between 1 and 5'}), 400
    if not Movie.query.get(movie_id):
        return jsonify({'error': 'Movie not found'}), 404

    existing = Rating.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if existing:
        existing.score = score
        existing.review = review
        db.session.commit()
        return jsonify({'message': 'Rating updated'})

    rating = Rating(user_id=user_id, movie_id=movie_id, score=score, review=review)
    db.session.add(rating)
    db.session.commit()
    return jsonify({'message': 'Rating submitted', 'rating_id': rating.rating_id}), 201

@ratings_bp.route('/movie/<int:movie_id>', methods=['GET'])
def get_movie_ratings(movie_id):
    ratings = Rating.query.filter_by(movie_id=movie_id, is_flagged=False).order_by(Rating.created_at.desc()).all()
    return jsonify([{
        'id': r.rating_id,
        'score': r.score,
        'review': r.review,
        'user_name': r.user.name,
        'created_at': r.created_at.isoformat()
    } for r in ratings])
