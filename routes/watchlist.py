from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db, Watchlist, Movie
from sqlalchemy import func

watchlist_bp = Blueprint('watchlist', __name__)

@watchlist_bp.route('/', methods=['GET'])
@jwt_required()
def get_watchlist():
    user_id = int(get_jwt_identity())
    entries = Watchlist.query.filter_by(user_id=user_id).order_by(Watchlist.created_at.desc()).all()
    result = []
    for e in entries:
        m = e.movie
        result.append({
            'watchlist_id': e.watchlist_id,
            'movie': {
                'id': m.movie_id,
                'title': m.title,
                'genre': m.genre,
                'release_year': m.release_year,
                'tmdb_rating': m.tmdb_rating,
                'poster_url': m.poster_url,
                'synopsis': m.synopsis,
            },
            'added_at': e.created_at.isoformat()
        })
    return jsonify(result)

@watchlist_bp.route('/add', methods=['POST'])
@jwt_required()
def add_to_watchlist():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    movie_id = data.get('movie_id')
    if not movie_id:
        return jsonify({'error': 'movie_id required'}), 400
    if not Movie.query.get(movie_id):
        return jsonify({'error': 'Movie not found'}), 404
    existing = Watchlist.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if existing:
        return jsonify({'message': 'Already in watchlist'}), 200
    entry = Watchlist(user_id=user_id, movie_id=movie_id)
    db.session.add(entry)
    db.session.commit()
    return jsonify({'message': 'Added to watchlist', 'watchlist_id': entry.watchlist_id}), 201

@watchlist_bp.route('/remove/<int:movie_id>', methods=['DELETE'])
@jwt_required()
def remove_from_watchlist(movie_id):
    user_id = int(get_jwt_identity())
    entry = Watchlist.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if not entry:
        return jsonify({'error': 'Not in watchlist'}), 404
    db.session.delete(entry)
    db.session.commit()
    return jsonify({'message': 'Removed from watchlist'})
