import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

DEFAULT_CONFIG = {
    "firecrawl_api_key": os.getenv("FIRECRAWL_API_KEY"),
    "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY"),
    "target_websites": [
        "https://hk.finance.yahoo.com/topic/%E6%96%B0%E8%82%A1IPO/",
        "https://www.etnet.com.hk/www/tc/stocks/ipo-news",
        "https://www.21jingji.com/",
        "https://finance.eastmoney.com/",
        "https://finance.sina.com.cn/stock/hkstock/",
        "http://www.aastocks.com/en/stocks/market/ipo/iponews.aspx",
        "https://stcn.com/article/list/gmg.html"
    ],
    "keywords": [
        "A + H Dual Listing",
        "证监会",
        "A1 Filing",
        "Hong Kong IPO filing",
        "Application Proof",
        "Filing with CSRC",
        "Spin-off in Hong Kong",
        "IPO hearing",
        "HK IPO Market Rumors",
        "二次上市",
        "先A后H",
        "中概股回归",
        "通过聆讯",
        "拟赴港上市",
        "拆分上市",
        "境外上市备案",
        "港交所 递表",
        "H股上市"
    ],
    "search_period_days": 30,
    "max_news_items": 10,
    "recipient_email": ""
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def get_config():
    return load_config()
