import pandas as pd
import os
from datetime import datetime

class DataProcessor:
    def __init__(self):
        self.data = []

    def consolidate_data(self, en_data, zh_data, etnet_data_map):
        """
        en_data: List of dicts with EN info
        zh_data: List of dicts with ZH info
        etnet_data_map: Dict mapping stock_code -> etnet_info dict
        """
        consolidated = []
        
        # Create a map for quick lookup of ZH names
        zh_map = {item.get('Stock Code'): item.get('Stock Name ZH', 'N/A') for item in zh_data}

        for item in en_data:
            stock_code = item.get('Stock Code', 'N/A')
            zh_name = zh_map.get(stock_code, 'N/A')
            etnet_info = etnet_data_map.get(stock_code, {
                "address": "N/A", "phone": "N/A", "website": "N/A", "email": "N/A"
            })
            
            # Format Company (ZH) as clickable link if website is available
            website_val = str(etnet_info.get('website', 'N/A')).strip()
            if website_val != "N/A" and website_val != "":
                # Ensure the URL has a scheme
                website_url = website_val if website_val.startswith('http') else f"http://{website_val}"
                company_zh_display = f"[{zh_name}]({website_url})"
            else:
                company_zh_display = zh_name

            consolidated.append({
                "Company (EN)": item.get('Stock Name', 'N/A'),
                "Company (ZH)": company_zh_display,
                "Stock Code": stock_code,
                "Listing Date": item.get('Listing Date', 'N/A'),
                "Status": item.get('Status', 'N/A'),
                "Origin": item.get('Origin', 'N/A'),
                "Sector": item.get('Sector', 'N/A'),
                "Contact Email": etnet_info.get('email', 'N/A'),
                "Contact Phone": etnet_info.get('phone', 'N/A'),
                "Address in HK": etnet_info.get('address', 'N/A')
                # "Company Website": etnet_info.get('website', 'N/A') # Removed Company Website column
            })
            
        self.data = consolidated
        return consolidated

    def generate_markdown_string(self):
        """
        Generates the Markdown report content as a string.
        """
        df = pd.DataFrame(self.data)
        
        # Fill NaN with "N/A" just in case
        df = df.fillna("N/A")
        
        return df.to_markdown(index=False)

    def export_markdown(self, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        df = pd.DataFrame(self.data)
        
        # Fill NaN with "N/A" just in case
        df = df.fillna("N/A")
        
        filename = f"HKEX_IPO_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# HKEX IPO Report - {datetime.now().strftime('%Y-%m-%d')}\n\n")
            f.write(df.to_markdown(index=False))
            
        return filepath
