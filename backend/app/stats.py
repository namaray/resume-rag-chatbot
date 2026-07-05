import os
import json
import logging
import datetime

logger = logging.getLogger("resume-chatbot")

class StatsTracker:
    def __init__(self, data_dir: str):
        self.stats_file = os.path.join(data_dir, "stats.json")
        self.stats = {
            "total_questions": 0,
            "avg_response_time_ms": 0,
            "last_active": None
        }
        self.load()

    def load(self):
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.stats = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load stats: {e}")
        else:
            self.save()

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")

    def record_query(self, response_time_ms: float):
        current_total = self.stats.get("total_questions", 0)
        current_avg = self.stats.get("avg_response_time_ms", 0)

        # Calculate new moving average
        new_total = current_total + 1
        new_avg = ((current_avg * current_total) + response_time_ms) / new_total

        self.stats["total_questions"] = new_total
        self.stats["avg_response_time_ms"] = int(new_avg)
        self.stats["last_active"] = datetime.datetime.utcnow().isoformat()
        
        self.save()

    def get_stats(self):
        return self.stats
