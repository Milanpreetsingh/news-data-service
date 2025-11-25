# Quick Start Guide

## Current Status ✅

Your News Data Service is ready to run! Here's what's already set up:

- ✅ **Dependencies installed** (FastAPI, PostgreSQL driver, Redis, Google Gemini, etc.)
- ✅ **Docker containers running** (PostgreSQL + PostGIS, Redis)
- ✅ **Database created** with proper schemas (users, articles, user_events tables)
- ✅ **2000 news articles loaded** into PostgreSQL
- ✅ **All API code complete** (Authentication, News endpoints, Trending)

---

## Before You Start

### Get Google Gemini API Key (FREE)

1. Visit: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy your API key
4. Edit `.env` file:
   ```bash
   nano .env
   ```
5. Replace `your_google_gemini_api_key_here` with your actual key
6. Save and exit (Ctrl+X, then Y, then Enter)

---

## Start the Application

```bash
cd /Users/milanpreetsingh/Desktop/news-data-service
source venv/bin/activate
uvicorn app.main:app --reload
```

The API will start at: **http://localhost:8000**

---

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Testing the APIs

### 1. Create a User Account

```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123"
  }'
```

### 2. Login and Get Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }' \
  -c cookies.txt -D headers.txt
```

**Note**: 
- The JWT access token is returned in both the response body AND the `Authorization` header
- The refresh token is set as an HTTP-only cookie (stored in `cookies.txt` with `-c` flag)
- Copy the `access_token` from the response body or extract from the `Authorization` header in `headers.txt`

### 2b. Refresh Your Access Token

When your access token expires, use the refresh token to get a new one:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -b cookies.txt \
  -D headers.txt
```

**Note**: The refresh token is automatically sent from the cookie. New access token is in the response and `Authorization` header.

### 2c. Logout

```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -b cookies.txt
```

This clears the refresh token cookie.

### 3. Use the Token for News APIs

Replace `YOUR_TOKEN` with the actual token:

```bash
# Get news by category
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/news/category?category=world&limit=5"

# Search news (with LLM entity extraction)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/news/search?query=technology+trends&limit=5"

# Get nearby news
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/news/nearby?lat=19.07&lon=72.87&radius=50&limit=5"

# Get by score
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/news/score?min_score=0.7&limit=5"

# Unified endpoint with filters
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/news?category=world&min_score=0.6&limit=5"
```

### 4. Trending News (After Simulating Events)

```bash
# First, simulate user events
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/news/trending/simulate-events?num_events=1000"

# Then get trending news
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/news/trending?lat=19.07&lon=72.87&limit=10"
```

---

## Project Structure

```
news-data-service/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── core/
│   │   ├── config.py          # Settings and env variables
│   │   ├── database.py        # PostgreSQL connection
│   │   ├── redis.py           # Redis connection
│   │   └── security.py        # JWT token functions
│   ├── models/
│   │   └── schemas.py         # Pydantic models
│   ├── services/
│   │   ├── auth_service.py    # Authentication logic
│   │   ├── news_service.py    # News retrieval logic
│   │   ├── llm_service.py     # Google Gemini integration
│   │   └── trending_service.py # Trending calculations
│   └── api/
│       ├── dependencies.py    # Auth middleware
│       └── routes/
│           ├── auth.py        # Signup/Login endpoints
│           ├── news.py        # News endpoints
│           └── trending.py    # Trending endpoint
├── scripts/
│   ├── init.sql              # Database schema
│   └── ingest_data.py        # Data loading script
├── data/
│   └── news_data.json        # News articles (2000 items)
├── docker-compose.yml         # Docker setup
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables
```

---

## Available API Endpoints

### Authentication (No token required)
- `POST /api/v1/auth/signup` - Create account
- `POST /api/v1/auth/login` - Get JWT token

### News APIs (Token required)
- `GET /api/v1/news/category` - Get by category
- `GET /api/v1/news/score` - Get by relevance score
- `GET /api/v1/news/source` - Get by source name
- `GET /api/v1/news/search` - Search with LLM (entity extraction + summaries)
- `GET /api/v1/news/nearby` - Get location-based news
- `GET /api/v1/news` - Unified endpoint with all filters
- `GET /api/v1/news/trending` - Get trending news by location
- `POST /api/v1/news/trending/simulate-events` - Generate user events

---

## Features Implemented

### Core Features
✅ JWT Authentication (signup/login)
✅ 6 News API endpoints
✅ LLM-powered entity extraction (Google Gemini)
✅ LLM-generated article summaries
✅ Full-text search (PostgreSQL ts_vector)
✅ Geospatial search (PostGIS ST_Distance)
✅ Category, source, score filtering
✅ Trending news with geohash caching

### Database
✅ PostgreSQL 15 with PostGIS extension
✅ Full-text search indexes (GIN)
✅ Geospatial indexes (GiST)
✅ Automatic triggers for search vectors
✅ 2000 news articles loaded

Enjoy building! 🚀
