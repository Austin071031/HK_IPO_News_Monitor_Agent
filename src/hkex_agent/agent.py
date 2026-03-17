import os
import sys
import queue
import threading
from .scraper import Scraper
from .llm_processor import LLMProcessor
from .data_processor import DataProcessor

class HKEXAgent:
    def __init__(self, firecrawl_key, deepseek_key, logger=None):
        self.firecrawl_key = firecrawl_key
        self.deepseek_key = deepseek_key
        self.logger = logger
        self.scraper = Scraper(self.firecrawl_key)
        self.llm = LLMProcessor(self.deepseek_key)
        self.processor = DataProcessor()
        self.is_running = False

    def log(self, message):
        if self.logger:
            self.logger(message)
        else:
            print(f"[HKEX Agent] {message}")

    def run(self):
        self.is_running = True
        try:
            self.log("Initializing services...")
            
            # Step 1: HKEX EN
            self.log("Scraping HKEX (EN)...")
            en_content = self.scraper.scrape_hkex_en()
            if not en_content:
                raise Exception("Failed to scrape HKEX (EN)")
            
            self.log("Extracting EN data with LLM...")
            en_data = self.llm.extract_en_data(en_content)
            self.log(f"Extracted {len(en_data)} records from EN source.")
            
            if not self.is_running: return None

            # Step 2: HKEX ZH
            self.log("Scraping HKEX (ZH)...")
            zh_content = self.scraper.scrape_hkex_zh()
            if not zh_content:
                raise Exception("Failed to scrape HKEX (ZH)")
            
            self.log("Extracting ZH data with LLM...")
            zh_data = self.llm.extract_zh_data(zh_content)
            self.log(f"Extracted {len(zh_data)} records from ZH source.")
            
            if not self.is_running: return None

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
                    etnet_info = self.scraper.scrape_etnet(stock_code)
                    etnet_data_map[stock_code] = etnet_info
                    
                    # 3.2 Firecrawl Search - Date & Status
                    self.log(f"[{i+1}/{len(en_data)}] Searching IPO Date/Status for: {company_name} ({stock_code})...")
                    date_status_content = self.scraper.search_ipo_date_status(stock_code, company_name)
                    
                    if date_status_content:
                        self.log(f"Extracting IPO Date/Status for {stock_code}...")
                        date_status_info = self.llm.extract_ipo_date_status(date_status_content, stock_code, company_name)
                        if date_status_info:
                            for key in ["Listing Date", "Status"]:
                                if date_status_info.get(key) and date_status_info.get(key) != "N/A":
                                    item[key] = date_status_info.get(key)

                    # 3.3 Firecrawl Search - Origin & Sector
                    self.log(f"[{i+1}/{len(en_data)}] Searching IPO Origin/Sector for: {company_name} ({stock_code})...")
                    origin_sector_content = self.scraper.search_ipo_origin_sector(stock_code, company_name)
                    
                    if origin_sector_content:
                        self.log(f"Extracting IPO Origin/Sector for {stock_code}...")
                        origin_sector_info = self.llm.extract_ipo_origin_sector(origin_sector_content, stock_code, company_name)
                        if origin_sector_info:
                            for key in ["Origin", "Sector"]:
                                if origin_sector_info.get(key) and origin_sector_info.get(key) != "N/A":
                                    item[key] = origin_sector_info.get(key)
            
            if not self.is_running: return None

            # Step 4: Consolidate
            self.log("Consolidating data...")
            consolidated_data = self.processor.consolidate_data(en_data, zh_data, etnet_data_map)
            
            # Generate markdown string using the processor's method to ensure original format
            markdown_table = self.processor.generate_markdown_string()
            
            self.log(f"HKEX extraction completed! Found {len(consolidated_data)} companies.")
            return markdown_table

        except Exception as e:
            self.log(f"Error in HKEX Agent: {str(e)}")
            raise e
        finally:
            self.is_running = False

    def stop(self):
        self.is_running = False
