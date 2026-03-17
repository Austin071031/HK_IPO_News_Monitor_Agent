import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue
import os
import sys
import json

# Add parent directory to path to allow imports if run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper import Scraper
from src.llm_processor import LLMProcessor
from src.data_processor import DataProcessor

class IPOAgentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HKEX IPO Info AI Agent")
        self.root.geometry("800x600")
        
        # Load config
        self.config = self._load_config()
        
        # Variables
        default_fc_key = self.config.get("firecrawl_key", os.getenv("FIRECRAWL_API_KEY", ""))
        default_ds_key = self.config.get("deepseek_key", os.getenv("DEEPSEEK_API_KEY", ""))
        
        self.firecrawl_key = tk.StringVar(value=default_fc_key)
        self.deepseek_key = tk.StringVar(value=default_ds_key)
        self.status_var = tk.StringVar(value="Ready")
        self.is_running = False
        self.log_queue = queue.Queue()
        
        self._setup_ui()
        self._check_queue()

    def _get_config_path(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(root_dir, "config.json")

    def _load_config(self):
        config_path = self._get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
        return {}

    def _save_config(self):
        config_path = self._get_config_path()
        config = {
            "firecrawl_key": self.firecrawl_key.get(),
            "deepseek_key": self.deepseek_key.get()
        }
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def _setup_ui(self):
        # API Key Section
        api_frame = ttk.LabelFrame(self.root, text="API Configuration", padding=10)
        api_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(api_frame, text="Firecrawl API Key:").grid(row=0, column=0, sticky="w")
        ttk.Entry(api_frame, textvariable=self.firecrawl_key, width=50, show="*").grid(row=0, column=1, padx=5)
        
        ttk.Label(api_frame, text="DeepSeek API Key:").grid(row=1, column=0, sticky="w")
        ttk.Entry(api_frame, textvariable=self.deepseek_key, width=50, show="*").grid(row=1, column=1, padx=5)
        
        # Control Section
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        self.start_btn = ttk.Button(control_frame, text="Start Extraction", command=self.start_process)
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="Stop", command=self.stop_process, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        ttk.Label(control_frame, textvariable=self.status_var).pack(side="left", padx=20)
        
        # Progress Bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", mode="indeterminate")
        self.progress.pack(fill="x", padx=10, pady=5)
        
        # Log Area
        log_frame = ttk.LabelFrame(self.root, text="Execution Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=20)
        self.log_area.pack(fill="both", expand=True)

    def _check_queue(self):
        try:
            while True:
                msg_type, msg_content = self.log_queue.get_nowait()
                if msg_type == "log":
                    self.log_area.insert("end", msg_content + "\n")
                    self.log_area.see("end")
                elif msg_type == "error":
                    messagebox.showerror("Error", msg_content)
                    self.reset_ui()
                elif msg_type == "success":
                    messagebox.showinfo("Success", msg_content)
                    self.reset_ui()
                elif msg_type == "status":
                    self.status_var.set(msg_content)
                elif msg_type == "reset":
                    self.reset_ui()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._check_queue)

    def log(self, message):
        self.log_queue.put(("log", message))

    def update_status(self, status):
        self.log_queue.put(("status", status))

    def show_error(self, error):
        self.log_queue.put(("error", error))

    def show_success(self, message):
        self.log_queue.put(("success", message))

    def start_process(self):
        if not self.firecrawl_key.get() or not self.deepseek_key.get():
            messagebox.showerror("Error", "Please provide both API keys.")
            return
            
        # Save keys to config
        self._save_config()
            
        self.is_running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress.start(10)
        self.status_var.set("Running...")
        self.log_area.delete(1.0, "end")
        
        threading.Thread(target=self.run_task, daemon=True).start()

    def stop_process(self):
        self.is_running = False
        self.log("Stopping process... (finishing current step)")
        self.update_status("Stopping...")

    def run_task(self):
        try:
            self.log("Initializing services...")
            # Use local variables for keys to avoid thread access issues with StringVar
            fc_key = self.firecrawl_key.get()
            ds_key = self.deepseek_key.get()
            
            scraper = Scraper(fc_key)
            llm = LLMProcessor(ds_key)
            processor = DataProcessor()
            
            if not self.is_running: 
                self.log_queue.put(("reset", None))
                return

            # Step 1: HKEX EN
            self.log("Scraping HKEX (EN)...")
            en_content = scraper.scrape_hkex_en()
            if not en_content:
                raise Exception("Failed to scrape HKEX (EN)")
            
            self.log("Extracting EN data with LLM...")
            en_data = llm.extract_en_data(en_content)
            self.log(f"Extracted {len(en_data)} records from EN source.")
            
            if not self.is_running: 
                self.log_queue.put(("reset", None))
                return

            # Step 2: HKEX ZH
            self.log("Scraping HKEX (ZH)...")
            zh_content = scraper.scrape_hkex_zh()
            if not zh_content:
                raise Exception("Failed to scrape HKEX (ZH)")
            
            self.log("Extracting ZH data with LLM...")
            zh_data = llm.extract_zh_data(zh_content)
            self.log(f"Extracted {len(zh_data)} records from ZH source.")
            
            if not self.is_running: 
                self.log_queue.put(("reset", None))
                return

            # Step 3: Etnet & Search
            etnet_data_map = {}
            
            # Let's use the stock codes from EN data
            for i, item in enumerate(en_data):
                if not self.is_running: break
                stock_code = item.get("Stock Code")
                company_name = item.get("Stock Name", "")

                if stock_code and stock_code != "N/A":
                    # 3.1 Etnet
                    self.log(f"[{i+1}/{len(en_data)}] Scraping Etnet for Stock Code: {stock_code}...")
                    etnet_info = scraper.scrape_etnet(stock_code)
                    etnet_data_map[stock_code] = etnet_info
                    
                    # 3.2 Firecrawl Search - Date & Status
                    self.log(f"[{i+1}/{len(en_data)}] Searching IPO Date/Status for: {company_name} ({stock_code})...")
                    date_status_content = scraper.search_ipo_date_status(stock_code, company_name)
                    
                    if date_status_content:
                        self.log(f"Extracting IPO Date/Status for {stock_code}...")
                        date_status_info = llm.extract_ipo_date_status(date_status_content, stock_code, company_name)
                        if date_status_info:
                            for key in ["Listing Date", "Status"]:
                                if date_status_info.get(key) and date_status_info.get(key) != "N/A":
                                    item[key] = date_status_info.get(key)

                    # 3.3 Firecrawl Search - Origin & Sector
                    self.log(f"[{i+1}/{len(en_data)}] Searching IPO Origin/Sector for: {company_name} ({stock_code})...")
                    origin_sector_content = scraper.search_ipo_origin_sector(stock_code, company_name)
                    
                    if origin_sector_content:
                        self.log(f"Extracting IPO Origin/Sector for {stock_code}...")
                        origin_sector_info = llm.extract_ipo_origin_sector(origin_sector_content, stock_code, company_name)
                        if origin_sector_info:
                            for key in ["Origin", "Sector"]:
                                if origin_sector_info.get(key) and origin_sector_info.get(key) != "N/A":
                                    item[key] = origin_sector_info.get(key)
            
            if not self.is_running: 
                self.log_queue.put(("reset", None))
                return

            # Step 4: Consolidate
            self.log("Consolidating data...")
            consolidated_data = processor.consolidate_data(en_data, zh_data, etnet_data_map)
            
            # Step 5: Export
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
            filepath = processor.export_markdown(output_dir)
            self.log(f"Report saved to: {filepath}")
            
            self.show_success(f"Extraction completed!\nSaved to: {filepath}")

        except Exception as e:
            self.log(f"Error: {str(e)}")
            self.show_error(str(e))

    def reset_ui(self):
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.progress.stop()
        self.status_var.set("Ready")

if __name__ == "__main__":
    root = tk.Tk()
    app = IPOAgentApp(root)
    root.mainloop()
