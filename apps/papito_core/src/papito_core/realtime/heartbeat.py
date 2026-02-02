"""
PAPITO MAMITO AI - HEARTBEAT DAEMON
===================================
Always-on daemon that keeps Papito alive and healthy.

Features:
- Continuous health monitoring
- Automatic component restart on failure
- Scheduled task execution
- Status reporting
- Graceful shutdown handling

Architecture:
    ┌──────────────────────────────────────────────────┐
    │              HEARTBEAT DAEMON                    │
    │                                                  │
    │  ┌────────────┐  ┌────────────┐  ┌────────────┐ │
    │  │ Health     │  │ Scheduler  │  │ Component  │ │
    │  │ Monitor    │  │ (Cron)     │  │ Supervisor │ │
    │  └────────────┘  └────────────┘  └────────────┘ │
    │         │              │               │        │
    │         └──────────────┼───────────────┘        │
    │                        ▼                        │
    │              [Status Reporter]                  │
    └──────────────────────────────────────────────────┘

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .event_dispatcher import (
    Event,
    EventType,
    EventPriority,
    EventDispatcher,
    get_event_dispatcher,
)

logger = logging.getLogger("papito.heartbeat")


class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentStatus(str, Enum):
    """Component running status."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    RESTARTING = "restarting"


@dataclass
class ComponentInfo:
    """Information about a managed component."""
    name: str
    status: ComponentStatus = ComponentStatus.STOPPED
    start_func: Callable[[], Awaitable[bool]] | None = None
    stop_func: Callable[[], Awaitable[None]] | None = None
    health_check: Callable[[], Awaitable[bool]] | None = None
    
    # Stats
    started_at: datetime | None = None
    stopped_at: datetime | None = None
    restarts: int = 0
    last_error: str = ""
    consecutive_failures: int = 0
    
    def uptime_seconds(self) -> float:
        """Calculate uptime in seconds."""
        if not self.started_at or self.status != ComponentStatus.RUNNING:
            return 0.0
        return (datetime.now(timezone.utc) - self.started_at).total_seconds()


@dataclass
class ScheduledTask:
    """A scheduled task to run periodically."""
    name: str
    func: Callable[[], Awaitable[None]]
    interval_seconds: int
    last_run: datetime | None = None
    next_run: datetime | None = None
    runs: int = 0
    errors: int = 0
    enabled: bool = True
    
    def is_due(self) -> bool:
        """Check if task is due to run."""
        if not self.enabled:
            return False
        if self.next_run is None:
            return True
        return datetime.now(timezone.utc) >= self.next_run
    
    def schedule_next(self) -> None:
        """Schedule next run based on interval."""
        self.next_run = datetime.now(timezone.utc) + timedelta(seconds=self.interval_seconds)


class HeartbeatDaemon:
    """
    Always-on daemon that keeps Papito healthy and running.
    
    Features:
    - Component supervision with auto-restart
    - Scheduled task execution
    - Health status aggregation
    - Graceful shutdown on SIGTERM/SIGINT
    - Event emission for monitoring
    
    Usage:
        daemon = HeartbeatDaemon()
        
        # Register components
        daemon.register_component(
            name="x_stream",
            start_func=x_listener.start,
            stop_func=x_listener.stop,
            health_check=lambda: x_listener._running
        )
        
        # Register scheduled tasks
        daemon.schedule(
            name="post_content",
            func=content_poster,
            interval_seconds=3600
        )
        
        # Run daemon
        await daemon.run()
    """
    
    def __init__(
        self,
        heartbeat_interval: int = 30,
        max_component_restarts: int = 5,
        restart_cooldown: int = 60,
    ):
        """Initialize the heartbeat daemon.
        
        Args:
            heartbeat_interval: Seconds between health checks
            max_component_restarts: Max restarts before giving up
            restart_cooldown: Seconds to wait between restarts
        """
        self.heartbeat_interval = heartbeat_interval
        self.max_component_restarts = max_component_restarts
        self.restart_cooldown = restart_cooldown
        
        self._components: Dict[str, ComponentInfo] = {}
        self._scheduled_tasks: Dict[str, ScheduledTask] = {}
        
        self._running = False
        self._started_at: datetime | None = None
        self._shutdown_event = asyncio.Event()
        
        self.dispatcher = get_event_dispatcher()
        
        # Stats
        self._heartbeats_sent = 0
        self._tasks_executed = 0
        self._component_restarts = 0
        
        logger.info("HeartbeatDaemon initialized")
    
    def register_component(
        self,
        name: str,
        start_func: Callable[[], Awaitable[bool]],
        stop_func: Callable[[], Awaitable[None]],
        health_check: Callable[[], Awaitable[bool]] | None = None,
    ) -> None:
        """Register a component for supervision.
        
        Args:
            name: Unique component name
            start_func: Async function to start the component (returns success bool)
            stop_func: Async function to stop the component
            health_check: Async function returning True if healthy
        """
        self._components[name] = ComponentInfo(
            name=name,
            start_func=start_func,
            stop_func=stop_func,
            health_check=health_check,
        )
        logger.info(f"Registered component: {name}")
    
    def unregister_component(self, name: str) -> bool:
        """Unregister a component.
        
        Returns:
            True if component was removed
        """
        if name in self._components:
            del self._components[name]
            logger.info(f"Unregistered component: {name}")
            return True
        return False
    
    def schedule(
        self,
        name: str,
        func: Callable[[], Awaitable[None]],
        interval_seconds: int,
    ) -> None:
        """Schedule a recurring task.
        
        Args:
            name: Unique task name
            func: Async function to execute
            interval_seconds: Interval between executions
        """
        task = ScheduledTask(
            name=name,
            func=func,
            interval_seconds=interval_seconds,
        )
        task.schedule_next()
        self._scheduled_tasks[name] = task
        logger.info(f"Scheduled task: {name} (every {interval_seconds}s)")
    
    def unschedule(self, name: str) -> bool:
        """Remove a scheduled task.
        
        Returns:
            True if task was removed
        """
        if name in self._scheduled_tasks:
            del self._scheduled_tasks[name]
            logger.info(f"Unscheduled task: {name}")
            return True
        return False
    
    async def _start_component(self, comp: ComponentInfo) -> bool:
        """Start a single component.
        
        Args:
            comp: Component to start
            
        Returns:
            True if started successfully
        """
        if comp.status == ComponentStatus.RUNNING:
            return True
        
        if not comp.start_func:
            logger.warning(f"No start function for {comp.name}")
            return False
        
        comp.status = ComponentStatus.STARTING
        
        try:
            success = await comp.start_func()
            
            if success:
                comp.status = ComponentStatus.RUNNING
                comp.started_at = datetime.now(timezone.utc)
                comp.consecutive_failures = 0
                logger.info(f"Component started: {comp.name}")
                return True
            else:
                comp.status = ComponentStatus.FAILED
                comp.last_error = "start_func returned False"
                comp.consecutive_failures += 1
                logger.error(f"Component failed to start: {comp.name}")
                return False
                
        except Exception as e:
            comp.status = ComponentStatus.FAILED
            comp.last_error = str(e)
            comp.consecutive_failures += 1
            logger.exception(f"Error starting {comp.name}: {e}")
            return False
    
    async def _stop_component(self, comp: ComponentInfo) -> None:
        """Stop a single component.
        
        Args:
            comp: Component to stop
        """
        if comp.status == ComponentStatus.STOPPED:
            return
        
        if not comp.stop_func:
            comp.status = ComponentStatus.STOPPED
            return
        
        comp.status = ComponentStatus.STOPPING
        
        try:
            await comp.stop_func()
            comp.status = ComponentStatus.STOPPED
            comp.stopped_at = datetime.now(timezone.utc)
            logger.info(f"Component stopped: {comp.name}")
            
        except Exception as e:
            comp.status = ComponentStatus.STOPPED
            comp.last_error = str(e)
            logger.exception(f"Error stopping {comp.name}: {e}")
    
    async def _restart_component(self, comp: ComponentInfo) -> bool:
        """Restart a component.
        
        Args:
            comp: Component to restart
            
        Returns:
            True if restarted successfully
        """
        if comp.restarts >= self.max_component_restarts:
            logger.error(f"Max restarts reached for {comp.name}, not restarting")
            return False
        
        comp.status = ComponentStatus.RESTARTING
        comp.restarts += 1
        self._component_restarts += 1
        
        logger.info(f"Restarting component: {comp.name} (restart #{comp.restarts})")
        
        await self._stop_component(comp)
        await asyncio.sleep(self.restart_cooldown)
        
        return await self._start_component(comp)
    
    async def _check_component_health(self, comp: ComponentInfo) -> bool:
        """Check if a component is healthy.
        
        Args:
            comp: Component to check
            
        Returns:
            True if healthy
        """
        if comp.status != ComponentStatus.RUNNING:
            return False
        
        if not comp.health_check:
            return True  # No health check = assume healthy
        
        try:
            return await comp.health_check()
        except Exception as e:
            logger.warning(f"Health check failed for {comp.name}: {e}")
            return False
    
    async def _run_scheduled_tasks(self) -> None:
        """Run any scheduled tasks that are due."""
        for task in self._scheduled_tasks.values():
            if not task.is_due():
                continue
            
            try:
                logger.debug(f"Running scheduled task: {task.name}")
                await task.func()
                task.runs += 1
                task.last_run = datetime.now(timezone.utc)
                self._tasks_executed += 1
                logger.debug(f"Task completed: {task.name}")
                
            except Exception as e:
                task.errors += 1
                logger.exception(f"Scheduled task {task.name} failed: {e}")
            
            finally:
                task.schedule_next()
    
    async def _heartbeat_loop(self) -> None:
        """Main heartbeat loop."""
        logger.info("Heartbeat loop started")
        
        while self._running and not self._shutdown_event.is_set():
            try:
                # Check component health
                for name, comp in self._components.items():
                    is_healthy = await self._check_component_health(comp)
                    
                    if not is_healthy and comp.status == ComponentStatus.RUNNING:
                        logger.warning(f"Component unhealthy: {name}")
                        await self._restart_component(comp)
                
                # Run scheduled tasks
                await self._run_scheduled_tasks()
                
                # Emit heartbeat event
                self._heartbeats_sent += 1
                await self.dispatcher.emit(Event(
                    type=EventType.HEARTBEAT,
                    priority=EventPriority.LOW,
                    source="heartbeat_daemon",
                    content=f"Heartbeat #{self._heartbeats_sent}",
                    metadata=self.get_status(),
                ))
                
                # Wait for next heartbeat or shutdown
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=self.heartbeat_interval
                    )
                except asyncio.TimeoutError:
                    pass  # Normal timeout, continue loop
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(5)  # Prevent tight loop on error
        
        logger.info("Heartbeat loop stopped")
    
    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            sig_name = signal.Signals(signum).name
            logger.info(f"Received {sig_name}, initiating shutdown...")
            self._shutdown_event.set()
        
        # Handle SIGTERM and SIGINT
        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    async def start(self) -> None:
        """Start the daemon and all components."""
        if self._running:
            logger.warning("Daemon already running")
            return
        
        logger.info("=" * 60)
        logger.info("STARTING PAPITO HEARTBEAT DAEMON")
        logger.info("=" * 60)
        
        self._running = True
        self._started_at = datetime.now(timezone.utc)
        self._shutdown_event.clear()
        
        # Set up signal handlers
        self._setup_signal_handlers()
        
        # Start the event dispatcher
        await self.dispatcher.start()
        
        # Start all registered components
        for name, comp in self._components.items():
            logger.info(f"Starting component: {name}")
            await self._start_component(comp)
        
        logger.info("All components started")
    
    async def stop(self) -> None:
        """Stop the daemon and all components."""
        if not self._running:
            return
        
        logger.info("=" * 60)
        logger.info("STOPPING PAPITO HEARTBEAT DAEMON")
        logger.info("=" * 60)
        
        self._running = False
        self._shutdown_event.set()
        
        # Stop all components
        for name, comp in self._components.items():
            logger.info(f"Stopping component: {name}")
            await self._stop_component(comp)
        
        # Stop the dispatcher
        await self.dispatcher.stop()
        
        logger.info("Heartbeat daemon stopped")
    
    async def run(self) -> None:
        """Run the daemon until shutdown signal.
        
        This is the main entry point for running Papito autonomously.
        """
        await self.start()
        
        try:
            await self._heartbeat_loop()
        finally:
            await self.stop()
    
    def get_health(self) -> HealthStatus:
        """Get overall health status.
        
        Returns:
            Aggregated health status
        """
        if not self._running:
            return HealthStatus.UNKNOWN
        
        statuses = []
        for comp in self._components.values():
            if comp.status == ComponentStatus.RUNNING:
                statuses.append(HealthStatus.HEALTHY)
            elif comp.status == ComponentStatus.RESTARTING:
                statuses.append(HealthStatus.DEGRADED)
            else:
                statuses.append(HealthStatus.UNHEALTHY)
        
        if not statuses:
            return HealthStatus.HEALTHY
        
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.DEGRADED
    
    def get_status(self) -> Dict[str, Any]:
        """Get full daemon status."""
        uptime = 0.0
        if self._started_at:
            uptime = (datetime.now(timezone.utc) - self._started_at).total_seconds()
        
        return {
            "running": self._running,
            "health": self.get_health().value,
            "uptime_seconds": uptime,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "heartbeats_sent": self._heartbeats_sent,
            "tasks_executed": self._tasks_executed,
            "component_restarts": self._component_restarts,
            "components": {
                name: {
                    "status": comp.status.value,
                    "uptime_seconds": comp.uptime_seconds(),
                    "restarts": comp.restarts,
                    "last_error": comp.last_error,
                }
                for name, comp in self._components.items()
            },
            "scheduled_tasks": {
                name: {
                    "enabled": task.enabled,
                    "interval_seconds": task.interval_seconds,
                    "runs": task.runs,
                    "errors": task.errors,
                    "next_run": task.next_run.isoformat() if task.next_run else None,
                }
                for name, task in self._scheduled_tasks.items()
            },
        }


# Global daemon instance
_daemon: HeartbeatDaemon | None = None


def get_heartbeat_daemon() -> HeartbeatDaemon:
    """Get the global heartbeat daemon instance."""
    global _daemon
    if _daemon is None:
        _daemon = HeartbeatDaemon()
    return _daemon
