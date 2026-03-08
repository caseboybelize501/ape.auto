"""
APE - Autonomous Production Engineer
Grafana Dashboard Provisioning

Pre-configured dashboards for APE monitoring.
"""

DASHBOARDS = {
    "ape-overview": {
        "dashboard": {
            "id": None,
            "uid": "ape-overview",
            "title": "APE - Overview",
            "tags": ["ape", "overview"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "Generation Runs",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "sum(ape_generation_runs_total)",
                            "legendFormat": "Total Runs",
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                },
                {
                    "id": 2,
                    "title": "Success Rate",
                    "type": "gauge",
                    "targets": [
                        {
                            "expr": "sum(ape_generation_runs_total{status='completed'}) / sum(ape_generation_runs_total) * 100",
                            "legendFormat": "Success %",
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
                    "fieldConfig": {
                        "defaults": {
                            "min": 0,
                            "max": 100,
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "red", "value": 0},
                                    {"color": "yellow", "value": 80},
                                    {"color": "green", "value": 95},
                                ]
                            }
                        }
                    },
                },
                {
                    "id": 3,
                    "title": "Active WebSocket Connections",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "ape_websocket_connections",
                            "legendFormat": "Connections",
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0},
                },
                {
                    "id": 4,
                    "title": "Production Health",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "avg(ape_production_health)",
                            "legendFormat": "Health",
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0},
                    "fieldConfig": {
                        "defaults": {
                            "mappings": [
                                {"type": "value", "options": {"0": {"text": "Unhealthy"}}},
                                {"type": "value", "options": {"1": {"text": "Healthy"}}},
                            ]
                        }
                    },
                },
                {
                    "id": 5,
                    "title": "Generation Duration (p95)",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, rate(ape_generation_duration_seconds_bucket[5m]))",
                            "legendFormat": "p95",
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                },
                {
                    "id": 6,
                    "title": "Critic Pass Results",
                    "type": "piechart",
                    "targets": [
                        {
                            "expr": "sum by (result) (ape_critic_passes_total)",
                            "legendFormat": "{{result}}",
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                },
            ],
            "refresh": "5s",
            "schemaVersion": 38,
            "version": 1,
        },
        "folder": "APE",
    },
    "ape-pipeline": {
        "dashboard": {
            "id": None,
            "uid": "ape-pipeline",
            "title": "APE - Pipeline Details",
            "tags": ["ape", "pipeline"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "Files Generated per Level",
                    "type": "bargauge",
                    "targets": [
                        {
                            "expr": "sum by (level) (ape_generation_files_total)",
                            "legendFormat": "Level {{level}}",
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                },
                {
                    "id": 2,
                    "title": "Critic Pass Duration",
                    "type": "heatmap",
                    "targets": [
                        {
                            "expr": "rate(ape_critic_duration_seconds_sum[5m]) / rate(ape_critic_duration_seconds_count[5m])",
                            "legendFormat": "Pass {{pass_number}}",
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                },
                {
                    "id": 3,
                    "title": "Repair Attempts",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "rate(ape_critic_repairs_total[5m])",
                            "legendFormat": "{{result}}",
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                },
                {
                    "id": 4,
                    "title": "Generation Halts (GATE-4)",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "sum(increase(ape_critic_halts_total[24h]))",
                            "legendFormat": "Halts (24h)",
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                },
            ],
            "refresh": "10s",
            "schemaVersion": 38,
            "version": 1,
        },
        "folder": "APE",
    },
    "ape-production": {
        "dashboard": {
            "id": None,
            "uid": "ape-production",
            "title": "APE - Production Monitoring",
            "tags": ["ape", "production"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "Deployments",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "sum(ape_deployments_total)",
                            "legendFormat": "Total",
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                },
                {
                    "id": 2,
                    "title": "Rollbacks",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "sum(increase(ape_rollbacks_total[24h]))",
                            "legendFormat": "Rollbacks (24h)",
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
                },
                {
                    "id": 3,
                    "title": "Regressions",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "sum by (severity) (rate(ape_regressions_total[5m]))",
                            "legendFormat": "{{severity}}",
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                },
                {
                    "id": 4,
                    "title": "Deployment Duration by Environment",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, rate(ape_deployment_duration_seconds_bucket[5m])) by (environment)",
                            "legendFormat": "{{environment}} p95",
                        }
                    ],
                    "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8},
                },
            ],
            "refresh": "5s",
            "schemaVersion": 38,
            "version": 1,
        },
        "folder": "APE",
    },
}

# Datasource configuration
DATASOURCES = [
    {
        "name": "Prometheus",
        "type": "prometheus",
        "access": "proxy",
        "url": "http://prometheus:9090",
        "isDefault": True,
        "editable": True,
    }
]

# Dashboard provider configuration
PROVIDER_CONFIG = {
    "apiVersion": 1,
    "providers": [
        {
            "name": "APE Dashboards",
            "orgId": 1,
            "folder": "APE",
            "type": "file",
            "disableDeletion": False,
            "updateIntervalSeconds": 30,
            "options": {
                "path": "/etc/grafana/provisioning/dashboards/ape"
            }
        }
    ]
}
