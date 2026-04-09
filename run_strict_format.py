#!/usr/bin/env python3
"""
Strict Format HK IPO Monitor Agent Runner.
Uses Strict20260404Reporter to ensure exact format matching 2026-04-04 report.
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

def deduplicate_hkex_data(data):
    """
    Basic deduplication for HKEX data by stock code.
    """
    if not data or not isinstance(data, list):
        return data
    
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

def convert_to_strict_hkex_format(hkex_markdown_table):
    """
    Convert HKEX markdown table to list of dicts for strict reporter.
    Assumes the table follows the standard HKEX format.
    """
    if not hkex_markdown_table:
        return []
    
    lines = hkex_markdown_table.strip().split('\n')
    if len(lines) < 3:
        return []  # Need at least header, separator, and one data row
    
    # Parse header
    header_line = lines[0]
    header_fields = [field.strip() for field in header_line.strip('|').split('|')]
    
    # Parse data rows
    data_rows = []
    for line in lines[2:]:  # Skip header and separator
        if not line.strip() or line.startswith('|---'):
            continue
        
        values = [value.strip() for value in line.strip('|').split('|')]
        if len(values) != len(header_fields):
            continue
        
        # Create dict
        row_dict = {}
        for i, field in enumerate(header_fields):
            row_dict[field] = values[i]
        
        data_rows.append(row_dict)
    
    return data_rows

def convert_to_strict_ipo_format(ipo_markdown_table):
    """
    Convert IPO markdown table to list of dicts for strict reporter.
    Handles the format from IPOReporter.
    """
    if not ipo_markdown_table:
        return []
    
    lines = ipo_markdown_table.strip().split('\n')
    if len(lines) < 3:
        return []
    
    # Parse header (from IPOReporter)
    header_line = lines[0]
    header_fields = [field.strip() for field in header_line.strip('|').split('|')]
    
    # Field mapping to strict format
    field_mapping = {
        'Company (EN)': 'company_en',
        'Company (ZH)': 'company_zh',
        'Status': 'status',
        'Date': 'date',
        'Sector': 'sector',
        'Notes': 'notes',
        'Email': 'contact_email',
        'Phone': 'contact_phone',
        'Address': 'hk_address'
    }
    
    # Parse data rows
    data_rows = []
    for line in lines[2:]:  # Skip header and separator
        if not line.strip() or line.startswith('|---'):
            continue
        
        values = [value.strip() for value in line.strip('|').split('|')]
        if len(values) != len(header_fields):
            continue
        
        # Create dict with mapped field names
        row_dict = {}
        for i, field in enumerate(header_fields):
            if field in field_mapping:
                mapped_field = field_mapping[field]
                row_dict[mapped_field] = values[i]
        
        # Try to extract source URL from notes if it's a link
        notes = row_dict.get('notes', '')
        if notes.startswith('[') and '](' in notes and ')' in notes:
            # Extract URL from markdown link format [text](url)
            try:
                text_end = notes.find('](')
                url_start = text_end + 2
                url_end = notes.find(')', url_start)
                if url_end > url_start:
                    row_dict['source'] = notes[url_start:url_end]
                    # Keep only text part for notes
                    row_dict['notes'] = notes[1:text_end]
            except:
                pass
        
        data_rows.append(row_dict)
    
    return data_rows

def run_strict_format_agents():
    """Run both agents and generate strict format report."""
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
        hkex_result = hkex_agent.run()
        
        # Convert HKEX result to raw data
        if isinstance(hkex_result, str):
            hkex_raw_data = convert_to_strict_hkex_format(hkex_result)
        elif isinstance(hkex_result, list):
            hkex_raw_data = hkex_result
        else:
            hkex_raw_data = []
            log_message("Warning: HKEX Agent returned unexpected format")
        
        # Apply basic deduplication
        hkex_raw_data = deduplicate_hkex_data(hkex_raw_data)
        log_message(f"HKEX data prepared: {len(hkex_raw_data)} companies")
        
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
        ipo_result = hk_ipo_agent.run()
        
        # Convert IPO result to raw data
        if isinstance(ipo_result, str):
            ipo_raw_data = convert_to_strict_ipo_format(ipo_result)
        elif isinstance(ipo_result, list):
            ipo_raw_data = ipo_result
        else:
            ipo_raw_data = []
            log_message("Warning: HK IPO Agent returned unexpected format")
        
        log_message(f"IPO data prepared: {len(ipo_raw_data)} companies")
        
        # Generate strict format report
        log_message("--- Generating Strict Format Report (2026-04-04 style) ---")
        
        try:
            # Import strict reporter
            from src.hk_ipo_agent.strict_reporter import Strict20260404Reporter
            strict_reporter = Strict20260404Reporter()
            
            # Create output directory
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Generate and save strict report
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
            md_filename = f"Strict_HK_IPO_Report_{timestamp}.md"
            md_filepath = os.path.join(output_dir, md_filename)
            
            # Generate report content
            report_content = strict_reporter.generate_strict_report(hkex_raw_data, ipo_raw_data)
            
            # Save to file
            with open(md_filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            log_message(f"[OK] Strict format report saved to: {md_filepath}")
            
            # Convert to PDF using enhanced converter
            try:
                log_message("Attempting PDF conversion...")
                
                # Try enhanced converter first
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
                return md_filepath
                    
            except Exception as e:
                log_message(f"PDF conversion error: {e}")
                traceback.print_exc()
                return md_filepath  # Return markdown path instead
            
        except ImportError as e:
            log_message(f"[ERROR] Strict reporter not available: {e}")
            log_message("Please ensure strict_reporter.py is in src/hk_ipo_agent/")
            raise
            
    except Exception as e:
        log_message(f"Error running agents: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    log_message("Starting HK IPO Monitor Agent (Strict Format Version)...")
    result_path = run_strict_format_agents()
    
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