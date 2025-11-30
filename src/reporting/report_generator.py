"""
Report Generation Module
Automated PDF and HTML report generation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from jinja2 import Template
import plotly.graph_objects as go
import plotly.io as pio
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """
    Generate HTML and PDF reports
    """
    
    def __init__(self):
        self.logger = logger
        self.report_data = {}
    
    def generate_daily_summary(self, df: pd.DataFrame, output_path: Path) -> Path:
        """
        Generate daily summary report
        
        Args:
            df: Test results DataFrame
            output_path: Output file path
            
        Returns:
            Path to generated report
        """
        self.logger.info("Generating daily summary report...")
        
        # Calculate metrics
        metrics = self._calculate_summary_metrics(df)
        
        # Create HTML report
        html_content = self._create_html_report(metrics, df)
        
        # Save
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        self.logger.info(f"Report saved to {output_path}")
        
        return output_path
    
    def _calculate_summary_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate summary metrics"""
        # Overall metrics
        total_devices = df['device_id'].nunique()
        total_tests = len(df)
        overall_yield = (df['result'] == 'pass').sum() / len(df) * 100
        
        # Device-level yield
        device_yield = df.groupby('device_id')['result'].apply(
            lambda x: 1 if (x == 'pass').all() else 0
        )
        device_yield_pct = device_yield.mean() * 100
        
        # Test time
        avg_test_time = df['test_time_ms'].mean()
        total_test_time_hours = df['test_time_ms'].sum() / (1000 * 60 * 60)
        
        # Test-level yield
        test_yield = df.groupby('test_name')['result'].apply(
            lambda x: (x == 'pass').sum() / len(x) * 100
        ).sort_values()
        
        # Failure analysis
        failures = df[df['result'] == 'fail']
        top_failing_tests = failures['test_name'].value_counts().head(5)
        
        # Bin distribution
        bin_dist = df['bin'].value_counts().sort_index()
        
        return {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_devices': total_devices,
            'total_tests': total_tests,
            'overall_yield': overall_yield,
            'device_yield': device_yield_pct,
            'passing_devices': int(device_yield.sum()),
            'failing_devices': int((device_yield == 0).sum()),
            'avg_test_time': avg_test_time,
            'total_test_time_hours': total_test_time_hours,
            'lowest_yield_test': test_yield.index[0] if len(test_yield) > 0 else 'N/A',
            'lowest_yield_value': test_yield.iloc[0] if len(test_yield) > 0 else 0,
            'top_failing_tests': top_failing_tests.to_dict(),
            'bin_distribution': bin_dist.to_dict(),
            'test_yield_summary': test_yield.describe().to_dict()
        }
    
    def _create_html_report(self, metrics: Dict, df: pd.DataFrame) -> str:
        """Create HTML report content"""
        
        # Create visualizations
        charts_html = self._create_charts(df)
        
        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <title>POSIVA Daily Summary Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1f77b4;
            border-bottom: 3px solid #1f77b4;
            padding-bottom: 10px;
        }
        h2 {
            color: #333;
            margin-top: 30px;
            border-left: 4px solid #1f77b4;
            padding-left: 10px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .metric-card.green {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        .metric-card.red {
            background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
        }
        .metric-card.blue {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #1f77b4;
            color: white;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .status-good {
            color: green;
            font-weight: bold;
        }
        .status-warn {
            color: orange;
            font-weight: bold;
        }
        .status-bad {
            color: red;
            font-weight: bold;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 POSIVA Daily Summary Report</h1>
        <p><strong>Generated:</strong> {{ date }}</p>
        
        <h2>🎯 Key Metrics</h2>
        <div class="metrics-grid">
            <div class="metric-card green">
                <div class="metric-label">Device Yield</div>
                <div class="metric-value">{{ "%.1f"|format(device_yield) }}%</div>
                <div class="metric-label">{{ passing_devices }}/{{ total_devices }} devices</div>
            </div>
            
            <div class="metric-card blue">
                <div class="metric-label">Test Yield</div>
                <div class="metric-value">{{ "%.1f"|format(overall_yield) }}%</div>
                <div class="metric-label">{{ total_tests|int }} total tests</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Avg Test Time</div>
                <div class="metric-value">{{ "%.1f"|format(avg_test_time) }}</div>
                <div class="metric-label">milliseconds</div>
            </div>
            
            <div class="metric-card red">
                <div class="metric-label">Failing Devices</div>
                <div class="metric-value">{{ failing_devices }}</div>
                <div class="metric-label">{{ "%.1f"|format(100 - device_yield) }}%</div>
            </div>
        </div>
        
        <h2>⚠️ Top Failing Tests</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Failure Count</th>
                    <th>% of Total Failures</th>
                </tr>
            </thead>
            <tbody>
                {% for test, count in top_failing_tests.items() %}
                <tr>
                    <td>{{ test }}</td>
                    <td>{{ count }}</td>
                    <td>{{ "%.1f"|format(count / total_tests * 100) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <h2>📦 Bin Distribution</h2>
        <table>
            <thead>
                <tr>
                    <th>Bin</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody>
                {% for bin, count in bin_distribution.items() %}
                <tr>
                    <td>Bin {{ bin }}</td>
                    <td>{{ count }}</td>
                    <td>{{ "%.1f"|format(count / total_tests * 100) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <h2>📈 Visualizations</h2>
        {{ charts_html|safe }}
        
        <h2>💡 Recommendations</h2>
        <ul>
            {% if device_yield < 90 %}
            <li class="status-bad">⚠️ Device yield ({{ "%.1f"|format(device_yield) }}%) is below target (90%). Investigate root causes.</li>
            {% else %}
            <li class="status-good">✅ Device yield ({{ "%.1f"|format(device_yield) }}%) meets target.</li>
            {% endif %}
            
            <li>🔍 Focus on top failing test: <strong>{{ lowest_yield_test }}</strong> ({{ "%.1f"|format(lowest_yield_value) }}% yield)</li>
            
            {% if total_test_time_hours > 10 %}
            <li class="status-warn">⏱️ Total test time ({{ "%.1f"|format(total_test_time_hours) }} hours) is high. Consider test time optimization.</li>
            {% endif %}
        </ul>
        
        <div class="footer">
            <p>POSIVA Analytics Platform • Generated automatically</p>
        </div>
    </div>
</body>
</html>
        """)
        
        html = template.render(**metrics, charts_html=charts_html)
        
        return html
    
    def _create_charts(self, df: pd.DataFrame) -> str:
        """Create chart HTML"""
        from src.analytics.yield_analytics import YieldAnalytics
        
        ya = YieldAnalytics(df)
        
        # Create charts
        charts = []
        
        # Yield by test
        fig1 = ya.plot_yield_trend(by='lot')
        charts.append(pio.to_html(fig1, include_plotlyjs='cdn', full_html=False))
        
        # Pareto
        fig2 = ya.plot_pareto(top_n=10)
        charts.append(pio.to_html(fig2, include_plotlyjs=False, full_html=False))
        
        return '\n'.join(charts)
    
    def generate_custom_report(self, 
                               df: pd.DataFrame,
                               title: str,
                               sections: List[str],
                               output_path: Path) -> Path:
        """
        Generate custom report with selected sections
        
        Args:
            df: Data
            title: Report title
            sections: List of sections to include
            output_path: Output path
            
        Returns:
            Path to report
        """
        self.logger.info(f"Generating custom report: {title}")
        
        # Build report based on sections
        metrics = self._calculate_summary_metrics(df)
        
        # Create simplified HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial; padding: 20px; }}
        h1 {{ color: #1f77b4; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; }}
        th {{ background-color: #1f77b4; color: white; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>Generated: {metrics['date']}</p>
    <h2>Summary</h2>
    <p>Device Yield: {metrics['device_yield']:.1f}%</p>
    <p>Total Devices: {metrics['total_devices']}</p>
</body>
</html>
        """
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(html)
        
        self.logger.info(f"Custom report saved to {output_path}")
        
        return output_path


class EmailReporter:
    """
    Email report sender (placeholder - requires SMTP configuration)
    """
    
    def __init__(self, smtp_config: Optional[Dict] = None):
        self.smtp_config = smtp_config or {}
        self.logger = logger
    
    def send_report(self, 
                    report_path: Path,
                    recipients: List[str],
                    subject: str) -> bool:
        """
        Send report via email
        
        Args:
            report_path: Path to report file
            recipients: Email addresses
            subject: Email subject
            
        Returns:
            Success status
        """
        self.logger.info(f"Email report feature - would send {report_path} to {recipients}")
        self.logger.warning("Email sending not configured. Add SMTP settings to enable.")
        
        # Placeholder for actual email implementation
        # Would use smtplib here
        
        return False
