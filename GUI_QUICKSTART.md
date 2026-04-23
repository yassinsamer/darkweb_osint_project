# Enhanced GUI - Quick Start Guide

## What's New

Your Dark Web OSINT GUI has been completely enhanced with the following features:

### 1. **Tabbed Interface**
- **Dashboard Tab**: Overview of all statistics, risk breakdown, and critical findings
- **All Findings Tab**: Detailed table view of every finding with filtering capabilities  
- **Logs Tab**: Real-time logging of all operations

### 2. **Auto-Report Generation**
- When you click "Start Crawl", the system automatically:
  1. Performs dark web crawling
  2. **Automatically generates PDF report** with all findings
  3. Loads findings into the GUI table
  4. Updates dashboard statistics
  5. Shows success notification

### 3. **Findings Display**
- Complete table showing all findings with:
  - Risk Level (CRITICAL/HIGH/MEDIUM/LOW with color indicators)
  - Risk Score (0-100)
  - Classification (credential_leak, data_breach, etc.)
  - Source URL
  - Keyword/Topic
  - Confidence Level
  - Date Discovered

### 4. **Risk Filtering**
- Filter findings by risk level: All, Critical, High, Medium, Low
- Real-time filtering without reloading data
- Right-click on any finding for detailed information

### 5. **Report Features**
- **Generate Report**: Create comprehensive PDF on demand
- **View PDF Report**: Open generated PDF in your default viewer
- **Export to CSV**: Export all findings to spreadsheet format

### 6. **Dashboard Statistics**
- Total Findings count
- Successful Crawls
- Extracted Data Points
- Critical Findings (Risk >= 85)
- High-Risk Findings (Risk 70-84)
- Top URLs by findings count
- Top Keywords discovered
- Risk breakdown chart
- Critical findings list

## How to Use

### Step 1: Launch the GUI
```bash
python gui.py
```
Or double-click `launch_gui.bat`

### Step 2: Set Target Company
1. Enter company name in the "Target Company" field
2. Click "Set Company" button

### Step 3: Start Crawling
1. Click "▶ Start Crawl" button
2. Monitor progress in the Logs tab
3. Wait for automatic report generation (2-5 seconds after crawl completes)

### Step 4: View Results

**Option A - Dashboard View:**
- Stay on Dashboard tab to see overview
- Check statistics and risk breakdown
- Review critical findings list

**Option B - Detailed Findings:**
1. Click "📊 View Findings" or go to "All Findings" tab
2. See complete table of all findings
3. Filter by risk level if desired
4. Right-click any finding for details

**Option C - PDF Report:**
1. Click "📖 View PDF Report" to open in PDF viewer
2. Review detailed analysis and mitigation strategies
3. Print or share the report

### Step 5: Export Data
1. Go to "All Findings" tab
2. Click "📥 Export Findings"
3. Save as CSV for external analysis
4. Or click "Save Logs" in Logs tab to save session logs

## Key Features

### Automatic After Crawling
✅ PDF report auto-generated  
✅ Findings table auto-loaded  
✅ Dashboard auto-refreshed  
✅ Success notification shown  

### Real-Time Updates
✅ Risk filter updates instantly  
✅ Dashboard refreshes on demand  
✅ Logs update as operations run  

### Data Export
✅ CSV export of all findings  
✅ Log file export  
✅ PDF report generation  

### Risk Indicators
🔴 **CRITICAL** - Risk >= 85 (Immediate action)  
🟠 **HIGH** - Risk 70-84 (24-hour response)  
🟡 **MEDIUM** - Risk 50-69 (1-week response)  
🟢 **LOW** - Risk < 50 (Monitor)  

## PDF Report Contents

The auto-generated report includes:
- Executive Summary with statistics
- Detailed findings table
- Critical & high-risk analysis
- Extracted data elements
- Recommended immediate actions
- Comprehensive mitigation strategies
- Best practices & recommendations
- Legal disclaimers

## Status Bar Information

The bottom status bar shows:
- **Ready** - System ready for input
- **🔄 Running** - Operation in progress
- **✅ Ready** - Last operation completed successfully
- **⚠️ Error** - Issue occurred (check Logs tab)

## Keyboard Tips

- Use arrow keys to navigate the findings table
- Right-click on findings for context menu
- Ctrl+Tab to switch between tabs
- Click table headers to sort by column

## Troubleshooting

**No findings shown?**
- Make sure crawler has run successfully
- Check Logs tab for errors
- Click Refresh button to reload

**PDF won't open?**
- Click "Generate Report" to create a new one
- Check if PDF viewer is installed
- Try "View PDF Report" button

**GUI freezes?**
- Check if crawler is still running in Logs
- Wait for operation to complete
- Close and reopen GUI if needed

## Next Steps

1. ✅ Run your first crawl
2. ✅ Review findings in the GUI
3. ✅ Check the generated PDF report
4. ✅ Export findings to CSV for analysis
5. ✅ Take action on critical findings
6. ✅ Schedule follow-up crawls

## Support

If you encounter issues:
1. Check the Logs tab for error messages
2. Review findings displayed in table
3. Verify database file exists (findings.db)
4. Try refreshing or reopening GUI
5. Check the PDF report for detailed analysis

---

**Version**: 1.1 (Enhanced)  
**Last Updated**: April 14, 2026  
**Features**: Dashboard, Findings Table, Auto-Report, Filtering, Export
