import os
import time
import requests
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp

class Scraper:
    def __init__(self, firecrawl_api_key=None):
        self.firecrawl_api_key = firecrawl_api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.firecrawl_api_key:
            raise ValueError("Firecrawl API Key is required.")
        self.firecrawl_app = FirecrawlApp(api_key=self.firecrawl_api_key)
        self._aastocks_cache = None

    def _get_aastocks_content(self):
        """
        Helper to scrape AAStocks IPO summary page with caching.
        """
        if self._aastocks_cache:
            return self._aastocks_cache
            
        url = "http://www.aastocks.com/sc/stocks/market/ipo/upcomingipo/company-summary"
        try:
            # scrape_result = self.firecrawl_app.v1.scrape_url(url, formats=['markdown'])
            scrape_result = self.firecrawl_app.v1.scrape_url(url, formats=['markdown'])
            
            content = ""
            if hasattr(scrape_result, 'markdown'):
                content = scrape_result.markdown or ''
            else:
                content = scrape_result.get('markdown', '') if isinstance(scrape_result, dict) else ''
            
            if content:
                self._aastocks_cache = content
                return content
        except Exception as e:
            print(f"Error scraping AAStocks: {e}")
        
        return ""

    def scrape_hkex_en(self):
        url = "https://www2.hkexnews.hk/New-Listings/New-Listing-Information/Main-Board?sc_lang=en"
        try:
            # Using scrape_url for single page content
            # scrape_result = self.firecrawl_app.v1.scrape_url(url, formats=['markdown'])
            scrape_result = self.firecrawl_app.v1.scrape_url(url, formats=['markdown'])
            if hasattr(scrape_result, 'markdown'):
                return scrape_result.markdown or ''
            else:
                return scrape_result.get('markdown', '') if isinstance(scrape_result, dict) else ''
        except Exception as e:
            print(f"Error scraping HKEX EN: {e}")
            return None

    def scrape_hkex_zh(self):
        url = "https://sc.hkexnews.hk/TuniS/www2.hkexnews.hk/new-listings/new-listing-information/main-board?sc_lang=zh-cn"
        try:
            # scrape_result = self.firecrawl_app.v1.scrape_url(url, formats=['markdown'])
            scrape_result = self.firecrawl_app.v1.scrape_url(url, formats=['markdown'])
            if hasattr(scrape_result, 'markdown'):
                return scrape_result.markdown or ''
            else:
                return scrape_result.get('markdown', '') if isinstance(scrape_result, dict) else ''
        except Exception as e:
            print(f"Error scraping HKEX ZH: {e}")
            return None

    def scrape_etnet(self, stock_code):
        url = f'https://www.etnet.com.hk/www/tc/stocks/realtime/quote_ci_brief.php?code={stock_code}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for attempt in range(3):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                response.encoding = 'utf-8'
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                def get_value_by_label(soup, label):
                    tds = soup.find_all('td')
                    for i, td in enumerate(tds):
                        text = td.get_text(strip=True)
                        if label in text and len(text) < 20:
                            if i + 1 < len(tds):
                                return tds[i+1].get_text(strip=True)
                    return "N/A"

                address = get_value_by_label(soup, '公司地址')
                phone = get_value_by_label(soup, '電話號碼')
                website = get_value_by_label(soup, '集團網址')
                email = get_value_by_label(soup, '電郵地址')

                return {
                    "address": address,
                    "phone": phone,
                    "website": website,
                    "email": email
                }
            except Exception as e:
                print(f"Attempt {attempt+1} failed for stock {stock_code}: {e}")
                time.sleep(2)
        
        return {
            "address": "N/A",
            "phone": "N/A",
            "website": "N/A",
            "email": "N/A"
        }

    def search_ipo_date_status(self, stock_code, company_name):
        """
        Search for IPO listed date and status using Firecrawl, focusing on specific websites.
        Returns the search results in markdown format.
        """
        # New implementation uses scrape on specific AAStocks URL
        return self._get_aastocks_content()

    def search_ipo_origin_sector(self, stock_code, company_name):
        """
        Search for IPO origin and sector using Firecrawl, focusing on specific websites.
        Returns the search results in markdown format.
        """
        # New implementation uses scrape on specific AAStocks URL
        return self._get_aastocks_content()
