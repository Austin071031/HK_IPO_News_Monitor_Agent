import time

class IPOEnricher:
    def __init__(self, scraper, analyzer):
        self.scraper = scraper
        self.analyzer = analyzer

    def enrich_companies(self, companies_data):
        """
        Takes a list of company dictionaries and enriches them with website and contact info.
        """
        enriched_data = []
        
        for company in companies_data:
            print(f"Enriching data for: {company.get('company_en', 'Unknown')}")
            
            # Default values
            company['website_url'] = "N/A"
            company['contact_email'] = "N/A"
            company['contact_phone'] = "N/A"
            company['hk_address'] = "N/A"
            
            # 1. Find Website
            name_to_search = company.get('company_en') or company.get('company_zh')
            if not name_to_search:
                enriched_data.append(company)
                continue
                
            website_url = self.scraper.find_official_website(name_to_search)
            
            if website_url:
                company['website_url'] = website_url
                print(f"  Found website: {website_url}")
                
                # 2. Scrape Contact Page
                # Retry logic is partly handled in scraper, but we can loop here if needed.
                # Scraper tries to find "Contact" page specifically.
                contact_content = self.scraper.scrape_contact_info(website_url)
                
                if contact_content:
                    # 3. Extract Info with LLM
                    contact_info = self.analyzer.extract_contact_info(contact_content)
                    
                    print(f"{name_to_search} Contact info raw: {contact_info}")

                    if contact_info:
                        company['contact_email'] = contact_info.get('email', 'N/A')
                        company['contact_phone'] = contact_info.get('phone', 'N/A')
                        company['hk_address'] = contact_info.get('address', 'N/A')
                        print("  Extracted contact info.")
            else:
                print("  Website not found.")
            
            # Fallback: Search internet if contact info is still missing
            if company['contact_email'] == 'N/A' and company['contact_phone'] == 'N/A':
                print("  Contact info missing from official website. Searching internet...")
                contact_content = self.scraper.search_contact_info_internet(name_to_search)
                
                if contact_content:
                    contact_info = self.analyzer.extract_contact_info(contact_content)

                    print(f"{name_to_search} Contact info raw: {contact_info}")

                    if contact_info:
                        if contact_info.get('email') != 'N/A':
                            company['contact_email'] = contact_info.get('email')
                        if contact_info.get('phone') != 'N/A':
                            company['contact_phone'] = contact_info.get('phone')
                        if contact_info.get('address') != 'N/A':
                            company['hk_address'] = contact_info.get('address')
                        print("  Extracted contact info from internet search.")

            enriched_data.append(company)
            # Be polite to servers
            time.sleep(1)
            
        return enriched_data
