from firecrawl import FirecrawlApp
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse

class IPOScraper:
    def __init__(self, api_key):
        self.app = FirecrawlApp(api_key=api_key)

    def monitor(self, websites, keywords, days_back=30):
        """
        Searches for IPO news on specified websites using Firecrawl.
        
        Args:
            websites (list): List of target website URLs.
            keywords (list): List of keywords to search for.
            days_back (int): How many days back to check.
            
        Returns:
            list: A list of dictionaries containing news data.
        """
        all_results = []
        
        # Calculate date threshold
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Firecrawl search query construction
        # To avoid too many requests, we'll group keywords or do a broad search per site
        # Strategy: Search for "HK IPO" AND (keyword1 OR keyword2...) on specific sites
        
        # Since queries can't be infinitely long, we might need to simplify.
        # Let's try searching for the main concept "HK IPO" on the site, then filter locally.
        # Or iterate through a few key categories.
        
        # Simplification: User wants to "apply key word to filter and search".
        # We will search for "HK IPO" on these sites and then filter results by keywords.
        # This is more efficient than 20 queries per site.
        
        # [REVISED] The following code block is the old implementation.
        # It has been replaced by a new search logic that combines site queries and iterates through keyword pairs.
        # 
        # for site in websites:
        #     # Extract domain for site: operator
        #     domain = site.replace("https://", "").replace("http://", "").split("/")[0]
        #     
        #     # Construct query
        #     query = f"site:{domain} HK IPO news"
        #     
        #     print(f"Searching {domain}...")
        #     
        #     try:
        #         # Search using Firecrawl
        #         # limit=10 to get recent top results. Can be increased.
        #         search_results = self.app.search(
        #             query=query,
        #             limit=10,
        #             tbs="qdr:m",
        #             scrape_options={"formats": ["markdown"]}
        #         )
        #         
        #
        #         # Handle different response formats (v1 'data' vs v2 'web'/'news')
        #         items = []
        #         if isinstance(search_results, dict):
        #             if 'data' in search_results:
        #                 items = search_results['data']
        #             else:
        #                 if search_results.get('web'):
        #                     items.extend(search_results['web'])
        #                 if search_results.get('news'):
        #                     items.extend(search_results['news'])
        #         else:
        #             # Pydantic model handling
        #             try:
        #                 # Try to get web and news attributes
        #                 if hasattr(search_results, 'web') and search_results.web:
        #                     items.extend(search_results.web)
        #                 if hasattr(search_results, 'news') and search_results.news:
        #                     items.extend(search_results.news)
        #                     
        #                 # Fallback to data attribute if it exists
        #                 if not items and hasattr(search_results, 'data') and search_results.data:
        #                     items.extend(search_results.data)
        #             except Exception:
        #                 pass
        #         
        #         if not items:
        #             print(f"No results for {domain}")
        #             continue
        #
        #         for item in items:
        #             # Normalize item to dict if it's a Pydantic model
        #             item_dict = {}
        #             if hasattr(item, 'model_dump'):
        #                 item_dict = item.model_dump()
        #             elif hasattr(item, 'dict'):
        #                 item_dict = item.dict()
        #             elif isinstance(item, dict):
        #                 item_dict = item
        #             else:
        #                 # Try to access attributes directly
        #                 item_dict = {
        #                     'title': getattr(item, 'title', ''),
        #                     'url': getattr(item, 'url', ''),
        #                     'markdown': getattr(item, 'markdown', ''),
        #                     'content': getattr(item, 'content', ''),
        #                     'description': getattr(item, 'description', '')
        #                 }
        #
        #             # Keyword matching
        #             content = item_dict.get('markdown', '') or item_dict.get('content', '') or item_dict.get('description', '')
        #             title = item_dict.get('title', '') or item_dict.get('metadata', {}).get('title', '')
        #             
        #             # Robust URL extraction
        #             url = item_dict.get('url', '')
        #             if not url:
        #                 url = item_dict.get('link', '')
        #             if not url:
        #                 url = item_dict.get('metadata', {}).get('url', '')
        #             if not url:
        #                  url = item_dict.get('metadata', {}).get('sourceURL', '')
        #             
        #             text_to_check = (title + " " + content).lower()
        #             
        #             matched_keywords = [kw for kw in keywords if kw.lower() in text_to_check]
        #             
        #             if matched_keywords:
        #                 # Found a match!
        #                 all_results.append({
        #                     "title": title,
        #                     "url": url,
        #                     "content": content[:15000], # Limit content size for LLM
        #                     "source": domain,
        #                     "matched_keywords": matched_keywords
        #                 })
        #                 
        #     except Exception as e:
        #         print(f"Error searching {domain}: {e}")

        # [NEW IMPLEMENTATION STARTS HERE]
        
        seen_urls = set()
        
        # 1. Combine all target domains into a single site restriction clause
        domains = [site.replace("https://", "").replace("http://", "").split("/")[0] for site in websites]
        if not domains:
            print("No domains configured.")
            return []
            
        site_query = " OR ".join([f"site:{domain}" for domain in domains])
        site_query = f"({site_query})"

        # 2. Iterate through keywords in pairs
        # Helper to chunk keywords
        def chunk_list(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        keyword_batches = list(chunk_list(keywords, 2))
        
        for batch in keyword_batches:
            # Construct keyword part: (keyword1 OR keyword2)
            kw_query = " OR ".join([f'"{kw}"' for kw in batch]) # Quote keywords to be safe
            kw_query = f"({kw_query})"
            
            # Full query: (site:d1 OR site:d2) (kw1 OR kw2)
            query = f"{site_query} {kw_query}"
            
            print(f"Searching with query: {query}")
            
            try:
                # Search using Firecrawl
                search_results = self.app.search(
                    query=query,
                    limit=5, # Limit per batch to avoid overwhelming
                    tbs="qdr:m",
                    scrape_options={"formats": ["markdown"]}
                )
                
                # Handle different response formats (v1 'data' vs v2 'web'/'news')
                items = []
                if isinstance(search_results, dict):
                    if 'data' in search_results:
                        items = search_results['data']
                    else:
                        if search_results.get('web'):
                            items.extend(search_results['web'])
                        if search_results.get('news'):
                            items.extend(search_results['news'])
                else:
                    # Pydantic model handling
                    try:
                        # Try to get web and news attributes
                        if hasattr(search_results, 'web') and search_results.web:
                            items.extend(search_results.web)
                        if hasattr(search_results, 'news') and search_results.news:
                            items.extend(search_results.news)
                            
                        # Fallback to data attribute if it exists
                        if not items and hasattr(search_results, 'data') and search_results.data:
                            items.extend(search_results.data)
                    except Exception:
                        pass
                
                if not items:
                    print(f"No results for batch: {batch}")
                    continue

                for item in items:
                    # Normalize item to dict if it's a Pydantic model
                    item_dict = {}
                    if hasattr(item, 'model_dump'):
                        item_dict = item.model_dump()
                    elif hasattr(item, 'dict'):
                        item_dict = item.dict()
                    elif isinstance(item, dict):
                        item_dict = item
                    else:
                        # Try to access attributes directly
                        item_dict = {
                            'title': getattr(item, 'title', ''),
                            'url': getattr(item, 'url', ''),
                            'markdown': getattr(item, 'markdown', ''),
                            'content': getattr(item, 'content', ''),
                            'description': getattr(item, 'description', ''),
                            'published_date': getattr(item, 'published_date', '') or getattr(item, 'date', '') or getattr(item, 'metadata', {}).get('date', '') or getattr(item, 'metadata', {}).get('publishedDate', '')
                        }

                    # Robust URL extraction
                    url = item_dict.get('url', '')
                    if not url:
                        url = item_dict.get('link', '')
                    if not url:
                        url = item_dict.get('metadata', {}).get('url', '')
                    if not url:
                         url = item_dict.get('metadata', {}).get('sourceURL', '')

                    # Deduplication
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    # Content extraction
                    content = item_dict.get('markdown', '') or item_dict.get('content', '') or item_dict.get('description', '')
                    title = item_dict.get('title', '') or item_dict.get('metadata', {}).get('title', '')
                    
                    # Date extraction
                    published_date = item_dict.get('publishedDate', '') or item_dict.get('date', '') or item_dict.get('published_date', '')
                    if not published_date:
                        # published_date = item_dict.get('metadata', {}).get('date', '') or item_dict.get('metadata', {}).get('publishedDate', '')
                        meta = item_dict.get('metadata', {})
                        published_date = (
                            meta.get('date', '') or 
                            meta.get('publishedDate', '') or 
                            meta.get('published_time', '') or 
                            meta.get('modified_time', '') or 
                            meta.get('dc_date', '') or 
                            meta.get('dc_date_created', '')
                        )

                    # Store source domain
                    try:
                        source_domain = urlparse(url).netloc
                    except:
                        source_domain = "Unknown"

                    all_results.append({
                        "title": title,
                        "url": url,
                        "content": content[:15000], # Limit content size for LLM
                        "source": source_domain,
                        "matched_keywords": batch, # These were the query terms
                        "date": published_date
                    })
                        
            except Exception as e:
                print(f"Error searching batch {batch}: {e}")
                
        return all_results

    def find_official_website(self, company_name):
        """
        Finds the official website of a company.
        """
        query = f"{company_name} official website"
        try:
            results = self.app.search(query, limit=3)
            
            items = []
            if isinstance(results, dict):
                if 'data' in results:
                    items = results['data']
                elif results.get('web'):
                    items = results['web']
            else:
                # Pydantic model handling
                try:
                    if hasattr(results, 'web') and results.web:
                        items.extend(results.web)
                    elif hasattr(results, 'data') and results.data:
                        items.extend(results.data)
                except Exception:
                    pass
                    
            if items and len(items) > 0:
                item = items[0]
                if isinstance(item, dict):
                    return item.get('url')
                else:
                    return getattr(item, 'url', None)
        except Exception as e:
            print(f"Error finding website for {company_name}: {e}")
        return None

    def scrape_contact_info(self, website_url):
        """
        Scrapes contact info from a company website.
        """
        # 1. Search for contact page
        contact_url = None
        domain = website_url.replace("https://", "").replace("http://", "").split("/")[0]
        
        # Try to guess or find contact page
        # We can search specifically for the contact page using Firecrawl
        query = f"site:{domain} (Contact OR 联系我们)"
        try:
            results = self.app.search(query, limit=1)
            
            items = []
            if isinstance(results, dict):
                if 'data' in results:
                    items = results['data']
                elif results.get('web'):
                    items = results['web']
            else:
                # Pydantic model handling
                try:
                    if hasattr(results, 'web') and results.web:
                        items.extend(results.web)
                    elif hasattr(results, 'data') and results.data:
                        items.extend(results.data)
                except Exception:
                    pass
                    
            if items and len(items) > 0:
                item = items[0]
                if isinstance(item, dict):
                    contact_url = item.get('url')
                else:
                    contact_url = getattr(item, 'url', None)
            else:
                # Fallback to main page
                contact_url = website_url
                
            if not contact_url:
                contact_url = website_url
                
            # 2. Scrape the page
            scrape_result = self.app.scrape(contact_url, only_main_content=False)
            
            # Handle scrape result
            if isinstance(scrape_result, dict):
                return scrape_result.get('markdown', '')
            elif hasattr(scrape_result, 'markdown'):
                return scrape_result.markdown
            else:
                return ""
                
        except Exception as e:
            print(f"Error scraping contact info from {website_url}: {e}")
            
        return ""

    def search_contact_info_internet(self, company_name):
        """
        Searches the internet for the company's contact information.
        """
        query = f'"{company_name}" contact info email phone business collaboration'
        try:
            results = self.app.search(
                query=query,
                limit=1,
                scrape_options={"formats": ["markdown"]}
            )
            
            items = []
            if isinstance(results, dict):
                if 'data' in results:
                    items = results['data']
                elif results.get('web'):
                    items = results['web']
            else:
                try:
                    if hasattr(results, 'web') and results.web:
                        items.extend(results.web)
                    elif hasattr(results, 'data') and results.data:
                        items.extend(results.data)
                except Exception:
                    pass
            
            if items and len(items) > 0:
                item = items[0]
                # Extract markdown content
                if isinstance(item, dict):
                    return item.get('markdown', '') or item.get('content', '')
                else:
                    return getattr(item, 'markdown', '') or getattr(item, 'content', '')
            
        except Exception as e:
            print(f"Error searching internet for contact info of {company_name}: {e}")
            
        return ""
