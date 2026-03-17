from openai import OpenAI
import json
import re
import ast

class IPOAnalyzer:
    def __init__(self, api_key):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

    def _clean_and_parse_json(self, content):
        """
        Helper method to robustly clean and parse JSON content from LLM response.
        Handles <think> blocks, markdown code blocks, and raw JSON strings.
        Also handles Python dict string representation (single quotes).
        """
        try:
            # Remove <think>...</think> blocks if present (common in reasoning models)
            if "<think>" in content:
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            
            # Clean up markdown code blocks
            content = content.replace("```json", "").replace("```", "").strip()
            
            # Find the first '{' and last '}' to extract the JSON object
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            json_str = content
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx+1]
            
            # Try standard JSON parsing first
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # If JSON parsing fails, try ast.literal_eval (for Python dicts with single quotes)
                try:
                    return ast.literal_eval(json_str)
                except (ValueError, SyntaxError):
                    raise # Re-raise the original JSON error if fallback fails
            
        except Exception as e:
            print(f"JSON Parse Error: {e}")
            print(f"Content being parsed: {content[:500]}...") # Log first 500 chars for debugging
            return None

    def analyze_news(self, content, source_url, date=None, title=None):
        """
        Analyzes news content to extract IPO information.
        """
        prompt = f"""
        You are an expert financial analyst. Analyze the following news content about Hong Kong IPOs.
        Extract the following information for the company mentioned:
        1. Company (EN): English name of the company.
        2. Company (ZH): Chinese name of the company (if available).
        3. Current Status: The IPO status (e.g., Rumors, A1 Submitted, Hearing Passed, Listed, etc.).
        4. Sector: The industry sector the company belongs to (e.g., Technology, Finance, Healthcare, etc.).
        5. Date: The date of the news or event (Format: YYYY-MM-DD). If not explicitly stated, try to find it in the content.
        
        Content:
        {content[:10000]} 
        
        Output the result strictly in JSON format with keys: "company_en", "company_zh", "status", "sector", "date".
        If no relevant IPO information is found, return null.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured data from financial news."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            data = self._clean_and_parse_json(result)
            
            if data:
                data['source'] = source_url
                # Use provided date if available, otherwise use LLM extracted date
                # if date and str(date).strip() != "" and str(date).strip() != "N/A":
                #     data['date'] = date
                # elif not data.get('date'):
                #      data['date'] = "N/A"
                if date and str(date).strip() != "" and str(date).strip() != "N/A":
                    data['date'] = str(date)
                elif not data.get('date'):
                     data['date'] = "N/A"
                     
                # Format date to YYYY-MM-DD
                if data.get('date') and data['date'] != "N/A":
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', str(data['date']))
                    if date_match:
                        data['date'] = date_match.group(1)
                
                # Use the original title for the notes field
                if title:
                    data['notes'] = title
                else:
                    data['notes'] = "N/A"
                
                return data
            return None
            
        except Exception as e:
            print(f"Error analyzing news: {e}")
            return None

    def extract_contact_info(self, content):
        """
        Extracts contact information from a company's "Contact Us" page content.
        """
        prompt = f"""
        Extract the following contact information from the text below:
        1. Contact Email: Prioritize "Business Collaboration" or "Business" related email. If not found, use general/primary contact email.
        2. Contact Phone: Prioritize "Business Collaboration" or "Business" related phone. If not found, use general/primary contact phone.
        3. HK Address: Prioritize "Business Collaboration" or "Business" related address. If not found, use general/primary HK address.
        
        Text:
        {content[:5000]}
        
        Output strictly in JSON format with keys: "email", "phone", "address".
        Use "N/A" if information is missing.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts contact details."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            return self._clean_and_parse_json(result) or {"email": "N/A", "phone": "N/A", "address": "N/A"}
            
        except Exception as e:
            print(f"Error extracting contact info: {e}")
            return {"email": "N/A", "phone": "N/A", "address": "N/A"}
