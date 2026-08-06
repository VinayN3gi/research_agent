import os
import json
from models import KnowledgeBase, ResearchPlan
from utils.logger import get_logger

logger = get_logger("checkpoints")

CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

class CheckpointManager:
    @staticmethod
    def _get_filepath(job_id: str) -> str:
        return os.path.join(CHECKPOINT_DIR, f"{job_id}.json")

    @staticmethod
    def save(job_id: str, iteration: int, kb: KnowledgeBase, plan: ResearchPlan):
        filepath = CheckpointManager._get_filepath(job_id)
        data = {
            "iteration": iteration,
            "kb": kb.model_dump(),
            "plan": plan.model_dump()
        }
        with open(filepath, "w") as f:
            json.dump(data, f)
        logger.info(f"[{job_id}] Saved checkpoint at iteration {iteration}")

    @staticmethod
    def load(job_id: str):
        filepath = CheckpointManager._get_filepath(job_id)
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            return {
                "iteration": data["iteration"],
                "kb": KnowledgeBase.model_validate(data["kb"]),
                "plan": ResearchPlan.model_validate(data["plan"])
            }
        except Exception as e:
            logger.error(f"[{job_id}] Failed to load checkpoint: {e}")
            return None

    @staticmethod
    def clear(job_id: str):
        filepath = CheckpointManager._get_filepath(job_id)
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"[{job_id}] Cleared checkpoint")
