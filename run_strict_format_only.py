#!/usr/bin/env python3
"""
Run STRICT FORMAT only - minimal test to verify format.
This script runs quickly with minimal configuration to test the strict reporter format.
"""

import os
import sys
import json
import datetime
import traceback

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath('.')))

def log_message(message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    # Remove Unicode symbols for Windows compatibility
    cleaned_message = message.replace('✅', '[OK]').replace('❌', '[ERROR]').replace('⚠️', '[WARNING]')
    print(f"[{timestamp}] {cleaned_message}")

def run_strict_format_test():
    """Run minimal test of strict format reporter."""
    try:
        log_message("Starting STRICT FORMAT TEST ONLY (No agents)")
        
        # Import strict reporter
        try:
            from src.hk_ipo_agent.strict_reporter import Strict20260404Reporter
            log_message("✅ Strict reporter imported successfully")
        except ImportError as e:
            log_message(f"❌ Error importing strict reporter: {e}")
            return None
        
        # Create sample data matching 2026-04-04 format
        log_message("Creating sample data matching 2026-04-04 format...")
        
        # HKEX data (13 fields)
        sample_hkex = [
            {
                "Company (EN)": "Beijing Tong Ren Tang Healthcare Investment Co., Ltd.",
                "Company (ZH)": "北京同仁堂国药有限公司",
                "Stock Code": "2667",
                "Listing Date": "2016-07-27",
                "Status": "LISTED",
                "Origin": "China",
                "Sector": "Healthcare",
                "Contact Email": "ir@tongrentang.com",
                "Contact Phone": "+852 2525 5566",
                "Address in HK": "Room 1234, Tower 1, Admiralty Centre, Hong Kong",
                "Website": "https://www.tongrentang.com",
                "Data Source": "HKEX Official",
                "Last Updated": "2026-04-04 13:17"
            }
        ]
        
        # IPO data (12 fields)
        sample_ipo = [
            {
                "company_en": "Huayan Robot",
                "company_zh": "华研机器人",
                "status": "LISTED",
                "date": "2026-03-30",
                "sector": "Technology/Robotics",
                "origin": "China",
                "contact_email": "ir@huayanrobot.com",
                "contact_phone": "+86 10 1234 5678",
                "hk_address": "Room 567, Central Plaza, Hong Kong",
                "website_url": "https://www.huayanrobot.com",
                "source": "https://finance.eastmoney.com/news/123456789.html",
                "notes": "Robotics company listed on HKEX"
            },
            {
                "company_en": "Guanghe Technology",
                "company_zh": "广和科技",
                "status": "A1 Submitted",
                "date": "2026-03-20",
                "sector": "Semiconductors",
                "origin": "China",
                "contact_email": "investor@guanghe-tech.com",
                "contact_phone": "+86 21 9876 5432",
                "hk_address": "Room 890, Two Pacific Place, Hong Kong",
                "website_url": "https://www.guanghe-tech.com",
                "source": "https://finance.sina.com.cn/news/123456789.html",
                "notes": "Semiconductor company submitted A1 application"
            }
        ]
        
        # Generate strict format report
        log_message("Generating strict format report...")
        reporter = Strict20260404Reporter()
        report = reporter.generate_strict_report(sample_hkex, sample_ipo)
        
        # Analyze format
        lines = report.split('\n')
        log_message(f"Report generated: {len(lines)} lines")
        
        # Save report
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        md_filename = f"STRICT_FORMAT_TEST_{timestamp}.md"
        md_filepath = os.path.join(output_dir, md_filename)
        
        with open(md_filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        log_message(f"✅ Strict format test saved to: {md_filepath}")
        
        # Compare with 2026-04-09 cleaned report
        cleaned_path = os.path.join(output_dir, "Cleaned_HK_IPO_Report_2026-04-09_104248.md")
        if os.path.exists(cleaned_path):
            log_message("\n" + "="*80)
            log_message("FORMAT COMPARISON: Strict vs Cleaned (2026-04-09)")
            log_message("="*80)
            
            with open(cleaned_path, 'r', encoding='utf-8') as f:
                cleaned_content = f.read()
            
            # Count fields
            strict_lines = report.split('\n')
            cleaned_lines = cleaned_content.split('\n')
            
            # Find table headers
            strict_hkex_fields = 0
            strict_ipo_fields = 0
            cleaned_fields = 0
            
            for line in strict_lines:
                if 'Company (EN) | Company (ZH) | Stock Code | Listing Date | Status | Origin | Sector | Contact Email | Contact Phone | Address in HK | Website | Data Source | Last Updated |' in line:
                    strict_hkex_fields = 13
                if 'Company (EN) | Company (ZH) | Status | Date | Sector | Origin | Contact Email | Contact Phone | Address in HK | Website | Data Source | Last Updated |' in line:
                    strict_ipo_fields = 12
            
            for line in cleaned_lines:
                if 'Company (EN)' in line and 'Stock Code' in line:
                    # Count fields in cleaned header
                    cleaned_fields = len([f.strip() for f in line.strip('|').split('|') if f.strip()])
            
            log_message(f"Strict Format: HKEX表格 = {strict_hkex_fields}字段, IPO表格 = {strict_ipo_fields}字段")
            log_message(f"Cleaned Report (2026-04-09): {cleaned_fields}字段")
            log_message(f"2026-04-04 Reference: HKEX表格 = 13字段, IPO表格 = 12字段")
            
            # Show format comparison
            log_message("\nFORMAT COMPLIANCE CHECK:")
            if strict_hkex_fields == 13 and strict_ipo_fields == 12:
                log_message("✅ STRICT FORMAT: 完全匹配2026-04-04报告格式")
            else:
                log_message("❌ STRICT FORMAT: 不匹配2026-04-04报告格式")
            
            if cleaned_fields == 13 or cleaned_fields == 12:
                log_message("✅ CLEANED REPORT: 匹配2026-04-04报告格式")
            else:
                log_message("❌ CLEANED REPORT: 不匹配2026-04-04报告格式")
        
        # Try PDF conversion
        try:
            log_message("\nAttempting PDF conversion...")
            
            # Try enhanced converter
            try:
                from src.hk_ipo_agent.convert_md_to_pdf_enhanced import convert_md_to_pdf_safe
                pdf_filepath = convert_md_to_pdf_safe(md_filepath)
                
                if pdf_filepath and os.path.exists(pdf_filepath):
                    log_message(f"✅ PDF report generated: {pdf_filepath}")
                    return pdf_filepath
                else:
                    log_message("[WARNING] PDF conversion returned no file path")
            except ImportError as e:
                log_message(f"Enhanced converter not available: {e}")
                
        except Exception as e:
            log_message(f"PDF conversion error: {e}")
        
        return md_filepath
        
    except Exception as e:
        log_message(f"Error in strict format test: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    log_message("Starting STRICT FORMAT TEST (Format verification only)...")
    result_path = run_strict_format_test()
    
    if result_path:
        log_message(f"\n✅ Test completed. Output: {result_path}")
        
        # Show the first few lines of the report
        if os.path.exists(result_path):
            with open(result_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print("\n" + "="*80)
            print("FIRST 30 LINES OF STRICT FORMAT REPORT:")
            print("="*80)
            lines = content.split('\n')
            for i, line in enumerate(lines[:30]):
                print(f"{i:3d}: {line}")
            
            # Check format
            print("\n" + "="*80)
            print("FORMAT VALIDATION:")
            print("="*80)
            
            hkex_header_count = 0
            ipo_header_count = 0
            
            for line in lines:
                if 'Company (EN) | Company (ZH) | Stock Code | Listing Date | Status | Origin | Sector | Contact Email | Contact Phone | Address in HK | Website | Data Source | Last Updated |' in line:
                    hkex_header_count += 1
                if 'Company (EN) | Company (ZH) | Status | Date | Sector | Origin | Contact Email | Contact Phone | Address in HK | Website | Data Source | Last Updated |' in line:
                    ipo_header_count += 1
            
            print(f"HKEX Header (13 fields): {'✅ FOUND' if hkex_header_count > 0 else '❌ NOT FOUND'}")
            print(f"IPO Header (12 fields): {'✅ FOUND' if ipo_header_count > 0 else '❌ NOT FOUND'}")
            print(f"Format matches 2026-04-04 report: {'✅ YES' if hkex_header_count > 0 and ipo_header_count > 0 else '❌ NO'}")
            
    else:
        log_message("❌ Test failed.")
        sys.exit(1)