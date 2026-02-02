"""
PAPITO MAMITO AI - VALUE METRICS DASHBOARD
==========================================
Real-time monitoring and visualization of value scoring performance.

Features:
- Live metrics endpoint for the webhook server
- Aggregated statistics across action types
- Pillar performance analysis
- Learning insights tracking
- Export capabilities for analysis

API Endpoints (add to webhook server):
    GET /metrics/overview     - Overall system health
    GET /metrics/actions      - Action statistics
    GET /metrics/pillars      - Pillar performance
    GET /metrics/learning     - Learning insights
    GET /metrics/export       - Export raw data

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path

from .value_score import ActionType, PillarID, get_value_calculator
from .action_gate import GateDecision, get_action_gate
from .action_learning import ActionOutcome, get_action_learner

logger = logging.getLogger("papito.metrics")


@dataclass
class MetricSnapshot:
    """A point-in-time snapshot of metrics."""
    timestamp: datetime
    metrics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics,
        }


@dataclass
class PillarPerformance:
    """Performance stats for a single pillar."""
    pillar_id: PillarID
    average_score: float
    min_score: float
    max_score: float
    sample_count: int
    trend: str  # "improving", "declining", "stable"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pillar_id": self.pillar_id.value,
            "pillar_name": self.pillar_id.name,
            "average_score": round(self.average_score, 2),
            "min_score": round(self.min_score, 2),
            "max_score": round(self.max_score, 2),
            "sample_count": self.sample_count,
            "trend": self.trend,
        }


class ValueMetricsDashboard:
    """
    Dashboard for monitoring Value Score Intelligence system.
    
    Provides comprehensive metrics on:
    - Action pass/block rates
    - Pillar performance over time
    - Learning system effectiveness
    - System health indicators
    
    Usage:
        dashboard = ValueMetricsDashboard()
        
        # Get overview
        overview = dashboard.get_overview()
        
        # Get action stats
        action_stats = dashboard.get_action_metrics()
        
        # Get pillar performance
        pillar_stats = dashboard.get_pillar_metrics()
        
        # Export data
        dashboard.export_metrics("metrics_export.json")
    """
    
    def __init__(self, history_hours: int = 24):
        """Initialize the metrics dashboard.
        
        Args:
            history_hours: Hours of history to track
        """
        self.history_hours = history_hours
        
        # Get component instances
        self.calculator = get_value_calculator()
        self.gate = get_action_gate()
        self.learner = get_action_learner()
        
        # Metrics history
        self._snapshots: List[MetricSnapshot] = []
        self._pillar_history: Dict[str, List[tuple[datetime, float]]] = {}
        
        logger.info("ValueMetricsDashboard initialized")
    
    def get_overview(self) -> Dict[str, Any]:
        """Get high-level system overview.
        
        Returns:
            Overview metrics including health score
        """
        gate_stats = self.gate.get_stats()
        learner_stats = self.learner.get_stats()
        
        # Calculate health score (0-100)
        health_score = self._calculate_health_score(gate_stats, learner_stats)
        
        # Determine status
        if health_score >= 80:
            status = "healthy"
            status_emoji = "🟢"
        elif health_score >= 60:
            status = "moderate"
            status_emoji = "🟡"
        else:
            status = "needs_attention"
            status_emoji = "🔴"
        
        return {
            "status": status,
            "status_emoji": status_emoji,
            "health_score": health_score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_actions_evaluated": gate_stats.get("total_evaluated", 0),
                "actions_passed": gate_stats.get("total_passed", 0),
                "actions_blocked": gate_stats.get("total_blocked", 0),
                "pass_rate": round(gate_stats.get("pass_rate", 0) * 100, 1),
                "learning_records": learner_stats.get("total_records", 0),
                "insights_generated": learner_stats.get("insights_generated", 0),
            },
            "thresholds": {
                "default": self.calculator.default_threshold,
                "by_action": self.calculator.thresholds,
            },
        }
    
    def get_action_metrics(self) -> Dict[str, Any]:
        """Get detailed action metrics by type.
        
        Returns:
            Metrics broken down by action type
        """
        gate_stats = self.gate.get_stats()
        learner_stats = self.learner.get_stats()
        
        action_breakdown = {}
        stats_by_type = learner_stats.get("stats_by_action_type", {})
        
        for action_type in ActionType:
            type_stats = stats_by_type.get(action_type.value, {})
            total = type_stats.get("total", 0)
            
            if total > 0:
                action_breakdown[action_type.value] = {
                    "total": total,
                    "blocked": type_stats.get("blocked", 0),
                    "success": type_stats.get("success", 0),
                    "neutral": type_stats.get("neutral", 0),
                    "failure": type_stats.get("failure", 0),
                    "error": type_stats.get("error", 0),
                    "pass_rate": round((type_stats.get("success", 0) + type_stats.get("neutral", 0)) / total * 100, 1),
                    "block_rate": round(type_stats.get("blocked", 0) / total * 100, 1),
                    "threshold": self.calculator.thresholds.get(action_type, self.calculator.default_threshold),
                }
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall": {
                "total_evaluated": gate_stats.get("total_evaluated", 0),
                "pass_rate": round(gate_stats.get("pass_rate", 0) * 100, 1),
                "average_score": round(gate_stats.get("average_score", 0), 1),
            },
            "by_action_type": action_breakdown,
            "decision_breakdown": {
                "passed": gate_stats.get("total_passed", 0),
                "blocked": gate_stats.get("total_blocked", 0),
                "deferred": gate_stats.get("total_deferred", 0),
                "escalated": gate_stats.get("total_escalated", 0),
            },
        }
    
    def get_pillar_metrics(self) -> Dict[str, Any]:
        """Get pillar-level performance metrics.
        
        Returns:
            Performance metrics for each ADD VALUE pillar
        """
        learner_stats = self.learner.get_stats()
        pillar_data = learner_stats.get("pillars_tracked", 0)
        
        pillar_metrics = {}
        
        for pillar in PillarID:
            # Get pillar history from learner
            history = self.learner._pillar_performance.get(pillar.value, [])
            
            if history:
                scores = [s for s, _ in history[-100:]]  # Last 100 samples
                
                performance = PillarPerformance(
                    pillar_id=pillar,
                    average_score=sum(scores) / len(scores),
                    min_score=min(scores),
                    max_score=max(scores),
                    sample_count=len(scores),
                    trend=self._calculate_trend(scores),
                )
                
                pillar_metrics[pillar.value] = performance.to_dict()
            else:
                pillar_metrics[pillar.value] = {
                    "pillar_id": pillar.value,
                    "pillar_name": pillar.name,
                    "status": "no_data",
                }
        
        # Find weak pillars (consistently low scores)
        weak_pillars = [
            pid for pid, data in pillar_metrics.items()
            if data.get("average_score", 100) < 50 and data.get("sample_count", 0) > 10
        ]
        
        # Find strong pillars
        strong_pillars = [
            pid for pid, data in pillar_metrics.items()
            if data.get("average_score", 0) > 75 and data.get("sample_count", 0) > 10
        ]
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pillars": pillar_metrics,
            "analysis": {
                "weak_pillars": weak_pillars,
                "strong_pillars": strong_pillars,
                "recommendation": self._get_pillar_recommendation(weak_pillars),
            },
            "weights": {p.value: w for p, w in self.calculator.DEFAULT_WEIGHTS.items()},
        }
    
    def get_learning_metrics(self) -> Dict[str, Any]:
        """Get learning system metrics.
        
        Returns:
            Learning insights and improvement tracking
        """
        learner_stats = self.learner.get_stats()
        
        # Get recent insights
        recent_insights = []
        for insight in self.learner._insights[-10:]:  # Last 10 insights
            if isinstance(insight, dict):
                recent_insights.append(insight)
        
        # Content pattern analysis
        content_patterns = {}
        for pattern, scores in list(self.learner._content_patterns.items())[:10]:
            if scores:
                content_patterns[pattern] = {
                    "sample_count": len(scores),
                    "average_engagement": round(sum(scores) / len(scores), 2),
                }
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overview": {
                "total_records": learner_stats.get("total_records", 0),
                "insights_generated": learner_stats.get("insights_generated", 0),
                "insights_applied": learner_stats.get("insights_applied", 0),
            },
            "recent_insights": recent_insights,
            "content_patterns": content_patterns,
            "recommendation": self._get_learning_recommendation(learner_stats),
        }
    
    def export_metrics(self, filepath: str | Path = None) -> Dict[str, Any]:
        """Export all metrics to a file.
        
        Args:
            filepath: Optional path to export to
            
        Returns:
            Complete metrics export
        """
        export_data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "export_version": "1.0",
            "overview": self.get_overview(),
            "action_metrics": self.get_action_metrics(),
            "pillar_metrics": self.get_pillar_metrics(),
            "learning_metrics": self.get_learning_metrics(),
        }
        
        if filepath:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, "w") as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Metrics exported to {filepath}")
        
        return export_data
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get actionable recommendations for improvement.
        
        Returns:
            List of prioritized recommendations
        """
        recommendations = []
        
        # Check pass rate
        gate_stats = self.gate.get_stats()
        pass_rate = gate_stats.get("pass_rate", 0)
        
        if pass_rate < 0.3:
            recommendations.append({
                "priority": "high",
                "area": "pass_rate",
                "issue": "Very low pass rate - most actions being blocked",
                "suggestion": "Review threshold settings or improve context gathering",
                "metrics": {"current_pass_rate": round(pass_rate * 100, 1)},
            })
        elif pass_rate > 0.9:
            recommendations.append({
                "priority": "medium",
                "area": "pass_rate",
                "issue": "Very high pass rate - gate may be too permissive",
                "suggestion": "Consider raising thresholds for quality control",
                "metrics": {"current_pass_rate": round(pass_rate * 100, 1)},
            })
        
        # Check pillar performance
        pillar_metrics = self.get_pillar_metrics()
        weak_pillars = pillar_metrics["analysis"]["weak_pillars"]
        
        if weak_pillars:
            recommendations.append({
                "priority": "high",
                "area": "pillars",
                "issue": f"Consistently weak pillars: {', '.join(weak_pillars)}",
                "suggestion": "Focus on improving these aspects of value delivery",
                "metrics": {"weak_pillars": weak_pillars},
            })
        
        # Check learning data
        learner_stats = self.learner.get_stats()
        if learner_stats.get("total_records", 0) < 50:
            recommendations.append({
                "priority": "low",
                "area": "learning",
                "issue": "Limited learning data available",
                "suggestion": "Continue operating to build more data for insights",
                "metrics": {"current_records": learner_stats.get("total_records", 0)},
            })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 99))
        
        return recommendations
    
    def _calculate_health_score(self, gate_stats: Dict, learner_stats: Dict) -> float:
        """Calculate overall health score (0-100)."""
        score = 50  # Base score
        
        # Pass rate contribution (up to +20)
        pass_rate = gate_stats.get("pass_rate", 0)
        if 0.3 <= pass_rate <= 0.8:
            score += 20  # Healthy range
        elif 0.2 <= pass_rate <= 0.9:
            score += 10  # Acceptable
        
        # Average score contribution (up to +15)
        avg_score = gate_stats.get("average_score", 0)
        if avg_score >= 70:
            score += 15
        elif avg_score >= 60:
            score += 10
        elif avg_score >= 50:
            score += 5
        
        # Learning data contribution (up to +10)
        records = learner_stats.get("total_records", 0)
        if records >= 500:
            score += 10
        elif records >= 100:
            score += 5
        elif records >= 50:
            score += 2
        
        # Insights applied contribution (up to +5)
        insights_applied = learner_stats.get("insights_applied", 0)
        if insights_applied >= 5:
            score += 5
        elif insights_applied >= 1:
            score += 2
        
        return min(100, max(0, score))
    
    def _calculate_trend(self, scores: List[float]) -> str:
        """Calculate trend direction from scores."""
        if len(scores) < 10:
            return "insufficient_data"
        
        # Compare first half vs second half
        mid = len(scores) // 2
        first_half_avg = sum(scores[:mid]) / mid
        second_half_avg = sum(scores[mid:]) / (len(scores) - mid)
        
        diff = second_half_avg - first_half_avg
        
        if diff > 5:
            return "improving"
        elif diff < -5:
            return "declining"
        else:
            return "stable"
    
    def _get_pillar_recommendation(self, weak_pillars: List[str]) -> str:
        """Generate recommendation based on weak pillars."""
        if not weak_pillars:
            return "All pillars performing well - maintain current approach"
        
        # Specific recommendations for known pillars
        recommendations = {
            "awareness": "Improve context gathering before responding",
            "define": "Clarify response objectives and target outcomes",
            "devise": "Develop more creative response strategies",
            "validate": "Double-check responses against value criteria",
            "act_upon": "Ensure responses are actionable for recipients",
            "learn": "Incorporate more learnings from past interactions",
            "understand": "Deepen understanding of user context and needs",
            "evolve": "Adapt responses based on changing trends",
        }
        
        specific_recs = [recommendations.get(p, "") for p in weak_pillars if p in recommendations]
        
        if specific_recs:
            return "; ".join(filter(None, specific_recs))
        
        return f"Focus on improving: {', '.join(weak_pillars)}"
    
    def _get_learning_recommendation(self, learner_stats: Dict) -> str:
        """Generate recommendation for learning system."""
        records = learner_stats.get("total_records", 0)
        insights = learner_stats.get("insights_generated", 0)
        applied = learner_stats.get("insights_applied", 0)
        
        if records < 50:
            return "Continue operating to gather more learning data"
        elif insights == 0:
            return "Run analysis to generate insights from accumulated data"
        elif applied == 0 and insights > 0:
            return "Review and apply generated insights to improve scoring"
        else:
            return "Learning system is functioning - continue monitoring"


# Global dashboard instance
_dashboard: ValueMetricsDashboard | None = None


def get_metrics_dashboard() -> ValueMetricsDashboard:
    """Get the global metrics dashboard instance."""
    global _dashboard
    if _dashboard is None:
        _dashboard = ValueMetricsDashboard()
    return _dashboard


# FastAPI routes for webhook server integration
def create_metrics_routes():
    """Create FastAPI routes for metrics endpoints.
    
    Returns:
        FastAPI router with metrics endpoints
    """
    try:
        from fastapi import APIRouter
        from fastapi.responses import JSONResponse
    except ImportError:
        logger.warning("FastAPI not available - metrics routes not created")
        return None
    
    router = APIRouter(prefix="/metrics", tags=["Metrics"])
    
    @router.get("/overview")
    async def metrics_overview():
        """Get system overview metrics."""
        dashboard = get_metrics_dashboard()
        return JSONResponse(content=dashboard.get_overview())
    
    @router.get("/actions")
    async def metrics_actions():
        """Get action-level metrics."""
        dashboard = get_metrics_dashboard()
        return JSONResponse(content=dashboard.get_action_metrics())
    
    @router.get("/pillars")
    async def metrics_pillars():
        """Get pillar performance metrics."""
        dashboard = get_metrics_dashboard()
        return JSONResponse(content=dashboard.get_pillar_metrics())
    
    @router.get("/learning")
    async def metrics_learning():
        """Get learning system metrics."""
        dashboard = get_metrics_dashboard()
        return JSONResponse(content=dashboard.get_learning_metrics())
    
    @router.get("/recommendations")
    async def metrics_recommendations():
        """Get improvement recommendations."""
        dashboard = get_metrics_dashboard()
        return JSONResponse(content=dashboard.get_recommendations())
    
    @router.get("/export")
    async def metrics_export():
        """Export all metrics."""
        dashboard = get_metrics_dashboard()
        return JSONResponse(content=dashboard.export_metrics())
    
    return router
