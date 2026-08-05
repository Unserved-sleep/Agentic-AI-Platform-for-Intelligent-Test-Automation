import json
from pathlib import Path
from shared.schemas import QAReport
from configs.config import ARTIFACTS_DIR

class ReportGenerator:
    """Generates HTML and JSON execution reports."""

    @staticmethod
    def generate_html_report(report: QAReport) -> str:
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>QA Automation Execution Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1e293b, #334155); padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .metrics-grid {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .card {{ background-color: #1e293b; padding: 20px; border-radius: 8px; flex: 1; border-left: 4px solid #3b82f6; }}
        .card.pass {{ border-left-color: #22c55e; }}
        .card.fail {{ border-left-color: #ef4444; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; background: #1e293b; border-radius: 8px; overflow: hidden; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ background-color: #334155; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
        .badge-passed {{ background-color: #166534; color: #4ade80; }}
        .badge-failed {{ background-color: #991b1b; color: #fca5a5; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Agentic AI Test Automation Execution Report</h1>
        <p>Generated at runtime | PostgreSQL Database: agentic_test_db</p>
    </div>

    <div class="metrics-grid">
        <div class="card"><h3>Total Tests</h3><h2>{report.total_tests}</h2></div>
        <div class="card pass"><h3>Pass Rate</h3><h2>{report.pass_rate_percentage}%</h2></div>
        <div class="card"><h3>UI Suite</h3><h2>{report.ui_passed} / {report.ui_tests_count} Passed</h2></div>
        <div class="card"><h3>API Suite</h3><h2>{report.api_passed} / {report.api_tests_count} Passed</h2></div>
        <div class="card pass"><h3>Self-Healed Tests</h3><h2>{report.healed_tests_count}</h2></div>
    </div>

    <h2>Test Execution History</h2>
    <table>
        <thead>
            <tr>
                <th>Run ID</th>
                <th>Test Type</th>
                <th>Script Path</th>
                <th>Status</th>
                <th>Duration (s)</th>
                <th>DB Assertions</th>
            </tr>
        </thead>
        <tbody>
"""
        for item in report.execution_history:
            badge_cls = "badge-passed" if item.status == "PASSED" else "badge-failed"
            html += f"""
            <tr>
                <td>{item.run_id}</td>
                <td>{item.test_type}</td>
                <td>{item.script_path}</td>
                <td><span class="badge {badge_cls}">{item.status}</span></td>
                <td>{item.duration_seconds}s</td>
                <td>{len(item.db_assertion_results)} checks</td>
            </tr>
"""
        html += """
        </tbody>
    </table>
</body>
</html>
"""
        report_file = ARTIFACTS_DIR / "execution_report.html"
        report_file.write_text(html, encoding="utf-8")
        return str(report_file)
