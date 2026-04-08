import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import json
import os
import datetime
import pandas as pd
from .hkex_agent.agent import HKEXAgent
from .hk_ipo_agent.agent import HKIPOAgent

# Try to import PDF conversion module, but handle if dependencies are missing
try:
    # Try enhanced converter first (has fallback to ReportLab)
    from .hk_ipo_agent.convert_md_to_pdf_enhanced import convert_md_to_pdf, convert_md_to_pdf_safe
    PDF_CONVERSION_AVAILABLE = True
    print("PDF conversion available (enhanced with fallback)")
except ImportError as e:
    print(f"PDF conversion dependencies not available: {e}")
    print("Trying ReportLab-only fallback...")
    try:
        from .hk_ipo_agent.convert_md_to_pdf_reportlab import convert_md_to_pdf_reportlab as convert_md_to_pdf
        PDF_CONVERSION_AVAILABLE = True
        print("PDF conversion available (ReportLab only)")
    except ImportError:
        print("No PDF conversion method available")
        PDF_CONVERSION_AVAILABLE = False
        convert_md_to_pdf = None

class CombinedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Combined HK IPO Scraper Agent")
        self.root.geometry("900x700")
        
        self.log_queue = queue.Queue()
        self.is_running = False
        self.hkex_agent = None
        self.hk_ipo_agent = None
        
        self.config = self.load_config()
        
        self.create_widgets()
        self.check_queue()

    def load_config(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.log(f"Error loading config: {e}")
        return {}

    def save_config(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self.log("Configuration saved.")
        except Exception as e:
            self.log(f"Error saving config: {e}")

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
        # Control Frame
        control_frame = ttk.LabelFrame(self.dashboard_frame, text="Control Panel")
        control_frame.pack(fill='x', padx=10, pady=5)
        
        self.start_btn = ttk.Button(control_frame, text="Start Combined Process", command=self.start_process)
        self.start_btn.pack(side='left', padx=10, pady=10)
        
        self.stop_btn = ttk.Button(control_frame, text="Stop", command=self.stop_process, state='disabled')
        self.stop_btn.pack(side='left', padx=10, pady=10)
        
        self.status_lbl = ttk.Label(control_frame, text="Status: Ready")
        self.status_lbl.pack(side='left', padx=20, pady=10)
        
        # Log Area
        log_frame = ttk.LabelFrame(self.dashboard_frame, text="Logs")
        log_frame.pack(expand=True, fill='both', padx=10, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, state='disabled')
        self.log_area.pack(expand=True, fill='both', padx=5, pady=5)

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
        self.firecrawl_key = ttk.Entry(api_frame, width=50, show="*")
        self.firecrawl_key.insert(0, self.config.get("firecrawl_api_key") or "")
        self.firecrawl_key.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(api_frame, text="DeepSeek API Key:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.deepseek_key = ttk.Entry(api_frame, width=50, show="*")
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
        self.sites_text.insert('1.0', "\n".join(self.config.get("target_websites") or []))
        
        # Keywords
        kw_frame = ttk.LabelFrame(scrollable_frame, text="Keywords (One per line)")
        kw_frame.pack(fill='x', padx=10, pady=5)
        
        self.kw_text = scrolledtext.ScrolledText(kw_frame, height=8, width=60)
        self.kw_text.pack(padx=5, pady=5)
        self.kw_text.insert('1.0', "\n".join(self.config.get("keywords") or []))
        
        # Save Button
        save_btn = ttk.Button(scrollable_frame, text="Save Configuration", command=self.save_settings)
        save_btn.pack(pady=10)

    def save_settings(self, show_msg=True):
        self.config["firecrawl_api_key"] = self.firecrawl_key.get().strip()
        self.config["deepseek_api_key"] = self.deepseek_key.get().strip()
        try:
            self.config["max_news_items"] = int(self.max_news_entry.get().strip())
        except ValueError:
            self.config["max_news_items"] = 10
            
        self.config["target_websites"] = [line.strip() for line in self.sites_text.get('1.0', 'end').splitlines() if line.strip()]
        self.config["keywords"] = [line.strip() for line in self.kw_text.get('1.0', 'end').splitlines() if line.strip()]
        
        self.save_config()
        if show_msg:
            messagebox.showinfo("Success", "Configuration saved successfully!")

    def log(self, message):
        self.log_queue.put(message)

    def check_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                self.log_area.configure(state='normal')
                self.log_area.insert('end', f"[{timestamp}] {msg}\n")
                self.log_area.see('end')
                self.log_area.configure(state='disabled')
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)

    def start_process(self):
        self.save_settings(show_msg=False)

        if not self.config.get("firecrawl_api_key") or not self.config.get("deepseek_api_key"):
            messagebox.showwarning("Missing Keys", "Please configure API keys in the Configuration tab.")
            return
            
        self.is_running = True
        self.start_btn.configure(state='disabled')
        self.stop_btn.configure(state='normal')
        self.status_lbl.configure(text="Status: Running...")
        
        threading.Thread(target=self.run_task, daemon=True).start()

    def stop_process(self):
        self.is_running = False
        if self.hkex_agent:
            self.hkex_agent.stop()
        if self.hk_ipo_agent:
            self.hk_ipo_agent.stop()
        self.log("Stopping process...")
        self.status_lbl.configure(text="Status: Stopping...")

    def run_task(self):
        try:
            # 1. Run HKEX Agent
            self.log("--- Starting Part 1: HKEX Agent ---")
            self.hkex_agent = HKEXAgent(
                self.config["firecrawl_api_key"],
                self.config["deepseek_api_key"],
                logger=self.log
            )
            hkex_data = self.hkex_agent.run()
            
            if not self.is_running: 
                self.reset_ui()
                return

            if not hkex_data:
                self.log("Warning: No data from HKEX Agent.")
                hkex_data = []

            # 2. Run HK IPO Agent
            self.log("--- Starting Part 2: HK IPO Agent ---")
            
            # Use config from self.config which is now up-to-date
            agent2_config = self.config.copy()
            
            # Defaults if empty lists (optional, but good for robustness)
            if not agent2_config.get("target_websites"):
                agent2_config["target_websites"] = [
                    "https://hk.finance.yahoo.com/topic/%E6%96%B0%E8%82%A1IPO/",
                    "https://www.etnet.com.hk/www/tc/stocks/ipo-news"
                ]
            if not agent2_config.get("keywords"):
                agent2_config["keywords"] = ["HK IPO", "New Listing"]

            self.hk_ipo_agent = HKIPOAgent(
                self.config["firecrawl_api_key"],
                self.config["deepseek_api_key"],
                config=agent2_config,
                logger=self.log
            )
            hk_ipo_data = self.hk_ipo_agent.run()
            
            if not self.is_running: 
                self.reset_ui()
                return

            if not hk_ipo_data:
                self.log("Warning: No data from HK IPO Agent.")
                hk_ipo_data = []

            # 3. Combine and Save
            self.log("--- Generating Combined Report ---")
            self.generate_report(hkex_data, hk_ipo_data)
            
            self.log("Process Completed Successfully!")
            messagebox.showinfo("Success", "Process Completed! Report generated.")

        except Exception as e:
            self.log(f"Error: {e}")
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            self.reset_ui()

    def reset_ui(self):
        self.is_running = False
        self.start_btn.configure(state='normal')
        self.stop_btn.configure(state='disabled')
        self.status_lbl.configure(text="Status: Ready")

    def generate_report(self, hkex_data, hk_ipo_data):
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"Combined_HK_IPO_Report_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Combined HK IPO Report\n")
            f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Table 1: HKEX Listed Companies
            f.write("## 1. HKEX Listed/Listing Companies\n\n")
            if hkex_data and isinstance(hkex_data, str):
                 f.write(hkex_data)
            elif hkex_data and isinstance(hkex_data, list):
                # Fallback if it is a list
                df1 = pd.DataFrame(hkex_data)
                f.write(df1.to_markdown(index=False))
            else:
                f.write("No data found.\n")
            f.write("\n\n")
            
            # Table 2: HK IPO News & Rumours
            f.write("## 2. HK IPO News & Rumours\n\n")
            if hk_ipo_data and isinstance(hk_ipo_data, str):
                f.write(hk_ipo_data)
            elif hk_ipo_data and isinstance(hk_ipo_data, list):
                 # Fallback if it is a list
                table_data = []
                for item in hk_ipo_data:
                    table_data.append({
                        "Company (EN)": item.get('company_en', 'N/A'),
                        "Company (ZH)": item.get('company_zh', 'N/A'),
                        "Status": item.get('status', 'N/A'),
                        "Date": item.get('date', 'N/A'),
                        "Sector": item.get('sector', 'N/A'),
                        "Notes": item.get('notes', 'N/A'),
                        "Source": item.get('source', 'N/A')
                    })
                df2 = pd.DataFrame(table_data)
                f.write(df2.to_markdown(index=False))
            else:
                f.write("No data found.\n")
            f.write("\n")
            
        self.log(f"Report saved to: {filepath}")
        
        # Convert Markdown to PDF if conversion module is available
        if PDF_CONVERSION_AVAILABLE and convert_md_to_pdf:
            try:
                pdf_filepath = filepath.replace('.md', '.pdf')
                self.log(f"Converting markdown to PDF: {pdf_filepath}")
                convert_md_to_pdf(filepath, pdf_filepath)
                self.log(f"PDF report generated: {pdf_filepath}")
            except Exception as e:
                self.log(f"PDF conversion failed: {e}")
                self.log("Note: Install dependencies with: pip install markdown-it-py playwright")
                self.log("Then run: playwright install chromium")
        else:
            self.log("PDF conversion not available. Install dependencies to enable PDF output.")
            self.log("Required: pip install markdown-it-py playwright && playwright install chromium")
        
        try:
            os.startfile(output_dir)
        except:
            pass
