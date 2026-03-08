"""
APE - Autonomous Production Engineer
Connectors Package

Integrations with external systems:
- Source control: GitHub, GitLab
- CI/CD: GitHub Actions, Jenkins, ArgoCD
- Observability: Datadog, Grafana, Sentry
- Issue trackers: Jira, Linear
"""

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
from connectors.connector_manager import ConnectorManager, SourceProfile

__all__ = [
    "GitHubConnector",
    "GitLabConnector",
    "GitHubActionsConnector",
    "JenkinsConnector",
    "ArgoCDConnector",
    "DatadogConnector",
    "GrafanaConnector",
    "SentryConnector",
    "JiraConnector",
    "LinearConnector",
    "ConnectorManager",
    "SourceProfile",
]
