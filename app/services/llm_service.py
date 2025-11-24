import json
import logging
import asyncio
import google.generativeai as genai
from typing import List, Dict
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def extract_entities(self, query: str) -> Dict:
        prompt = f"""
Extract information from this news query and return ONLY valid JSON without any markdown formatting:

Query: "{query}"

Return a JSON object with these fields:
- entities: list of named entities (people, organizations, locations, events)
- intent: one of ["category", "score", "search", "source", "nearby"]
- search_terms: list of keywords for searching
- location_hint: any location mentioned (or null)

Example output:
{{"entities": ["Elon Musk", "Twitter"], "intent": "search", "search_terms": ["Elon Musk", "Twitter", "acquisition"], "location_hint": "Palo Alto"}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            result = json.loads(text)
            return result
        except genai.types.BlockedPromptException as e:
            logger.warning(f"LLM blocked prompt for entity extraction: {e}")
            return {
                "entities": [],
                "intent": "search",
                "search_terms": query.split(),
                "location_hint": None
            }
        except genai.types.StopCandidateException as e:
            logger.warning(f"LLM stopped generation for entity extraction: {e}")
            return {
                "entities": [],
                "intent": "search",
                "search_terms": query.split(),
                "location_hint": None
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            return {
                "entities": [],
                "intent": "search",
                "search_terms": query.split(),
                "location_hint": None
            }
        except Exception as e:
            logger.error(f"LLM error in extract_entities: {e}")
            return {
                "entities": [],
                "intent": "search",
                "search_terms": query.split(),
                "location_hint": None
            }
    
    async def generate_summary(self, article_text: str) -> str:
        prompt = f"""
Summarize this news article in 2-3 concise sentences:

{article_text}

Summary:
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except genai.types.BlockedPromptException as e:
            logger.warning(f"LLM blocked prompt for summary: {e}")
            return "Summary unavailable."
        except genai.types.StopCandidateException as e:
            logger.warning(f"LLM stopped generation for summary: {e}")
            return "Summary unavailable."
        except Exception as e:
            logger.error(f"LLM error in generate_summary: {e}")
            return "Summary unavailable."
    
    async def generate_summaries_batch(self, articles: List[Dict]) -> List[str]:
        tasks = []
        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}"
            text = text[:2000]
            tasks.append(self.generate_summary(text))
        
        summaries = await asyncio.gather(*tasks, return_exceptions=True)
        
        result = []
        for summary in summaries:
            if isinstance(summary, Exception):
                logger.error(f"LLM summary failed in batch: {summary}")
                result.append("Summary unavailable.")
            else:
                result.append(summary)
        
        return result

llm_service = LLMService()
