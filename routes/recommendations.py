from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db, Movie, Rating, History, Watchlist
from sqlalchemy import func

recommendations_bp = Blueprint('recommendations', __name__)

def genre_based_recommendations(user_id, limit=10):
    rated = db.session.query(Rating.movie_id).filter_by(user_id=user_id).all()
    watched = db.session.query(History.movie_id).filter_by(user_id=user_id).all()
    seen_ids = set([r[0] for r in rated] + [h[0] for h in watched])

    if not seen_ids:
        movies = Movie.query.order_by(Movie.tmdb_rating.desc()).limit(limit).all()
        return movies, 'popular'

    genres = set()
    for movie_id in seen_ids:
        m = Movie.query.get(movie_id)
        if m:
            for g in m.genre.split(','):
                genres.add(g.strip())

    candidates = Movie.query.filter(
        ~Movie.movie_id.in_(seen_ids)
    ).all()

    scored = []
    for m in candidates:
        score = 0
        for g in m.genre.split(','):
            if g.strip() in genres:
                score += 1
        score += m.tmdb_rating / 10
        scored.append((m, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [m for m, s in scored[:limit]], 'genre-based'

def mood_based_recommendations(mood, user_id=None, limit=10):
    mood_genre_map = {
        'Happy': 'Comedy',
        'Thriller': 'Thriller',
        'Romantic': 'Romance',
        'Sad': 'Drama',
        'Action': 'Action',
        'Family': 'Family',
        'Horror': 'Horror',
        'Comedy': 'Comedy'
    }
    genre = mood_genre_map.get(mood, mood)
    movies = Movie.query.filter(
        Movie.genre.ilike(f'%{genre}%') | Movie.mood_tags.ilike(f'%{mood}%')
    ).order_by(Movie.tmdb_rating.desc()).limit(limit).all()
    return movies

@recommendations_bp.route('/', methods=['GET'])
@jwt_required()
def get_recommendations():
    user_id = int(get_jwt_identity())
    mood = request.args.get('mood')

    if mood:
        movies = mood_based_recommendations(mood, user_id)
        algo = 'mood-based'
    else:
        movies, algo = genre_based_recommendations(user_id)

    return jsonify({
        'algorithm': algo,
        'recommendations': [{
            'id': m.movie_id,
            'title': m.title,
            'genre': m.genre,
            'release_year': m.release_year,
            'tmdb_rating': m.tmdb_rating,
            'poster_url': m.poster_url,
            'synopsis': m.synopsis,
            'mood_tags': m.mood_tags,
        } for m in movies]
    })

@recommendations_bp.route('/popular', methods=['GET'])
def get_popular():
    limit = int(request.args.get('limit', 10))
    movies = Movie.query.order_by(Movie.tmdb_rating.desc()).limit(limit).all()
    return jsonify([{
        'id': m.movie_id,
        'title': m.title,
        'genre': m.genre,
        'release_year': m.release_year,
        'tmdb_rating': m.tmdb_rating,
        'poster_url': m.poster_url,
        'synopsis': m.synopsis,
    } for m in movies])
