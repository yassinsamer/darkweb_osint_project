#!/usr/bin/env python3
"""
Enhanced Dark Web OSINT GUI - Feature Guide
"""

GUI_FEATURES = """
╔════════════════════════════════════════════════════════════════════════════╗
║         Enhanced Dark Web OSINT GUI - Security Intelligence Platform        ║
╚════════════════════════════════════════════════════════════════════════════╝

OVERVIEW
========
The enhanced GUI provides a complete interface for dark web OSINT monitoring,
crawling, and reporting with integrated findings display and PDF report viewing.

MAIN FEATURES
=============

1. CONTROL PANEL (Top)
   ├─ Set Company: Define target company for monitoring
   ├─ ▶ Start Crawl: Begin dark web crawling (auto-generates report after completion)
   ├─ 📊 View Findings: Switch to findings table view
   ├─ 📄 Generate Report: Create comprehensive PDF report
   ├─ 📖 View PDF Report: Open the generated PDF report
   └─ 🔄 Refresh: Update all displays with latest data

2. TABBED INTERFACE
   
   TAB 1: 📈 DASHBOARD
   ───────────────────
   Shows comprehensive security statistics and risk breakdown:
   
   • Summary Statistics Panel:
     - Total Findings: All findings from dark web monitoring
     - Successful Crawls: Completed scan operations
     - Extracted Data Points: Individual data elements found
     - Critical Findings: Risk score ≥ 85
     - High-Risk Findings: Risk score 70-84
   
   • Top Data Section (Left):
     - Top URLs by findings count
     - Most frequent keywords discovered
   
   • Risk Assessment Section (Right):
     - Risk breakdown (CRITICAL/HIGH/MEDIUM/LOW)
     - Critical findings list with scores
   
   TAB 2: 🔍 ALL FINDINGS
   ──────────────────────
   Detailed table view of all security findings with filtering and export:
   
   • Filter Options:
     - Risk Level: All, Critical, High, Medium, Low
     - Real-time filtering and sorting
   
   • Findings Table Columns:
     - Risk Level: Visual indicator (🔴🟠🟡🟢) and label
     - Score: Risk score out of 100
     - Classification: Type (credential_leak, data_breach, etc.)
     - URL: Source URL from dark web
     - Keyword: Search term that triggered finding
     - Confidence: Detection confidence percentage
     - Date: When finding was discovered
   
   • Interactive Features:
     - Right-click on findings for detailed information
     - Sort by any column (click headers)
     - 📥 Export to CSV for external analysis
     - 🔄 Reload to refresh table
   
   TAB 3: 📋 LOGS
   ──────────────
   Real-time logging and debug information:
   
   • Shows all operations:
     - Crawling progress
     - Report generation status
     - Database queries
     - Errors and warnings
   
   • Log Management:
     - Clear all logs
     - Save logs to text file

AUTO FEATURES
=============

1. AFTER CRAWL COMPLETION:
   ✓ Automatically generates comprehensive PDF report
   ✓ Automatically loads and displays findings in table
   ✓ Updates dashboard statistics
   ✓ Shows success notification

2. AUTO-OPEN FUNCTIONALITY:
   • PDF Report: Open in default PDF viewer
   • Findings: Auto-load when switching tabs
   • Dashboard: Auto-refresh every interaction

DATA DISPLAY
============

Dashboard Risk Indicators:
   🔴 CRITICAL (Risk ≥ 85): Immediate action required
   🟠 HIGH (Risk 70-84): Address within 24 hours
   🟡 MEDIUM (Risk 50-69): Address within 1 week
   🟢 LOW (Risk < 50): Monitor and review

PDF REPORT CONTENTS
===================
The auto-generated PDF report includes:
   ✓ Executive Summary with statistics
   ✓ Detailed Findings Table
   ✓ Critical & High-Risk Analysis
   ✓ Extracted Data Elements
   ✓ Recommended Immediate Actions
   ✓ Comprehensive Mitigation Strategies
   ✓ Best Practices & Recommendations
   ✓ Report Information & Disclaimers

WORKFLOW EXAMPLE
================

1. Set Target Company:
   • Enter company name in "Target Company" field
   • Click "Set Company"

2. Start Monitoring:
   • Click "▶ Start Crawl"
   • Monitor progress in Logs tab
   • Wait for automatic report generation

3. View Results:
   • Check Dashboard tab for overview
   • Click "🔍 View Findings" to see detailed table
   • Right-click findings for details
   • Filter by risk level as needed

4. Review Report:
   • Click "📖 View PDF Report" to open in viewer
   • Review mitigation advice
   • Export findings to CSV if needed

5. Take Action:
   • Follow mitigation recommendations
   • Document all actions taken
   • Schedule follow-up assessment

KEYBOARD SHORTCUTS
==================
• Tab Navigation: Ctrl+Tab, Ctrl+Shift+Tab
• Tree Selection: Arrow keys
• Expand/Collapse: Left/Right arrow keys
• Context Menu: Right-click

STATUS BAR
==========
Bottom status bar shows:
   ✅ Ready: System ready for commands
   🔄 Running: Operation in progress
   ✓ Complete: Last operation finished
   ⚠️ Warning: Issues encountered

DATABASE OPERATIONS
====================
The GUI automatically queries the findings.db database:
   • Loads all findings with risk scores
   • Extracts data type and classification
   • Calculates statistics in real-time
   • Supports filtering and sorting

REPORT GENERATION
=================
Report Generator Command:
   python generate_full_report.py [output_file] [days_back]
   
Default: osint_full_report.pdf (30 days)

PDF Features:
   • Professional formatting (A4 size)
   • Color-coded risk levels
   • Detailed tables and summaries
   • Mitigation guidance
   • Legal disclaimers

TROUBLESHOOTING
===============

Issue: Database not found
Solution: Run crawler first to generate findings.db

Issue: No findings displayed
Solution: 
   1. Refresh dashboard (button in toolbar)
   2. Check Logs tab for errors
   3. Verify crawler completed successfully

Issue: PDF report won't open
Solution:
   1. Ensure osint_full_report.pdf exists
   2. Click "Generate Report" to create new one
   3. Use "View PDF Report" button

Issue: GUI crashes
Solution:
   1. Check Logs tab for error messages
   2. Verify all dependencies installed
   3. Try closing and reopening GUI

EXPORTING DATA
==============

Export Findings to CSV:
   1. Go to "All Findings" tab
   2. Click "📥 Export Findings"
   3. Choose save location
   4. File will contain all findings with all columns

Save Logs:
   1. Go to "Logs" tab
   2. Click "Save Logs"
   3. Choose save location
   4. Text file with all log entries

SECURITY NOTES
==============
✓ Findings are stored locally in SQLite database
✓ PDF reports are marked CONFIDENTIAL
✓ Logs contain sensitive information - handle carefully
✓ Always backup database before updating
✓ Use strong access controls for findings

PERFORMANCE
===========
• GUI optimized for 1000+ findings
• Table sorting instant on small datasets
• Filtering updates in real-time
• PDF generation: ~2-5 seconds
• Auto-refresh throttled to prevent lag

SUPPORT
=======
For issues or questions:
   1. Check Logs tab for error messages
   2. Review findings in table view
   3. Verify database integrity
   4. Check PDF report for detailed analysis
   5. Consult security team

═══════════════════════════════════════════════════════════════════════════════
Last Updated: 2026-04-14
Version: 1.1 (Enhanced)
"""

if __name__ == "__main__":
    print(GUI_FEATURES)
    
    # Also save to file with proper encoding
    with open("GUI_HELP.txt", "w", encoding='utf-8') as f:
        f.write(GUI_FEATURES)
    print("\n[✓] Help guide saved to GUI_HELP.txt")
