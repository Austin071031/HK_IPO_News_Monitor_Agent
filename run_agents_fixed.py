#!/usr/bin/env python3
"""
Fixed script to run the HK IPO Monitor Agent with enhanced reporter.
This version uses deduplication and clean formatting.
"""

import os
import sys
import json
import datetime
import traceback
from pathlib import Path

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath('.')))

def log_message(message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    # Remove Unicode symbols for Windows compatibility
    cleaned_message = message.replace('✅', '[OK]').replace('❌', '[ERROR]').replace('⚠️', '[WARNING]')
    print(f"[{timestamp}] {cleaned_message}")

def deduplicate_data(data):
    """
    Basic deduplication for HKEX data if needed.
    """
    if not data or not isinstance(data, list):
        return data
    
    # For HKEX data, deduplicate by stock code
    seen_codes = set()
    dedup_data = []
    
    for item in data:
        if isinstance(item, dict):
            stock_code = item.get('Stock Code', '')
            if stock_code and stock_code not in seen_codes:
                seen_codes.add(stock_code)
                dedup_data.append(item)
        else:
            dedup_data.append(item)
    
    return dedup_data

def run_agents_fixed():
    """Run both agents and generate cleaned report."""
    try:
        # Load config
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        log_message("Configuration loaded")
        
        # Check API keys
        if not config.get("firecrawl_api_key") or not config.get("deepseek_api_key"):
            raise ValueError("Missing API keys in config.json")
        
        # Import agents
        from src.hkex_agent.agent import HKEXAgent
        from src.hk_ipo_agent.agent import HKIPOAgent
        
        # Run HKEX Agent
        log_message("--- Starting Part 1: HKEX Agent ---")
        hkex_agent = HKEXAgent(
            config["firecrawl_api_key"],
            config["deepseek_api_key"],
            logger=log_message
        )
        hkex_data = hkex_agent.run()
        
        if not hkex_data:
            log_message("Warning: No data from HKEX Agent.")
            hkex_data = []
        
        # Run HK IPO Agent
        log_message("--- Starting Part 2: HK IPO Agent ---")
        
        # Use config
        agent2_config = config.copy()
        
        # Defaults if empty lists
        if not agent2_config.get("target_websites"):
            agent2_config["target_websites"] = [
                "https://hk.finance.yahoo.com/topic/%E6%96%B0%E8%82%A1IPO/",
                "https://www.etnet.com.hk/www/tc/stocks/ipo-news"
            ]
        if not agent2_config.get("keywords"):
            agent2_config["keywords"] = ["HK IPO", "New Listing"]
        
        hk_ipo_agent = HKIPOAgent(
            config["firecrawl_api_key"],
            config["deepseek_api_key"],
            config=agent2_config,
            logger=log_message
        )
        hk_ipo_data = hk_ipo_agent.run()
        
        if not hk_ipo_data:
            log_message("Warning: No data from HK IPO Agent.")
            hk_ipo_data = []
        
        # Generate cleaned combined report
        log_message("--- Generating Cleaned Combined Report ---")
        
        # Create output directory
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        
        # Try to use enhanced reporter if available
        try:
            from src.hk_ipo_agent.reporter_enhanced import EnhancedIPOReporter
            enhanced_reporter = EnhancedIPOReporter()
            
            # Generate cleaned IPO data table
            log_message("Using enhanced reporter with deduplication...")
            
            # Create markdown filename
            md_filename = f"Cleaned_HK_IPO_Report_{timestamp}.md"
            md_filepath = os.path.join(output_dir, md_filename)
            
            with open(md_filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Cleaned HK IPO Report\n")
                f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("*Note: Enhanced deduplication and cleaning applied*\n\n")
                
                # Table 1: HKEX Listed Companies
                f.write("## 1. HKEX Listed/Listing Companies\n\n")
                if hkex_data and isinstance(hkex_data, str):
                    f.write(hkex_data)
                elif hkex_data and isinstance(hkex_data, list):
                    # Apply basic deduplication to HKEX data
                    dedup_hkex = deduplicate_data(hkex_data)
                    import pandas as pd
                    df1 = pd.DataFrame(dedup_hkex)
                    f.write(df1.to_markdown(index=False))
                else:
                    f.write("No data found.\n")
                f.write("\n\n")
                
                # Table 2: HK IPO News & Rumours (using enhanced reporter)
                f.write("## 2. HK IPO News & Rumours\n\n")
                
                if hk_ipo_data:
                    # Generate cleaned table
                    cleaned_table = enhanced_reporter.generate_markdown_string(hk_ipo_data)
                    f.write(cleaned_table)
                else:
                    f.write("No data found.\n")
                
                # Add summary
                f.write("\n\n")
                f.write("## Summary\n\n")
                if hk_ipo_data:
                    dedup_count = len(enhanced_reporter.deduplicate_data(hk_ipo_data))
                    f.write(f"- Total IPO news items (deduplicated): {dedup_count}\n")
                    f.write(f"- Date range: {enhanced_reporter._get_date_range(hk_ipo_data)}\n")
                    f.write(f"- Status distribution: {enhanced_reporter._get_status_distribution(hk_ipo_data)}\n")
                
            log_message(f"Cleaned report saved to: {md_filepath}")
            
        except ImportError as e:
            log_message(f"Enhanced reporter not available: {e}")
            log_message("Falling back to original reporter...")
            
            # Fallback to original reporter
            from src.hk_ipo_agent.reporter import IPOReporter
            original_reporter = IPOReporter()
            
            # Create markdown filename
            md_filename = f"Combined_HK_IPO_Report_{timestamp}.md"
            md_filepath = os.path.join(output_dir, md_filename)
            
            with open(md_filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Combined HK IPO Report\n")
                f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Table 1: HKEX Listed Companies
                f.write("## 1. HKEX Listed/Listing Companies\n\n")
                if hkex_data and isinstance(hkex_data, str):
                    f.write(hkex_data)
                elif hkex_data and isinstance(hkex_data, list):
                    import pandas as pd
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
                    # Use original reporter for consistency
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
                    import pandas as pd
                    df2 = pd.DataFrame(table_data)
                    f.write(df2.to_markdown(index=False))
                else:
                    f.write("No data found.\n")
            
            log_message(f"Fallback report saved to: {md_filepath}")
        
        # Convert Markdown to PDF using enhanced converter with fallback
        try:
            log_message("Attempting PDF conversion with enhanced converter...")
            
            # Try enhanced converter first (supports fallback to ReportLab)
            try:
                from src.hk_ipo_agent.convert_md_to_pdf_enhanced import convert_md_to_pdf_safe
                pdf_filepath = convert_md_to_pdf_safe(md_filepath)
                
                if pdf_filepath and os.path.exists(pdf_filepath):
                    log_message(f"[OK] PDF report generated: {pdf_filepath}")
                    return pdf_filepath
                else:
                    log_message("[WARNING] PDF conversion returned no file path")
                    
            except ImportError as e:
                log_message(f"Enhanced converter not available: {e}")
                # Fallback to ReportLab directly
                try:
                    from src.hk_ipo_agent.convert_md_to_pdf_reportlab import convert_md_to_pdf_reportlab
                    pdf_filepath = md_filepath.replace('.md', '.pdf')
                    success = convert_md_to_pdf_reportlab(md_filepath, pdf_filepath)
                    
                    if success and os.path.exists(pdf_filepath):
                        log_message(f"[OK] PDF report generated via ReportLab: {pdf_filepath}")
                        return pdf_filepath
                except ImportError as e2:
                    log_message(f"ReportLab converter not available: {e2}")
            
            # If we get here, no PDF was created
            log_message("[WARNING] PDF conversion failed - returning markdown file only")
            log_message("Install dependencies: pip install playwright markdown-it-py reportlab")
            log_message("For browser: playwright install chromium")
            return md_filepath  # Return markdown path instead
            
        except Exception as e:
            log_message(f"PDF conversion error: {e}")
            traceback.print_exc()
            return md_filepath  # Return markdown path instead
            
    except Exception as e:
        log_message(f"Error running agents: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    log_message("Starting HK IPO Monitor Agent (Fixed Version)...")
    result_path = run_agents_fixed()
    
    if result_path:
        log_message(f"Process completed. Output: {result_path}")
        
        # Open output directory
        try:
            output_dir = os.path.dirname(result_path)
            os.startfile(output_dir)
        except:
            pass
    else:
        log_message("Process failed.")
        sys.exit(1)