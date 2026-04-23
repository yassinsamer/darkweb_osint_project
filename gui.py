import json
import threading
import subprocess
import os
import sqlite3
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import webbrowser
from datetime import datetime
from pathlib import Path

CONFIG_PATH = "config.json"
ORCHESTRATOR_CMD = ["python", "orchestrator.py"]
QUERY_CMD_BASE = ["python", "query_database.py"]
REPORT_PATH = "osint_full_report.pdf"
REPORT_GENERATOR = ["python", "generate_full_report.py"]

class DarkWebGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dark Web OSINT GUI - Security Intelligence Platform")
        self.geometry("1400x800")
        self.minsize(1200, 600)

        self.company_var = tk.StringVar()
        self.crawl_active = False
        self.create_widgets()

    def create_widgets(self):
                           
        control_frame = ttk.Frame(self, padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Label(control_frame, text="Target Company:", font=(None, 10)).pack(side=tk.LEFT, padx=5)
        ttk.Entry(control_frame, textvariable=self.company_var, width=30).pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Set Company", command=self.set_company).pack(side=tk.LEFT, padx=3)
        ttk.Button(control_frame, text="▶ Start Crawl", command=self.start_crawl).pack(side=tk.LEFT, padx=3)
        ttk.Button(control_frame, text="📊 View Findings", command=self.show_findings_view).pack(side=tk.LEFT, padx=3)
        ttk.Button(control_frame, text="📄 Generate Report", command=self.generate_report).pack(side=tk.LEFT, padx=3)
        ttk.Button(control_frame, text="📖 View PDF Report", command=self.open_pdf_report).pack(side=tk.LEFT, padx=3)
        ttk.Button(control_frame, text="🔄 Refresh", command=self.refresh_summary).pack(side=tk.LEFT, padx=3)

        self.status_label = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W, font=(None, 9))
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

                                              
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

                          
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="📈 Dashboard")
        self.create_dashboard_tab()

                         
        self.findings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.findings_frame, text="🔍 All Findings")
        self.create_findings_tab()

                     
        self.logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_frame, text="📋 Logs")
        self.create_logs_tab()

        self.load_company_from_config()
        self.refresh_summary()

    def create_dashboard_tab(self):
        """Create dashboard with summary statistics"""
        summary_frame = ttk.LabelFrame(self.dashboard_frame, text="Summary Statistics", padding=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=10)

        self.summary_labels = {}
        summary_stats = ["Total Findings", "Successful Crawls", "Extracted Data Points", 
                         "Critical Findings", "High-Risk Findings"]
        
        for idx, name in enumerate(summary_stats):
            label = ttk.Label(summary_frame, text=f"{name}: 0", font=(None, 11, "bold"))
            label.grid(row=0, column=idx, padx=10, pady=5, sticky=tk.W)
            self.summary_labels[name] = label

                                      
        content_frame = ttk.Frame(self.dashboard_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                                                    
        paned = ttk.PanedWindow(content_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

                                      
        left_frame = ttk.LabelFrame(paned, text="Top Data", padding=5)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Top URLs (by findings)", font=(None, 10, "bold")).pack(anchor=tk.W, pady=5)
        self.top_urls = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, state="disabled", height=8)
        self.top_urls.pack(fill=tk.BOTH, expand=True, pady=2)

        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        ttk.Label(left_frame, text="Top Keywords", font=(None, 10, "bold")).pack(anchor=tk.W)
        self.top_keywords = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, state="disabled", height=6)
        self.top_keywords.pack(fill=tk.BOTH, expand=True, pady=2)

                                            
        right_frame = ttk.LabelFrame(paned, text="Risk Assessment", padding=5)
        paned.add(right_frame, weight=1)

        ttk.Label(right_frame, text="Risk Breakdown", font=(None, 10, "bold")).pack(anchor=tk.W, pady=5)
        self.risk_summary = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, state="disabled", height=8)
        self.risk_summary.pack(fill=tk.BOTH, expand=True, pady=2)

        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        ttk.Label(right_frame, text="Critical Findings", font=(None, 10, "bold")).pack(anchor=tk.W)
        self.critical_findings = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, state="disabled", height=6)
        self.critical_findings.pack(fill=tk.BOTH, expand=True, pady=2)

    def create_findings_tab(self):
        """Create findings table view"""
        filter_frame = ttk.Frame(self.findings_frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(filter_frame, text="Filter by Risk:").pack(side=tk.LEFT, padx=5)
        self.risk_filter = ttk.Combobox(filter_frame, values=["All", "Critical", "High", "Medium", "Low"], state="readonly", width=15)
        self.risk_filter.set("All")
        self.risk_filter.pack(side=tk.LEFT, padx=5)
        self.risk_filter.bind("<<ComboboxSelected>>", lambda e: self.load_findings())

        ttk.Button(filter_frame, text="📥 Export Findings", command=self.export_findings).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="🔄 Reload", command=self.load_findings).pack(side=tk.LEFT, padx=5)

                                      
        tree_frame = ttk.Frame(self.findings_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.findings_tree = ttk.Treeview(tree_frame, columns=(
            "Risk", "Score", "Classification", "URL", "Keyword", "Confidence", "Date"
        ), height=20, show="tree headings")

        self.findings_tree.column("#0", width=30)
        self.findings_tree.column("Risk", width=70, anchor="center")
        self.findings_tree.column("Score", width=60, anchor="center")
        self.findings_tree.column("Classification", width=100)
        self.findings_tree.column("URL", width=300)
        self.findings_tree.column("Keyword", width=100)
        self.findings_tree.column("Confidence", width=80, anchor="center")
        self.findings_tree.column("Date", width=120)

        for col in ["Risk", "Score", "Classification", "URL", "Keyword", "Confidence", "Date"]:
            self.findings_tree.heading(col, text=col)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.findings_tree.yview)
        self.findings_tree.configure(yscroll=scrollbar.set)

        self.findings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

                                      
        self.findings_tree.bind("<Button-3>", self.show_finding_details)

    def create_logs_tab(self):
        """Create logs view"""
        button_frame = ttk.Frame(self.logs_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(button_frame, text="Clear Logs", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Logs", command=self.save_logs).pack(side=tk.LEFT, padx=5)

        self.output = scrolledtext.ScrolledText(self.logs_frame, wrap=tk.WORD, state="disabled")
        self.output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def load_company_from_config(self):
        if not os.path.exists(CONFIG_PATH):
            return
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            company = cfg.get("target_company", "")
            self.company_var.set(company)

    def set_company(self):
        company = self.company_var.get().strip()
        if not company:
            messagebox.showwarning("Input required", "Please enter a company name.")
            return
        self._update_config(company)
        self.log(f"[+] Target company set to '{company}' in config.json")

    def _update_config(self, company):
        cfg = {}
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        cfg["target_company"] = company
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        self.company_var.set(company)

    def start_crawl(self):
        """Start crawling and auto-generate report after completion"""
        if self.crawl_active:
            messagebox.showwarning("Crawl Active", "A crawl is already running.")
            return
        
        self.crawl_active = True
        thread = threading.Thread(target=self._run_crawl, daemon=True)
        thread.start()

    def _run_crawl(self):
        """Execute crawl and auto-generate report"""
        self.status_label.configure(text="🔄 Crawling in progress...")
        self.log(f"[~] Executing: {' '.join(ORCHESTRATOR_CMD)}")

        process = subprocess.Popen(
            ORCHESTRATOR_CMD, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            cwd=os.getcwd()
        )

        for line in process.stdout:
            self.log(line.rstrip())

        process.wait()
        self.log(f"[+] Crawl completed (exit code {process.returncode})")
        
                                             
        self.log("[~] Auto-generating report...")
        self.generate_report()
        
        self.crawl_active = False
        self.refresh_summary()
        self.load_findings()
        self.status_label.configure(text="✅ Ready - Report generated!")
        messagebox.showinfo("Success", "Crawl completed and report generated!")

    def generate_report(self):
        """Generate comprehensive PDF report"""
        self.status_label.configure(text="📄 Generating report...")
        self.log("[~] Generating comprehensive PDF report...")

        cmd = REPORT_GENERATOR + [REPORT_PATH, "30"]
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            cwd=os.getcwd()
        )

        for line in process.stdout:
            self.log(line.rstrip())

        process.wait()
        
        if process.returncode == 0:
            self.log(f"[✓] Report generated: {REPORT_PATH}")
            self.status_label.configure(text="✅ Report ready!")
        else:
            self.log(f"[!] Report generation failed (exit code {process.returncode})")

    def open_pdf_report(self):
        """Open the generated PDF report"""
        if not os.path.exists(REPORT_PATH):
            messagebox.showwarning("Report Not Found", f"Report file '{REPORT_PATH}' not found. Generate one first.")
            return
        
        self.log(f"[~] Opening report: {REPORT_PATH}")
        try:
            os.startfile(REPORT_PATH)
            self.log("[✓] Report opened in default viewer")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open report: {e}")

    def load_findings(self):
        """Load findings from database into treeview"""
                              
        for item in self.findings_tree.get_children():
            self.findings_tree.delete(item)

        db_path = "findings.db"
        if not os.path.exists(db_path):
            self.log("[!] No database found")
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

                             
            risk_filter = self.risk_filter.get()
            
            query = "SELECT id, url, keyword, risk_score, confidence, classification, found_at FROM findings"
            
            if risk_filter != "All":
                risk_map = {
                    "Critical": (85, 100),
                    "High": (70, 84),
                    "Medium": (50, 69),
                    "Low": (0, 49)
                }
                if risk_filter in risk_map:
                    min_risk, max_risk = risk_map[risk_filter]
                    query += f" WHERE risk_score >= {min_risk} AND risk_score <= {max_risk}"
            
            query += " ORDER BY risk_score DESC, found_at DESC"
            cursor.execute(query)
            findings = cursor.fetchall()

            row_id = 1
            for finding in findings:
                finding_id, url, keyword, risk_score, confidence, classification, found_at = finding
                
                                      
                if risk_score >= 85:
                    risk_level = "🔴 CRITICAL"
                elif risk_score >= 70:
                    risk_level = "🟠 HIGH"
                elif risk_score >= 50:
                    risk_level = "🟡 MEDIUM"
                else:
                    risk_level = "🟢 LOW"

                date_str = datetime.fromisoformat(found_at).strftime('%Y-%m-%d %H:%M')
                
                self.findings_tree.insert("", "end", iid=f"item_{row_id}", text=str(row_id), values=(
                    risk_level,
                    f"{int(risk_score)}/100",
                    classification or "Unknown",
                    url,
                    keyword or "N/A",
                    f"{int(confidence)}%",
                    date_str
                ))
                row_id += 1

            conn.close()
            self.log(f"[✓] Loaded {len(findings)} findings")
        except Exception as e:
            self.log(f"[!] Error loading findings: {e}")

    def show_finding_details(self, event):
        """Show detailed information about a finding"""
        selection = self.findings_tree.selection()
        if not selection:
            return

        item_id = selection[0]
        values = self.findings_tree.item(item_id)['values']
        
        details = f"""
Finding Details:
{'='*60}
Risk Level: {values[0]}
Risk Score: {values[1]}
Classification: {values[2]}
URL: {values[3]}
Keyword: {values[4]}
Confidence: {values[5]}
Discovered: {values[6]}
{'='*60}

Recommended Actions:
- Review the full PDF report for detailed mitigation advice
- Check the findings database for extracted data
- Take immediate action for critical findings
        """
        
        messagebox.showinfo("Finding Details", details)

    def show_findings_view(self):
        """Switch to findings view"""
        self.notebook.select(self.findings_frame)
        self.load_findings()

    def export_findings(self):
        """Export findings to CSV"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"findings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if not file_path:
            return

        db_path = "findings.db"
        if not os.path.exists(db_path):
            messagebox.showerror("Error", "No database found")
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, url, keyword, risk_score, confidence, classification, found_at 
                FROM findings ORDER BY risk_score DESC
            """)
            findings = cursor.fetchall()

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("ID,URL,Keyword,Risk Score,Confidence,Classification,Date\n")
                for finding in findings:
                    f.write(','.join([str(f) for f in finding]) + '\n')

            conn.close()
            self.log(f"[✓] Exported {len(findings)} findings to {file_path}")
            messagebox.showinfo("Success", f"Exported {len(findings)} findings to CSV")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

    def get_summary_data(self):
        data = {
            "total_findings": 0,
            "successful_crawls": 0,
            "extracted_data": 0,
            "critical_findings": 0,
            "high_findings": 0,
            "top_urls": [],
            "risk_summary": [],
            "top_keywords": [],
            "critical_list": []
        }
        db_path = "findings.db"
        if not os.path.exists(db_path):
            return data

        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*) FROM findings")
            data["total_findings"] = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM findings WHERE risk_score >= 85")
            data["critical_findings"] = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM findings WHERE risk_score >= 70 AND risk_score < 85")
            data["high_findings"] = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM extracted_data")
            data["extracted_data"] = c.fetchone()[0]
            
            c.execute("""
                SELECT url, COUNT(*) as count FROM findings 
                GROUP BY url ORDER BY count DESC LIMIT 5
            """)
            data["top_urls"] = c.fetchall()
            
            c.execute("""
                SELECT keyword, COUNT(*) as count FROM findings 
                GROUP BY keyword ORDER BY count DESC LIMIT 5
            """)
            data["top_keywords"] = c.fetchall()
            
            c.execute("""
                SELECT 
                    CASE 
                        WHEN risk_score >= 85 THEN 'CRITICAL'
                        WHEN risk_score >= 70 THEN 'HIGH'
                        WHEN risk_score >= 50 THEN 'MEDIUM'
                        ELSE 'LOW'
                    END as level,
                    COUNT(*) as count
                FROM findings
                GROUP BY level
                ORDER BY level DESC
            """)
            data["risk_summary"] = c.fetchall()
            
            c.execute("""
                SELECT url, risk_score, keyword FROM findings 
                WHERE risk_score >= 85 
                ORDER BY risk_score DESC LIMIT 5
            """)
            data["critical_list"] = c.fetchall()
            
            conn.close()
        except Exception as e:
            self.log(f"[!] Summary load error: {e}")
        return data

    def refresh_summary(self):
        summary = self.get_summary_data()
        self.summary_labels["Total Findings"].configure(
            text=f"Total Findings: {summary['total_findings']}"
        )
        self.summary_labels["Successful Crawls"].configure(
            text=f"Successful Crawls: {summary['total_findings']}"
        )
        self.summary_labels["Extracted Data Points"].configure(
            text=f"Extracted Data Points: {summary['extracted_data']}"
        )
        self.summary_labels["Critical Findings"].configure(
            text=f"Critical Findings: {summary['critical_findings']}"
        )
        self.summary_labels["High-Risk Findings"].configure(
            text=f"High-Risk Findings: {summary['high_findings']}"
        )

        self.top_urls.configure(state="normal")
        self.top_urls.delete(1.0, tk.END)
        if summary["top_urls"]:
            for url, count in summary["top_urls"]:
                self.top_urls.insert(tk.END, f"🔗 ({count}) {url}\n")
        else:
            self.top_urls.insert(tk.END, "No findings yet.\n")
        self.top_urls.configure(state="disabled")

        self.top_keywords.configure(state="normal")
        self.top_keywords.delete(1.0, tk.END)
        if summary["top_keywords"]:
            for keyword, count in summary["top_keywords"]:
                self.top_keywords.insert(tk.END, f"🏷️  {keyword}: {count}\n")
        else:
            self.top_keywords.insert(tk.END, "No keyword findings yet.\n")
        self.top_keywords.configure(state="disabled")

        self.risk_summary.configure(state="normal")
        self.risk_summary.delete(1.0, tk.END)
        if summary["risk_summary"]:
            risk_icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
            for level, count in summary["risk_summary"]:
                icon = risk_icons.get(level, "")
                self.risk_summary.insert(tk.END, f"{icon} {level}: {count}\n")
        else:
            self.risk_summary.insert(tk.END, "No risk assessments yet.\n")
        self.risk_summary.configure(state="disabled")

        self.critical_findings.configure(state="normal")
        self.critical_findings.delete(1.0, tk.END)
        if summary["critical_list"]:
            for url, score, keyword in summary["critical_list"]:
                self.critical_findings.insert(tk.END, f"🔴 {score:.0f}/100 - {keyword}\n")
        else:
            self.critical_findings.insert(tk.END, "No critical findings.\n")
        self.critical_findings.configure(state="disabled")

    def clear_log(self):
        self.output.configure(state="normal")
        self.output.delete(1.0, tk.END)
        self.output.configure(state="disabled")

    def save_logs(self):
        """Save logs to file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"osint_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.output.get(1.0, tk.END))
            self.log(f"[✓] Logs saved to {file_path}")
            messagebox.showinfo("Success", "Logs saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save logs: {e}")

    def log(self, message):
        self.output.configure(state="normal")
        self.output.insert(tk.END, message + "\n")
        self.output.see(tk.END)
        self.output.configure(state="disabled")

if __name__ == "__main__":
    app = DarkWebGUI()
    app.mainloop()
