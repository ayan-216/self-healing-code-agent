from typing import Dict, Any, List
from sqlalchemy.orm import Session
from src.core.db.models import PlatformMetric, AuditSession


class PlatformEvaluator:
    """
    Evaluation Engine calculating platform reliability, repair success rates,
    average retry counts, execution speed, and token cost metrics.
    """

    def compute_platform_metrics(self, db: Session) -> Dict[str, Any]:
        metrics = db.query(PlatformMetric).all()
        total_audits = len(metrics)

        if total_audits == 0:
            return {
                "total_audits_evaluated": 0,
                "repair_success_rate": 0.0,
                "average_retry_count": 0.0,
                "average_repair_time_seconds": 0.0,
                "total_token_usage": 0,
                "total_cost_usd": 0.0
            }

        passed_audits = sum(1 for m in metrics if m.validation_passed)
        success_rate = (passed_audits / total_audits) * 100.0
        avg_retries = sum(m.retry_count for m in metrics) / float(total_audits)
        avg_time = sum(m.execution_time_seconds for m in metrics) / float(total_audits)
        total_tokens = sum(m.token_usage for m in metrics)
        total_cost = sum(m.total_cost for m in metrics)

        return {
            "total_audits_evaluated": total_audits,
            "passed_audits": passed_audits,
            "repair_success_rate_percent": round(success_rate, 2),
            "average_retry_count": round(avg_retries, 2),
            "average_repair_time_seconds": round(avg_time, 2),
            "total_token_usage": total_tokens,
            "total_cost_usd": round(total_cost, 4)
        }


evaluator = PlatformEvaluator()
