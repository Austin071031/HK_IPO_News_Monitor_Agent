import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import datetime
import time
import os
from config import load_config, save_config

# Import logic modules
from scraper import IPOScraper
from analyzer import IPOAnalyzer
from enricher import IPOEnricher
# from reporter import PDFReporter
from reporter import IPOReporter
# from utils import open_email_draft
from utils import are_names_similar

class IPOMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HK IPO News & Rumors Monitor AI Agent")
        self.root.geometry("900x700")
        
        self.config = load_config()
        self.is_running = False
        
        # Workflow state
        self.step = 0
        self.news_items = []
        self.analyzed_companies = []
        self.scraper = None
        self.analyzer = None
        self.enricher = None
        self.reporter = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # Create Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.config_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.dashboard_frame, text='Dashboard')
        self.notebook.add(self.config_frame, text='Configuration')
        
        self.setup_dashboard()
        self.setup_config()
        
    def setup_dashboard(self):
        # Control Panel
        control_frame = ttk.LabelFrame(self.dashboard_frame, text="Control Panel")
        control_frame.pack(fill='x', padx=10, pady=5)
        
        self.start_btn = ttk.Button(control_frame, text="Start Monitoring", command=self.start_monitoring)
        self.start_btn.pack(side='left', padx=10, pady=10)
        
        self.status_lbl = ttk.Label(control_frame, text="Status: Ready")
        self.status_lbl.pack(side='left', padx=10, pady=10)
        
        # Logs
        log_frame = ttk.LabelFrame(self.dashboard_frame, text="Activity Log")
        log_frame.pack(expand=True, fill='both', padx=10, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, state='disabled', height=20)
        self.log_area.pack(expand=True, fill='both', padx=5, pady=5)
        
        # Progress
        self.progress = ttk.Progressbar(self.dashboard_frame, mode='indeterminate')
        self.progress.pack(fill='x', padx=10, pady=5)
        
    def setup_config(self):
        # Scrollable Config Frame
        canvas = tk.Canvas(self.config_frame)
        scrollbar = ttk.Scrollbar(self.config_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # API Keys
        api_frame = ttk.LabelFrame(scrollable_frame, text="API Keys")
        api_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(api_frame, text="Firecrawl API Key:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.firecrawl_key = ttk.Entry(api_frame, width=50)
        # Use 'or ""' to handle None values from config
        self.firecrawl_key.insert(0, self.config.get("firecrawl_api_key") or "")
        self.firecrawl_key.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(api_frame, text="DeepSeek API Key:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.deepseek_key = ttk.Entry(api_frame, width=50)
        # Use 'or ""' to handle None values from config
        self.deepseek_key.insert(0, self.config.get("deepseek_api_key") or "")
        self.deepseek_key.grid(row=1, column=1, padx=5, pady=5)
        
        # Settings
        settings_frame = ttk.LabelFrame(scrollable_frame, text="General Settings")
        settings_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(settings_frame, text="Max News Items to Analyze:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.max_news_entry = ttk.Entry(settings_frame, width=10)
        self.max_news_entry.insert(0, str(self.config.get("max_news_items", 10)))
        self.max_news_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        # Websites
        site_frame = ttk.LabelFrame(scrollable_frame, text="Target Websites (One per line)")
        site_frame.pack(fill='x', padx=10, pady=5)
        
        self.sites_text = scrolledtext.ScrolledText(site_frame, height=6, width=60)
        self.sites_text.pack(padx=5, pady=5)
        # Use 'or []' to handle None values from config
        self.sites_text.insert('1.0', "\n".join(self.config.get("target_websites") or []))
        
        # Keywords
        kw_frame = ttk.LabelFrame(scrollable_frame, text="Keywords (One per line)")
        kw_frame.pack(fill='x', padx=10, pady=5)
        
        self.kw_text = scrolledtext.ScrolledText(kw_frame, height=8, width=60)
        self.kw_text.pack(padx=5, pady=5)
        # Use 'or []' to handle None values from config
        self.kw_text.insert('1.0', "\n".join(self.config.get("keywords") or []))
        
        # Email
        # email_frame = ttk.LabelFrame(scrollable_frame, text="Email Settings")
        # email_frame.pack(fill='x', padx=10, pady=5)
        
        # ttk.Label(email_frame, text="Recipient Email:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        # self.email_entry = ttk.Entry(email_frame, width=40)
        # # Use 'or ""' to handle None values from config
        # self.email_entry.insert(0, self.config.get("recipient_email") or "")
        # self.email_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Save Button
        save_btn = ttk.Button(scrollable_frame, text="Save Configuration", command=self.save_settings)
        save_btn.pack(pady=10)
        
    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        def _update_log():
            self.log_area.configure(state='normal')
            self.log_area.insert('end', f"[{timestamp}] {message}\n")
            self.log_area.see('end')
            self.log_area.configure(state='disabled')
            
        self.root.after(0, _update_log)
        
    def save_settings(self):
        self.config["firecrawl_api_key"] = self.firecrawl_key.get().strip()
        self.config["deepseek_api_key"] = self.deepseek_key.get().strip()
        try:
            self.config["max_news_items"] = int(self.max_news_entry.get().strip())
        except ValueError:
            self.config["max_news_items"] = 10
            
        self.config["target_websites"] = [line.strip() for line in self.sites_text.get('1.0', 'end').splitlines() if line.strip()]
        self.config["keywords"] = [line.strip() for line in self.kw_text.get('1.0', 'end').splitlines() if line.strip()]
        # self.config["recipient_email"] = self.email_entry.get().strip()
        
        save_config(self.config)
        messagebox.showinfo("Success", "Configuration saved successfully!")
        self.log("Configuration saved.")
        
    # def start_monitoring(self):
    #     if self.is_running:
    #         return
    #         
    #     # Update config from UI first
    #     self.save_settings()
    #     
    #     # Validation
    #     if not self.config.get("firecrawl_api_key") or not self.config.get("deepseek_api_key"):
    #         messagebox.showwarning("Missing Keys", "Please configure API keys first.")
    #         return
    #         
    #     self.is_running = True
    #     self.start_btn.configure(state='disabled')
    #     self.status_lbl.configure(text="Status: Running...")
    #     self.progress.start(10)
    #     self.log("Starting monitoring task...")
    #     
    #     # Run in thread
    #     threading.Thread(target=self.run_task, daemon=True).start()

    # New Implementation for Human-in-the-loop workflow
    def start_monitoring(self):
        if self.is_running:
            return
            
        # Update config from UI first
        self.save_settings()
        
        # Validation
        if not self.config.get("firecrawl_api_key") or not self.config.get("deepseek_api_key"):
            messagebox.showwarning("Missing Keys", "Please configure API keys first.")
            return

        target_func = None
        step_desc = ""

        if self.step == 0:
            target_func = self.run_step_1_scrape
            step_desc = "Step 1: Scrape"
        elif self.step == 1:
            target_func = self.run_step_2_analyze
            step_desc = "Step 2: Analyze"
        elif self.step == 2:
            target_func = self.run_step_3_enrich_report
            step_desc = "Step 3: Enrich & Report"
        else:
            return

        self.is_running = True
        self.start_btn.configure(state='disabled')
        self.status_lbl.configure(text=f"Status: Running {step_desc}...")
        self.progress.start(10)
        self.log(f"Starting {step_desc}...")
        
        # Run in thread
        threading.Thread(target=target_func, daemon=True).start()

    def run_step_1_scrape(self):
        try:
            # Initialize modules
            firecrawl_key = self.config["firecrawl_api_key"]
            deepseek_key = self.config["deepseek_api_key"]
            websites = self.config["target_websites"]
            keywords = self.config["keywords"]
            days_back = self.config.get("search_period_days", 30)
            max_news = self.config.get("max_news_items", 10)
            
            # Instantiate components
            self.scraper = IPOScraper(firecrawl_key)
            self.analyzer = IPOAnalyzer(deepseek_key)
            self.enricher = IPOEnricher(self.scraper, self.analyzer)
            self.reporter = IPOReporter()
            
            # 1. Scrape
            self.log(f"Scanning {len(websites)} websites for the past {days_back} days...")
            news_items = self.scraper.monitor(websites, keywords, days_back)
            self.log(f"Found {len(news_items)} potential news items.")
            
            if not news_items:
                self.log("No news found. Stopping.")
                self.root.after(0, lambda: messagebox.showinfo("Info", "No news found matching your keywords."))
                self.is_running = False
                self.root.after(0, lambda: self.reset_ui(next_step_ready=False))
                return

            # Apply max limit
            if len(news_items) > max_news:
                self.log(f"Limiting analysis to top {max_news} items (out of {len(news_items)}).")
                news_items = news_items[:max_news]

            # Store results
            self.news_items = news_items
            
            # Complete step
            self.is_running = False
            self.root.after(0, lambda: self.reset_ui(next_step_ready=True))
            self.log("Step 1 Completed. Please proceed to Step 2.")
            
        except Exception as e:
            self.handle_error(e)

    def run_step_2_analyze(self):
        try:
            if not self.news_items:
                self.log("No news items to analyze.")
                self.is_running = False
                self.root.after(0, lambda: self.reset_ui(next_step_ready=False))
                return

            analyzed_companies = []
            self.log("Analyzing news with DeepSeek...")
            
            for i, item in enumerate(self.news_items):
                self.log(f"Analyzing item {i+1}/{len(self.news_items)}: {item['title'][:30]}...")
                # Use URL if available, otherwise fallback to source domain
                source_info = item.get('url')
                if not source_info:
                    source_info = item.get('source', 'Unknown Source')
                
                result = self.analyzer.analyze_news(item['content'], source_info, date=item.get('date'), title=item.get('title'))
                if result:
                    # Check if company name is valid
                    if not result.get('company_en'):
                        self.log("  No valid company name identified.")
                        continue

                    # Basic deduplication by company name
                    exists = False
                    for existing in analyzed_companies:
                        # if result.get('company_en') and result['company_en'] == existing.get('company_en'):
                        if result.get('company_en') and existing.get('company_en'):
                            if are_names_similar(result['company_en'], existing['company_en']):
                                exists = True
                                self.log(f"  Duplicate found: {result['company_en']} (similar to {existing['company_en']})")
                                break
                    
                    if not exists:
                        analyzed_companies.append(result)
                        self.log(f"  Identified: {result.get('company_en')}")
                else:
                    self.log("  No IPO info extracted.")
            
            self.log(f"Extracted {len(analyzed_companies)} unique companies.")
            
            if not analyzed_companies:
                self.log("No valid company data extracted.")
                self.is_running = False
                self.root.after(0, lambda: self.reset_ui(next_step_ready=False))
                return

            # Store results
            self.analyzed_companies = analyzed_companies
            
            # Complete step
            self.is_running = False
            self.root.after(0, lambda: self.reset_ui(next_step_ready=True))
            self.log("Step 2 Completed. Please proceed to Step 3.")
            
        except Exception as e:
            self.handle_error(e)

    def run_step_3_enrich_report(self):
        try:
            if not self.analyzed_companies:
                self.log("No companies to enrich.")
                self.is_running = False
                self.root.after(0, lambda: self.reset_ui(next_step_ready=False))
                return

            # 3. Enrich
            self.log("Enriching data with contact info (this may take a while)...")
            enriched_data = self.enricher.enrich_companies(self.analyzed_companies)
            
            # 4. Report
            self.log("Generating Markdown report...")
            md_path = self.reporter.generate_markdown_report(enriched_data)
            
            if md_path:
                self.log(f"Markdown report generated: {md_path}")
                
                # Open the folder containing the PDF
                try:
                    folder_path = os.path.dirname(os.path.abspath(md_path))
                    os.startfile(folder_path)
                    self.log(f"Opened folder: {folder_path}")
                except Exception as e:
                    self.log(f"Failed to open folder: {str(e)}")
            else:
                self.log("Failed to generate Markdown report.")
                self.root.after(0, lambda: messagebox.showerror("Error", "Failed to generate Markdown report."))
            
            self.log("Task completed successfully!")
            self.root.after(0, lambda: messagebox.showinfo("Done", "Monitoring completed. The report folder has been opened."))
            
            # Complete step (Reset to start)
            self.is_running = False
            self.root.after(0, lambda: self.reset_ui(next_step_ready=True)) # Resets to step 0
            
        except Exception as e:
            self.handle_error(e)

    def handle_error(self, e):
        self.log(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        self.is_running = False
        self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
        self.root.after(0, lambda: self.reset_ui(next_step_ready=False))

    def reset_ui(self, next_step_ready=False):
        self.progress.stop()
        self.start_btn.configure(state='normal')
        
        if next_step_ready:
            self.step += 1
            if self.step == 1:
                self.start_btn.configure(text="Start Step 2: Analyze")
                self.status_lbl.configure(text="Status: Ready for Step 2")
            elif self.step == 2:
                self.start_btn.configure(text="Start Step 3: Enrich & Report")
                self.status_lbl.configure(text="Status: Ready for Step 3")
            else:
                # Finished all steps
                self.step = 0
                self.start_btn.configure(text="Start Monitoring (Step 1)")
                self.status_lbl.configure(text="Status: Ready")
                # Clear data
                self.news_items = []
                self.analyzed_companies = []
        else:
            self.status_lbl.configure(text=f"Status: Step {self.step + 1} Stopped")


def main():
    root = tk.Tk()
    app = IPOMonitorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
