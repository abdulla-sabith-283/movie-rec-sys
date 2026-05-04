from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from database import db, Movie, Rating, Watchlist, History
from sqlalchemy import func

movies_bp = Blueprint('movies', __name__)

def movie_to_dict(movie, user_id=None):
    avg_rating = db.session.query(func.avg(Rating.score)).filter_by(movie_id=movie.movie_id).scalar()
    in_watchlist = False
    in_history = False
    if user_id:
        in_watchlist = Watchlist.query.filter_by(user_id=user_id, movie_id=movie.movie_id).first() is not None
        in_history = History.query.filter_by(user_id=user_id, movie_id=movie.movie_id).first() is not None
    return {
        'id': movie.movie_id,
        'title': movie.title,
        'genre': movie.genre,
        'language': movie.language,
        'release_year': movie.release_year,
        'tmdb_rating': movie.tmdb_rating,
        'poster_url': movie.poster_url,
        'synopsis': movie.synopsis,
        'cast': movie.cast,
        'director': movie.director,
        'streaming_platforms': movie.streaming_platforms,
        'mood_tags': movie.mood_tags,
        'avg_user_rating': round(avg_rating, 1) if avg_rating else None,
        'in_watchlist': in_watchlist,
        'in_history': in_history,
    }

@movies_bp.route('/', methods=['GET'])
def get_movies():
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        if uid:
            user_id = int(uid)
    except Exception:
        pass

    genre = request.args.get('genre')
    language = request.args.get('language')
    year = request.args.get('year')
    mood = request.args.get('mood')
    search = request.args.get('search')
    sort = request.args.get('sort', 'rating')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 12))

    query = Movie.query
    if genre:
        query = query.filter(Movie.genre.ilike(f'%{genre}%'))
    if language:
        query = query.filter(Movie.language == language)
    if year:
        query = query.filter(Movie.release_year == int(year))
    if mood:
        query = query.filter(Movie.mood_tags.ilike(f'%{mood}%'))
    if search:
        query = query.filter(Movie.title.ilike(f'%{search}%'))
    if sort == 'rating':
        query = query.order_by(Movie.tmdb_rating.desc())
    elif sort == 'year':
        query = query.order_by(Movie.release_year.desc())
    elif sort == 'title':
        query = query.order_by(Movie.title.asc())

    total = query.count()
    movies = query.offset((page - 1) * per_page).limit(per_page).all()
    return jsonify({
        'movies': [movie_to_dict(m, user_id) for m in movies],
        'total': total,
        'page': page,
        'pages': (total + per_page - 1) // per_page
    })

@movies_bp.route('/<int:movie_id>', methods=['GET'])
def get_movie(movie_id):
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        if uid:
            user_id = int(uid)
    except Exception:
        pass

    movie = Movie.query.get_or_404(movie_id)
    data = movie_to_dict(movie, user_id)

    reviews = Rating.query.filter_by(movie_id=movie_id, is_flagged=False).order_by(Rating.created_at.desc()).limit(10).all()
    data['reviews'] = [{
        'id': r.rating_id,
        'score': r.score,
        'review': r.review,
        'user_name': r.user.name,
        'created_at': r.created_at.isoformat()
    } for r in reviews]

    similar = Movie.query.filter(
        Movie.genre.ilike(f'%{movie.genre.split(",")[0].strip()}%'),
        Movie.movie_id != movie_id
    ).order_by(Movie.tmdb_rating.desc()).limit(6).all()
    data['similar_movies'] = [movie_to_dict(m, user_id) for m in similar]

    if user_id:
        existing = History.query.filter_by(user_id=user_id, movie_id=movie_id).first()
        if not existing:
            h = History(user_id=user_id, movie_id=movie_id)
            db.session.add(h)
            db.session.commit()

    return jsonify(data)

@movies_bp.route('/genres', methods=['GET'])
def get_genres():
    movies = Movie.query.all()
    genres = set()
    for m in movies:
        for g in m.genre.split(','):
            genres.add(g.strip())
    return jsonify(sorted(list(genres)))

@movies_bp.route('/moods', methods=['GET'])
def get_moods():
    return jsonify(['Happy', 'Thriller', 'Romantic', 'Sad', 'Action', 'Family', 'Horror', 'Comedy'])
