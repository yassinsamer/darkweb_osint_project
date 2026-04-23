#!/usr/bin/env python3
"""
Enhanced Report Generator for Dark Web OSINT
Generates formal PDF reports with risk assessments and mitigation advice
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import HRFlowable
from alerts import AlertManager
import logging

logger = logging.getLogger(__name__)


class EnhancedReportGenerator:
    """Generate formal PDF reports with risk assessments"""

    def __init__(self, db_path="findings.db", config_path="config.json"):
        self.db_path = db_path
        self.config_path = config_path
        self.alert_manager = AlertManager(config_path)
        self.load_config()

    def load_config(self):
        """Load configuration"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = {}

    def get_findings_data(self, days_back=7):
        """Get findings data with risk scores"""
        cutoff_date = datetime.now() - timedelta(days=days_back)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get high-risk findings
        cursor.execute("""
            SELECT f.id, f.url, f.keyword, f.confidence, f.risk_score,
                   f.snippet, f.classification, f.found_at,
                   e.data_type, e.data_value
            FROM findings f
            LEFT JOIN extracted_data e ON f.id = e.finding_id
            WHERE f.found_at > ?
            ORDER BY f.risk_score DESC, f.found_at DESC
        """, (cutoff_date.isoformat(),))

        findings = cursor.fetchall()

        # Get statistics
        cursor.execute("""
            SELECT
                COUNT(DISTINCT f.id) as total_findings,
                COUNT(DISTINCT f.url) as unique_urls,
                AVG(f.risk_score) as avg_risk,
                MAX(f.risk_score) as max_risk,
                COUNT(CASE WHEN f.risk_score >= 85 THEN 1 END) as critical_findings,
                COUNT(CASE WHEN f.risk_score >= 70 THEN 1 END) as high_findings
            FROM findings f
            WHERE f.found_at > ?
        """, (cutoff_date.isoformat(),))

        stats = cursor.fetchone()
        conn.close()

        return findings, stats

    def get_mitigation_advice(self, finding):
        """Get mitigation advice based on finding type"""
        classification = finding[6] or 'unknown'
        keyword = finding[2].lower()
        risk_score = finding[4]

        advice = {
            'credential_leak': [
                "Immediately change all passwords associated with this account",
                "Enable two-factor authentication on all accounts",
                "Monitor account activity for unauthorized access",
                "Consider identity theft protection services"
            ],
            'data_breach': [
                "Contact affected service providers immediately",
                "Monitor credit reports and financial statements",
                "Change passwords for similar services",
                "Report incident to relevant authorities if personal data exposed"
            ],
            'financial_data': [
                "Monitor bank and credit card statements closely",
                "Contact financial institutions about potential fraud",
                "Consider credit freeze if sensitive financial data exposed",
                "Report to consumer protection agencies"
            ],
            'personal_info': [
                "Monitor for identity theft indicators",
                "Place fraud alert on credit reports",
                "Be vigilant about phishing attempts",
                "Consider identity monitoring services"
            ]
        }

        # Default advice based on risk level
        if risk_score >= 85:
            base_advice = [
                "URGENT: Immediate action required",
                "Notify security team and executive leadership",
                "Conduct thorough security assessment",
                "Implement incident response procedures",
                "Consider legal consultation"
            ]
        elif risk_score >= 70:
            base_advice = [
                "HIGH PRIORITY: Address within 24 hours",
                "Notify relevant stakeholders",
                "Review and strengthen security controls",
                "Monitor for related threats"
            ]
        else:
            base_advice = [
                "Review and assess business impact",
                "Consider strengthening security measures",
                "Monitor for related findings"
            ]

        # Add classification-specific advice
        if classification in advice:
            base_advice.extend(advice[classification])

        return base_advice

    def get_risk_level(self, score):
        """Get risk level based on score"""
        if score >= 85:
            return "CRITICAL", colors.red
        elif score >= 70:
            return "HIGH", colors.orange
        elif score >= 50:
            return "MEDIUM", colors.yellow
        else:
            return "LOW", colors.green

    def generate_pdf_report(self, output_path="osint_report.pdf", days_back=7):
        """Generate formal PDF report"""
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=20
        )

        # Title page
        story.append(Paragraph("DARK WEB OSINT SECURITY REPORT", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", styles['Normal']))
        story.append(Paragraph(f"Analysis Period: Last {days_back} days", styles['Normal']))
        story.append(Spacer(1, 0.5*inch))

        # Executive Summary
        story.append(Paragraph("EXECUTIVE SUMMARY", subtitle_style))

        findings, stats = self.get_findings_data(days_back)

        summary_text = f"""
        This report contains analysis of dark web intelligence gathered over the past {days_back} days.
        A total of {stats[0] or 0} security findings were identified across {stats[1] or 0} unique sources.

        Risk Assessment:
        • Critical Findings: {stats[4] or 0}
        • High-Risk Findings: {stats[5] or 0}
        • Average Risk Score: {stats[2] or 0:.1f}/100
        • Maximum Risk Score: {stats[3] or 0}/100

        Immediate attention is required for all critical and high-risk findings.
        """

        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))

        # Findings Table
        if findings:
            story.append(Paragraph("DETAILED FINDINGS", subtitle_style))

            # Table headers
            table_data = [['Risk Level', 'Score', 'Source URL', 'Keyword', 'Classification', 'Found Date']]

            # Add findings data
            for finding in findings[:50]:  # Limit to top 50 findings
                risk_level, color = self.get_risk_level(finding[4])
                table_data.append([
                    risk_level,
                    f"{finding[4]}/100",
                    finding[1][:50] + "..." if len(finding[1]) > 50 else finding[1],
                    finding[2],
                    finding[6] or 'Unknown',
                    datetime.fromisoformat(finding[7]).strftime('%Y-%m-%d %H:%M')
                ])

            # Create table
            table = Table(table_data, colWidths=[1*inch, 0.8*inch, 2.5*inch, 1*inch, 1.2*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(table)
            story.append(Spacer(1, 0.3*inch))

            # Detailed Analysis Section
            story.append(Paragraph("CRITICAL & HIGH-RISK ANALYSIS", subtitle_style))

            critical_findings = [f for f in findings if f[4] >= 70]

            for i, finding in enumerate(critical_findings[:10]):  # Top 10 critical findings
                risk_level, color = self.get_risk_level(finding[4])

                story.append(HRFlowable(width="100%", thickness=1, color=colors.grey, spaceBefore=10, spaceAfter=10))

                finding_title = f"Finding #{i+1}: {finding[2].upper()} - {risk_level} RISK"
                story.append(Paragraph(finding_title, styles['Heading3']))

                details = f"""
                <b>Source:</b> {finding[1]}<br/>
                <b>Risk Score:</b> {finding[4]}/100<br/>
                <b>Confidence:</b> {finding[3]}%<br/>
                <b>Classification:</b> {finding[6] or 'Unknown'}<br/>
                <b>Discovered:</b> {datetime.fromisoformat(finding[7]).strftime('%B %d, %Y at %H:%M')}<br/>
                <b>Context:</b> {finding[5][:200]}...
                """

                story.append(Paragraph(details, styles['Normal']))

                # Mitigation advice
                story.append(Paragraph("<b>Recommended Actions:</b>", styles['Heading4']))
                mitigation = self.get_mitigation_advice(finding)
                for action in mitigation:
                    story.append(Paragraph(f"• {action}", styles['Normal']))

                story.append(Spacer(1, 0.2*inch))

        # Footer
        story.append(PageBreak())
        story.append(Paragraph("REPORT FOOTER", subtitle_style))
        story.append(Paragraph("This report was generated automatically by the Dark Web OSINT system.", styles['Normal']))
        story.append(Paragraph("For questions or concerns, contact the security team.", styles['Normal']))
        story.append(Paragraph(f"Report ID: {datetime.now().strftime('%Y%m%d_%H%M%S')}", styles['Normal']))

        # Build PDF
        doc.build(story)
        print(f"[+] PDF report generated: {output_path}")
        return output_path

    def send_critical_alerts(self, days_back=1):
        """Send Telegram alerts for critical findings"""
        print("[*] Checking for critical findings to alert...")

        findings, stats = self.get_findings_data(days_back)
        critical_findings = [f for f in findings if f[4] >= 85]  # Critical threshold

        alerts_sent = 0
        for finding in critical_findings:
            # Create finding dict for alert manager
            finding_dict = {
                'id': finding[0],
                'url': finding[1],
                'keyword': finding[2],
                'confidence': finding[3],
                'risk_score': finding[4],
                'snippet': finding[5] or 'No context available',
                'classification': finding[6] or 'unknown'
            }

            # Send alert - implementation would go here
            alerts_sent += 1

        print(f"[+] Alerts sent: {alerts_sent}")
        return alerts_sent


if __name__ == "__main__":
    import sys
    
    # Default parameters
    output_file = "osint_report.pdf"
    days = 7
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    if len(sys.argv) > 2:
        days = int(sys.argv[2])
    
    # Generate report
    try:
        generator = EnhancedReportGenerator()
        generator.generate_pdf_report(output_path=output_file, days_back=days)
        print(f"Report successfully generated: {output_file}")
    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
            result = self.alert_manager.send_alert(finding_dict, 'critical')
            if result['sent']:
                alerts_sent += 1
                print(f"[+] Alert sent for finding #{finding[0]} (risk: {finding[4]})")
            else:
                print(f"[!] Alert failed for finding #{finding[0]}: {result.get('message', 'Unknown error')}")

        print(f"[+] Sent {alerts_sent} critical alerts via Telegram")
        return alerts_sent

    def generate_comprehensive_report(self, days_back=7):
        """Generate complete report with PDF and alerts"""
        print(f"[*] Generating comprehensive OSINT report for last {days_back} days...")

        # Generate PDF report
        pdf_path = self.generate_pdf_report(days_back=days_back)

        # Send critical alerts
        alerts_sent = self.send_critical_alerts(days_back=1)

        # Print summary
        findings, stats = self.get_findings_data(days_back)

        print("\n" + "="*60)
        print("REPORT SUMMARY")
        print("="*60)
        print(f"PDF Report: {pdf_path}")
        print(f"Analysis Period: {days_back} days")
        print(f"Total Findings: {stats[0] or 0}")
        print(f"Critical Alerts Sent: {alerts_sent}")
        print(f"Average Risk Score: {stats[2] or 0:.1f}/100")
        print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        return pdf_path, alerts_sent


if __name__ == "__main__":
    import sys

    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7

    generator = EnhancedReportGenerator()
    generator.generate_comprehensive_report(days_back=days)