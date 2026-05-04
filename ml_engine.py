import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
import logging

logger = logging.getLogger(__name__)


# ── Content-Based Filtering ────────────────────────────────────────────────────

def build_content_features(movies):
    """
    Build a TF-IDF feature matrix from movie metadata.
    Combines genre, cast, director, synopsis, and mood_tags
    with genre/director weighted higher by repetition.
    """
    corpus = []
    for m in movies:
        parts = []
        genre = (m.genre or '').replace(',', ' ')
        parts.append((genre + ' ') * 3)
        director = (m.director or '').replace(',', ' ')
        parts.append((director + ' ') * 2)
        cast = (m.cast or '').replace(',', ' ')
        parts.append(cast)
        synopsis = m.synopsis or ''
        parts.append(synopsis)
        mood = (m.mood_tags or '').replace(',', ' ')
        parts.append((mood + ' ') * 2)
        corpus.append(' '.join(parts).lower())

    vectorizer = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),
        max_features=5000,
        min_df=1
    )
    tfidf_matrix = vectorizer.fit_transform(corpus)
    return tfidf_matrix, vectorizer


def content_based_recommend(target_movie_ids, all_movies, top_n=10, exclude_ids=None):
    """
    Given a list of movie IDs the user has interacted with,
    recommend movies using content-based filtering (TF-IDF cosine similarity).
    Returns list of (movie, score) sorted by score desc.
    """
    if not all_movies:
        return []

    exclude_ids = set(exclude_ids or [])
    exclude_ids.update(target_movie_ids)

    movie_id_to_idx = {m.movie_id: i for i, m in enumerate(all_movies)}
    tfidf_matrix, _ = build_content_features(all_movies)

    target_indices = [movie_id_to_idx[mid] for mid in target_movie_ids if mid in movie_id_to_idx]
    if not target_indices:
        return []

    target_vectors = tfidf_matrix[target_indices]
    sim_scores = cosine_similarity(target_vectors, tfidf_matrix)
    avg_scores = sim_scores.mean(axis=0)

    results = []
    for i, m in enumerate(all_movies):
        if m.movie_id in exclude_ids:
            continue
        score = float(avg_scores[i])
        rating_bonus = (m.tmdb_rating or 0) / 100.0
        results.append((m, score + rating_bonus))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]


def similar_movies_content(movie_id, all_movies, top_n=6):
    """
    Find movies similar to a given movie using content-based similarity.
    """
    if not all_movies:
        return []

    movie_id_to_idx = {m.movie_id: i for i, m in enumerate(all_movies)}
    if movie_id not in movie_id_to_idx:
        return []

    tfidf_matrix, _ = build_content_features(all_movies)
    idx = movie_id_to_idx[movie_id]
    sim_scores = cosine_similarity(tfidf_matrix[idx], tfidf_matrix).flatten()

    results = []
    for i, m in enumerate(all_movies):
        if m.movie_id == movie_id:
            continue
        results.append((m, float(sim_scores[i])))

    results.sort(key=lambda x: x[1], reverse=True)
    return [m for m, s in results[:top_n]]


# ── Collaborative Filtering ────────────────────────────────────────────────────

def build_user_item_matrix(ratings, user_ids, movie_ids):
    """
    Build a dense user-item rating matrix.
    Rows = users, Cols = movies, Values = rating scores (0 if not rated).
    """
    user_idx = {uid: i for i, uid in enumerate(user_ids)}
    movie_idx = {mid: j for j, mid in enumerate(movie_ids)}
    matrix = np.zeros((len(user_ids), len(movie_ids)), dtype=np.float32)
    for r in ratings:
        if r.user_id in user_idx and r.movie_id in movie_idx:
            matrix[user_idx[r.user_id]][movie_idx[r.movie_id]] = r.score
    return matrix


def collaborative_filter_recommend(target_user_id, ratings, all_movies, top_n=10, exclude_ids=None):
    """
    User-based collaborative filtering using cosine similarity.
    Finds similar users, then recommends movies they rated highly
    that the target user hasn't seen.
    Returns list of (movie, score).
    """
    exclude_ids = set(exclude_ids or [])

    all_user_ids = list({r.user_id for r in ratings})
    all_movie_ids = [m.movie_id for m in all_movies]
    movie_id_to_obj = {m.movie_id: m for m in all_movies}

    if target_user_id not in all_user_ids or len(all_user_ids) < 2:
        return []

    matrix = build_user_item_matrix(ratings, all_user_ids, all_movie_ids)
    user_idx = {uid: i for i, uid in enumerate(all_user_ids)}
    movie_idx = {mid: j for j, mid in enumerate(all_movie_ids)}

    target_vec = matrix[user_idx[target_user_id]].reshape(1, -1)

    # Similarity of target user vs all users
    sims = cosine_similarity(target_vec, matrix).flatten()
    sims[user_idx[target_user_id]] = 0  # exclude self

    # Weighted average of other users' ratings
    weighted_scores = np.zeros(len(all_movie_ids), dtype=np.float64)
    sim_sum = np.zeros(len(all_movie_ids), dtype=np.float64)

    for uid, i in user_idx.items():
        if uid == target_user_id:
            continue
        sim = float(sims[i])
        if sim <= 0:
            continue
        weighted_scores += sim * matrix[i]
        sim_sum += sim * (matrix[i] > 0).astype(np.float64)

    sim_sum[sim_sum == 0] = 1
    pred_scores = weighted_scores / sim_sum

    # Movies the user has already rated/watched
    user_rated = {r.movie_id for r in ratings if r.user_id == target_user_id}
    exclude_ids.update(user_rated)

    results = []
    for mid, j in movie_idx.items():
        if mid in exclude_ids:
            continue
        m = movie_id_to_obj.get(mid)
        if not m:
            continue
        score = float(pred_scores[j])
        tmdb_bonus = (m.tmdb_rating or 0) / 100.0
        results.append((m, score + tmdb_bonus))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]


# ── Hybrid Recommender ─────────────────────────────────────────────────────────

def hybrid_recommend(user_id, ratings, history, all_movies, top_n=10):
    """
    Hybrid recommender:
    - Uses collaborative filtering if user has >= 3 ratings.
    - Uses content-based if user has interaction history.
    - Blends both when enough data exists.
    - Falls back to popularity when cold-start.

    Returns: (movies_list, algorithm_label)
    """
    user_ratings = [r for r in ratings if r.user_id == user_id]
    user_history = [h for h in history if h.user_id == user_id]

    interacted_ids = list({r.movie_id for r in user_ratings} | {h.movie_id for h in user_history})
    exclude_ids = set(interacted_ids)

    has_ratings = len(user_ratings) >= 3
    has_history = len(interacted_ids) >= 1
    has_other_users = len({r.user_id for r in ratings if r.user_id != user_id}) >= 2

    movie_id_to_obj = {m.movie_id: m for m in all_movies}

    # Cold start — return popular movies
    if not has_history:
        popular = sorted(all_movies, key=lambda m: m.tmdb_rating or 0, reverse=True)
        return popular[:top_n], 'popular'

    # Content-based only (not enough other users for CF)
    if has_history and (not has_ratings or not has_other_users):
        results = content_based_recommend(interacted_ids, all_movies, top_n=top_n, exclude_ids=exclude_ids)
        movies = [m for m, s in results]
        return movies, 'content-based'

    # Collaborative filtering only
    if has_ratings and has_other_users and not has_history:
        results = collaborative_filter_recommend(user_id, ratings, all_movies, top_n=top_n, exclude_ids=exclude_ids)
        movies = [m for m, s in results]
        return movies if movies else _fallback(all_movies, exclude_ids, top_n), 'collaborative'

    # Hybrid: blend CF + content-based scores
    cf_results = collaborative_filter_recommend(user_id, ratings, all_movies, top_n=top_n * 2, exclude_ids=exclude_ids)
    cb_results = content_based_recommend(interacted_ids, all_movies, top_n=top_n * 2, exclude_ids=exclude_ids)

    # Normalise scores into [0,1] range and blend 60% CF + 40% CB
    cf_map = {m.movie_id: s for m, s in cf_results}
    cb_map = {m.movie_id: s for m, s in cb_results}

    all_candidate_ids = set(cf_map) | set(cb_map)

    cf_max = max(cf_map.values(), default=1) or 1
    cb_max = max(cb_map.values(), default=1) or 1

    blended = []
    for mid in all_candidate_ids:
        m = movie_id_to_obj.get(mid)
        if not m:
            continue
        cf_score = (cf_map.get(mid, 0) / cf_max) * 0.6
        cb_score = (cb_map.get(mid, 0) / cb_max) * 0.4
        blended.append((m, cf_score + cb_score))

    blended.sort(key=lambda x: x[1], reverse=True)
    movies = [m for m, s in blended[:top_n]]

    algo = 'hybrid (CF + content-based)' if has_ratings else 'content-based'
    return movies if movies else _fallback(all_movies, exclude_ids, top_n), algo


def _fallback(all_movies, exclude_ids, top_n):
    return [m for m in sorted(all_movies, key=lambda m: m.tmdb_rating or 0, reverse=True) if m.movie_id not in exclude_ids][:top_n]


# ── Mood-Based ─────────────────────────────────────────────────────────────────

MOOD_GENRE_MAP = {
    'Happy':    ['Comedy', 'Animation', 'Family', 'Musical'],
    'Thriller': ['Thriller', 'Mystery', 'Crime'],
    'Romantic': ['Romance', 'Drama'],
    'Sad':      ['Drama', 'History'],
    'Action':   ['Action', 'Adventure', 'Sci-Fi'],
    'Family':   ['Family', 'Animation'],
    'Horror':   ['Horror'],
    'Comedy':   ['Comedy'],
}

def mood_recommend(mood, all_movies, top_n=10):
    """
    Return movies filtered by mood, then sorted by rating.
    Uses TF-IDF cosine similarity as a secondary rank within the mood bucket.
    """
    genres = MOOD_GENRE_MAP.get(mood, [mood])

    def matches_mood(m):
        m_genres = [g.strip().lower() for g in (m.genre or '').split(',')]
        m_mood = (m.mood_tags or '').lower()
        for g in genres:
            if g.lower() in m_genres or g.lower() in m_mood:
                return True
        return False

    mood_movies = [m for m in all_movies if matches_mood(m)]
    mood_movies.sort(key=lambda m: m.tmdb_rating or 0, reverse=True)
    return mood_movies[:top_n]
