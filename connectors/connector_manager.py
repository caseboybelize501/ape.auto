"""
APE - Autonomous Production Engineer
Connector Manager

Central registry and health management for all connectors.
Manages source profiles and connection pooling.
"""

from datetime import datetime
from typing import Optional, Type
from enum import Enum

from contracts.models.tenant import SourceProfile, ConnectionStatus

from connectors.github import GitHubConnector
from connectors.gitlab import GitLabConnector
from connectors.github_actions import GitHubActionsConnector
from connectors.jenkins import JenkinsConnector
from connectors.argocd import ArgoCDConnector
from connectors.datadog import DatadogConnector
from connectors.grafana import GrafanaConnector
from connectors.sentry import SentryConnector
from connectors.jira import JiraConnector
from connectors.linear import LinearConnector


class SourceType(str, Enum):
    REPO = "repo"
    CI = "ci"
    CD = "cd"
    OBSERVABILITY = "observability"
    ISSUE_TRACKER = "issue_tracker"


class ConnectorManager:
    """
    Central manager for all connectors.
    
    Provides:
    - Connector registry
    - Connection pooling
    - Health monitoring
    - Credential management
    """
    
    # Connector type mappings
    REPO_CONNECTORS: dict[str, Type] = {
        "github": GitHubConnector,
        "gitlab": GitLabConnector,
    }
    
    CI_CONNECTORS: dict[str, Type] = {
        "github_actions": GitHubActionsConnector,
        "jenkins": JenkinsConnector,
    }
    
    CD_CONNECTORS: dict[str, Type] = {
        "argocd": ArgoCDConnector,
    }
    
    OBSERVABILITY_CONNECTORS: dict[str, Type] = {
        "datadog": DatadogConnector,
        "grafana": GrafanaConnector,
        "sentry": SentryConnector,
    }
    
    ISSUE_TRACKER_CONNECTORS: dict[str, Type] = {
        "jira": JiraConnector,
        "linear": LinearConnector,
    }
    
    def __init__(self):
        """Initialize connector manager."""
        self._profiles: dict[str, SourceProfile] = {}
        self._connectors: dict[str, object] = {}
        self._health_cache: dict[str, tuple[bool, Optional[str], datetime]] = {}
        self._health_cache_ttl_seconds = 60
    
    def register_profile(self, profile: SourceProfile) -> None:
        """
        Register a source profile.
        
        Args:
            profile: Source profile to register
        """
        self._profiles[profile.id] = profile
    
    def get_profile(self, profile_id: str) -> Optional[SourceProfile]:
        """
        Get source profile by ID.
        
        Args:
            profile_id: Profile ID
        
        Returns:
            Source profile or None
        """
        return self._profiles.get(profile_id)
    
    def get_connector(
        self,
        profile_id: str,
        credentials: Optional[dict] = None
    ) -> Optional[object]:
        """
        Get or create connector for profile.
        
        Args:
            profile_id: Profile ID
            credentials: Optional credentials override
        
        Returns:
            Connector instance or None
        """
        # Check cache
        if profile_id in self._connectors:
            return self._connectors[profile_id]
        
        profile = self.get_profile(profile_id)
        if not profile:
            return None
        
        # Get credentials
        creds = credentials or profile.connection_config
        
        # Create connector based on type
        connector = self._create_connector(
            profile.source_type,
            profile.provider,
            creds
        )
        
        if connector:
            self._connectors[profile_id] = connector
        
        return connector
    
    def _create_connector(
        self,
        source_type: str,
        provider: str,
        config: dict
    ) -> Optional[object]:
        """
        Create connector instance.
        
        Args:
            source_type: Source type
            provider: Provider name
            config: Connection config
        
        Returns:
            Connector instance or None
        """
        try:
            if source_type == SourceType.REPO:
                connector_class = self.REPO_CONNECTORS.get(provider)
                if connector_class:
                    if provider == "github":
                        return connector_class(config.get("token"))
                    elif provider == "gitlab":
                        return connector_class(
                            config.get("token"),
                            config.get("url", "https://gitlab.com")
                        )
            
            elif source_type == SourceType.CI:
                connector_class = self.CI_CONNECTORS.get(provider)
                if connector_class:
                    if provider == "github_actions":
                        return connector_class(config.get("token"))
                    elif provider == "jenkins":
                        return connector_class(
                            config.get("url"),
                            config.get("user"),
                            config.get("token")
                        )
            
            elif source_type == SourceType.CD:
                connector_class = self.CD_CONNECTORS.get(provider)
                if connector_class:
                    if provider == "argocd":
                        return connector_class(
                            config.get("url"),
                            config.get("token"),
                            config.get("verify_ssl", True)
                        )
            
            elif source_type == SourceType.OBSERVABILITY:
                connector_class = self.OBSERVABILITY_CONNECTORS.get(provider)
                if connector_class:
                    if provider == "datadog":
                        return connector_class(
                            config.get("api_key"),
                            config.get("app_key"),
                            config.get("site", "datadoghq.com")
                        )
                    elif provider == "grafana":
                        return connector_class(
                            config.get("url"),
                            config.get("api_key"),
                            config.get("org_id", 1)
                        )
                    elif provider == "sentry":
                        return connector_class(
                            config.get("org_slug"),
                            config.get("api_key"),
                            config.get("base_url", "https://sentry.io/api")
                        )
            
            elif source_type == SourceType.ISSUE_TRACKER:
                connector_class = self.ISSUE_TRACKER_CONNECTORS.get(provider)
                if connector_class:
                    if provider == "jira":
                        return connector_class(
                            config.get("url"),
                            config.get("user"),
                            config.get("token")
                        )
                    elif provider == "linear":
                        return connector_class(config.get("api_key"))
            
            return None
        except Exception:
            return None
    
    def check_health(
        self,
        profile_id: str,
        force_refresh: bool = False
    ) -> tuple[bool, Optional[str]]:
        """
        Check connector health.
        
        Args:
            profile_id: Profile ID
            force_refresh: Force fresh check
        
        Returns:
            Tuple of (healthy, error_message)
        """
        # Check cache
        now = datetime.utcnow()
        if not force_refresh and profile_id in self._health_cache:
            healthy, error, cached_at = self._health_cache[profile_id]
            if (now - cached_at).total_seconds() < self._health_cache_ttl_seconds:
                return healthy, error
        
        # Get connector
        connector = self.get_connector(profile_id)
        if not connector:
            self._health_cache[profile_id] = (False, "Connector not found", now)
            return False, "Connector not found"
        
        # Check health
        try:
            if hasattr(connector, "test_connection"):
                healthy, error = connector.test_connection()
            else:
                healthy, error = True, None
            
            self._health_cache[profile_id] = (healthy, error, now)
            
            # Update profile status
            if profile_id in self._profiles:
                profile = self._profiles[profile_id]
                profile.status = ConnectionStatus.CONNECTED if healthy else ConnectionStatus.ERROR
                profile.health_error = error
                profile.last_health_check = now
            
            return healthy, error
        except Exception as e:
            self._health_cache[profile_id] = (False, str(e), now)
            return False, str(e)
    
    def check_all_health(self) -> dict[str, tuple[bool, Optional[str]]]:
        """
        Check health of all registered connectors.
        
        Returns:
            Dict of profile_id -> (healthy, error)
        """
        results = {}
        for profile_id in self._profiles:
            results[profile_id] = self.check_health(profile_id)
        return results
    
    def get_repo_connector(
        self,
        platform: str,
        credentials: dict
    ) -> Optional[object]:
        """
        Get repository connector by platform.
        
        Args:
            platform: Platform name (github, gitlab)
            credentials: Platform credentials
        
        Returns:
            Connector instance or None
        """
        return self._create_connector(SourceType.REPO, platform, credentials)
    
    def get_ci_connector(
        self,
        platform: str,
        credentials: dict
    ) -> Optional[object]:
        """
        Get CI connector by platform.
        
        Args:
            platform: Platform name (github_actions, jenkins)
            credentials: Platform credentials
        
        Returns:
            Connector instance or None
        """
        return self._create_connector(SourceType.CI, platform, credentials)
    
    def get_observability_connector(
        self,
        platform: str,
        credentials: dict
    ) -> Optional[object]:
        """
        Get observability connector by platform.
        
        Args:
            platform: Platform name (datadog, grafana, sentry)
            credentials: Platform credentials
        
        Returns:
            Connector instance or None
        """
        return self._create_connector(SourceType.OBSERVABILITY, platform, credentials)
    
    def get_issue_tracker_connector(
        self,
        platform: str,
        credentials: dict
    ) -> Optional[object]:
        """
        Get issue tracker connector by platform.
        
        Args:
            platform: Platform name (jira, linear)
            credentials: Platform credentials
        
        Returns:
            Connector instance or None
        """
        return self._create_connector(SourceType.ISSUE_TRACKER, platform, credentials)
    
    def invalidate_cache(self, profile_id: Optional[str] = None) -> None:
        """
        Invalidate health cache.
        
        Args:
            profile_id: Optional specific profile to invalidate
        """
        if profile_id:
            self._health_cache.pop(profile_id, None)
        else:
            self._health_cache.clear()
    
    def list_profiles(
        self,
        source_type: Optional[str] = None,
        provider: Optional[str] = None
    ) -> list[SourceProfile]:
        """
        List profiles with optional filters.
        
        Args:
            source_type: Filter by source type
            provider: Filter by provider
        
        Returns:
            List of matching profiles
        """
        profiles = list(self._profiles.values())
        
        if source_type:
            profiles = [p for p in profiles if p.source_type == source_type]
        if provider:
            profiles = [p for p in profiles if p.provider == provider]
        
        return profiles


# Global instance
_connector_manager: Optional[ConnectorManager] = None


def get_connector_manager() -> ConnectorManager:
    """Get global connector manager instance."""
    global _connector_manager
    if _connector_manager is None:
        _connector_manager = ConnectorManager()
    return _connector_manager
