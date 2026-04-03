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
        "considering HongKong IPO",
        "plans HongKong IPO",
        "seeking HongKong IPO",
        "HongKong IPO hearing",
        "A1 Filing",
        "HongKong IPO filing",
        "Application Proof",
        "Filing with CSRC",
        "Spin-off in HongKong",
        "HongKong IPO Market Rumors",
        "港股传闻",
        "港股IPO传闻",
        "通过聆讯 港股",
        "拟赴港上市",
        "拟赴港IPO",
        "拟港股上市",
        "拟拆分上市 港股",
        "拟分拆上市 港股",
        "港交所 递表"
    ],
    "search_period_days": 30,
    "max_news_items": 15,
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
