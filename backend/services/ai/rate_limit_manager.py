import time
from datetime import datetime
from collections import defaultdict
import logging
import threading

logger = logging.getLogger("ai_service")
logger.setLevel(logging.INFO)

class RateLimitManager:
    """
    Tracks and manages rate limits for Gemini API keys and models proactively.
    Thread-safe and supports calendar-day resets.
    """
    def __init__(self):
        # Validated strings for V4 models (Google AI Studio)
        self.LIMITS = {
            "gemini-3.1-flash-lite-preview": {"rpm": 15, "rpd": 500},
            "gemini-2.5-flash-lite": {"rpm": 10, "rpd": 20},
            "gemini-2.5-flash": {"rpm": 5, "rpd": 20},
            "gemini-3-flash-preview": {"rpm": 5, "rpd": 20},
        }
        
        # Usage tracking: key -> model -> data
        self.usage = defaultdict(lambda: defaultdict(lambda: {
            "rpm_count": 0, 
            "rpd_count": 0, 
            "last_minute": time.time(), 
            "last_day_str": datetime.now().strftime("%Y-%m-%d")
        }))
        
        self.lock = threading.Lock()

    def _get_usage_data(self, api_key: str, model: str):
        # Must be called within lock
        data = self.usage[api_key][model]
        now = time.time()
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Reset RPM counter if a minute has passed
        if now - data["last_minute"] > 60:
            data["rpm_count"] = 0
            data["last_minute"] = now
            
        # Reset RPD counter if calendar day has changed
        if data["last_day_str"] != today_str:
            logger.info(f" [AI] Resetting daily counters for {api_key[:8]}... {model}")
            data["rpd_count"] = 0
            data["last_day_str"] = today_str
            
        return data

    def can_use(self, api_key: str, model: str) -> bool:
        """Check if a specific key and model can be used without exceeding limits."""
        with self.lock:
            data = self._get_usage_data(api_key, model)
            limits = self.LIMITS.get(model, {"rpm": 2, "rpd": 50}) 
            
            if data["rpm_count"] >= limits["rpm"]:
                return False
                
            if data["rpd_count"] >= limits["rpd"]:
                return False
                
            return True

    def record_usage(self, api_key: str, model: str):
        """Invoke this every time a request is successfully sent."""
        with self.lock:
            data = self._get_usage_data(api_key, model)
            data["rpm_count"] += 1
            data["rpd_count"] += 1

    def mark_exhausted(self, api_key: str, model: str, error_type="quota"):
        """Call this if a 429 is received despite proactive checks."""
        with self.lock:
            data = self._get_usage_data(api_key, model)
            limits = self.LIMITS.get(model, {"rpm": 15, "rpd": 1000})
            
            if error_type == "quota":
                data["rpd_count"] = limits["rpd"]
                logger.warning(f" [AI] Quota exhausted for model {model} with key {api_key[:8]}...")
            else:
                data["rpm_count"] = limits["rpm"]
                logger.warning(f" [AI] Rate limit hit for model {model} with key {api_key[:8]}...")

# Global Singleton
manager = RateLimitManager()
