# HK IPO Monitor Agent

This application is an automated monitoring pipeline that combines two specialized AI agents to gather, analyze, and report on Hong Kong Initial Public Offerings (IPOs).

## Architecture & Orchestration

The project is orchestrated to run two independent scraping and analysis agents sequentially, merging their outputs into a single, comprehensive Markdown report. 

### Orchestrators
The pipeline can be executed in two different modes, each driven by its own orchestrator:

1. **GUI Orchestrator (`src/gui.py` & `main.py`)**: 
   - Provides a user-friendly interface (`tkinter`) to configure settings, input API keys, and monitor the scraping process via real-time logs.
   - Manages the sequential execution of the agents in background threads to keep the UI responsive.
2. **Headless Orchestrator (`run_pipeline.py`)**:
   - A command-line script designed for automated execution (e.g., via cron jobs or CI/CD pipelines).
   - Reads configuration from `config.json` or environment variables and runs the pipeline synchronously, generating the final report.

### The Agents
1. **HKEX IPO Info Analysis Agent (`src/hkex_agent`)**: 
   - Scrapes official listed and listing company information directly from the HKEX website.
   - Uses Firecrawl to navigate the site and DeepSeek to extract structured data.
2. **HK IPO News & Rumours Agent (`src/hk_ipo_agent`)**: 
   - Scrapes news portals and financial websites (e.g., Yahoo Finance, ET Net) for rumours and news about upcoming IPOs.
   - Uses Firecrawl to extract article content and DeepSeek to analyze the sentiment and summarize the findings.

## Features
- **Unified Pipeline**: Automatically runs both scraping processes and merges the results.
- **Dual Execution Modes**: Choose between a visual GUI or a headless CLI.
- **Comprehensive Reporting**: Outputs a single Markdown report containing:
  - Table of HKEX Listed/Listing Companies.
  - Table of HK IPO News & Rumours.
- **Configurable**: Easily adjust API keys, target websites, search keywords, and limits.

## Prerequisites
- Python 3.8+
- [Firecrawl API Key](https://www.firecrawl.dev/)
- [DeepSeek API Key](https://platform.deepseek.com/)

## Installation

1. Clone the repository and navigate to the project directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. GUI Mode (Interactive)
Best for manual runs and configuring settings visually.

```bash
python main.py
```
1. Switch to the **Configuration** tab to enter your Firecrawl and DeepSeek API keys, target websites, and keywords.
2. Click **Save Configuration** (this updates `config.json`).
3. Switch back to the **Dashboard** and click **Start Combined Process**.
4. The final report will be saved to the `output/` directory.

### 2. Headless Mode (Automated)
Best for scheduled tasks or background execution.

1. Ensure your `config.json` is set up (either by running the GUI once or creating it manually) with your API keys. Alternatively, set the environment variables `FIRECRAWL_API_KEY` and `DEEPSEEK_API_KEY`.
2. Run the pipeline script:
```bash
python run_pipeline.py
```
3. The script will log its progress to the terminal and generate the report in the `output/` directory.

## Project Structure
- `main.py`: Entry point for the GUI application.
- `run_pipeline.py`: Entry point for headless/CLI execution.
- `src/gui.py`: Orchestrator for the GUI, managing agent execution and UI state.
- `src/hkex_agent/`: Core logic, scrapers, and LLM processors for the HKEX official data agent.
- `src/hk_ipo_agent/`: Core logic, scrapers, and LLM processors for the IPO news and rumours agent.
- `config.json`: (Generated) Stores user preferences, target URLs, keywords, and API keys.
- `output/`: (Generated) Directory where the final Markdown reports are saved.
