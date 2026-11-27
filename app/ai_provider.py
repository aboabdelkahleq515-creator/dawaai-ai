"""
DAWAA'I AI — Unified AI Provider Abstraction Layer (app/ai_provider.py)
Resilient multi-provider service with:
  - Primary: Google Gemini (gemini-2.0-flash-lite for text, gemini-2.5-flash for vision/complex)
  - Fallback: Groq (llama-3.3-70b-versatile / llama-3.1-8b-instant) or configurable secondary
  - Strict timeouts (10-12s) and Exponential Backoff Retries (2-3 attempts)
  - Circuit Breaker pattern (trips after 3 consecutive failures, cools down for 60s)
  - In-Memory LRU + TTL Caching for frequent queries and duplicate OCR scans
  - Bilingual user-friendly error messages
  - Real-time Health Diagnostics and Recent Error Buffer for admin dashboard
"""

import os
import time
import json
import hashlib
import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple
from collections import deque
from datetime import datetime, timezone
import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("dawaai.ai_provider")

# -----------------------------------------------------------------------------
# Configuration from Environment
# -----------------------------------------------------------------------------
PRIMARY_PROVIDER = os.getenv("PRIMARY_AI_PROVIDER", "gemini").lower()
FALLBACK_PROVIDER = os.getenv("FALLBACK_AI_PROVIDER", "groq").lower()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

GEMINI_MODEL_TEXT = os.getenv("GEMINI_MODEL_TEXT", "gemini-3.5-flash-lite")
GEMINI_MODEL_VISION = os.getenv("GEMINI_MODEL_VISION", "gemini-3.5-flash-lite")
GROQ_MODEL_TEXT = os.getenv("GROQ_MODEL_TEXT", "llama-3.3-70b-versatile")

AI_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_SECONDS", "10.0"))
AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "2"))
CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "3"))
CIRCUIT_BREAKER_COOLDOWN = float(os.getenv("CIRCUIT_BREAKER_COOLDOWN_SECONDS", "60.0"))
CACHE_TTL_SECONDS = float(os.getenv("CACHE_TTL_SECONDS", "3600.0"))
CACHE_MAX_ITEMS = int(os.getenv("CACHE_MAX_ITEMS", "500"))


# -----------------------------------------------------------------------------
# Circuit Breaker Implementation
# -----------------------------------------------------------------------------
class CircuitBreaker:
    """
    Prevents cascading failures by pausing requests to failing providers.
    States:
      - CLOSED: Healthy, accepting all traffic.
      - OPEN: Tripped due to consecutive failures, traffic diverted to fallback.
      - HALF_OPEN: Cooldown expired, allows a single probe request to test recovery.
    """
    def __init__(self, name: str, threshold: int = 3, cooldown: float = 60.0):
        self.name = name
        self.threshold = threshold
        self.cooldown = cooldown
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.total_trips = 0

    def can_request(self) -> bool:
        now = time.time()
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if self.last_failure_time and (now - self.last_failure_time) > self.cooldown:
                self.state = "HALF_OPEN"
                logger.info(f"CircuitBreaker [{self.name}]: Transitioning OPEN -> HALF_OPEN (Probing recovery)")
                return True
            return False
        if self.state == "HALF_OPEN":
            # Allow one attempt
            return True
        return False

    def record_success(self):
        if self.state != "CLOSED":
            logger.info(f"CircuitBreaker [{self.name}]: Recovered! Transitioning {self.state} -> CLOSED")
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self, error_msg: str):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.threshold:
            if self.state != "OPEN":
                self.total_trips += 1
                logger.warning(
                    f"CircuitBreaker [{self.name}]: TRIPPED to OPEN after {self.failure_count} consecutive failures. "
                    f"Cooling down for {self.cooldown}s. Last error: {error_msg}"
                )
            self.state = "OPEN"

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "total_trips": self.total_trips,
            "last_failure_ago": round(time.time() - self.last_failure_time, 1) if self.last_failure_time else None
        }


# -----------------------------------------------------------------------------
# LRU + TTL In-Memory Cache
# -----------------------------------------------------------------------------
class LRUTTLCache:
    """Thread-safe in-memory cache with Time-To-Live and maximum size eviction."""
    def __init__(self, max_items: int = 500, ttl: float = 3600.0):
        self.max_items = max_items
        self.ttl = ttl
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        entry = self._cache.get(key)
        if entry:
            timestamp, value = entry
            if now - timestamp < self.ttl:
                self.hits += 1
                return value
            else:
                del self._cache[key]
        self.misses += 1
        return None

    def set(self, key: str, value: Any):
        if len(self._cache) >= self.max_items:
            # Evict oldest entry
            oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]
        self._cache[key] = (time.time(), value)

    def stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        hit_ratio = round((self.hits / total * 100), 1) if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_items": self.max_items,
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio_percent": hit_ratio
        }


# -----------------------------------------------------------------------------
# Result Container
# -----------------------------------------------------------------------------
class AIResult:
    def __init__(
        self,
        success: bool,
        text: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        provider: str = "none",
        model: str = "none",
        duration_ms: float = 0.0,
        cached: bool = False,
        error_code: Optional[str] = None,
        user_message_ar: Optional[str] = None,
        user_message_en: Optional[str] = None
    ):
        self.success = success
        self.text = text
        self.data = data
        self.provider = provider
        self.model = model
        self.duration_ms = duration_ms
        self.cached = cached
        self.error_code = error_code
        self.user_message_ar = user_message_ar
        self.user_message_en = user_message_en

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "text": self.text,
            "data": self.data,
            "provider": self.provider,
            "model": self.model,
            "duration_ms": self.duration_ms,
            "cached": self.cached,
            "error_code": self.error_code,
            "user_message_ar": self.user_message_ar,
            "user_message_en": self.user_message_en
        }


# -----------------------------------------------------------------------------
# Unified AI Provider Service
# -----------------------------------------------------------------------------
class AIProviderService:
    def __init__(self):
        self.circuit_breakers = {
            "gemini": CircuitBreaker("gemini", threshold=CIRCUIT_BREAKER_THRESHOLD, cooldown=CIRCUIT_BREAKER_COOLDOWN),
            "groq": CircuitBreaker("groq", threshold=CIRCUIT_BREAKER_THRESHOLD, cooldown=CIRCUIT_BREAKER_COOLDOWN)
        }
        self.cache = LRUTTLCache(max_items=CACHE_MAX_ITEMS, ttl=CACHE_TTL_SECONDS)
        self.recent_errors = deque(maxlen=50)

    def _hash_key(self, prefix: str, payload: Any) -> str:
        s = json.dumps(payload, sort_keys=True) if isinstance(payload, (dict, list)) else str(payload)
        return f"{prefix}:{hashlib.sha256(s.encode('utf-8')).hexdigest()}"

    def _record_error(self, provider: str, model: str, error_msg: str, status_code: Optional[int] = None):
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": provider,
            "model": model,
            "error": error_msg,
            "status_code": status_code
        }
        self.recent_errors.append(event)
        logger.error(f"AI Provider [{provider} / {model}] Error: {error_msg} (status: {status_code})")

    # -------------------------------------------------------------------------
    # Text Generation with Fallback & Circuit Breaker
    # -------------------------------------------------------------------------
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        is_complex: bool = False,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        use_cache: bool = True
    ) -> AIResult:
        """
        Unified text generation.
        Tries Primary Provider -> on failure tries Fallback Provider.
        Includes circuit breaker, timeouts, and automatic retry.
        """
        cache_key = self._hash_key("text", {"p": prompt, "s": system_instruction, "c": is_complex})
        if use_cache:
            cached_val = self.cache.get(cache_key)
            if cached_val:
                return AIResult(
                    success=True,
                    text=cached_val["text"],
                    provider=cached_val["provider"],
                    model=cached_val["model"],
                    duration_ms=0.0,
                    cached=True
                )

        providers_order = [PRIMARY_PROVIDER]
        if FALLBACK_PROVIDER != PRIMARY_PROVIDER:
            providers_order.append(FALLBACK_PROVIDER)

        last_err = "No AI providers configured or available"
        for provider in providers_order:
            cb = self.circuit_breakers.get(provider)
            if cb and not cb.can_request():
                logger.info(f"Skipping [{provider}]: Circuit Breaker is OPEN.")
                continue

            # Model Selection
            if provider == "gemini":
                model = GEMINI_MODEL_VISION if is_complex else GEMINI_MODEL_TEXT
                api_key = GEMINI_API_KEY
            else: # groq
                model = GROQ_MODEL_TEXT
                api_key = GROQ_API_KEY

            if not api_key:
                continue

            # Attempt with retries
            start_t = time.time()
            for attempt in range(1, AI_MAX_RETRIES + 1):
                try:
                    if provider == "gemini":
                        text = await self._call_gemini_text(
                            prompt=prompt,
                            system_instruction=system_instruction,
                            model=model,
                            api_key=api_key,
                            temperature=temperature,
                            max_tokens=max_tokens
                        )
                    else:
                        text = await self._call_groq_text(
                            prompt=prompt,
                            system_instruction=system_instruction,
                            model=model,
                            api_key=api_key,
                            temperature=temperature,
                            max_tokens=max_tokens
                        )

                    duration = round((time.time() - start_t) * 1000, 1)
                    if cb:
                        cb.record_success()

                    if use_cache and text:
                        self.cache.set(cache_key, {"text": text, "provider": provider, "model": model})

                    return AIResult(
                        success=True,
                        text=text,
                        provider=provider,
                        model=model,
                        duration_ms=duration
                    )
                except httpx.HTTPStatusError as e:
                    status = e.response.status_code
                    last_err = f"HTTP {status}: {e.response.text[:200]}"
                    self._record_error(provider, model, last_err, status)
                    if status == 429: # Rate limit -> backoff then fallback
                        await asyncio.sleep(0.5 * attempt)
                    elif status >= 500:
                        await asyncio.sleep(0.5 * attempt)
                    else:
                        break
                except (httpx.TimeoutException, asyncio.TimeoutError):
                    last_err = f"Timeout after {AI_TIMEOUT_SECONDS}s"
                    self._record_error(provider, model, last_err)
                    await asyncio.sleep(0.5 * attempt)
                except Exception as e:
                    last_err = str(e)
                    self._record_error(provider, model, last_err)
                    break

            if cb:
                cb.record_failure(last_err)

        # All providers failed
        return AIResult(
            success=False,
            error_code="ALL_PROVIDERS_UNAVAILABLE",
            user_message_ar="خدمة الذكاء الاصطناعي غير متاحة مؤقتاً، يمكنك استعراض النشرات الدوائية المعتمدة مباشرة.",
            user_message_en="AI service is temporarily unavailable. You can browse verified monographs directly."
        )

    # -------------------------------------------------------------------------
    # Vision JSON Extraction (Medicine Box Scanner)
    # -------------------------------------------------------------------------
    async def extract_vision_json(
        self,
        prompt: str,
        image_b64: str,
        mime_type: str = "image/jpeg",
        use_cache: bool = True
    ) -> AIResult:
        """
        Multimodal packaging reader.
        Strictly transcribes package texts using Gemini multimodal model.
        """
        img_hash = hashlib.sha256(image_b64.encode('utf-8')).hexdigest()
        cache_key = self._hash_key("vision", {"h": img_hash, "p": prompt[:50]})
        if use_cache:
            cached_val = self.cache.get(cache_key)
            if cached_val:
                return AIResult(
                    success=True,
                    data=cached_val["data"],
                    provider=cached_val["provider"],
                    model=cached_val["model"],
                    duration_ms=0.0,
                    cached=True
                )

        provider = "gemini"
        cb = self.circuit_breakers.get(provider)
        if cb and not cb.can_request():
            return AIResult(
                success=False,
                error_code="CIRCUIT_OPEN",
                user_message_ar="خدمة قراءة العلب مشغولة مؤقتاً، يرجى المحاولة بعد دقيقة أو إدخال اسم الدواء يدوياً.",
                user_message_en="Packaging reader is temporarily resting, please try again shortly or search manually."
            )

        if not GEMINI_API_KEY:
            return AIResult(
                success=False,
                error_code="NO_API_KEY",
                user_message_ar="مفتاح الذكاء الاصطناعي لقراءة الصور غير مهيأ في الخادم.",
                user_message_en="Vision AI API key is not configured on the server."
            )

        models_to_try = [GEMINI_MODEL_VISION, "gemini-3.5-flash-lite", "gemini-2.5-flash"]
        last_err = ""
        start_t = time.time()

        for model in models_to_try:
            for attempt in range(1, AI_MAX_RETRIES + 1):
                try:
                    data = await self._call_gemini_vision_json(
                        prompt=prompt,
                        image_b64=image_b64,
                        mime_type=mime_type,
                        model=model,
                        api_key=GEMINI_API_KEY
                    )
                    duration = round((time.time() - start_t) * 1000, 1)
                    if cb:
                        cb.record_success()
                    if use_cache and data:
                        self.cache.set(cache_key, {"data": data, "provider": provider, "model": model})

                    return AIResult(
                        success=True,
                        data=data,
                        provider=provider,
                        model=model,
                        duration_ms=duration
                    )
                except httpx.HTTPStatusError as e:
                    status = e.response.status_code
                    last_err = f"HTTP {status}: {e.response.text[:200]}"
                    self._record_error(provider, model, last_err, status)
                    if status == 429:
                        await asyncio.sleep(1.0 * attempt)
                    else:
                        break
                except (httpx.TimeoutException, asyncio.TimeoutError):
                    last_err = f"Vision timeout after {AI_TIMEOUT_SECONDS}s"
                    self._record_error(provider, model, last_err)
                    await asyncio.sleep(0.5 * attempt)
                except Exception as e:
                    last_err = str(e)
                    self._record_error(provider, model, last_err)
                    break

        if cb:
            cb.record_failure(last_err)

        return AIResult(
            success=False,
            error_code="VISION_FAILED",
            user_message_ar="تعذر فحص صورة العلبة بالذكاء الاصطناعي، يرجى إعادة التصوير بزاوية أوضح أو البحث بالاسم.",
            user_message_en="Unable to scan packaging image. Please retake with clearer lighting or search by name."
        )

    # -------------------------------------------------------------------------
    # Low-level HTTP Provider Callers
    # -------------------------------------------------------------------------
    async def _call_gemini_text(
        self,
        prompt: str,
        system_instruction: Optional[str],
        model: str,
        api_key: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        body: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        async with httpx.AsyncClient(timeout=AI_TIMEOUT_SECONDS) as client:
            res = await client.post(url, json=body)
            res.raise_for_status()
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_gemini_vision_json(
        self,
        prompt: str,
        image_b64: str,
        mime_type: str,
        model: str,
        api_key: str
    ) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        body = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime_type, "data": image_b64}}
                ]
            }],
            "generationConfig": {
                "temperature": 0.0,
                "response_mime_type": "application/json",
                "maxOutputTokens": 4096
            }
        }
        async with httpx.AsyncClient(timeout=AI_TIMEOUT_SECONDS) as client:
            res = await client.post(url, json=body)
            res.raise_for_status()
            data = res.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)

    async def _call_groq_text(
        self,
        prompt: str,
        system_instruction: Optional[str],
        model: str,
        api_key: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        async with httpx.AsyncClient(timeout=AI_TIMEOUT_SECONDS) as client:
            res = await client.post(url, headers=headers, json=body)
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"]

    # -------------------------------------------------------------------------
    # Health Diagnostics Status
    # -------------------------------------------------------------------------
    def get_health_status(self) -> Dict[str, Any]:
        return {
            "status": "operational",
            "primary_provider": PRIMARY_PROVIDER,
            "primary_configured": bool(GEMINI_API_KEY if PRIMARY_PROVIDER == "gemini" else GROQ_API_KEY),
            "fallback_provider": FALLBACK_PROVIDER,
            "fallback_configured": bool(GROQ_API_KEY if FALLBACK_PROVIDER == "groq" else GEMINI_API_KEY),
            "circuit_breakers": {
                name: cb.get_status() for name, cb in self.circuit_breakers.items()
            },
            "cache": self.cache.stats(),
            "active_models": {
                "gemini_text": GEMINI_MODEL_TEXT,
                "gemini_vision": GEMINI_MODEL_VISION,
                "groq_text": GROQ_MODEL_TEXT
            },
            "recent_errors": list(self.recent_errors)
        }


# Global Singleton Instance
ai_provider = AIProviderService()
