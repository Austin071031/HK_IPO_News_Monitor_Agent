import os
import json
import re
from openai import OpenAI

class LLMProcessor:
    def __init__(self, api_key=None, base_url="https://api.deepseek.com"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DeepSeek API Key is required.")
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)

    def extract_en_data(self, markdown_content):
        prompt = """
        You are a data extraction assistant. Extract the following information from the provided markdown text of HKEX new listings:
        - Stock Code (e.g., 2715)
        - Stock Name (Company Name)
        - Listing Date
        - Status (IPO status)
        - Origin (Mainland China, HK, or Overseas)
        - Sector (Industry)

        Return the result as a JSON list of objects. Each object should have keys: "Stock Code", "Stock Name", "Listing Date", "Status", "Origin", "Sector".
        If any field is missing, use "N/A".
        Only return the JSON list, no markdown formatting or other text.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured data from text."},
                    {"role": "user", "content": f"{prompt}\n\nText:\n{markdown_content}"}
                ],
                stream=False
            )
            content = response.choices[0].message.content
            # Try to find JSON block if mixed with text
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(content)
        except Exception as e:
            print(f"Error extracting EN data: {e}")
            return []

    def extract_zh_data(self, markdown_content):
        prompt = """
        You are a data extraction assistant. Extract the following information from the provided markdown text of HKEX new listings (Chinese version):
        - Stock Code (e.g., 2715)
        - Stock Name (Company Name in Chinese)

        Return the result as a JSON list of objects. Each object should have keys: "Stock Code", "Stock Name ZH".
        Only return the JSON list, no markdown formatting or other text.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured data from text."},
                    {"role": "user", "content": f"{prompt}\n\nText:\n{markdown_content}"}
                ],
                stream=False
            )
            content = response.choices[0].message.content
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(content)
        except Exception as e:
            print(f"Error extracting ZH data: {e}")
            return []

    def extract_ipo_date_status(self, search_content, stock_code=None, company_name=None):
        prompt = f"""
        You are a data extraction assistant. Extract the following IPO information from the provided search results or page content.
        
        Target Company:
        - Stock Code: {stock_code or 'N/A'}
        - Company Name: {company_name or 'N/A'}
        
        Please find the entry for this specific company in the text.

        Extract:
        - IPO Listed Date (Format: 12 Feb 2026, or "N/A" if not found)
        - IPO Status (e.g., Listed, Delisted, Trading Halted, or "N/A")
        
        Return the result as a single JSON object with keys: "Listing Date", "Status".
        Only return the JSON object, no markdown formatting.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured data from text."},
                    {"role": "user", "content": f"{prompt}\n\nSearch Results:\n{search_content}"}
                ],
                stream=False
            )
            content = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(content)
        except Exception as e:
            print(f"Error extracting IPO date/status: {e}")
            return {
                "Listing Date": "N/A",
                "Status": "N/A"
            }

    def extract_ipo_origin_sector(self, search_content, stock_code=None, company_name=None):
        prompt = f"""
        You are a data extraction assistant. Extract the following IPO information from the provided search results or page content.
        
        Target Company:
        - Stock Code: {stock_code or 'N/A'}
        - Company Name: {company_name or 'N/A'}
        
        Please find the entry for this specific company in the text.

        Extract:
        - Origin (Where the company comes from: "Mainland China", "HK", "Overseas", or "N/A")
        - Sector (Industry the company belongs to, or "N/A")
        
        Return the result as a single JSON object with keys: "Origin", "Sector".
        Only return the JSON object, no markdown formatting.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured data from text."},
                    {"role": "user", "content": f"{prompt}\n\nSearch Results:\n{search_content}"}
                ],
                stream=False
            )
            content = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(content)
        except Exception as e:
            print(f"Error extracting IPO origin/sector: {e}")
            return {
                "Origin": "N/A",
                "Sector": "N/A"
            }
