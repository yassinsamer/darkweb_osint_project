                      
"""
Comprehensive PDF Report Generator
Generates a full security report with findings, URLs, risk scores, and mitigation strategies
"""

import json
import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfgen import canvas
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveReportGenerator:
    """Generate comprehensive PDF security reports"""

    def __init__(self, db_path="findings.db", config_path="config.json"):
        self.db_path = db_path
        self.target_company = self._load_target_company(config_path)
        self.check_and_create_sample_data()

    def _load_target_company(self, config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f).get("target_company", "")
        except Exception:
            return ""

    def check_and_create_sample_data(self):
        """Ensure the database tables exist — never insert fake sample data."""
        from enhanced_database import FindingsDB
        FindingsDB(self.db_path)                                      

    def create_sample_database(self):
        """Create sample database with test findings for demonstration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

                               
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                keyword TEXT,
                snippet TEXT,
                confidence REAL,
                risk_score REAL,
                classification TEXT,
                found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

                                     
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extracted_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                finding_id INTEGER,
                data_type TEXT,
                data_value TEXT,
                FOREIGN KEY(finding_id) REFERENCES findings(id)
            )
        """)

                              
        sample_findings = [
            ("http://example-dark.onion/profile", "admin_credentials", "Found admin panel with credentials exposed", 95, 92, "credential_leak"),
            ("http://marketplace-dark.onion/shop", "credit_card_data", "Credit card data in public database", 98, 95, "financial_data"),
            ("http://forum-dark.onion/users", "user_database", "Exposed user database with personal info", 92, 88, "data_breach"),
            ("http://leak-dark.onion/corporate", "company_data", "Corporate files leaked on dark web", 90, 85, "data_breach"),
            ("http://stolen-dark.onion/accounts", "email_passwords", "Email and password combinations for sale", 88, 82, "credential_leak"),
            ("http://breach-dark.onion/customers", "customer_list", "Customer list with phone numbers", 85, 78, "personal_info"),
            ("http://data-dark.onion/financial", "bank_info", "Banking information exposed", 82, 80, "financial_data"),
            ("http://threat-dark.onion/report", "ransomware", "Ransomware threat targeting sector", 80, 75, "malware"),
            ("http://paste-dark.onion/leak", "api_keys", "API keys and secrets exposed", 78, 72, "credential_leak"),
            ("http://vendor-dark.onion/supply", "supply_chain", "Supply chain partner credentials", 75, 70, "credential_leak"),
        ]

                                
        for url, keyword, snippet, confidence, risk_score, classification in sample_findings:
            cursor.execute("""
                INSERT INTO findings (url, keyword, snippet, confidence, risk_score, classification)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (url, keyword, snippet, confidence, risk_score, classification))

                                       
        finding_id = 1
        extracted_data_samples = [
            (finding_id, "email", "admin@company.com"),
            (finding_id, "password_hash", "$2b$12$encrypted..."),
            (2, "card_number", "****-****-****-1234"),
            (2, "cvv_range", "Likely 700-900"),
            (3, "records_count", "50,000+"),
            (3, "fields", "Name, Email, Phone, Address"),
        ]

        for finding_id, data_type, data_value in extracted_data_samples:
            cursor.execute("""
                INSERT INTO extracted_data (finding_id, data_type, data_value)
                VALUES (?, ?, ?)
            """, (finding_id, data_type, data_value))

        conn.commit()
        conn.close()
        logger.info(f"Sample database created at {self.db_path}")

    def get_findings_data(self, days_back=30):
        """Get findings data with risk scores"""
        if not os.path.exists(self.db_path):
            logger.error(f"Database not found: {self.db_path}")
            return [], None

        cutoff_date = datetime.now() - timedelta(days=days_back)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

                                                             
            cursor.execute("""
                SELECT DISTINCT f.id, f.url, f.keyword, f.confidence, f.risk_score,
                       f.snippet, f.classification, f.found_at
                FROM findings f
                WHERE f.found_at > ? AND f.target_company = ?
                ORDER BY f.risk_score DESC, f.found_at DESC
            """, (cutoff_date.isoformat(), self.target_company))

            findings = cursor.fetchall()

                                                               
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT f.id) as total_findings,
                    COUNT(DISTINCT f.url) as unique_urls,
                    AVG(COALESCE(f.risk_score, 0)) as avg_risk,
                    MAX(COALESCE(f.risk_score, 0)) as max_risk,
                    COUNT(CASE WHEN f.risk_score >= 85 THEN 1 END) as critical_findings,
                    COUNT(CASE WHEN f.risk_score >= 70 AND f.risk_score < 85 THEN 1 END) as high_findings,
                    COUNT(CASE WHEN f.risk_score >= 50 AND f.risk_score < 70 THEN 1 END) as medium_findings,
                    COUNT(CASE WHEN f.risk_score < 50 THEN 1 END) as low_findings
                FROM findings f
                WHERE f.found_at > ? AND f.target_company = ?
            """, (cutoff_date.isoformat(), self.target_company))

            stats = cursor.fetchone()
            conn.close()

            return findings, stats

        except Exception as e:
            logger.error(f"Error querying database: {e}")
            return [], None

    def get_extracted_data(self, finding_id):
        """Get extracted data for a finding"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data_type, data_value FROM extracted_data WHERE finding_id = ?",
                (finding_id,)
            )
            data = cursor.fetchall()
            conn.close()
            return data
        except:
            return []

    def get_mitigation_advice(self, finding):
        """Get mitigation advice based on finding type"""
        classification = finding[6] or 'unknown'
        risk_score = finding[4]

        advice_map = {
            'credential_leak': [
                "Immediately change all passwords associated with this account",
                "Enable multi-factor authentication (MFA) on all accounts",
                "Monitor account activity for unauthorized access",
                "Consider credit monitoring and identity theft protection services",
                "Notify affected users immediately",
                "Reset API keys and access tokens"
            ],
            'data_breach': [
                "Contact all affected individuals immediately",
                "Begin formal incident response procedures",
                "Preserve forensic evidence",
                "Notify relevant regulatory authorities",
                "Coordinate with legal and PR teams",
                "Implement data access controls",
                "Conduct security audit of affected systems"
            ],
            'financial_data': [
                "Place fraud alerts on affected financial accounts",
                "Monitor all associated bank and credit card accounts",
                "Contact financial institutions immediately",
                "Consider credit freeze if extensive financial data exposed",
                "Report to appropriate financial regulatory bodies",
                "Review insurance coverage for breach liability"
            ],
            'personal_info': [
                "Monitor for identity theft indicators",
                "Place fraud alert on credit reports",
                "Set up credit monitoring services",
                "Be vigilant about phishing and social engineering attempts",
                "Monitor dark web for continued data sales",
                "Document all notifications sent"
            ],
            'malware': [
                "Isolate affected systems immediately",
                "Run comprehensive malware scans",
                "Update all antivirus and endpoint protection",
                "Review system logs for compromise indicators",
                "Perform forensic analysis",
                "Patch all known vulnerabilities"
            ]
        }

                                   
        if risk_score >= 85:
            base_advice = [
                "🔴 CRITICAL: Immediate action required - activate incident response team NOW",
                "Escalate to senior leadership and board-level executives",
                "Begin legal consultation immediately",
                "Implement crisis communication plan",
                "Consider involving law enforcement (FBI/Secret Service)",
                "Document all actions taken for compliance and legal purposes"
            ]
        elif risk_score >= 70:
            base_advice = [
                "🟠 HIGH PRIORITY: Address within 24 hours",
                "Notify relevant stakeholders and domain owners",
                "Strengthen security controls and monitoring",
                "Begin preliminary investigation",
                "Prepare communications to affected parties"
            ]
        elif risk_score >= 50:
            base_advice = [
                "🟡 MEDIUM PRIORITY: Address within 1 week",
                "Investigate and assess business impact",
                "Review and strengthen related security measures",
                "Monitor for related threats",
                "Plan remediation activities"
            ]
        else:
            base_advice = [
                "🟢 LOW PRIORITY: Monitor and maintain records",
                "Review security policies and best practices",
                "Consider as part of ongoing security assessment",
                "Document for future reference"
            ]

                                            
        if classification in advice_map:
            base_advice.extend(advice_map[classification])

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

    def generate_pdf_report(self, output_path="osint_full_report.pdf", days_back=30):
        """Generate comprehensive PDF report"""
        logger.info(f"Generating PDF report: {output_path}")

        doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=0.75*inch, bottomMargin=0.75*inch)
        styles = getSampleStyleSheet()
        story = []

                       
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            spaceAfter=10,
            alignment=1,
            textColor=colors.HexColor('#1a1a1a'),
            fontName='Helvetica-Bold'
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=12,
            textColor=colors.HexColor('#333333'),
            fontName='Helvetica-Bold',
            borderColor=colors.HexColor('#cccccc'),
            borderBottomWidth=2,
            borderBottomPadding=8
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            leading=14
        )

                                              
        story.append(Paragraph("DARK WEB OSINT SECURITY ASSESSMENT", title_style))
        story.append(Paragraph("COMPREHENSIVE FINDINGS REPORT", styles['Heading2']))
        story.append(Spacer(1, 0.3*inch))

        doc_date = datetime.now().strftime('%B %d, %Y at %H:%M:%S')
        report_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        story.append(Paragraph(f"<b>Report Generated:</b> {doc_date}", styles['Normal']))
        story.append(Paragraph(f"<b>Report ID:</b> {report_id}", styles['Normal']))
        story.append(Paragraph(f"<b>Target Company:</b> {self.target_company or 'N/A'}", styles['Normal']))
        story.append(Paragraph(f"<b>Analysis Period:</b> Last {days_back} days", styles['Normal']))
        story.append(Paragraph(f"<b>Classification:</b> CONFIDENTIAL", styles['Normal']))
        story.append(Spacer(1, 0.5*inch))

                                                     
        story.append(Paragraph("EXECUTIVE SUMMARY", subtitle_style))

        findings, stats = self.get_findings_data(days_back)

        if stats:
            summary_text = f"""
This report documents a comprehensive dark web OSINT analysis conducted over the past {days_back} days.
<br/><br/>

<b>KEY STATISTICS:</b><br/>
• Total Findings Identified: <b>{stats[0] or 0}</b><br/>
• Unique Source URLs: <b>{stats[1] or 0}</b><br/>
• Average Risk Score: <b>{stats[2]:.1f}/100</b><br/>
• Maximum Risk Score: <b>{max(stats[3] or 0, 0):.0f}/100</b><br/>
<br/>

<b>RISK BREAKDOWN:</b><br/>
• Critical Findings (≥85): <b style="color:red">{stats[4] or 0}</b><br/>
• High-Risk Findings (70-84): <b style="color:orange">{stats[5] or 0}</b><br/>
• Medium-Risk Findings (50-69): <b style="color:#cc9900">{stats[6] or 0}</b><br/>
• Low-Risk Findings (&lt;50): <b style="color:green">{stats[7] or 0}</b><br/>
<br/>

<b>IMMEDIATE ACTIONS REQUIRED:</b><br/>
Immediate attention is required for all {stats[4] or 0} critical findings (risk score ≥ 85).
High-risk findings ({stats[5] or 0}) must be addressed within 24 hours.
All findings in this report include specific mitigation recommendations.
            """
            story.append(Paragraph(summary_text, styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))

                                                           
        if findings:
            story.append(PageBreak())
            story.append(Paragraph("DETAILED FINDINGS OVERVIEW", subtitle_style))

                                        
            table_data = [['Risk', 'Score', 'Classification', 'Source URL', 'Keyword', 'Discovered']]

            for finding in findings:
                risk_level, _ = self.get_risk_level(finding[4])
                url_display = finding[1][:40] + "..." if len(finding[1]) > 40 else finding[1]
                discovered = datetime.fromisoformat(finding[7]).strftime('%Y-%m-%d')
                
                table_data.append([
                    risk_level,
                    f"{int(finding[4])}/100",
                    finding[6] or 'Unknown',
                    url_display,
                    finding[2] or 'N/A',
                    discovered
                ])

            table = Table(table_data, colWidths=[0.9*inch, 0.8*inch, 1.2*inch, 2.3*inch, 1.2*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a1a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (0, 0), (1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9f9f9')),
                ('BACKGROUND', (0, 1), (0, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            story.append(table)
            story.append(Spacer(1, 0.3*inch))

                                                                           
            story.append(PageBreak())
            story.append(Paragraph("CRITICAL & HIGH-RISK FINDINGS - DETAILED ANALYSIS", subtitle_style))

            critical_findings = [f for f in findings if f[4] >= 70]

            for i, finding in enumerate(critical_findings[:15]):                   
                risk_level, risk_color = self.get_risk_level(finding[4])

                finding_title = f"Finding #{i+1}: {risk_level} RISK"
                story.append(HRFlowable(width="100%", thickness=2, color=risk_color, spaceBefore=10, spaceAfter=10))
                story.append(Paragraph(finding_title, styles['Heading3']))

                details = f"""
<b>Keyword/Topic:</b> {finding[2] or 'N/A'}<br/>
<b>Source URL:</b> {finding[1]}<br/>
<b>Risk Score:</b> {int(finding[4])}/100 ({risk_level})<br/>
<b>Confidence Level:</b> {int(finding[3])}%<br/>
<b>Classification:</b> {finding[6] or 'Unknown'}<br/>
<b>Discovered:</b> {datetime.fromisoformat(finding[7]).strftime('%B %d, %Y at %H:%M')}<br/>
<b>Description:</b> {finding[5] or 'No context available'}<br/>
                """

                story.append(Paragraph(details, normal_style))
                story.append(Spacer(1, 0.15*inch))

                                                 
                extracted = self.get_extracted_data(finding[0])
                if extracted:
                    story.append(Paragraph("<b>Extracted Data Elements:</b>", styles['Heading4']))
                    for data_type, data_value in extracted:
                        story.append(Paragraph(f"• <b>{data_type}:</b> {data_value}", styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))

                                   
                story.append(Paragraph("<b>RECOMMENDED IMMEDIATE ACTIONS:</b>", styles['Heading4']))
                mitigation = self.get_mitigation_advice(finding)
                for action in mitigation:
                    story.append(Paragraph(f"• {action}", normal_style))

                story.append(Spacer(1, 0.2*inch))

                                                                                     
                if (i + 1) % 3 == 0 and i < len(critical_findings) - 1:
                    story.append(PageBreak())

                                                                   
            story.append(PageBreak())
            story.append(Paragraph("COMPREHENSIVE MITIGATION STRATEGY", subtitle_style))

            mitigation_strategies = {
                'IMMEDIATE (0-6 hours)': [
                    'Activate incident response team and crisis management',
                    'Notify all stakeholders and affected parties',
                    'Isolate compromised systems and disable affected credentials',
                    'Begin digital forensics on affected systems',
                    'Monitor for ongoing threats and data exfiltration',
                    'Engage legal counsel and review regulatory obligations'
                ],
                'URGENT (6-24 hours)': [
                    'Conduct full extent assessment of data exposure',
                    'Reset all passwords and security credentials',
                    'Enable enhanced monitoring on all systems',
                    'Review and patch security vulnerabilities',
                    'Implement additional access controls',
                    'Prepare customer notification and communication materials'
                ],
                'SHORT-TERM (1-7 days)': [
                    'Complete forensic investigation and analysis',
                    'Implement enhanced logging and monitoring',
                    'Conduct security awareness training',
                    'Review and update incident response procedures',
                    'Implement additional 2FA/MFA requirements',
                    'Monitor credit bureaus and threat intelligence feeds'
                ],
                'MEDIUM-TERM (1-4 weeks)': [
                    'Complete full security assessment and penetration testing',
                    'Implement security improvements and remediations',
                    'Develop enhanced data protection policies',
                    'Establish dark web monitoring services',
                    'Conduct third-party security audit',
                    'Review and update business continuity plans'
                ]
            }

            for timeframe, actions in mitigation_strategies.items():
                story.append(Paragraph(f"<b>{timeframe}:</b>", styles['Heading4']))
                for action in actions:
                    story.append(Paragraph(f"✓ {action}", styles['Normal']))
                story.append(Spacer(1, 0.15*inch))

                                                       
            story.append(PageBreak())
            story.append(Paragraph("RECOMMENDATIONS & BEST PRACTICES", subtitle_style))

            recommendations = """
<b>1. Implement Continuous Monitoring:</b><br/>
Deploy real-time dark web monitoring to identify threats targeting your organization.
Monitor for mentions of your company name, domains, and key executives.<br/>
<br/>

<b>2. Strengthen Access Controls:</b><br/>
Implement multi-factor authentication (MFA) for all critical systems.<br/>
Enforce strong password policies and regular rotation.<br/>
Utilize principle of least privilege for system access.<br/>
<br/>

<b>3. Data Protection:</b><br/>
Implement data loss prevention (DLP) solutions.<br/>
Encrypt sensitive data at rest and in transit.<br/>
Minimize collection and retention of sensitive data.<br/>
<br/>

<b>4. Employee Training:</b><br/>
Conduct regular security awareness training.<br/>
Implement phishing simulation and testing.<br/>
Establish clear incident reporting procedures.<br/>
<br/>

<b>5. Incident Response:</b><br/>
Develop and maintain comprehensive incident response plan.<br/>
Conduct regular tabletop exercises and drills.<br/>
Establish clear escalation procedures.<br/>
Document all incidents and lessons learned.<br/>
<br/>

<b>6. Threat Intelligence:</b><br/>
Subscribe to threat intelligence feeds.<br/>
Participate in information sharing communities.<br/>
Monitor relevant security advisories and alerts.<br/>
<br/>

<b>7. Compliance & Legal:</b><br/>
Ensure compliance with all relevant regulations (GDPR, CCPA, etc.).<br/>
Maintain documentation of all security measures.<br/>
Review insurance coverage for cyber incidents.<br/>
Establish relationships with legal counsel specializing in cybersecurity.<br/>
            """

            story.append(Paragraph(recommendations, styles['Normal']))

                                                     
            story.append(PageBreak())
            story.append(Paragraph("REPORT INFORMATION & DISCLAIMERS", subtitle_style))

            footer_text = f"""
<b>Report Details:</b><br/>
Report ID: {report_id}<br/>
Generated: {doc_date}<br/>
Analysis Period: {days_back} days<br/>
Total Findings: {stats[0] or 0}<br/>
Critical Findings: {stats[4] or 0}<br/>
<br/>

<b>Classification:</b> CONFIDENTIAL<br/>
This report contains sensitive security information and should be handled as confidential.
<br/><br/>

<b>Disclaimer:</b><br/>
This report is generated automatically by the Dark Web OSINT system based on available data.
While efforts have been made to ensure accuracy, findings should be validated independently.
The absence of findings does not guarantee the absence of threats.<br/>
<br/>

<b>Contact Information:</b><br/>
For questions, concerns, or additional analysis, contact your security team.<br/>
For emergencies, activate your incident response procedures immediately.<br/>
<br/>

<b>Next Steps:</b><br/>
1. Distribute this report to all authorized personnel<br/>
2. Initiate response procedures for critical findings<br/>
3. Schedule follow-up assessment in 7 days<br/>
4. Document all remediation efforts<br/>
5. Monitor effectiveness of implemented measures<br/>
            """

            story.append(Paragraph(footer_text, styles['Normal']))

                   
        doc.build(story)
        logger.info(f"[✓] PDF report successfully generated: {output_path}")
        print(f"\n{'='*60}")
        print(f"[✓] REPORT GENERATED SUCCESSFULLY!")
        print(f"{'='*60}")
        print(f"Report Path: {output_path}")
        print(f"Report Size: {os.path.getsize(output_path) / 1024:.2f} KB")
        print(f"Findings Included: {len(findings)}")
        print(f"Critical Findings: {stats[4] if stats else 0}")
        print(f"{'='*60}\n")

        return output_path

if __name__ == "__main__":
    import sys

                        
    output_file = "osint_full_report.pdf"
    days = 30

                                  
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    if len(sys.argv) > 2:
        days = int(sys.argv[2])

                     
    try:
        generator = ComprehensiveReportGenerator()
        generator.generate_pdf_report(output_path=output_file, days_back=days)
        print(f"✓ Report ready for distribution: {output_file}")
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
