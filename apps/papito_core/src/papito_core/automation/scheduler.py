"""Release scheduling utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Sequence

from pydantic import BaseModel

from ..models import ReleasePlan


class ReleaseAction(BaseModel):
    """Represents a scheduled action for a release."""

    platform: str
    action: str
    scheduled_date: date


class ReleaseSchedule(BaseModel):
    """Compiled schedule for a release rollout."""

    release_title: str
    start_date: date
    actions: List[ReleaseAction]


@dataclass
class ReleaseScheduler:
    """Create multi-platform release schedules."""

    def build_schedule(
        self,
        plan: ReleasePlan,
        *,
        start_date: date,
        drip_interval_days: int = 2,
        promo_lead_days: int = 7,
    ) -> ReleaseSchedule:
        """Generate a schedule that staggers releases across platforms."""

        if drip_interval_days < 0:
            raise ValueError("drip_interval_days cannot be negative.")

        actions: List[ReleaseAction] = []
        release_day = max(start_date, plan.release_date)
        promo_day = release_day - timedelta(days=promo_lead_days)

        # Pre-release promo
        actions.append(
            ReleaseAction(
                platform="multi-channel",
                action="Launch gratitude livestream teaser",
                scheduled_date=promo_day,
            )
        )

        for index, platform in enumerate(plan.distribution_targets):
            drop_date = release_day + timedelta(days=index * drip_interval_days)
            actions.append(
                ReleaseAction(
                    platform=platform,
                    action=f"Distribute '{plan.release_title}'",
                    scheduled_date=drop_date,
                )
            )
            actions.append(
                ReleaseAction(
                    platform=platform,
                    action="Publish behind-the-scenes spotlight",
                    scheduled_date=drop_date + timedelta(days=1),
                )
            )

        # Post-release gratitude roll-call
        actions.append(
            ReleaseAction(
                platform="multi-channel",
                action="Share gratitude roll-call and analytics recap",
                scheduled_date=release_day + timedelta(days=max(len(plan.distribution_targets), 1) * drip_interval_days + 2),
            )
        )

        return ReleaseSchedule(
            release_title=plan.release_title,
            start_date=start_date,
            actions=actions,
        )
