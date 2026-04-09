#!/usr/bin/env python3
"""
Strict Format Reporter for HK IPO Monitor Agent.
Follows EXACT format of the 2026-04-04 report.
"""

import os
import datetime
import json
from collections import OrderedDict


class Strict20260404Reporter:
    """
    Reporter that strictly follows the 2026-04-04 report format.
    
    Format specifications from 2026-04-04 report:
    
    HKEX Table (13 columns):
    | Company (EN) | Company (ZH) | Stock Code | Listing Date | Status | Origin | Sector | Contact Email | Contact Phone | Address in HK | Website | Data Source | Last Updated |
    
    IPO News Table (12 columns):
    | Company (EN) | Company (ZH) | Status | Date | Sector | Origin | Contact Email | Contact Phone | Address in HK | Website | Data Source | Last Updated |
    """
    
    def __init__(self):
        # Exact headers from 2026-04-04 report
        self.HKEX_HEADER = "| Company (EN) | Company (ZH) | Stock Code | Listing Date | Status | Origin | Sector | Contact Email | Contact Phone | Address in HK | Website | Data Source | Last Updated |"
        self.IPO_HEADER = "| Company (EN) | Company (ZH) | Status | Date | Sector | Origin | Contact Email | Contact Phone | Address in HK | Website | Data Source | Last Updated |"
        
        self.HKEX_SEPARATOR = "|---|---|---|---|---|---|---|---|---|---|---|---|---|"
        self.IPO_SEPARATOR = "|---|---|---|---|---|---|---|---|---|---|---|---|"
        
        # Field mappings for data transformation
        self.HKEX_FIELDS = [
            "Company (EN)", "Company (ZH)", "Stock Code", "Listing Date", 
            "Status", "Origin", "Sector", "Contact Email", "Contact Phone", 
            "Address in HK", "Website", "Data Source", "Last Updated"
        ]
        
        self.IPO_FIELDS = [
            "Company (EN)", "Company (ZH)", "Status", "Date", 
            "Sector", "Origin", "Contact Email", "Contact Phone", 
            "Address in HK", "Website", "Data Source", "Last Updated"
        ]
    
    def _clean_value(self, value):
        """Clean a field value for table display."""
        if value is None:
            return ""
        
        value_str = str(value).strip()
        if value_str.lower() in ['', 'n/a', 'none', 'nan', 'null']:
            return ""
        
        # Remove excessive whitespace and line breaks
        value_str = ' '.join(value_str.split())
        
        # Escape pipe characters for Markdown tables
        value_str = value_str.replace('|', '\\|')
        
        # Truncate very long values
        if len(value_str) > 100:
            value_str = value_str[:97] + "..."
        
        return value_str
    
    def _format_website_link(self, company_name, website_url):
        """Format website as clickable link if URL is valid."""
        if not website_url or not isinstance(website_url, str):
            return company_name if company_name else ""
        
        website_url = website_url.strip()
        if not website_url.startswith('http'):
            website_url = f"https://{website_url}"
        
        # Basic URL validation
        if '.' in website_url and len(website_url) > 10:
            if company_name:
                return f"[{company_name}]({website_url})"
            else:
                return f"[Website]({website_url})"
        
        return company_name if company_name else ""
    
    def _format_source_link(self, notes, source_url):
        """Format source as clickable link if URL is valid."""
        if not source_url or not isinstance(source_url, str):
            return notes if notes else ""
        
        source_url = source_url.strip()
        if not source_url.startswith('http'):
            return notes if notes else ""
        
        if notes and len(notes) > 5:
            # Truncate long notes for display
            display_notes = notes[:40] + "..." if len(notes) > 43 else notes
            return f"[{display_notes}]({source_url})"
        
        return f"[Source]({source_url})"
    
    def prepare_hkex_data(self, hkex_raw_data):
        """
        Prepare HKEX data for strict format.
        
        Args:
            hkex_raw_data: List of dicts from HKEX agent
        
        Returns:
            List of dicts with all 13 fields
        """
        prepared_data = []
        
        for item in hkex_raw_data:
            if not isinstance(item, dict):
                continue
            
            # Extract values with defaults
            company_en = self._clean_value(item.get("Company (EN)", item.get("Stock Name", "")))
            company_zh = self._clean_value(item.get("Company (ZH)", ""))
            
            # Check if company_zh is already a Markdown link
            if company_zh.startswith('[') and '](' in company_zh and ')' in company_zh:
                # Already a link, keep as is
                pass
            else:
                # Format as link if website available
                website = item.get("Website", item.get("Company Website", ""))
                if website and website.lower() != "n/a":
                    company_zh = self._format_website_link(company_zh, website)
            
            prepared_item = {
                "Company (EN)": company_en,
                "Company (ZH)": company_zh,
                "Stock Code": self._clean_value(item.get("Stock Code", "")),
                "Listing Date": self._clean_value(item.get("Listing Date", "")),
                "Status": self._clean_value(item.get("Status", "")),
                "Origin": self._clean_value(item.get("Origin", "")),
                "Sector": self._clean_value(item.get("Sector", "")),
                "Contact Email": self._clean_value(item.get("Contact Email", item.get("Email", ""))),
                "Contact Phone": self._clean_value(item.get("Contact Phone", item.get("Phone", ""))),
                "Address in HK": self._clean_value(item.get("Address in HK", item.get("Address", ""))),
                "Website": self._clean_value(item.get("Website", item.get("Company Website", ""))),
                "Data Source": self._clean_value(item.get("Data Source", "HKEX Official")),
                "Last Updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            
            prepared_data.append(prepared_item)
        
        return prepared_data
    
    def prepare_ipo_data(self, ipo_raw_data):
        """
        Prepare IPO news data for strict format.
        
        Args:
            ipo_raw_data: List of dicts from HK IPO agent
        
        Returns:
            List of dicts with all 12 fields
        """
        prepared_data = []
        
        for item in ipo_raw_data:
            if not isinstance(item, dict):
                continue
            
            # Extract values with field name mappings
            company_en = self._clean_value(item.get("company_en", item.get("Company (EN)", "")))
            company_zh = self._clean_value(item.get("company_zh", item.get("Company (ZH)", "")))
            
            # Format website link for Chinese company name
            website = item.get("website_url", item.get("website", ""))
            if website and website.lower() != "n/a":
                company_zh = self._format_website_link(company_zh, website)
            
            # Format source link for notes
            notes = self._clean_value(item.get("notes", ""))
            source = item.get("source", "")
            if source and source.startswith('http'):
                notes = self._format_source_link(notes, source)
            
            prepared_item = {
                "Company (EN)": company_en,
                "Company (ZH)": company_zh,
                "Status": self._clean_value(item.get("status", "")),
                "Date": self._clean_value(item.get("date", "")),
                "Sector": self._clean_value(item.get("sector", "")),
                "Origin": self._clean_value(item.get("origin", "")),
                "Contact Email": self._clean_value(item.get("contact_email", item.get("email", ""))),
                "Contact Phone": self._clean_value(item.get("contact_phone", item.get("phone", ""))),
                "Address in HK": self._clean_value(item.get("hk_address", item.get("address", ""))),
                "Website": self._clean_value(item.get("website_url", item.get("website", ""))),
                "Data Source": self._clean_value(item.get("source", "News Portal")),
                "Last Updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            
            prepared_data.append(prepared_item)
        
        return prepared_data
    
    def generate_hkex_table(self, prepared_data):
        """
        Generate HKEX table in strict format.
        
        Args:
            prepared_data: Prepared HKEX data from prepare_hkex_data()
        
        Returns:
            String with complete HKEX table
        """
        if not prepared_data:
            return "No data available."
        
        lines = []
        
        # Header
        lines.append(self.HKEX_HEADER)
        lines.append(self.HKEX_SEPARATOR)
        
        # Data rows
        for item in prepared_data:
            row_parts = []
            for field in self.HKEX_FIELDS:
                value = item.get(field, "")
                row_parts.append(value)
            
            row_line = "| " + " | ".join(row_parts) + " |"
            lines.append(row_line)
        
        return "\n".join(lines)
    
    def generate_ipo_table(self, prepared_data):
        """
        Generate IPO news table in strict format.
        
        Args:
            prepared_data: Prepared IPO data from prepare_ipo_data()
        
        Returns:
            String with complete IPO news table
        """
        if not prepared_data:
            return "No data available."
        
        lines = []
        
        # Header
        lines.append(self.IPO_HEADER)
        lines.append(self.IPO_SEPARATOR)
        
        # Data rows
        for item in prepared_data:
            row_parts = []
            for field in self.IPO_FIELDS:
                value = item.get(field, "")
                row_parts.append(value)
            
            row_line = "| " + " | ".join(row_parts) + " |"
            lines.append(row_line)
        
        return "\n".join(lines)
    
    def generate_strict_report(self, hkex_raw_data, ipo_raw_data, timestamp=None):
        """
        Generate complete report in strict 2026-04-04 format.
        
        Args:
            hkex_raw_data: Raw HKEX data from HKEX agent
            ipo_raw_data: Raw IPO data from HK IPO agent
            timestamp: Optional custom timestamp (defaults to now)
        
        Returns:
            String with complete report
        """
        if timestamp is None:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare data
        hkex_data = self.prepare_hkex_data(hkex_raw_data)
        ipo_data = self.prepare_ipo_data(ipo_raw_data)
        
        # Generate tables
        hkex_table = self.generate_hkex_table(hkex_data)
        ipo_table = self.generate_ipo_table(ipo_data)
        
        # Build report
        report_lines = []
        
        # Title and metadata
        report_lines.append("HK IPO Monitor Report")
        report_lines.append("")  # Empty line
        report_lines.append("Combined HK IPO Report")
        report_lines.append("")  # Empty line
        report_lines.append(f"Generated on: {timestamp}")
        report_lines.append(f"Report ID: HKIPO_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
        report_lines.append("")  # Empty line
        
        # HKEX Section
        report_lines.append("## HKEX Listed/Listing Companies")
        report_lines.append("")  # Empty line
        report_lines.append(hkex_table)
        report_lines.append("")  # Empty line
        
        # IPO News Section
        report_lines.append("## HK IPO News & Rumours")
        report_lines.append("")  # Empty line
        report_lines.append(ipo_table)
        
        return "\n".join(report_lines)
    
    def save_strict_report(self, hkex_raw_data, ipo_raw_data, output_dir="output"):
        """
        Generate and save report in strict format.
        
        Args:
            hkex_raw_data: Raw HKEX data
            ipo_raw_data: Raw IPO data
            output_dir: Output directory
        
        Returns:
            Path to saved Markdown file
        """
        import os
        
        # Create output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate report
        report_content = self.generate_strict_report(hkex_raw_data, ipo_raw_data)
        
        # Save to file
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"Strict_HK_IPO_Report_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return filepath


# Quick test function
def test_strict_reporter():
    """Test the strict reporter with sample data."""
    reporter = Strict20260404Reporter()
    
    # Sample HKEX data
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
    
    # Sample IPO data
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
        }
    ]
    
    # Generate report
    report = reporter.generate_strict_report(sample_hkex, sample_ipo)
    
    print("=== Test Strict Reporter Output ===")
    print(report)
    print("=" * 60)
    
    # Save test report
    test_dir = "test_output"
    saved_path = reporter.save_strict_report(sample_hkex, sample_ipo, test_dir)
    print(f"Test report saved to: {saved_path}")
    
    return report


if __name__ == "__main__":
    test_strict_reporter()