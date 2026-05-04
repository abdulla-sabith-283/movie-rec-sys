from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db, History, Movie

history_bp = Blueprint('history', __name__)

@history_bp.route('/', methods=['GET'])
@jwt_required()
def get_history():
    user_id = int(get_jwt_identity())
    entries = History.query.filter_by(user_id=user_id).order_by(History.watched_at.desc()).all()
    seen = set()
    result = []
    for e in entries:
        if e.movie_id in seen:
            continue
        seen.add(e.movie_id)
        m = e.movie
        result.append({
            'history_id': e.history_id,
            'movie': {
                'id': m.movie_id,
                'title': m.title,
                'genre': m.genre,
                'release_year': m.release_year,
                'tmdb_rating': m.tmdb_rating,
                'poster_url': m.poster_url,
                'synopsis': m.synopsis,
            },
            'watched_at': e.watched_at.isoformat()
        })
    return jsonify(result)

@history_bp.route('/mark-watched', methods=['POST'])
@jwt_required()
def mark_watched():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    movie_id = data.get('movie_id')
    if not movie_id:
        return jsonify({'error': 'movie_id required'}), 400
    existing = History.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if existing:
        return jsonify({'message': 'Already marked as watched'})
    h = History(user_id=user_id, movie_id=movie_id)
    db.session.add(h)
    db.session.commit()
    return jsonify({'message': 'Marked as watched'}), 201
