# News Data Service

A contextual news data retrieval system with LLM-powered insights, geospatial search, and trending news features.

## Features

- JWT-based authentication
- Category, source, and score-based filtering
- Full-text search with LLM entity extraction
- Geospatial nearby news search
- Trending news feed with user event simulation
- Redis caching for trending feeds
- Auto-generated API documentation (Swagger)

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15 with PostGIS
- **Cache**: Redis
- **LLM**: Google Gemini 1.5 Flash
- **Deployment**: Docker, Render.com, Neon.tech, Upstash

## Setup

### 1. Clone and Install

```bash
cd news-data-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your Google Gemini API key:
```
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Start Docker Services

```bash
docker-compose up -d
```

### 4. Copy News Data

```bash
mkdir -p data
cp /path/to/news_data.json data/
```

### 5. Ingest Data

```bash
python scripts/ingest_data.py
```

### 6. Run Application

```bash
uvicorn app.main:app --reload
```

API will be available at: http://localhost:8000

Swagger docs at: http://localhost:8000/docs

## API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - Create account
- `POST /api/v1/auth/login` - Login and get JWT token (returns token in response + sets refresh token cookie + Authorization header)
- `POST /api/v1/auth/refresh` - Get new access token using refresh token from cookie
- `POST /api/v1/auth/logout` - Clear refresh token cookie

### News Endpoints (Requires JWT)
- `GET /api/v1/news/category?category=Technology`
- `GET /api/v1/news/score?min_score=0.7`
- `GET /api/v1/news/source?source_name=Reuters`
- `GET /api/v1/news/search?query=Elon+Musk`
- `GET /api/v1/news/nearby?lat=37.42&lon=-122.08&radius=10`
- `GET /api/v1/news?category=Technology&min_score=0.7` (Unified)
- `GET /api/v1/news/trending?lat=37.42&lon=-122.08`

### Trending Simulation
- `POST /api/v1/news/trending/simulate-events?num_events=1000`

## Usage

1. **Signup**: Create account at `/api/v1/auth/signup`
2. **Login**: Get JWT token at `/api/v1/auth/login`
3. **Use Token**: Add `Authorization: Bearer <token>` header
4. **Simulate Events**: Run `/api/v1/news/trending/simulate-events`
5. **Query News**: Use any news endpoint

## Deployment

See deployment guides in `/docs` folder.
