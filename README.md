# Combined HK IPO Scrape Agent

This application combines two agents:
1. **HKEX IPO Info Analysis Agent**: Scrapes listed/listing company info from HKEX.
2. **HK IPO News & Rumours Agent**: Scrapes news and rumours about upcoming IPOs.

## Features
- Unified GUI to run both scraping processes.
- Outputs a single Markdown report containing:
  - Table of HKEX Listed/Listing Companies.
  - Table of HK IPO News & Rumours.
- Configurable API keys (Firecrawl, DeepSeek) and search parameters.

## Usage
1. Install dependencies: `pip install -r requirements.txt`
2. Run the application: `python main.py`
3. Enter your API keys.
4. Click "Start Combined Process".
5. The report will be generated in the `output` folder.

## Structure
- `src/hkex_agent`: Logic for HKEX scraping.
- `src/hk_ipo_agent`: Logic for IPO news scraping.
- `src/gui.py`: Main GUI application.
- `main.py`: Entry point.
