from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database.models import RequestModel, ResponseModel
from datetime import datetime, timedelta

class AnalyticsEngine:
    def __init__(self):
        # Estimated cost configuration per token
        self.remote_cost_per_token = 0.20 / 1_000_000  # $0.20 per 1M tokens

    def get_summary(self, db: Session) -> dict:
        total = db.query(RequestModel).count()
        if total == 0:
            return {
                "total_requests": 0,
                "local_requests": 0,
                "remote_requests": 0,
                "escalated_requests": 0,
                "tokens_spent_remote": 0,
                "tokens_spent_local": 0,
                "tokens_saved_local": 0,
                "estimated_cost_usd": 0.0,
                "estimated_savings_usd": 0.0,
                "cache_hit_rate": 0.0,
                "average_latency_ms": 0.0,
                "energy_saved_kwh": 0.0,
                "co2_saved_kg": 0.0,
                "phone_charges_saved": 0,
                "daily_stats": []
            }

        local_reqs = db.query(RequestModel).filter(RequestModel.routed_to == "local").count()
        remote_reqs = db.query(RequestModel).filter(RequestModel.routed_to == "remote").count()
        
        # Escalated requests are routed_to == "local" but final_route contains "ESCALATED"
        escalated_reqs = db.query(RequestModel).filter(
            RequestModel.final_route.like("%ESCALATED%")
        ).count()

        # Token metrics
        totals = db.query(
            func.sum(RequestModel.prompt_tokens).label("prompt"),
            func.sum(RequestModel.completion_tokens).label("completion"),
            func.sum(RequestModel.latency_ms).label("latency")
        ).first()

        # Remote tokens
        remote_totals = db.query(
            func.sum(RequestModel.prompt_tokens).label("prompt"),
            func.sum(RequestModel.completion_tokens).label("completion")
        ).filter(RequestModel.final_route.like("%REMOTE%")).first()

        # Local tokens
        local_totals = db.query(
            func.sum(RequestModel.prompt_tokens).label("prompt"),
            func.sum(RequestModel.completion_tokens).label("completion")
        ).filter(RequestModel.final_route == "LOCAL").first()

        r_prompt = (remote_totals.prompt or 0) if remote_totals else 0
        r_completion = (remote_totals.completion or 0) if remote_totals else 0
        r_spent = r_prompt + r_completion

        l_prompt = (local_totals.prompt or 0) if local_totals else 0
        l_completion = (local_totals.completion or 0) if local_totals else 0
        l_spent = l_prompt + l_completion

        # Cached requests count
        cached_count = db.query(ResponseModel).filter(ResponseModel.is_cached == True).count()
        cache_hit_rate = (cached_count / total) * 100

        # Saved tokens:
        # 1. Any request resolved purely via "LOCAL" (prompt + completion saved)
        # 2. Any request resolved via Cache (since it saved querying remote or local)
        local_saved_query = db.query(
            func.sum(RequestModel.prompt_tokens + RequestModel.completion_tokens)
        ).filter(RequestModel.final_route == "LOCAL").scalar() or 0
        
        cache_saved_query = db.query(
            func.sum(RequestModel.prompt_tokens + RequestModel.completion_tokens)
        ).join(ResponseModel).filter(ResponseModel.is_cached == True).scalar() or 0

        tokens_saved = local_saved_query + cache_saved_query

        # Cost and Savings Calculations
        est_cost = r_spent * self.remote_cost_per_token
        est_savings = tokens_saved * self.remote_cost_per_token

        # Cloud 70B datacenter inference averages ~0.0035 kWh per 1k tokens (including server cooling & PUE) vs ~0.00015 kWh local NPU/GPU
        # Grid carbon intensity average ~0.385 kg CO2 per kWh
        energy_saved_kwh = (tokens_saved / 1000.0) * 0.0035
        co2_saved_kg = energy_saved_kwh * 0.385
        phone_charges_saved = int(energy_saved_kwh * 80)

        avg_latency = (totals.latency or 0) / total if totals else 0.0

        # Retrieve last 7 days daily statistics for charting
        # Use func.date() which works reliably with SQLite (returns strings) and Postgres
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        try:
            daily_records = db.query(
                func.date(RequestModel.timestamp).label("day"),
                func.count(RequestModel.id).label("count"),
                func.sum(RequestModel.latency_ms).label("latency_sum"),
                func.sum(RequestModel.prompt_tokens + RequestModel.completion_tokens).label("tokens_sum")
            ).filter(RequestModel.timestamp >= seven_days_ago)\
             .group_by(func.date(RequestModel.timestamp))\
             .order_by(func.date(RequestModel.timestamp))\
             .all()
        except Exception:
            daily_records = []

        daily_stats = []
        for rec in daily_records:
            if rec.day is None:
                continue
            
            # rec.day is a string from func.date() in SQLite (e.g., "2026-07-09")
            day_str = str(rec.day) if rec.day else ""
            count = rec.count or 0
            avg_day_latency = (rec.latency_sum / count) if count > 0 else 0.0
            
            # Estimate daily remote tokens to get daily cost
            try:
                daily_r_tokens = db.query(
                    func.sum(RequestModel.prompt_tokens + RequestModel.completion_tokens)
                ).filter(
                    func.date(RequestModel.timestamp) == rec.day,
                    RequestModel.final_route.like("%REMOTE%")
                ).scalar() or 0
            except Exception:
                daily_r_tokens = 0
            daily_cost = daily_r_tokens * self.remote_cost_per_token

            # Daily savings from local/cached
            try:
                daily_saved_tokens = db.query(
                    func.sum(RequestModel.prompt_tokens + RequestModel.completion_tokens)
                ).filter(
                    func.date(RequestModel.timestamp) == rec.day,
                    RequestModel.final_route == "LOCAL"
                ).scalar() or 0
            except Exception:
                daily_saved_tokens = 0
            
            try:
                daily_saved_cached = db.query(
                    func.sum(RequestModel.prompt_tokens + RequestModel.completion_tokens)
                ).join(ResponseModel).filter(
                    func.date(RequestModel.timestamp) == rec.day,
                    ResponseModel.is_cached == True
                ).scalar() or 0
            except Exception:
                daily_saved_cached = 0
            
            daily_savings = (daily_saved_tokens + daily_saved_cached) * self.remote_cost_per_token

            daily_stats.append({
                "date": day_str,
                "requests": count,
                "latency_ms": round(avg_day_latency, 2),
                "cost_usd": round(daily_cost, 6),
                "savings_usd": round(daily_savings, 6)
            })

        return {
            "total_requests": total,
            "local_requests": local_reqs,
            "remote_requests": remote_reqs,
            "escalated_requests": escalated_reqs,
            "tokens_spent_remote": r_spent,
            "tokens_spent_local": l_spent,
            "tokens_saved_local": tokens_saved,
            "estimated_cost_usd": round(est_cost, 6),
            "estimated_savings_usd": round(est_savings, 6),
            "cache_hit_rate": round(cache_hit_rate, 2),
            "average_latency_ms": round(avg_latency, 2),
            "energy_saved_kwh": round(energy_saved_kwh, 4),
            "co2_saved_kg": round(co2_saved_kg, 4),
            "phone_charges_saved": phone_charges_saved,
            "daily_stats": daily_stats
        }

