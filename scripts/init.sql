CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    url TEXT,
    publication_date TIMESTAMP,
    source_name VARCHAR(255),
    category TEXT[],
    relevance_score FLOAT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    location GEOGRAPHY(POINT, 4326),
    search_vector TSVECTOR,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_articles_category ON articles USING GIN(category);
CREATE INDEX idx_articles_source ON articles(source_name);
CREATE INDEX idx_articles_score ON articles(relevance_score DESC);
CREATE INDEX idx_articles_location ON articles USING GIST(location);
CREATE INDEX idx_articles_search ON articles USING GIN(search_vector);
CREATE INDEX idx_articles_pub_date ON articles(publication_date DESC);

CREATE TABLE IF NOT EXISTS user_events (
    id SERIAL PRIMARY KEY,
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(20) CHECK (event_type IN ('view', 'click', 'share')),
    user_lat DOUBLE PRECISION,
    user_lon DOUBLE PRECISION,
    user_location GEOGRAPHY(POINT, 4326),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_events_article ON user_events(article_id);
CREATE INDEX idx_events_created_at ON user_events(created_at DESC);
CREATE INDEX idx_events_location ON user_events USING GIST(user_location);
CREATE INDEX idx_events_user ON user_events(user_id);

CREATE OR REPLACE FUNCTION update_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.description, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER articles_search_vector_update
    BEFORE INSERT OR UPDATE ON articles
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vector();

CREATE OR REPLACE FUNCTION update_location() RETURNS trigger AS $$
BEGIN
    -- For articles table
    IF TG_TABLE_NAME = 'articles' THEN
        IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
            NEW.location := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)::geography;
        END IF;
    END IF;
    
    -- For user_events table
    IF TG_TABLE_NAME = 'user_events' THEN
        IF NEW.user_lat IS NOT NULL AND NEW.user_lon IS NOT NULL THEN
            NEW.user_location := ST_SetSRID(ST_MakePoint(NEW.user_lon, NEW.user_lat), 4326)::geography;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER articles_location_update
    BEFORE INSERT OR UPDATE ON articles
    FOR EACH ROW
    EXECUTE FUNCTION update_location();

CREATE TRIGGER events_location_update
    BEFORE INSERT OR UPDATE ON user_events
    FOR EACH ROW
    EXECUTE FUNCTION update_location();
