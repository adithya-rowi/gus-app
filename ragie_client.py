import os
import requests
import logging

logger = logging.getLogger(__name__)

RAGIE_API_BASE = "https://api.ragie.ai"


class RagieError(Exception):
    pass


class RagieClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("RAGIE_API_KEY")
        if not self.api_key:
            raise ValueError("RAGIE_API_KEY is required")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def retrieve(self, query: str, top_k: int = 5, rerank: bool = True, 
                 filter_metadata: dict = None, partition: str = None) -> dict:
        url = f"{RAGIE_API_BASE}/retrievals"
        
        payload = {
            "query": query,
            "top_k": top_k,
            "rerank": rerank
        }
        
        if filter_metadata:
            payload["filter"] = filter_metadata
        if partition:
            payload["partition"] = partition
            
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not isinstance(data, dict):
                raise RagieError("Invalid response format from Ragie API")
            
            return data
        except requests.exceptions.HTTPError as e:
            logger.error(f"Ragie API HTTP error: {e}")
            raise RagieError(f"Ragie API error: {e.response.status_code} - {e.response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ragie API request error: {e}")
            raise RagieError(f"Failed to connect to Ragie API: {str(e)}")
        except ValueError as e:
            logger.error(f"Ragie API JSON parse error: {e}")
            raise RagieError("Invalid JSON response from Ragie API")

    def get_context(self, query: str, top_k: int = 5) -> str:
        result = self.retrieve(query, top_k=top_k)
        
        chunks = result.get("scored_chunks", result.get("scoredChunks", []))
        
        if not chunks:
            return ""
        
        if not isinstance(chunks, list):
            raise RagieError("Invalid chunks format in Ragie response")
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            if not isinstance(chunk, dict):
                continue
            text = chunk.get("text", "")
            if text:
                score = chunk.get("score", 0)
                try:
                    score_str = f"{float(score):.2f}"
                except (ValueError, TypeError):
                    score_str = "N/A"
                context_parts.append(f"[Source {i}] (relevance: {score_str})\n{text}")
        
        if not context_parts:
            return ""
        
        return "\n\n---\n\n".join(context_parts)

    def health_check(self) -> bool:
        try:
            self.retrieve("test", top_k=1)
            return True
        except RagieError:
            return False
        except Exception as e:
            logger.error(f"Ragie health check failed: {e}")
            return False


def get_ragie_client() -> RagieClient:
    return RagieClient()
