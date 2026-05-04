# MovieHub - Movie Recommendation System

A full-stack movie recommendation web application built with Flask (Python backend) and vanilla JavaScript/HTML/CSS frontend.

## Architecture

- **Backend**: Flask (Python) with SQLAlchemy ORM, JWT authentication
- **Frontend**: Vanilla JS/HTML/CSS (served as static files by Flask)
- **Database**: SQLite (`moviedb.sqlite3`) — auto-created on first run
- **Port**: 5000 (all interfaces `0.0.0.0`)

## Features

- User registration & login with JWT authentication (strong password validation)
- Browse movies with filters: genre, language, year, sort, mood
- Movie detail page with cast, synopsis, streaming platforms, similar movies
- Personalised recommendations (genre-based + mood-based)
- Watchlist management (add/remove)
- Watch history tracking
- Movie ratings & reviews (1-5 stars)
- Admin dashboard: stats, review moderation, user management

## Project Structure

```
app.py              # Flask app entry point
database.py         # SQLAlchemy models (User, Movie, Rating, Watchlist, History, Recommendation)
seed.py             # Seed data (20 movies + admin user)
routes/
  auth.py           # /api/auth/* — register, login, me
  movies.py         # /api/movies/* — browse, detail, genres
  watchlist.py      # /api/watchlist/* — add/remove/list
  ratings.py        # /api/ratings/* — submit rating
  history.py        # /api/history/* — view/mark watched
  recommendations.py # /api/recommendations/* — genre/mood-based
  admin.py          # /api/admin/* — stats, reviews, users
static/
  index.html        # Single-page app HTML
  style.css         # Dark theme CSS
  app.js            # Frontend JavaScript (SPA logic)
```

## Default Admin Credentials

- Email: `admin@moviehub.com`
- Password: `Admin@123`

## Running Locally

```bash
python3 app.py
```

## Deployment

Uses gunicorn:
```
gunicorn --bind=0.0.0.0:5000 --reuse-port app:app
```
