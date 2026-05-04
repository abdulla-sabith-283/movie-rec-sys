from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db, Movie, Rating, History
from ml_engine import hybrid_recommend, mood_recommend, similar_movies_content
import logging

logger = logging.getLogger(__name__)
recommendations_bp = Blueprint('recommendations', __name__)


def _movie_dict(m):
    return {
        'id': m.movie_id,
        'title': m.title,
        'genre': m.genre,
        'language': m.language,
        'release_year': m.release_year,
        'tmdb_rating': m.tmdb_rating,
        'poster_url': m.poster_url,
        'synopsis': m.synopsis,
        'mood_tags': m.mood_tags,
        'streaming_platforms': m.streaming_platforms,
    }


@recommendations_bp.route('/', methods=['GET'])
@jwt_required()
def get_recommendations():
    user_id = int(get_jwt_identity())
    mood = request.args.get('mood')

    all_movies = Movie.query.all()

    if mood:
        movies = mood_recommend(mood, all_movies)
        return jsonify({
            'algorithm': f'mood-based ({mood})',
            'algorithm_type': 'mood',
            'recommendations': [_movie_dict(m) for m in movies]
        })

    all_ratings = Rating.query.all()
    all_history = History.query.all()

    try:
        movies, algo = hybrid_recommend(
            user_id=user_id,
            ratings=all_ratings,
            history=all_history,
            all_movies=all_movies,
            top_n=12
        )
    except Exception as e:
        logger.error(f"ML recommendation error: {e}")
        movies = sorted(all_movies, key=lambda m: m.tmdb_rating or 0, reverse=True)[:12]
        algo = 'popular (fallback)'

    return jsonify({
        'algorithm': algo,
        'algorithm_type': _algo_type(algo),
        'recommendations': [_movie_dict(m) for m in movies]
    })


@recommendations_bp.route('/similar/<int:movie_id>', methods=['GET'])
def get_similar(movie_id):
    all_movies = Movie.query.all()
    try:
        similar = similar_movies_content(movie_id, all_movies, top_n=6)
    except Exception as e:
        logger.error(f"Similar movies error: {e}")
        similar = Movie.query.filter(Movie.movie_id != movie_id).order_by(Movie.tmdb_rating.desc()).limit(6).all()
    return jsonify([_movie_dict(m) for m in similar])


@recommendations_bp.route('/popular', methods=['GET'])
def get_popular():
    limit = int(request.args.get('limit', 10))
    movies = Movie.query.order_by(Movie.tmdb_rating.desc()).limit(limit).all()
    return jsonify([_movie_dict(m) for m in movies])


def _algo_type(algo):
    if 'hybrid' in algo:
        return 'hybrid'
    if 'collaborative' in algo:
        return 'collaborative'
    if 'content' in algo:
        return 'content'
    if 'mood' in algo:
        return 'mood'
    return 'popular'
