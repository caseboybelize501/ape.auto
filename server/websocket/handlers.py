"""
APE - Autonomous Production Engineer
WebSocket Handlers

Handlers for different types of real-time updates.
"""

from typing import Optional
from datetime import datetime
import json

from server.websocket.manager import manager


class GenerationProgressHandler:
    """
    Handler for generation progress updates.
    """
    
    @staticmethod
    async def on_level_start(
        run_id: str,
        level: int,
        file_count: int
    ) -> None:
        """
        Notify when a generation level starts.
        
        Args:
            run_id: Generation run ID
            level: Level number
            file_count: Number of files in level
        """
        await manager.broadcast_to_room(
            run_id,
            {
                "type": "generation.level_start",
                "run_id": run_id,
                "level": level,
                "file_count": file_count,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    @staticmethod
    async def on_file_complete(
        run_id: str,
        level: int,
        file_path: str,
        status: str,
        duration_ms: Optional[int] = None
    ) -> None:
        """
        Notify when a file generation completes.
        
        Args:
            run_id: Generation run ID
            level: Level number
            file_path: Generated file path
            status: complete/failed
            duration_ms: Generation duration
        """
        await manager.broadcast_to_room(
            run_id,
            {
                "type": "generation.file_complete",
                "run_id": run_id,
                "level": level,
                "file_path": file_path,
                "status": status,
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    @staticmethod
    async def on_level_complete(
        run_id: str,
        level: int,
        passed: int,
        failed: int,
        duration_ms: Optional[int] = None
    ) -> None:
        """
        Notify when a generation level completes.
        
        Args:
            run_id: Generation run ID
            level: Level number
            passed: Files that passed critic
            failed: Files that failed critic
            duration_ms: Level duration
        """
        await manager.broadcast_to_room(
            run_id,
            {
                "type": "generation.level_complete",
                "run_id": run_id,
                "level": level,
                "passed": passed,
                "failed": failed,
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    @staticmethod
    async def on_run_complete(
        run_id: str,
        total_files: int,
        total_passed: int,
        duration_ms: Optional[int] = None
    ) -> None:
        """
        Notify when a generation run completes.
        
        Args:
            run_id: Generation run ID
            total_files: Total files generated
            total_passed: Files that passed all critic passes
            duration_ms: Total run duration
        """
        await manager.broadcast_to_room(
            run_id,
            {
                "type": "generation.run_complete",
                "run_id": run_id,
                "total_files": total_files,
                "total_passed": total_passed,
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


class CriticResultHandler:
    """
    Handler for critic validation results.
    """
    
    @staticmethod
    async def on_pass_result(
        run_id: str,
        level: int,
        file_path: str,
        pass_number: int,
        passed: bool,
        details: Optional[dict] = None
    ) -> None:
        """
        Notify when a critic pass completes.
        
        Args:
            run_id: Generation run ID
            level: Level number
            file_path: File being critiqued
            pass_number: Pass number (1-4)
            passed: Whether pass succeeded
            details: Pass-specific details
        """
        pass_names = {
            1: "syntax",
            2: "contract",
            3: "completeness",
            4: "logic",
        }
        
        await manager.broadcast_to_room(
            run_id,
            {
                "type": "critic.pass_result",
                "run_id": run_id,
                "level": level,
                "file_path": file_path,
                "pass_number": pass_number,
                "pass_name": pass_names.get(pass_number, "unknown"),
                "passed": passed,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    @staticmethod
    async def on_repair_start(
        run_id: str,
        level: int,
        file_path: str,
        attempt: int
    ) -> None:
        """
        Notify when a repair attempt starts.
        
        Args:
            run_id: Generation run ID
            level: Level number
            file_path: File being repaired
            attempt: Attempt number
        """
        await manager.broadcast_to_room(
            run_id,
            {
                "type": "critic.repair_start",
                "run_id": run_id,
                "level": level,
                "file_path": file_path,
                "attempt": attempt,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    @staticmethod
    async def on_halt(
        run_id: str,
        level: int,
        file_path: str,
        failing_passes: list,
        attempts: int
    ) -> None:
        """
        Notify when generation halts due to critic failures.
        
        Args:
            run_id: Generation run ID
            level: Level number
            file_path: File that caused halt
            failing_passes: List of failing pass numbers
            attempts: Number of repair attempts
        """
        await manager.broadcast_to_room(
            run_id,
            {
                "type": "critic.halt",
                "run_id": run_id,
                "level": level,
                "file_path": file_path,
                "failing_passes": failing_passes,
                "attempts": attempts,
                "gate": "GATE-4",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


class NotificationHandler:
    """
    Handler for system notifications.
    """
    
    @staticmethod
    async def send_notification(
        tenant_id: str,
        title: str,
        message: str,
        level: str = "info",
        data: Optional[dict] = None
    ) -> int:
        """
        Send a notification to all tenant connections.
        
        Args:
            tenant_id: Target tenant ID
            title: Notification title
            message: Notification message
            level: Notification level (info, warning, error, critical)
            data: Additional data
        
        Returns:
            Number of connections notified
        """
        return await manager.send_to_tenant(
            tenant_id,
            {
                "type": "notification",
                "level": level,
                "title": title,
                "message": message,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    @staticmethod
    async def send_gate_alert(
        tenant_id: str,
        gate: str,
        run_id: str,
        action_required: str
    ) -> int:
        """
        Send a gate approval alert.
        
        Args:
            tenant_id: Target tenant ID
            gate: Gate name (GATE-1, GATE-2, GATE-3, GATE-4)
            run_id: Generation run ID
            action_required: Required action
        
        Returns:
            Number of connections notified
        """
        return await manager.send_to_tenant(
            tenant_id,
            {
                "type": "gate_alert",
                "gate": gate,
                "run_id": run_id,
                "action_required": action_required,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    @staticmethod
    async def send_production_alert(
        tenant_id: str,
        alert_type: str,
        deployment_id: str,
        details: dict
    ) -> int:
        """
        Send a production monitoring alert.
        
        Args:
            tenant_id: Target tenant ID
            alert_type: Alert type (regression, rollback, self_repair)
            deployment_id: Deployment ID
            details: Alert details
        
        Returns:
            Number of connections notified
        """
        return await manager.send_to_tenant(
            tenant_id,
            {
                "type": "production_alert",
                "alert_type": alert_type,
                "deployment_id": deployment_id,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
