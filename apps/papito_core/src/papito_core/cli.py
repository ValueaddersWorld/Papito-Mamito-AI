"""Command-line interface for Papito Mamito workflows."""

from __future__ import annotations

import csv
import json
import time
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from .automation import AnalyticsSummary, ReleaseScheduler, StreamingAnalyticsService
from .config import PapitoPaths
from .engines import SunoClient, SunoError
from .fanbase import FanbaseRegistry
from .models import (
    AudioGenerationResult,
    BlogBrief,
    FanProfile,
    MerchItem,
    ReleasePlan,
    ReleaseTrack,
    SongIdeationRequest,
)
from .settings import get_settings
from .storage import ReleaseCatalog
from .utils import timestamped_filename, write_text
from .voice import describe_voice
from .workflows import BlogWorkflow, MusicWorkflow, ReleaseWorkflow

app = typer.Typer(help="Papito Mamito AI creative control center.", add_completion=False)
console = Console()

paths = PapitoPaths()
paths.ensure()
catalog = ReleaseCatalog(paths=paths)
fanbase_registry = FanbaseRegistry(paths=paths)

fan_app = typer.Typer(help="Manage the Papito fanbase.")
merch_app = typer.Typer(help="Manage merch offerings.")
app.add_typer(fan_app, name="fan")
app.add_typer(merch_app, name="merch")


@app.command("voice")
def voice_profile() -> None:
    """Display Papito Mamito's voice guide."""

    console.print(Panel(Markdown(describe_voice()), title="Papito Voice Blueprint"))


@app.command("blog")
def blog_draft(
    title: str = typer.Option(..., prompt=True, help="Blog headline."),
    focus_track: Optional[str] = typer.Option(None, help="Track featured in this entry."),
    gratitude_theme: str = typer.Option("Grateful for the journey.", help="Gratitude focus."),
    empowerment_lesson: str = typer.Option("Own your greatness daily.", help="Empowerment lesson."),
    unity_message: str = typer.Option("We move together, stronger.", help="Community focus."),
    call_to_action: str = typer.Option(
        "Share this blessing with someone building their dream.",
        help="Closing invitation.",
    ),
    save: bool = typer.Option(False, help="Persist the draft to content/blogs."),
) -> None:
    """Generate a Papito-style daily blog entry."""

    workflow = BlogWorkflow()
    brief = BlogBrief(
        title=title,
        focus_track=focus_track,
        gratitude_theme=gratitude_theme,
        empowerment_lesson=empowerment_lesson,
        unity_message=unity_message,
        call_to_action=call_to_action,
    )
    draft = workflow.generate(brief)

    console.print(Panel(Markdown(f"# {draft.title}\n\n{draft.body}"), title="Daily Blog Draft"))

    if save:
        filename = timestamped_filename(brief.title)
        path = paths.blogs / filename
        write_text(path, f"# {draft.title}\n\n{draft.body}\n")
        console.print(f"[green]Saved blog to[/green] {path.relative_to(paths.root)}")


@fan_app.command("add")
def fan_add(
    name: str = typer.Option(..., prompt=True, help="Fan name or alias."),
    location: Optional[str] = typer.Option(None, help="Where the supporter is located."),
    support_level: str = typer.Option("friend", help="Support level (friend, core, vip, investor, etc.)."),
    favorite_track: Optional[str] = typer.Option(None, help="Fan's favourite Papito track."),
    notes: Optional[str] = typer.Option(None, help="Additional notes or shout-out message."),
) -> None:
    """Add a supporter to the fanbase registry."""

    fan = FanProfile(
        name=name,
        location=location,
        support_level=support_level,
        favorite_track=favorite_track,
        notes=notes,
    )
    fanbase_registry.add_fan(fan)
    console.print(f"[green]Added fan:[/green] {fan.name} ({fan.support_level})")


@fan_app.command("list")
def fan_list() -> None:
    """List registered supporters."""

    fans = fanbase_registry.list_fans()
    if not fans:
        console.print("[yellow]No fans recorded yet. Add one with `papito fan add`.[/yellow]")
        return

    table = Table(title="Papito Fanbase")
    table.add_column("Name", style="cyan")
    table.add_column("Support Level")
    table.add_column("Location")
    table.add_column("Favourite Track")
    table.add_column("Notes")
    for fan in fans:
        table.add_row(
            fan.name,
            fan.support_level,
            fan.location or "n/a",
            fan.favorite_track or "n/a",
            fan.notes or "",
        )
    console.print(table)


@fan_app.command("shoutouts")
def fan_shoutouts(limit: int = typer.Option(5, help="How many fans to shout out.")) -> None:
    """Generate gratitude shout-outs for top supporters."""

    fans = fanbase_registry.list_fans()
    if not fans:
        console.print("[yellow]No supporters found. Add fans before creating shout-outs.[/yellow]")
        return

    sorted_fans = sorted(fans, key=lambda f: f.join_date, reverse=True)
    shoutouts = sorted_fans[: max(limit, 1)]
    console.print("[bold green]Gratitude roll call:[/bold green]")
    for fan in shoutouts:
        location = f" from {fan.location}" if fan.location else ""
        track = f" vibing to '{fan.favorite_track}'" if fan.favorite_track else ""
        console.print(f"- [magenta]{fan.name}[/magenta]{location} ({fan.support_level}){track}")


@merch_app.command("add")
def merch_add(
    sku: str = typer.Option(..., prompt=True, help="Unique SKU identifier."),
    name: str = typer.Option(..., prompt=True, help="Merch item name."),
    description: str = typer.Option(..., prompt=True, help="Short description."),
    price: float = typer.Option(..., prompt=True, min=0, help="Price for the item."),
    url: Optional[str] = typer.Option(None, help="Purchase link."),
    inventory: Optional[int] = typer.Option(None, min=0, help="Available inventory (if tracked)."),
    currency: str = typer.Option("USD", help="Currency code."),
) -> None:
    """Add or update a merch item."""

    items = {item.sku: item for item in fanbase_registry.list_merch()}
    items[sku] = MerchItem(
        sku=sku,
        name=name,
        description=description,
        price=price,
        currency=currency,
        url=url,
        inventory=inventory,
    )
    fanbase_registry.sync_merch(list(items.values()))
    console.print(f"[green]Merch catalog updated with SKU {sku}.[/green]")


@merch_app.command("list")
def merch_list() -> None:
    """Display current merch catalog."""

    items = fanbase_registry.list_merch()
    if not items:
        console.print("[yellow]Merch catalog is empty. Add items with `papito merch add`.[/yellow]")
        return

    table = Table(title="Papito Merch Catalog")
    table.add_column("SKU", style="cyan")
    table.add_column("Name")
    table.add_column("Price")
    table.add_column("Inventory")
    table.add_column("Link")
    for item in items:
        price_display = f"{item.price:.2f} {item.currency}"
        inventory_display = str(item.inventory) if item.inventory is not None else "∞"
        table.add_row(
            item.sku,
            item.name,
            price_display,
            inventory_display,
            item.url or "n/a",
        )
    console.print(table)


@app.command("song")
def song_ideation(
    title_hint: Optional[str] = typer.Option(None, help="Optional working title."),
    mood: str = typer.Option("uplifting", help="Mood descriptor."),
    tempo_bpm: int = typer.Option(108, min=60, max=180, help="Tempo in BPM."),
    key: str = typer.Option("A Minor", help="Primary musical key."),
    theme_focus: str = typer.Option("gratitude", help="Core theme."),
    story_seed: Optional[str] = typer.Option(None, help="Narrative idea."),
    save: bool = typer.Option(False, help="Persist track JSON to content/releases/tracks."),
    audio: bool = typer.Option(False, help="Attempt Suno audio generation (requires SUNO_API_KEY)."),
    audio_tag: List[str] = typer.Option(
        [],
        "--audio-tag",
        help="Additional tag to send with Suno audio requests. Can be passed multiple times.",
    ),
    audio_duration: Optional[int] = typer.Option(
        None,
        "--audio-duration",
        min=30,
        max=300,
        help="Desired audio length in seconds (30-300).",
    ),
    instrumental: bool = typer.Option(False, help="Generate instrumental audio."),
    poll: bool = typer.Option(
        False,
        help="Poll Suno for task completion after submission (basic polling).",
    ),
    poll_attempts: int = typer.Option(
        12,
        help="Maximum polling attempts when --poll is enabled.",
    ),
    poll_interval: float = typer.Option(
        5.0,
        help="Seconds between polling attempts when --poll is enabled.",
    ),
) -> None:
    """Generate a track concept."""

    workflow = MusicWorkflow()
    request = SongIdeationRequest(
        title_hint=title_hint,
        mood=mood,
        tempo_bpm=tempo_bpm,
        key=key,
        theme_focus=theme_focus,
        story_seed=story_seed,
    )
    try:
        track, audio_result = workflow.compose(
            request,
            generate_audio=audio,
            audio_tags=audio_tag,
            audio_duration_seconds=audio_duration,
            instrumental=instrumental,
        )
    except RuntimeError as exc:
        console.print(f"[yellow]{exc}[/yellow]")
        track = workflow.ideate_track(request)
        audio_result = None

    if audio_result:
        audio_result = _maybe_poll_audio(
            workflow=workflow,
            initial_result=audio_result,
            poll=poll,
            poll_attempts=poll_attempts,
            poll_interval=poll_interval,
        )
        track = workflow.enrich_track_with_audio(track, audio_result)

    payload = json.dumps(track.model_dump(mode="json"), indent=2)
    console.print(Panel(Markdown(f"```json\n{payload}\n```"), title="Track Concept"))

    if save:
        filename = timestamped_filename(track.title, suffix=".json")
        path = paths.release_tracks / filename
        write_text(path, payload)
        console.print(f"[green]Saved track concept to[/green] {path.relative_to(paths.root)}")

    if audio_result:
        console.print(
            Panel(
                Markdown(f"```json\n{json.dumps(audio_result.model_dump(mode='json'), indent=2)}\n```"),
                title="Audio Generation",
            )
        )
        if audio_result.audio_url:
            console.print(f"[green]Audio ready:[/green] {audio_result.audio_url}")
        else:
            console.print(
                f"[yellow]Audio task status:[/yellow] {audio_result.status}. "
                "Use `papito song` with --poll later or call the Suno dashboard to retrieve the final mix."
            )
        updated_catalog_paths = catalog.update_track_audio(track)
        if updated_catalog_paths:
            targets = ", ".join(str(path.relative_to(paths.root)) for path in updated_catalog_paths)
            console.print(f"[green]Updated release catalog entries:[/green] {targets}")


@app.command("release")
def release_plan(
    release_title: str = typer.Option(..., prompt=True, help="Name of the release."),
    release_type: str = typer.Option("single", help="Release type (album, single, ep)."),
    release_date: str = typer.Option(
        date.today().isoformat(),
        help="Release date in YYYY-MM-DD.",
    ),
    track_files: list[Path] = typer.Option(
        [],
        "--track-file",
        "-t",
        help="Paths to JSON track specs generated by `papito song --save`.",
    ),
    save: bool = typer.Option(True, help="Persist plan to the release catalog."),
) -> None:
    """Create a release plan from one or more track specs."""

    release_type_normalized = release_type.lower()
    if release_type_normalized not in {"album", "single", "ep"}:
        raise typer.BadParameter("Release type must be one of: album, single, ep.")

    tracks: list[ReleaseTrack] = []
    for track_file in track_files:
        data = json.loads(track_file.read_text(encoding="utf-8"))
        tracks.append(ReleaseTrack.model_validate(data))

    if not tracks:
        console.print("[yellow]No track specs supplied - generating a default concept.[/yellow]")
        default_track = MusicWorkflow().ideate_track(SongIdeationRequest())
        tracks.append(default_track)

    try:
        release_date_parsed = datetime.strptime(release_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise typer.BadParameter("release-date must be in YYYY-MM-DD format.") from exc

    workflow = ReleaseWorkflow()
    plan = workflow.build_plan(
        release_title=release_title,
        release_date=release_date_parsed,
        release_type=release_type_normalized,
        tracks=tracks,
    )

    payload = json.dumps(plan.model_dump(mode="json"), indent=2)
    console.print(Panel(Markdown(f"```json\n{payload}\n```"), title="Release Plan"))

    if save:
        path = catalog.save(plan)
        console.print(f"[green]Saved release plan to[/green] {path.relative_to(paths.root)}")


@app.command("release-package")
def release_package(
    plan_path: Optional[Path] = typer.Option(
        None,
        "--plan-path",
        help="Path to a release plan JSON file.",
    ),
    release_title: Optional[str] = typer.Option(
        None,
        "--release-title",
        help="Lookup a plan by title from the catalog.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        help="Destination file for the distribution payload JSON.",
    ),
    audio_required: bool = typer.Option(
        False,
        "--audio-required",
        help="Fail if tracks are missing audio assets.",
    ),
) -> None:
    """Generate a distribution-ready payload for streaming platforms."""

    plan: ReleasePlan | None = None
    if plan_path:
        data = json.loads(plan_path.read_text(encoding="utf-8"))
        plan = ReleasePlan.model_validate(data)
    elif release_title:
        for existing_plan_path in catalog.list():
            data = json.loads(existing_plan_path.read_text(encoding="utf-8"))
            candidate = ReleasePlan.model_validate(data)
            if candidate.release_title.lower() == release_title.lower():
                plan = candidate
                break
        if plan is None:
            raise typer.BadParameter(f"Release '{release_title}' not found in catalog.")
    else:
        raise typer.BadParameter("Provide either --plan-path or --release-title.")

    payload_tracks: list[dict[str, object]] = []
    missing_audio: list[str] = []
    for track in plan.tracks:
        audio = track.audio
        if audio is None or not audio.audio_url:
            missing_audio.append(track.title)
        payload_tracks.append(
            {
                "title": track.title,
                "tempo_bpm": track.tempo_bpm,
                "key": track.key,
                "mood": track.mood,
                "theme": track.theme,
                "audio_url": audio.audio_url if audio else None,
                "preview_url": audio.preview_url if audio else None,
                "lyric": audio.lyric if audio else None,
            }
        )

    if missing_audio and audio_required:
        raise typer.BadParameter(
            f"Tracks missing audio assets: {', '.join(missing_audio)}. Generate audio before packaging."
        )

    distribution_payload = {
        "release_title": plan.release_title,
        "release_date": plan.release_date.isoformat(),
        "distribution_targets": plan.distribution_targets,
        "tracks": payload_tracks,
        "notes": {
            "missing_audio": missing_audio,
        },
    }

    destination = output or (
        paths.distribution_packages / timestamped_filename(plan.release_title, suffix=".json")
    )
    write_text(destination, json.dumps(distribution_payload, indent=2))
    console.print(f"[green]Distribution payload saved to[/green] {destination.relative_to(paths.root)}")

@app.command("analytics")
def analytics_summary(
    input_path: Path = typer.Argument(..., exists=True, dir_okay=False, help="Path to analytics JSON data."),
    save: bool = typer.Option(False, help="Persist the summary to content/analytics."),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        help="Optional path to write the analytics summary JSON.",
    ),
) -> None:
    """Aggregate streaming analytics from a JSON payload."""

    service = StreamingAnalyticsService()
    report = service.from_path(input_path)

    summary_table = Table(title="Streaming Analytics Summary")
    summary_table.add_column("Metric", style="cyan", no_wrap=True)
    summary_table.add_column("Value", style="magenta")
    summary_table.add_row("Timeframe start", report.timeframe_start.isoformat())
    summary_table.add_row("Timeframe end", report.timeframe_end.isoformat())
    summary_table.add_row("Total streams", f"{report.total_streams:,}")
    summary_table.add_row("Total listeners", f"{report.total_listeners:,}")
    summary_table.add_row("Total saves", f"{report.total_saves:,}")
    summary_table.add_row("Top platforms", ", ".join(report.top_platforms) or "n/a")

    breakdown_table = Table(title="Platform Breakdown")
    breakdown_table.add_column("Platform")
    breakdown_table.add_column("Streams", justify="right")
    breakdown_table.add_column("Listeners", justify="right")
    breakdown_table.add_column("Saves", justify="right")
    breakdown_table.add_column("Followers", justify="right")

    for platform, stats in sorted(report.platform_breakdown.items()):
        breakdown_table.add_row(
            platform,
            f"{stats.get('streams', 0):,}",
            f"{stats.get('listeners', 0):,}",
            f"{stats.get('saves', 0):,}",
            f"{stats.get('followers', 0):,}",
        )

    console.print(summary_table)
    console.print(breakdown_table)

    if save or output:
        target = output or (paths.analytics_reports / timestamped_filename("analytics-summary", suffix=".json"))
        write_text(target, json.dumps(report.model_dump(mode="json"), indent=2))
        log_path = paths.analytics_reports / "log.csv"
        _append_analytics_log(log_path, report)
        console.print(f"[green]Saved analytics summary to[/green] {target.relative_to(paths.root)}")


@app.command("schedule")
def schedule_release(
    plan_path: Path = typer.Argument(..., exists=True, dir_okay=False, help="Path to a release plan JSON."),
    start_date: str = typer.Option(date.today().isoformat(), help="Start date for release rollout."),
    drip_interval_days: int = typer.Option(
        2,
        min=0,
        help="Days between platform drops.",
    ),
    promo_lead_days: int = typer.Option(
        7,
        min=0,
        help="Days prior to release to start promo.",
    ),
    save: bool = typer.Option(False, help="Persist the schedule to content/schedules."),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        help="Optional path to write the schedule JSON.",
    ),
) -> None:
    """Generate a multi-platform release schedule."""

    plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
    plan = ReleasePlan.model_validate(plan_data)
    try:
        start_date_parsed = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise typer.BadParameter("start-date must be in YYYY-MM-DD format.") from exc

    scheduler = ReleaseScheduler()
    schedule = scheduler.build_schedule(
        plan,
        start_date=start_date_parsed,
        drip_interval_days=drip_interval_days,
        promo_lead_days=promo_lead_days,
    )

    table = Table(title=f"{schedule.release_title} Schedule")
    table.add_column("Date", style="green")
    table.add_column("Platform", style="cyan")
    table.add_column("Action", style="magenta")

    for action in sorted(schedule.actions, key=lambda item: item.scheduled_date):
        table.add_row(str(action.scheduled_date), action.platform, action.action)

    console.print(table)

    if save or output:
        filename = timestamped_filename(f"{schedule.release_title}-schedule", suffix=".json")
        target = output or (paths.schedule_reports / filename)
        write_text(target, json.dumps(schedule.model_dump(mode="json"), indent=2))
        console.print(f"[green]Saved schedule to[/green] {target.relative_to(paths.root)}")


@app.command("doctor")
def doctor(
    check_suno: bool = typer.Option(
        False,
        "--check-suno",
        help="Attempt a lightweight Suno API call to verify connectivity.",
    ),
    analytics_path: Optional[Path] = typer.Option(
        None,
        "--analytics-path",
        help="Optional analytics export to validate against the current schema.",
    ),
) -> None:
    """Run environment checks to validate the local Papito setup."""

    checks: list[tuple[str, bool, str]] = []

    def add_check(name: str, ok: bool, detail: str) -> None:
        checks.append((name, ok, detail))

    directories = {
        "docs": paths.docs,
        "content": paths.content,
        "blogs": paths.blogs,
        "releases": paths.releases,
        "analytics": paths.analytics_reports,
        "schedules": paths.schedule_reports,
    }
    for label, dir_path in directories.items():
        ok = dir_path.exists()
        detail = str(dir_path) if ok else f"missing -> {dir_path}"
        add_check(f"path:{label}", ok, detail)

    settings = get_settings()
    has_key = bool(settings.suno_api_key)
    add_check("Suno API key", has_key, "set" if has_key else "not set")

    if has_key or check_suno:
        if has_key:
            try:
                client = SunoClient(
                    api_key=settings.suno_api_key,
                    base_url=settings.suno_base_url,
                    model=settings.suno_model,
                    timeout=settings.suno_timeout,
                )
                add_check("Suno client initialisation", True, "ready")
                if check_suno:
                    try:
                        client.ping()
                        add_check("Suno API ping", True, "reachable")
                    except SunoError as exc:
                        add_check("Suno API ping", False, str(exc))
            except SunoError as exc:
                add_check("Suno client initialisation", False, str(exc))
        else:
            add_check("Suno client initialisation", False, "missing SUNO_API_KEY")
    else:
        add_check("Suno client initialisation", False, "skipped (no key)")

    if analytics_path:
        service = StreamingAnalyticsService()
        try:
            service.from_path(analytics_path)
            add_check("Analytics schema", True, f"validated {analytics_path}")
        except Exception as exc:  # pragma: no cover - validation failure path
            add_check("Analytics schema", False, str(exc))

    table = Table(title="Papito Doctor Report")
    table.add_column("Check")
    table.add_column("Status", style="green")
    table.add_column("Detail", style="magenta")

    overall_ok = True
    for name, ok, detail in checks:
        status_text = "OK" if ok else "FAIL"
        table.add_row(name, status_text if ok else f"[red]{status_text}[/red]", detail)
        if not ok:
            overall_ok = False

    console.print(table)
    if overall_ok:
        console.print("[green]All checks passed. Papito is ready to groove![/green]")
    else:
        console.print("[yellow]Some checks failed. Review the details above before proceeding.[/yellow]")


def _append_analytics_log(log_path: Path, report: AnalyticsSummary) -> None:
    """Append a summary row to the analytics log."""

    log_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "timeframe_start",
        "timeframe_end",
        "total_streams",
        "total_listeners",
        "total_saves",
        "top_platforms",
    ]
    row = {
        "timeframe_start": report.timeframe_start.isoformat(),
        "timeframe_end": report.timeframe_end.isoformat(),
        "total_streams": report.total_streams,
        "total_listeners": report.total_listeners,
        "total_saves": report.total_saves,
        "top_platforms": ",".join(report.top_platforms),
    }
    exists = log_path.exists()
    with log_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def _maybe_poll_audio(
    *,
    workflow: MusicWorkflow,
    initial_result: AudioGenerationResult,
    poll: bool,
    poll_attempts: int,
    poll_interval: float,
) -> AudioGenerationResult:
    """Optionally poll Suno for completion and return the final audio result."""

    if not poll:
        return initial_result

    engine = workflow.get_audio_engine()
    if engine is None or not initial_result.task_id:
        return initial_result

    current = initial_result
    for _ in range(max(poll_attempts, 0)):
        if current.status.lower() in {"complete", "completed", "ready", "succeeded"}:
            break
        time.sleep(max(poll_interval, 1.0))
        try:
            current = engine.poll(current.task_id)
        except Exception as exc:  # pragma: no cover - network failure fallback
            console.print(f"[red]Polling error:[/red] {exc}")
            break

    return current


# ============================================================
# Autonomous Agent Commands
# ============================================================

agent_app = typer.Typer(help="Manage the autonomous Papito agent.")
queue_app = typer.Typer(help="Manage the content approval queue.")
app.add_typer(agent_app, name="agent")
app.add_typer(queue_app, name="queue")


@app.command("post-now")
def post_now(
    content_type: str = typer.Option(
        "morning_blessing",
        "--content-type",
        help="Content type to generate and publish immediately (e.g. morning_blessing, music_wisdom, fan_appreciation).",
    ),
) -> None:
    """Generate and publish one post immediately using the autonomous scheduler."""

    try:
        from .automation.autonomous_scheduler import get_scheduler
    except ImportError as exc:
        console.print(f"[red]Missing dependencies:[/red] {exc}")
        raise typer.Exit(1)

    async def _run() -> None:
        scheduler = get_scheduler()
        result = await scheduler.trigger_post_now(content_type)
        if result.get("posted"):
            console.print("[green]✓ Posted successfully[/green]")
            tweet_url = result.get("tweet_url")
            if tweet_url:
                console.print(tweet_url)
        else:
            console.print("[yellow]Post generated but not published.[/yellow]")
            error = result.get("error")
            if error:
                console.print(f"[red]{error}[/red]")

    try:
        import asyncio

        asyncio.run(_run())
    except Exception as exc:
        console.print(f"[red]Post-now failed:[/red] {exc}")
        raise typer.Exit(1)


@agent_app.command("start")
def agent_start(
    interval: int = typer.Option(60, help="Seconds between agent iterations."),
    debug: bool = typer.Option(False, help="Enable debug logging."),
) -> None:
    """Start the autonomous Papito agent.
    
    The agent will continuously:
    - Generate scheduled content (morning blessing, afternoon engagement, evening spotlight)
    - Publish approved content from the queue
    - Respond to fan interactions
    - Collect platform analytics
    
    Press Ctrl+C to stop the agent.
    """
    try:
        from .automation import AutonomousAgent
    except ImportError as e:
        console.print(f"[red]Missing dependencies:[/red] {e}")
        console.print("Run: pip install firebase-admin openai anthropic apscheduler")
        raise typer.Exit(1)
    
    console.print(Panel(
        "[bold green]🎵 Starting Papito Autonomous Agent 🎵[/bold green]\n\n"
        "The agent will manage social media presence automatically.\n"
        f"Check interval: {interval} seconds\n\n"
        "Press Ctrl+C to stop.",
        title="Papito Agent"
    ))
    
    try:
        agent = AutonomousAgent(debug=debug)
        
        # Connect to platforms
        connections = agent.connect_platforms()
        
        conn_table = Table(title="Platform Connections")
        conn_table.add_column("Platform")
        conn_table.add_column("Status")
        
        for platform, connected in connections.items():
            status = "[green]✓ Connected[/green]" if connected else "[yellow]✗ Not configured[/yellow]"
            conn_table.add_row(platform.title(), status)
        
        console.print(conn_table)
        
        if not any(connections.values()):
            console.print("[yellow]Warning: No platforms connected. Agent will queue content but cannot publish.[/yellow]")
            console.print("Configure credentials in .env file. See env.example for details.")
        
        console.print("\n[bold]Agent running...[/bold]\n")
        agent.start(interval_seconds=interval)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Agent stopped by user.[/yellow]")
    except Exception as e:
        console.print(f"[red]Agent error:[/red] {e}")
        raise typer.Exit(1)


@agent_app.command("status")
def agent_status() -> None:
    """Show current agent and platform status."""
    try:
        from .automation import AutonomousAgent
        from .queue import ReviewQueue
    except ImportError as e:
        console.print(f"[red]Missing dependencies:[/red] {e}")
        raise typer.Exit(1)
    
    settings = get_settings()
    
    # Check credentials
    creds_table = Table(title="Configured Credentials")
    creds_table.add_column("Service")
    creds_table.add_column("Status")
    
    checks = [
        ("Firebase", settings.has_firebase_credentials()),
        ("Instagram", settings.has_instagram_credentials()),
        ("X / Twitter", settings.has_x_credentials()),
        ("Buffer", settings.has_buffer_credentials()),
        ("OpenAI", settings.has_openai_credentials()),
        ("Anthropic", settings.has_anthropic_credentials()),
        ("Telegram", settings.has_telegram_credentials()),
        ("Discord", settings.has_discord_credentials()),
    ]
    
    for name, configured in checks:
        status = "[green]✓ Configured[/green]" if configured else "[dim]✗ Not set[/dim]"
        creds_table.add_row(name, status)
    
    console.print(creds_table)
    
    # Queue stats
    try:
        queue = ReviewQueue()
        stats = queue.get_stats()
        
        stats_table = Table(title="Content Queue")
        stats_table.add_column("Status")
        stats_table.add_column("Count", justify="right")
        
        stats_table.add_row("Pending Review", str(stats.pending_review))
        stats_table.add_row("Approved", str(stats.approved))
        stats_table.add_row("Published", str(stats.published))
        stats_table.add_row("Rejected", str(stats.rejected))
        stats_table.add_row("Failed", str(stats.failed))
        
        console.print(stats_table)
    except Exception as e:
        console.print(f"[yellow]Could not fetch queue stats:[/yellow] {e}")


@agent_app.command("once")
def agent_once(
    debug: bool = typer.Option(False, help="Enable debug logging."),
) -> None:
    """Run a single iteration of the agent.
    
    Useful for testing or cron-based execution.
    """
    try:
        from .automation import AutonomousAgent
    except ImportError as e:
        console.print(f"[red]Missing dependencies:[/red] {e}")
        raise typer.Exit(1)
    
    console.print("[bold]Running single agent iteration...[/bold]")
    
    agent = AutonomousAgent(debug=debug)
    agent.connect_platforms()
    summary = agent.run_once()
    
    console.print(f"\n[green]Iteration complete.[/green]")
    if summary.get("errors"):
        for error in summary["errors"]:
            console.print(f"[red]Error:[/red] {error}")


@queue_app.command("list")
def queue_list(
    status: str = typer.Option("pending", help="Filter by status: pending, approved, all"),
    limit: int = typer.Option(20, help="Maximum items to show"),
) -> None:
    """List content in the review queue."""
    try:
        from .queue import ReviewQueue
        from .database import get_firebase_client
    except ImportError as e:
        console.print(f"[red]Missing dependencies:[/red] {e}")
        raise typer.Exit(1)
    
    db = get_firebase_client()
    
    if status == "pending":
        items = db.get_pending_queue_items(limit=limit)
    elif status == "approved":
        items = db.get_approved_ready_to_publish(limit=limit)
    else:
        # Get all recent items
        items = db.get_pending_queue_items(limit=limit)
    
    if not items:
        console.print(f"[yellow]No {status} items in queue.[/yellow]")
        return
    
    table = Table(title=f"Content Queue ({status})")
    table.add_column("ID", style="dim", max_width=12)
    table.add_column("Type")
    table.add_column("Platform")
    table.add_column("Title", max_width=30)
    table.add_column("Status")
    table.add_column("Scheduled")
    
    for item in items:
        scheduled = item.scheduled_at.strftime("%Y-%m-%d %H:%M") if item.scheduled_at else "ASAP"
        status_color = {
            "pending_review": "yellow",
            "approved": "green",
            "rejected": "red",
            "published": "blue",
        }.get(item.status, "white")
        
        table.add_row(
            item.id[:12] if item.id else "—",
            item.content_type,
            item.platform,
            item.title[:30] if item.title else "—",
            f"[{status_color}]{item.status}[/{status_color}]",
            scheduled
        )
    
    console.print(table)


@queue_app.command("approve")
def queue_approve(
    item_id: str = typer.Argument(..., help="Queue item ID to approve"),
) -> None:
    """Approve a content item for publishing."""
    try:
        from .queue import ReviewQueue
    except ImportError as e:
        console.print(f"[red]Missing dependencies:[/red] {e}")
        raise typer.Exit(1)
    
    queue = ReviewQueue()
    if queue.approve(item_id, reviewer="cli"):
        console.print(f"[green]✓ Approved item {item_id}[/green]")
    else:
        console.print(f"[red]Failed to approve item {item_id}[/red]")


@queue_app.command("reject")
def queue_reject(
    item_id: str = typer.Argument(..., help="Queue item ID to reject"),
    reason: str = typer.Option(..., prompt=True, help="Reason for rejection"),
) -> None:
    """Reject a content item."""
    try:
        from .queue import ReviewQueue
    except ImportError as e:
        console.print(f"[red]Missing dependencies:[/red] {e}")
        raise typer.Exit(1)
    
    queue = ReviewQueue()
    if queue.reject(item_id, reason=reason, reviewer="cli"):
        console.print(f"[green]✓ Rejected item {item_id}[/green]")
    else:
        console.print(f"[red]Failed to reject item {item_id}[/red]")


@queue_app.command("add")
def queue_add(
    content_type: str = typer.Option(..., prompt=True, help="Content type (morning_blessing, gratitude, etc)"),
    platform: str = typer.Option("instagram", help="Target platform"),
    title: str = typer.Option(..., prompt=True, help="Content title"),
    body: str = typer.Option(..., prompt=True, help="Content body/caption"),
    auto_approve: bool = typer.Option(True, help="Auto-approve (skip manual review)"),
) -> None:
    """Add content to the publishing queue."""
    try:
        from .queue import ReviewQueue
        from .queue.review_queue import ContentCategory
    except ImportError as e:
        console.print(f"[red]Missing dependencies:[/red] {e}")
        raise typer.Exit(1)
    
    # Map content type to category
    category_map = {
        "morning_blessing": ContentCategory.DAILY_BLESSING,
        "daily_blessing": ContentCategory.DAILY_BLESSING,
        "gratitude": ContentCategory.GRATITUDE,
        "fan_shoutout": ContentCategory.FAN_SHOUTOUT,
        "music_quote": ContentCategory.MUSIC_QUOTE,
        "affirmation": ContentCategory.AFFIRMATION,
        "new_release": ContentCategory.NEW_RELEASE,
        "announcement": ContentCategory.ANNOUNCEMENT,
    }
    
    category = category_map.get(content_type.lower())
    
    queue = ReviewQueue()
    item_id = queue.add_to_queue(
        content_type=content_type,
        platform=platform,
        title=title,
        body=body,
        category=category
    )
    
    console.print(f"[green]✓ Added to queue: {item_id}[/green]")
    if category and category in queue.AUTO_APPROVE_CATEGORIES:
        console.print("[dim]This content type auto-approves and will be published on schedule.[/dim]")
    else:
        console.print("[yellow]This content requires manual review before publishing.[/yellow]")


@app.command("setup-firebase")
def setup_firebase(
    service_account_path: Path = typer.Option(
        ..., 
        prompt=True,
        exists=True,
        help="Path to Firebase service account JSON file"
    ),
) -> None:
    """Configure Firebase for the autonomous agent.
    
    This command helps set up Firebase by validating the service account
    and testing the Firestore connection.
    """
    import json as json_module
    
    try:
        # Validate the JSON file
        with open(service_account_path) as f:
            creds = json_module.load(f)
        
        project_id = creds.get("project_id")
        if not project_id:
            console.print("[red]Invalid service account file: missing project_id[/red]")
            raise typer.Exit(1)
        
        console.print(f"[green]✓ Valid service account for project:[/green] {project_id}")
        
        # Show .env configuration
        console.print("\n[bold]Add these to your .env file:[/bold]\n")
        console.print(f"FIREBASE_PROJECT_ID={project_id}")
        console.print(f"FIREBASE_SERVICE_ACCOUNT_PATH={service_account_path.absolute()}")
        
        # Try to initialize Firebase
        try:
            from .database import get_firebase_client
            import os
            
            os.environ["FIREBASE_PROJECT_ID"] = project_id
            os.environ["FIREBASE_SERVICE_ACCOUNT_PATH"] = str(service_account_path.absolute())
            
            # Clear cached settings
            from .settings import get_settings
            get_settings.cache_clear()
            
            db = get_firebase_client()
            console.print("\n[green]✓ Successfully connected to Firestore![/green]")
            
        except Exception as e:
            console.print(f"\n[yellow]Could not test Firestore connection:[/yellow] {e}")
            console.print("Make sure to add the environment variables to your .env file.")
        
    except json_module.JSONDecodeError:
        console.print("[red]Invalid JSON in service account file[/red]")
        raise typer.Exit(1)


# ============================================================
# Content Calendar Commands
# ============================================================

calendar_app = typer.Typer(help="Manage the content calendar and scheduling.")
app.add_typer(calendar_app, name="calendar")


@calendar_app.command("generate")
def calendar_generate(
    days: int = typer.Option(7, help="Number of days to generate calendar for."),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        help="Optional path to save the calendar JSON.",
    ),
    preview: bool = typer.Option(True, help="Display calendar preview in terminal."),
) -> None:
    """Generate a content calendar for the next N days.
    
    Uses ContentScheduler to create optimized posting schedule with:
    - 6 daily time slots in WAT timezone
    - Content type variety (blessings, snippets, wisdom, etc.)
    - Platform-specific content (X, Instagram)
    
    Example:
        papito calendar generate --days 30 --output content_calendar.json
    """
    try:
        from .automation import ContentScheduler, ContentType
    except ImportError as e:
        console.print(f"[red]Missing dependencies:[/red] {e}")
        raise typer.Exit(1)
    
    scheduler = ContentScheduler()
    schedule = scheduler.generate_schedule(days=days)
    
    if not schedule:
        console.print("[yellow]No posts scheduled. This may happen if all slots for today have passed.[/yellow]")
        return
    
    console.print(f"\n[bold green]📅 Generated Content Calendar for {days} Days[/bold green]\n")
    console.print(f"Timezone: {scheduler.config.timezone}")
    console.print(f"Posts per day: {scheduler.config.min_posts_per_day}-{scheduler.config.max_posts_per_day}")
    console.print(f"Total posts scheduled: {len(schedule)}\n")
    
    if preview:
        # Group by date
        from collections import defaultdict
        by_date = defaultdict(list)
        
        for post in schedule:
            date_str = post.scheduled_at.strftime("%Y-%m-%d")
            by_date[date_str].append(post)
        
        for date_str in sorted(by_date.keys())[:7]:  # Show first 7 days
            posts = by_date[date_str]
            
            table = Table(title=f"📆 {date_str}")
            table.add_column("Time (WAT)", style="cyan")
            table.add_column("Content Type", style="green")
            table.add_column("Platform", style="magenta")
            
            for post in sorted(posts, key=lambda p: p.scheduled_at):
                time_str = post.scheduled_at.strftime("%H:%M")
                content_type = post.post_type.replace("_", " ").title()
                platform = post.generation_params.get("platform", "multi")
                table.add_row(time_str, content_type, platform)
            
            console.print(table)
            console.print()
        
        if len(by_date) > 7:
            console.print(f"[dim]... and {len(by_date) - 7} more days[/dim]\n")
    
    # Save to file if requested
    if output:
        import json as json_module
        
        calendar_data = {
            "generated_at": datetime.now().isoformat(),
            "timezone": scheduler.config.timezone,
            "days": days,
            "total_posts": len(schedule),
            "posts": [
                {
                    "scheduled_at": post.scheduled_at.isoformat(),
                    "post_type": post.post_type,
                    "platform": post.generation_params.get("platform"),
                    "status": post.status,
                }
                for post in schedule
            ]
        }
        
        write_text(output, json_module.dumps(calendar_data, indent=2))
        console.print(f"[green]✓ Calendar saved to[/green] {output}")


@calendar_app.command("slots")
def calendar_slots() -> None:
    """Display the configured daily posting slots.
    
    Shows the 6 optimized time slots for Papito's Afrobeat audience.
    """
    try:
        from .automation import ContentScheduler
    except ImportError as e:
        console.print(f"[red]Missing dependencies:[/red] {e}")
        raise typer.Exit(1)
    
    scheduler = ContentScheduler()
    
    console.print(f"\n[bold green]⏰ Daily Posting Slots ({scheduler.config.timezone})[/bold green]\n")
    
    table = Table(title="Optimized Posting Times")
    table.add_column("Time (WAT)", style="cyan")
    table.add_column("Priority", style="magenta")
    table.add_column("Content Types", style="green")
    table.add_column("Platforms", style="yellow")
    
    for slot in sorted(scheduler.config.posting_slots, key=lambda s: s.hour * 60 + s.minute):
        time_str = f"{slot.hour:02d}:{slot.minute:02d}"
        priority = "⭐" * min(slot.priority, 5)
        content_types = ", ".join([ct.value.replace("_", " ").title() for ct in slot.content_types])
        platforms = ", ".join(slot.platforms)
        
        table.add_row(time_str, priority, content_types, platforms)
    
    console.print(table)
    console.print(f"\n[dim]Priority indicates engagement potential (more ⭐ = higher)[/dim]")


@calendar_app.command("next")
def calendar_next() -> None:
    """Show the next scheduled posting slot.
    
    Useful for checking when the next automatic post will be generated.
    """
    try:
        from .automation import ContentScheduler
    except ImportError as e:
        console.print(f"[red]Missing dependencies:[/red] {e}")
        raise typer.Exit(1)
    
    scheduler = ContentScheduler()
    now = scheduler.get_current_time_wat()
    next_slot = scheduler.get_next_posting_slot()
    
    console.print(f"\n[bold]Current time (WAT):[/bold] {now.strftime('%Y-%m-%d %H:%M')}\n")
    
    if next_slot:
        next_time = f"{next_slot.hour:02d}:{next_slot.minute:02d}"
        content_types = ", ".join([ct.value.replace("_", " ").title() for ct in next_slot.content_types])
        
        console.print(f"[green]📍 Next posting slot:[/green] {next_time} WAT")
        console.print(f"[cyan]Content options:[/cyan] {content_types}")
        console.print(f"[magenta]Platforms:[/magenta] {', '.join(next_slot.platforms)}")
        console.print(f"[yellow]Priority:[/yellow] {'⭐' * next_slot.priority}")
    else:
        console.print("[yellow]No more slots today. First slot tomorrow is at 07:00 WAT.[/yellow]")
