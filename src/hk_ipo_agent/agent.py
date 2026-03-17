import os
import sys
import threading
import time
from .scraper import IPOScraper
from .analyzer import IPOAnalyzer
from .enricher import IPOEnricher
from .reporter import IPOReporter
from .utils import are_names_similar

class HKIPOAgent:
    def __init__(self, firecrawl_key, deepseek_key, config=None, logger=None):
        self.firecrawl_key = firecrawl_key
        self.deepseek_key = deepseek_key
        self.config = config or {}
        self.logger = logger
        self.is_running = False
        
        self.scraper = IPOScraper(self.firecrawl_key)
        self.analyzer = IPOAnalyzer(self.deepseek_key)
        self.enricher = IPOEnricher(self.scraper, self.analyzer)
        self.reporter = IPOReporter()
        
        self.news_items = []
        self.analyzed_companies = []
        self.enriched_data = []

    def log(self, message):
        if self.logger:
            self.logger(message)
        else:
            print(f"[HK IPO Agent] {message}")

    def run(self):
        self.is_running = True
        try:
            # Step 1: Scrape
            websites = self.config.get("target_websites", [])
            keywords = self.config.get("keywords", [])
            days_back = self.config.get("search_period_days", 30)
            max_news = self.config.get("max_news_items", 10)

            self.log(f"Scanning {len(websites)} websites for the past {days_back} days...")
            news_items = self.scraper.monitor(websites, keywords, days_back)
            self.log(f"Found {len(news_items)} potential news items.")

            if not news_items:
                self.log("No news found.")
                return []

            if len(news_items) > max_news:
                self.log(f"Limiting analysis to top {max_news} items.")
                news_items = news_items[:max_news]
            
            self.news_items = news_items
            
            if not self.is_running: return []

            # Step 2: Analyze
            analyzed_companies = []
            self.log("Analyzing news with DeepSeek...")
            
            for i, item in enumerate(self.news_items):
                if not self.is_running: break
                self.log(f"Analyzing item {i+1}/{len(self.news_items)}: {item.get('title', '')[:30]}...")
                
                source_info = item.get('url') or item.get('source', 'Unknown Source')
                
                result = self.analyzer.analyze_news(
                    item.get('content', ''), 
                    source_info, 
                    date=item.get('date'), 
                    title=item.get('title')
                )
                
                if result:
                    if not result.get('company_en'):
                        continue

                    # Deduplication
                    exists = False
                    for existing in analyzed_companies:
                        if result.get('company_en') and existing.get('company_en'):
                            if are_names_similar(result['company_en'], existing['company_en']):
                                exists = True
                                self.log(f"  Duplicate found: {result['company_en']}")
                                break
                    
                    if not exists:
                        analyzed_companies.append(result)
                        self.log(f"  Identified: {result.get('company_en')}")
            
            self.analyzed_companies = analyzed_companies
            self.log(f"Extracted {len(analyzed_companies)} unique companies.")
            
            if not analyzed_companies:
                self.log("No valid company data extracted.")
                return []

            if not self.is_running: return []

            # Step 3: Enrich
            self.log("Enriching data with contact info...")
            enriched_data = self.enricher.enrich_companies(self.analyzed_companies)
            self.enriched_data = enriched_data
            
            self.log("HK IPO extraction completed!")
            
            # Generate markdown string using reporter
            markdown_table = self.reporter.generate_markdown_string(enriched_data)
            return markdown_table

        except Exception as e:
            self.log(f"Error in HK IPO Agent: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e
        finally:
            self.is_running = False

    def stop(self):
        self.is_running = False
