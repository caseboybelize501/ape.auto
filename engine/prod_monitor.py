"""
APE - Autonomous Production Engineer
Production Monitor

Monitors production deployments for regressions:
- Error rate monitoring
- Latency monitoring
- Sentry fingerprint tracking
- Auto-rollback triggers
- Self-repair initiation
"""

from datetime import datetime, timedelta
from typing import Optional

from contracts.models.deploy import Deployment, DeployStatus, HealthStatus
from contracts.models.repair import ProductionRegressionSignal, SelfRepairSession


class ProductionMonitor:
    """
    Monitors production for regressions.
    """
    
    def __init__(self, observability_connector, sentry_connector=None):
        """
        Initialize production monitor.
        
        Args:
            observability_connector: Datadog/Grafana connector
            sentry_connector: Sentry connector for error tracking
        """
        self.observability = observability_connector
        self.sentry = sentry_connector
    
    def monitor_deployment(
        self,
        deployment: Deployment,
        window_minutes: int = 15
    ) -> dict:
        """
        Monitor deployment for regressions.
        
        Args:
            deployment: Deployment to monitor
            window_minutes: Monitoring window
        
        Returns:
            Monitoring results dict
        """
        from_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        
        # Get service health
        health = self.observability.get_service_health(
            service="production-app",
            window_minutes=window_minutes
        )
        
        # Check for regressions
        regression = self.detect_regression(deployment, health)
        
        # Check Sentry for new errors
        sentry_issues = []
        if self.sentry:
            sentry_issues = self.sentry.get_new_issues_since(
                since=from_time,
                project_slug="production"
            )
        
        return {
            "deployment_id": deployment.id,
            "window_minutes": window_minutes,
            "health": health,
            "regression_detected": regression is not None,
            "regression": regression,
            "sentry_new_issues": len(sentry_issues),
            "sentry_issues": sentry_issues[:5],  # Top 5
            "status": "healthy" if not regression else "regression",
            "monitored_at": datetime.utcnow(),
        }
    
    def detect_regression(
        self,
        deployment: Deployment,
        health: dict
    ) -> Optional[ProductionRegressionSignal]:
        """
        Detect production regression.
        
        Args:
            deployment: Deployment
            health: Service health data
        
        Returns:
            Regression signal if detected, None otherwise
        """
        error_rate = health.get("error_rate", {})
        latency = health.get("latency", {})
        
        # Check error rate regression (>20% increase)
        if error_rate:
            current = error_rate.get("current", 0)
            baseline = deployment.created_at  # Would need stored baseline
            
            # Simplified check
            if current > 0.05:  # >5% error rate
                return ProductionRegressionSignal(
                    id=f"regression-{deployment.id}-{datetime.utcnow().strftime('%H%M%S')}",
                    deployment_id=deployment.id,
                    signal_type="error_rate",
                    metric_name="error_rate",
                    baseline_value=0.01,  # Would be stored baseline
                    current_value=current,
                    regression_percentage=((current - 0.01) / 0.01 * 100) if current > 0.01 else 0,
                    severity="high" if current > 0.1 else "medium",
                )
        
        # Check latency regression (>30% increase)
        if latency:
            p99_current = latency.get("p99", 0)
            if p99_current > 500:  # >500ms p99
                return ProductionRegressionSignal(
                    id=f"regression-{deployment.id}-{datetime.utcnow().strftime('%H%M%S')}",
                    deployment_id=deployment.id,
                    signal_type="latency",
                    metric_name="p99_latency",
                    baseline_value=200,
                    current_value=p99_current,
                    regression_percentage=((p99_current - 200) / 200 * 100),
                    severity="medium",
                )
        
        return None
    
    def should_auto_rollback(
        self,
        signal: ProductionRegressionSignal
    ) -> bool:
        """
        Determine if auto-rollback should be triggered.
        
        Args:
            signal: Regression signal
        
        Returns:
            True if should rollback
        """
        # Auto-rollback conditions:
        # - Error rate > 100% of baseline (2x)
        # - Data corruption detected
        # - Critical severity
        
        if signal.regression_percentage > 100:
            return True
        
        if signal.severity == "critical":
            return True
        
        if "data" in signal.metric_name.lower() or "corrupt" in signal.metric_name.lower():
            return True
        
        return False
    
    def localize_error(
        self,
        error_traceback: str,
        generated_files: list[str]
    ) -> tuple[Optional[str], Optional[int]]:
        """
        Localize production error to specific file.
        
        Args:
            error_traceback: Production error traceback
            generated_files: Files generated by APE
        
        Returns:
            Tuple of (file_path, line_number)
        """
        # Parse traceback for file paths
        import re
        
        traceback_pattern = r'File "([^"]+)", line (\d+)'
        matches = re.findall(traceback_pattern, error_traceback)
        
        for file_path, line_num in matches:
            # Check if file is in generated files
            for gen_file in generated_files:
                if gen_file in file_path or file_path.endswith(gen_file):
                    return gen_file, int(line_num)
        
        return None, None
    
    def initiate_self_repair(
        self,
        deployment: Deployment,
        signal: ProductionRegressionSignal,
        localized_file: Optional[str],
        localized_line: Optional[int]
    ) -> SelfRepairSession:
        """
        Initiate self-repair session.
        
        Args:
            deployment: Deployment with regression
            signal: Regression signal
            localized_file: Localized file path
            localized_line: Localized line number
        
        Returns:
            SelfRepairSession
        """
        session = SelfRepairSession(
            id=f"repair-{deployment.id}-{datetime.utcnow().strftime('%H%M%S')}",
            deployment_id=deployment.id,
            regression_signal_id=signal.id,
            localized_file=localized_file,
            localized_line=localized_line,
            created_at=datetime.utcnow(),
        )
        
        return session
    
    def get_production_metrics(
        self,
        deployment: Deployment,
        window_minutes: int = 60
    ) -> dict:
        """
        Get production metrics for deployment.
        
        Args:
            deployment: Deployment
            window_minutes: Metrics window
        
        Returns:
            Metrics dict
        """
        from_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        
        metrics = {}
        
        if self.observability:
            health = self.observability.get_service_health(
                service="production-app",
                window_minutes=window_minutes
            )
            metrics.update(health)
        
        if self.sentry:
            issues = self.sentry.get_new_issues_since(
                since=from_time,
                project_slug="production"
            )
            metrics["new_sentry_issues"] = len(issues)
        
        return {
            "deployment_id": deployment.id,
            "window_minutes": window_minutes,
            "metrics": metrics,
            "collected_at": datetime.utcnow(),
        }
