import sys
import os
import json
import datetime
import pandas as pd

# Ensure the current directory is in sys.path so we can import src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.hkex_agent.agent import HKEXAgent
from src.hk_ipo_agent.agent import HKIPOAgent

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
    return {}

def log(message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def generate_report(hkex_data, hk_ipo_data):
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
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
        
    log(f"Report saved to: {filepath}")
    return filepath

def main():
    log("Starting Headless HK IPO Monitor Pipeline...")
    config = load_config()

    firecrawl_key = config.get("firecrawl_api_key") or os.environ.get("FIRECRAWL_API_KEY")
    deepseek_key = config.get("deepseek_api_key") or os.environ.get("DEEPSEEK_API_KEY")

    if not firecrawl_key or not deepseek_key:
        log("Error: Missing Firecrawl or DeepSeek API keys in config.json or environment variables.")
        sys.exit(1)

    try:
        # 1. Run HKEX Agent
        log("--- Starting Part 1: HKEX Agent ---")
        hkex_agent = HKEXAgent(
            firecrawl_key,
            deepseek_key,
            logger=log
        )
        hkex_data = hkex_agent.run()
        
        if not hkex_data:
            log("Warning: No data from HKEX Agent.")
            hkex_data = []

        # 2. Run HK IPO Agent
        log("--- Starting Part 2: HK IPO Agent ---")
        agent2_config = config.copy()
        
        if not agent2_config.get("target_websites"):
            agent2_config["target_websites"] = [
                "https://hk.finance.yahoo.com/topic/%E6%96%B0%E8%82%A1IPO/",
                "https://www.etnet.com.hk/www/tc/stocks/ipo-news"
            ]
        if not agent2_config.get("keywords"):
            agent2_config["keywords"] = ["HK IPO", "New Listing"]

        hk_ipo_agent = HKIPOAgent(
            firecrawl_key,
            deepseek_key,
            config=agent2_config,
            logger=log
        )
        hk_ipo_data = hk_ipo_agent.run()
        
        if not hk_ipo_data:
            log("Warning: No data from HK IPO Agent.")
            hk_ipo_data = []

        # 3. Combine and Save
        log("--- Generating Combined Report ---")
        filepath = generate_report(hkex_data, hk_ipo_data)
        
        log(f"Process Completed Successfully! Final report at: {filepath}")

    except Exception as e:
        log(f"Fatal Error during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
