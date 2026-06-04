"""JSON reporter for EnvSentry machine-readable output.

This module provides a JSON reporter that produces stable, parseable
output suitable for CI/CD integration and automation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from envsentry import __version__
from envsentry.models import AuditResult


class JSONReporter:
    """JSON reporter that produces stable, machine-readable output.

    Output structure:
    {
        "tool_version": "1.0.0",
        "project_path": "/path/to/project",
        "scan_timestamp": "2024-01-15T10:30:00Z",
        "summary": {
            "total_findings": 5,
            "by_severity": {
                "error": 2,
                "warning": 3
            }
        },
        "findings": [
            {
                "code": "ENV001",
                "severity": "error",
                "variable": "DATABASE_PASSWORD",
                "file": "/path/to/.env",
                "line": 10,
                "message": "Required variable is missing",
                "remediation": "Add DATABASE_PASSWORD to your .env file"
            }
        ]
    }

    Security: NEVER includes actual environment variable values.
    """

    def report(self, audit_result: AuditResult) -> str:
        """Generate JSON report from audit result.

        Args:
            audit_result: The complete audit result to serialize.

        Returns:
            JSON string with stable key ordering and consistent formatting.
        """
        # Build the output structure
        output = {
            "tool_version": __version__,
            "project_path": audit_result.project_path,
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_findings": len(audit_result.findings),
                "by_severity": audit_result.summary,
            },
            "findings": [
                {
                    "code": finding.code,
                    "severity": finding.severity,
                    "variable": finding.variable,
                    "file": finding.file,
                    "line": finding.line,
                    "message": finding.message,
                    "remediation": finding.remediation,
                }
                for finding in audit_result.findings
            ],
        }

        # Serialize with stable ordering
        return json.dumps(output, sort_keys=True, indent=2)
