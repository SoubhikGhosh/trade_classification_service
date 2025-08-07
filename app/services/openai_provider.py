import httpx
import openai
import json
import time
import logging
from typing import List, Dict

from .ai_provider_interface import AIProviderInterface
from ..config import settings
from ..schemas import ClassifiedDocumentsResponse, NonExtractedDocuments

logger = logging.getLogger(__name__)

class OpenAIProvider(AIProviderInterface):
    """Concrete implementation of the AI provider for OpenAI-compatible APIs."""
    
    def __init__(self):
        http_client = httpx.Client(http2=True, verify=False)
        try:
            self.client = openai.OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                http_client=http_client
            )
            logger.info("OpenAI client initialized successfully.")
        except Exception as e:
            logger.error("Failed to initialize OpenAI client", exc_info=True)
            raise

    def cluster_classify_and_sequence(
        self,
        image_parts: List[Dict],
        prompt: str,
        request_id: str
    ) -> ClassifiedDocumentsResponse:
        """Calls the OpenAI-compatible API and logs detailed metrics."""
        
        log_extra = {"request_id": request_id}
        prompt_part = [{"type": "text", "text": prompt}]
        combined_parts = prompt_part + image_parts
        
        messages = [{"role": "user", "content": combined_parts}]

        start_time = time.perf_counter()
        
        try:
            response = self.client.beta.chat.completions.parse(
                model=settings.MODEL_NAME,
                messages=messages,
                temperature=settings.TEMPERATURE,
                top_p=settings.TOP_P,
                response_format=NonExtractedDocuments,
                reasoning_effort=settings.REASONING_EFFORT,
                max_completion_tokens=settings.MAX_COMPLETION_TOKENS
            )
        except Exception:
            logger.error("API call to OpenAI provider failed", extra=log_extra, exc_info=True)
            raise

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        # --- Structured Metric Logging ---
        token_usage = response.usage.to_dict() if response.usage else {}
        log_metric_data = {
            "request_id": request_id,
            "metric_type": "ai_call_performance",
            "model_name": settings.MODEL_NAME,
            "latency_ms": round(latency_ms, 2),
            "token_usage": token_usage
        }
        logger.info("AI call performance metric", extra=log_metric_data)

        # Safely parse the response content
        try:
            response_json_str = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
            raw_response = json.loads(response_json_str)
            # Validate that the parsed response matches the expected Pydantic model
            validated_response = NonExtractedDocuments.model_validate(raw_response)
        except (IndexError, json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse or validate model response: {e}. Response: '{getattr(response.choices[0].message, 'content', 'N/A')}'", extra=log_extra)
            raise ValueError("Could not parse a valid JSON object from the model's response.")

        # Transform raw response to the standardized ClassifiedDocumentsResponse
        classified_docs = []
        for doc in validated_response.documents:
            classified_docs.append({
                "document_id": doc.document_id,
                "document_type": doc.document_type,
                "document_summary": doc.document_summary,
                "pages": doc.pages,
                "reasoning": None, # Set to None as the prompt doesn't request it
                "confidence_score": None # Set to None as the prompt doesn't request it
            })

        return ClassifiedDocumentsResponse(
            request_id=request_id,
            documents=classified_docs,
            processing_metadata={"ai_call_latency_ms": latency_ms, "token_usage": token_usage}
        )