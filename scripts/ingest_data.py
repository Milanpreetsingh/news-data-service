import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
import asyncpg

async def ingest_data():
    print("Starting data ingestion...")
    
    conn = await asyncpg.connect(settings.DATABASE_URL)
    
    data_file = Path(__file__).parent.parent / "data" / "news_data.json"
    
    if not data_file.exists():
        print(f"Error: Data file not found at {data_file}")
        print("Please copy your news_data.json to the data/ directory")
        return
    
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'articles' in data:
        articles = data['articles']
    elif isinstance(data, list):
        articles = data
    else:
        print("Error: Unexpected JSON structure")
        return
    
    print(f"Found {len(articles)} articles to insert")
    
    await conn.execute("TRUNCATE TABLE articles CASCADE")
    
    inserted = 0
    for article in articles:
        try:
            category_array = article.get('category', [])
            if isinstance(category_array, str):
                category_array = [category_array]
            
            pub_date = article.get('publication_date')
            if pub_date and isinstance(pub_date, str):
                pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
            
            await conn.execute(
                """
                INSERT INTO articles 
                (id, title, description, url, publication_date, source_name, 
                 category, relevance_score, latitude, longitude)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                article.get('id'),
                article.get('title'),
                article.get('description'),
                article.get('url'),
                pub_date,
                article.get('source_name'),
                category_array,
                article.get('relevance_score'),
                article.get('latitude'),
                article.get('longitude')
            )
            inserted += 1
            
            if inserted % 100 == 0:
                print(f"Inserted {inserted} articles...")
        
        except Exception as e:
            print(f"Error inserting article {article.get('id')}: {e}")
            continue
    
    await conn.close()
    
    print(f"Data ingestion complete! Inserted {inserted} articles.")

if __name__ == "__main__":
    asyncio.run(ingest_data())
