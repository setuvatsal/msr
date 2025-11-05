import os
import random
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

app = FastAPI()

# Secret for session cookies - keep in env for production
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Database simulation (in production, use a real database)
users_db = {}
songs_db = []


def initialize_songs():
    if songs_db:
        return
    genres = [
        'Pop', 'Rock', 'Hip Hop', 'R&B', 'Electronic', 'Jazz', 'Classical', 'Country', 'Latin', 'Indie'
    ]
    moods = ['Happy', 'Sad', 'Energetic', 'Calm', 'Romantic', 'Emotional', 'Party', 'Chill']

    artists = [
        'The Weeknd', 'Taylor Swift', 'Drake', 'Billie Eilish', 'Ed Sheeran',
        'Ariana Grande', 'Post Malone', 'Dua Lipa', 'Justin Bieber', 'Olivia Rodrigo',
        'Harry Styles', 'BTS', 'Bad Bunny', 'The Beatles', 'Queen', 'Coldplay',
        'Imagine Dragons', 'Bruno Mars', 'Adele', 'Beyoncé', 'Eminem', 'Rihanna'
    ]

    song_titles = [
        'Memories', 'Dreams', 'Starlight', 'Echoes', 'Midnight', 'Sunrise',
        'Forever', 'Dancing', 'Heartbeat', 'Paradise', 'Waves', 'Fire',
        'Thunder', 'Lights', 'Shadow', 'Moments', 'Heaven', 'Alive',
        'Better', 'Perfect', 'Beautiful', 'Amazing', 'Wonder', 'Magic'
    ]

    preview_count = 50
    for i in range(2000):
        song = {
            'id': i + 1,
            'title': f"{random.choice(song_titles)} {random.choice(['Night', 'Day', 'Love', 'Soul', 'Beat', 'Vibe', ''])}".strip(),
            'artist': random.choice(artists),
            'genre': random.choice(genres),
            'mood': random.choice(moods),
            'duration': f"{random.randint(2, 5)}:{random.randint(10, 59):02d}",
            'album': f"Album {random.randint(1, 50)}",
            'year': random.randint(2015, 2024),
            'plays': random.randint(1000, 10000000)
        }
        # assign a small preview audio (one of a set of placeholders)
        song['preview'] = f"/static/previews/preview{(i % preview_count) + 1}.wav"
        songs_db.append(song)


def generate_preview_files():
    """Generate a set of WAV preview files in static/previews if they don't exist.
    Creates a number of short sine-wave WAVs so the player has local files to play.
    This produces a manageable number of small files (50 by default).
    """
    out_dir = os.path.join('static', 'previews')
    os.makedirs(out_dir, exist_ok=True)
    try:
        import wave
        import struct
        import math
        sample_rate = 22050
        duration_s = 1.6
        preview_count = 50
        # generate 50 different tones by varying frequency and amplitude
        for idx in range(preview_count):
            path = os.path.join(out_dir, f'preview{idx+1}.wav')
            if os.path.exists(path):
                continue
            # make frequency vary across range ~220..220+(idx*15)
            freq = 220.0 + (idx * 12.0)
            amp = 0.28 + ((idx % 6) * 0.02)
            frames = []
            total_frames = int(sample_rate * duration_s)
            for n in range(total_frames):
                t = n / sample_rate
                # gentle fade-in/out to avoid clicks
                envelope = 1.0
                fade_len = int(0.03 * sample_rate)
                if n < fade_len:
                    envelope = n / fade_len
                if n > total_frames - fade_len:
                    envelope = (total_frames - n) / fade_len
                value = amp * envelope * math.sin(2 * math.pi * freq * t)
                frames.append(int(max(min(value * 32767.0, 32767), -32768)))
            with wave.open(path, 'w') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(struct.pack('<' + ('h' * len(frames)), *frames))
    except Exception:
        # generation failures are non-fatal; player will fallback to remote audio
        pass


@app.on_event("startup")
def startup_event():
    initialize_songs()
    # generate local preview audio files for the player
    generate_preview_files()


@app.get("/", name="index")
async def index(request: Request):
    user_id = request.session.get('user_id')
    if not user_id:
        return RedirectResponse(url=request.url_for('login'))
    return RedirectResponse(url=request.url_for('home'))


@app.get('/login', name='login')
async def login_get(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})


@app.post('/login', name='login_post')
async def login_post(request: Request):
    form = await request.form()
    username = form.get('username')
    password = form.get('password')
    if username in users_db and users_db[username]['password'] == password:
        request.session['user_id'] = username
        return RedirectResponse(url=request.url_for('home'), status_code=303)
    return templates.TemplateResponse('login.html', {'request': request, 'error': 'Invalid credentials'})


@app.get('/register', name='register')
async def register_get(request: Request):
    return templates.TemplateResponse('register.html', {'request': request})


@app.post('/register', name='register_post')
async def register_post(request: Request):
    form = await request.form()
    username = form.get('username')
    password = form.get('password')
    email = form.get('email')
    if username in users_db:
        return templates.TemplateResponse('register.html', {'request': request, 'error': 'Username already exists'})
    users_db[username] = {
        'password': password,
        'email': email,
        'name': username,
        'bio': '',
        'favorite_genres': [],
        'favorite_moods': [],
        'playlists': []
    }
    request.session['user_id'] = username
    return RedirectResponse(url=request.url_for('home'), status_code=303)


@app.get('/logout', name='logout')
async def logout(request: Request):
    request.session.pop('user_id', None)
    return RedirectResponse(url=request.url_for('login'))


@app.get('/home', name='home')
async def home(request: Request):
    user_id = request.session.get('user_id')
    if not user_id:
        return RedirectResponse(url=request.url_for('login'))
    user = users_db.get(user_id, {})
    moods = ['Happy', 'Sad', 'Energetic', 'Calm', 'Romantic', 'Emotional', 'Party', 'Chill']
    mood_playlists = {}
    for mood in moods:
        mood_songs = [song for song in songs_db if song['mood'] == mood]
        mood_playlists[mood] = random.sample(mood_songs, min(20, len(mood_songs)))
    popular = sorted(songs_db, key=lambda x: x['plays'], reverse=True)[:20]
    recent = sorted(songs_db, key=lambda x: x['year'], reverse=True)[:20]
    # personalized "For you" row: prefer user's favorite genres/moods, fall back to popular
    for_you = []
    try:
        fav_genres = set(user.get('favorite_genres', []))
        fav_moods = set(user.get('favorite_moods', []))
        if fav_genres or fav_moods:
            candidates = [s for s in songs_db if (s['genre'] in fav_genres) or (s['mood'] in fav_moods)]
            # if not enough candidates, include popular to fill
            if len(candidates) < 12:
                extra = [s for s in popular if s not in candidates]
                candidates.extend(extra)
            random.shuffle(candidates)
            for_you = candidates[:12]
        else:
            # no user preferences — show a shuffled subset of popular
            tmp = popular.copy()
            random.shuffle(tmp)
            for_you = tmp[:12]
    except Exception:
        for_you = popular[:12]
    return templates.TemplateResponse('home.html', {
        'request': request,
        'user': user,
        'mood_playlists': mood_playlists,
        'popular': popular,
        'recent': recent,
        'for_you': for_you,
        'moods': moods
    })


@app.get('/profile', name='profile')
async def profile_get(request: Request):
    user_id = request.session.get('user_id')
    if not user_id:
        return RedirectResponse(url=request.url_for('login'))
    user = users_db.get(user_id)
    genres = list(set([song['genre'] for song in songs_db]))
    moods = list(set([song['mood'] for song in songs_db]))
    return templates.TemplateResponse('profile.html', {'request': request, 'user': user, 'genres': genres, 'moods': moods})


@app.post('/profile', name='profile_post')
async def profile_post(request: Request):
    user_id = request.session.get('user_id')
    if not user_id:
        return RedirectResponse(url=request.url_for('login'))
    form = await request.form()
    user = users_db[user_id]
    user['name'] = form.get('name', user_id)
    user['email'] = form.get('email', '')
    user['bio'] = form.get('bio', '')
    # FormData supports getlist for multiple inputs with same name
    user['favorite_genres'] = form.getlist('genres') if hasattr(form, 'getlist') else []
    user['favorite_moods'] = form.getlist('moods') if hasattr(form, 'getlist') else []
    return RedirectResponse(url=request.url_for('profile'), status_code=303)


@app.get('/recommendations', name='recommendations')
async def recommendations(request: Request):
    user_id = request.session.get('user_id')
    if not user_id:
        return RedirectResponse(url=request.url_for('login'))
    user = users_db.get(user_id, {})
    mood = request.query_params.get('mood', '')
    genre = request.query_params.get('genre', '')
    q = request.query_params.get('q', '').strip()
    recommended = songs_db.copy()
    if mood:
        recommended = [song for song in recommended if song['mood'] == mood]
    if genre:
        recommended = [song for song in recommended if song['genre'] == genre]
    # Support simple search by title or artist
    if q:
        q_low = q.lower()
        recommended = [song for song in recommended if q_low in song['title'].lower() or q_low in song['artist'].lower()]
    if user.get('favorite_genres') or user.get('favorite_moods'):
        priority_songs = [song for song in recommended if song['genre'] in user.get('favorite_genres', []) or song['mood'] in user.get('favorite_moods', [])]
        other_songs = [song for song in recommended if song not in priority_songs]
        recommended = priority_songs + other_songs
    random.shuffle(recommended)
    recommended = recommended[:50]
    # build lists for filter controls
    all_genres = sorted(list({s['genre'] for s in songs_db}))
    all_moods = sorted(list({s['mood'] for s in songs_db}))
    return templates.TemplateResponse('recommendations.html', {'request': request, 'songs': recommended, 'mood': mood, 'genre': genre, 'user': user, 'q': q, 'all_genres': all_genres, 'all_moods': all_moods})


@app.get('/playlist/{mood}', name='playlist')
async def playlist(request: Request, mood: str):
    user_id = request.session.get('user_id')
    if not user_id:
        return RedirectResponse(url=request.url_for('login'))
    mood_songs = [song for song in songs_db if song['mood'] == mood]
    random.shuffle(mood_songs)
    return templates.TemplateResponse('playlist.html', {'request': request, 'songs': mood_songs[:50], 'mood': mood, 'user': users_db.get(user_id)})


@app.get('/song/{song_id}', name='song')
async def song_page(request: Request, song_id: int):
    user_id = request.session.get('user_id')
    if not user_id:
        return RedirectResponse(url=request.url_for('login'))
    song = next((s for s in songs_db if s['id'] == song_id), None)
    if not song:
        return RedirectResponse(url=request.url_for('recommendations'))
    # increment plays (simple simulation)
    try:
        song['plays'] = int(song.get('plays', 0)) + 1
    except Exception:
        song['plays'] = 1

    # Build related recommendations: same genre, then same mood, then popular
    related = [s for s in songs_db if s['genre'] == song['genre'] and s['id'] != song_id]
    if len(related) < 10:
        extra = [s for s in songs_db if s['mood'] == song['mood'] and s['id'] != song_id and s not in related]
        related.extend(extra)
    if len(related) < 10:
        popular = [s for s in sorted(songs_db, key=lambda x: x['plays'], reverse=True) if s['id'] != song_id and s not in related]
        related.extend(popular)
    random.shuffle(related)
    related = related[:10]

    return templates.TemplateResponse('song.html', {'request': request, 'song': song, 'recs': related, 'user': users_db.get(user_id)})


if __name__ == '__main__':
    # Run on port 8001 to avoid conflicts with static "Go Live" servers
    uvicorn.run('music_rec_system:app', host='127.0.0.1', port=8001, reload=True)
