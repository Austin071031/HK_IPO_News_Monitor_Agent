import os
from src.hkex_agent.llm_processor import LLMProcessor
from src.hkex_agent.scraper import Scraper

def test_extraction():
    firecrawl_key = os.environ.get("FIRECRAWL_API_KEY")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    
    # We will test extracting data for "Sigenergy Technology Co., Ltd." (6656)
    stock_code = "6656"
    company_name = "Sigenergy Technology Co., Ltd."
    
    scraper = Scraper(firecrawl_key)
    llm = LLMProcessor(deepseek_key)
    
    print(f"Testing Origin/Sector extraction for {company_name} ({stock_code})...")
    origin_sector_content = scraper.search_ipo_origin_sector(stock_code, company_name)
    if origin_sector_content:
        origin_sector_info = llm.extract_ipo_origin_sector(origin_sector_content, stock_code, company_name)
        print("Result:", origin_sector_info)
    else:
        print("Failed to get search content.")
        
    print(f"Testing Date/Status extraction for {company_name} ({stock_code})...")
    date_status_content = scraper.search_ipo_date_status(stock_code, company_name)
    if date_status_content:
        date_status_info = llm.extract_ipo_date_status(date_status_content, stock_code, company_name)
        print("Result:", date_status_info)
    else:
        print("Failed to get search content.")

if __name__ == "__main__":
    test_extraction()
