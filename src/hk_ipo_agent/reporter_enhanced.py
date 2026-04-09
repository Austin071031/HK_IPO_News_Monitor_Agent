#!/usr/bin/env python3
"""
Enhanced reporter for HK IPO Monitor Agent with deduplication and clean formatting.
"""

import os
import datetime
import hashlib
from collections import OrderedDict


class EnhancedIPOReporter:
    def __init__(self):
        self.original_reporter = None
        try:
            # Try to import original reporter for compatibility
            from .reporter import IPOReporter
            self.original_reporter = IPOReporter()
        except ImportError:
            pass

    def deduplicate_data(self, data):
        """
        Deduplicate data based on company name, date, and source.
        Prioritizes more complete records and removes duplicates.
        """
        if not data:
            return []
            
        # Create a dictionary for deduplication
        dedup_dict = OrderedDict()
        
        for item in data:
            # Create a unique key based on company name and date
            company_en = item.get('company_en', '').strip().lower()
            date_str = str(item.get('date', ''))[:10]  # Get YYYY-MM-DD part
            
            if company_en and date_str:
                key = f"{company_en}_{date_str}"
            else:
                # Fallback: use notes/source as key
                notes = str(item.get('notes', ''))[:50].lower()
                source = str(item.get('source', ''))[:50].lower()
                key = f"{notes}_{source}"
            
            # Check if we already have this item
            if key in dedup_dict:
                existing_item = dedup_dict[key]
                
                # Score items by completeness (more fields = better)
                existing_score = self._score_completeness(existing_item)
                new_score = self._score_completeness(item)
                
                # Keep the more complete record
                if new_score > existing_score:
                    dedup_dict[key] = item
                # If scores are equal, prefer the one with "A1 Submitted" or "Rumors" status
                elif new_score == existing_score:
                    existing_status = existing_item.get('status', '').lower()
                    new_status = item.get('status', '').lower()
                    
                    status_priority = {
                        'a1 submitted': 5,
                        'application proof': 4,
                        'rumors': 3,
                        'announced': 2,
                        'planning': 1,
                        'none': 0
                    }
                    
                    existing_priority = status_priority.get(existing_status, 0)
                    new_priority = status_priority.get(new_status, 0)
                    
                    if new_priority > existing_priority:
                        dedup_dict[key] = item
            else:
                dedup_dict[key] = item
        
        return list(dedup_dict.values())
    
    def _score_completeness(self, item):
        """Score an item based on how complete its data is."""
        score = 0
        
        # Check each field for non-empty values
        fields = ['company_en', 'company_zh', 'status', 'date', 'sector', 
                 'notes', 'contact_email', 'contact_phone', 'hk_address']
        
        for field in fields:
            value = str(item.get(field, '')).strip()
            if value and value.lower() != 'n/a':
                score += 1
        
        # Bonus points for URLs
        if str(item.get('source', '')).startswith('http'):
            score += 1
        if str(item.get('website_url', '')).startswith('http'):
            score += 1
        
        return score
    
    def clean_table_data(self, data):
        """
        Clean and format table data for better presentation.
        """
        cleaned_data = []
        
        for item in data:
            cleaned_item = {}
            
            # Clean each field
            cleaned_item['Company (EN)'] = self._clean_field(item.get('company_en', ''))
            cleaned_item['Company (ZH)'] = self._clean_field(item.get('company_zh', ''))
            cleaned_item['Status'] = self._clean_status(item.get('status', ''))
            cleaned_item['Date'] = self._clean_date(item.get('date', ''))
            cleaned_item['Sector'] = self._clean_field(item.get('sector', ''))
            
            # Handle notes with source link
            notes = self._clean_field(item.get('notes', ''))
            source = str(item.get('source', '')).strip()
            if source.startswith('http') and notes:
                # Truncate long notes for better display
                if len(notes) > 50:
                    notes_display = notes[:47] + '...'
                else:
                    notes_display = notes
                cleaned_item['Notes'] = f"[{notes_display}]({source})"
            else:
                cleaned_item['Notes'] = notes
            
            cleaned_item['Email'] = self._clean_field(item.get('contact_email', ''))
            cleaned_item['Phone'] = self._clean_field(item.get('contact_phone', ''))
            cleaned_item['Address'] = self._clean_field(item.get('hk_address', ''))
            
            cleaned_data.append(cleaned_item)
        
        return cleaned_data
    
    def _clean_field(self, value):
        """Clean a field value."""
        if not value:
            return ''
        
        value_str = str(value).strip()
        if value_str.lower() in ['', 'n/a', 'none', 'nan']:
            return ''
        
        # Remove excessive whitespace
        value_str = ' '.join(value_str.split())
        
        return value_str
    
    def _clean_status(self, status):
        """Standardize status values."""
        if not status:
            return ''
        
        status_str = str(status).strip().lower()
        
        # Map to standard status values
        status_map = {
            'a1 submitted': 'A1 Submitted',
            'a1 filing': 'A1 Submitted',
            'application proof': 'Application Proof',
            'hearing passed': 'Hearing Passed',
            'rumors': 'Rumors',
            'rumour': 'Rumors',
            'rumoured': 'Rumors',
            'announced': 'Announced',
            'planning': 'Planning',
            'considering': 'Considering',
            'seeking': 'Seeking',
            'filing': 'Filing',
            'none': 'None'
        }
        
        # Try exact match first
        if status_str in status_map:
            return status_map[status_str]
        
        # Try partial matches
        for key, value in status_map.items():
            if key in status_str:
                return value
        
        # Capitalize first letter if no match
        return status_str.capitalize()
    
    def _clean_date(self, date_str):
        """Clean and format date."""
        if not date_str:
            return ''
        
        date_str = str(date_str).strip()
        
        # Try to extract YYYY-MM-DD format
        import re
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
        if date_match:
            return date_match.group(1)
        
        return date_str[:10] if len(date_str) >= 10 else date_str
    
    def generate_markdown_string(self, data):
        """
        Generate clean Markdown table string from data.
        """
        if not data:
            return "No data available.\n"
        
        # Deduplicate and clean data
        dedup_data = self.deduplicate_data(data)
        cleaned_data = self.clean_table_data(dedup_data)
        
        if not cleaned_data:
            return "No data available after cleaning.\n"
        
        # Sort by date (newest first)
        def get_sort_key(item):
            date_str = item.get('Date', '')
            try:
                return datetime.datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.datetime.min
            except:
                return datetime.datetime.min
        
        cleaned_data.sort(key=get_sort_key, reverse=True)
        
        # Generate Markdown table
        headers = ["Company (EN)", "Company (ZH)", "Status", "Date", "Sector", "Notes", "Email", "Phone", "Address"]
        
        output = []
        output.append("| " + " | ".join(headers) + " |")
        output.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        for item in cleaned_data:
            row = []
            for header in headers:
                value = item.get(header, '')
                
                # Escape pipe characters for Markdown
                if isinstance(value, str):
                    value = value.replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')
                
                row.append(value)
            
            output.append("| " + " | ".join(row) + " |")
        
        return "\n".join(output)
    
    def generate_markdown_report(self, data, filename=None, title="HK IPO Analysis Report"):
        """
        Generate a complete Markdown report file.
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            filename = os.path.join(output_dir, f"{title.replace(' ', '_')}_{timestamp}.md")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n")
                f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Generate and write the table
                table_content = self.generate_markdown_string(data)
                f.write(table_content)
                
                # Add summary
                f.write("\n\n")
                f.write("## Summary\n\n")
                f.write(f"- Total companies analyzed: {len(self.deduplicate_data(data))}\n")
                f.write(f"- Date range: {self._get_date_range(data)}\n")
                f.write(f"- Status distribution: {self._get_status_distribution(data)}\n")
            
            print(f"Enhanced Markdown report generated: {filename}")
            return filename
            
        except Exception as e:
            print(f"Error generating enhanced Markdown report: {e}")
            # Fallback to original reporter if available
            if self.original_reporter:
                return self.original_reporter.generate_markdown_report(data, filename)
            return None
    
    def _get_date_range(self, data):
        """Get the date range of the data."""
        if not data:
            return "N/A"
        
        dates = []
        for item in data:
            date_str = self._clean_date(item.get('date', ''))
            if date_str:
                try:
                    dates.append(datetime.datetime.strptime(date_str, "%Y-%m-%d"))
                except:
                    pass
        
        if not dates:
            return "N/A"
        
        min_date = min(dates).strftime("%Y-%m-%d")
        max_date = max(dates).strftime("%Y-%m-%d")
        
        if min_date == max_date:
            return min_date
        return f"{min_date} to {max_date}"
    
    def _get_status_distribution(self, data):
        """Get status distribution statistics."""
        if not data:
            return "N/A"
        
        status_count = {}
        dedup_data = self.deduplicate_data(data)
        
        for item in dedup_data:
            status = self._clean_status(item.get('status', ''))
            if status:
                status_count[status] = status_count.get(status, 0) + 1
        
        if not status_count:
            return "No status information"
        
        distribution = []
        for status, count in sorted(status_count.items(), key=lambda x: x[1], reverse=True):
            distribution.append(f"{status}: {count}")
        
        return "; ".join(distribution)


def test_enhanced_reporter():
    """Test the enhanced reporter with sample data."""
    test_data = [
        {
            'company_en': 'Test Company A',
            'company_zh': '测试公司A',
            'status': 'A1 Submitted',
            'date': '2026-04-01',
            'sector': 'Technology',
            'notes': 'Testing notes',
            'source': 'https://example.com/test1',
            'contact_email': 'test@example.com',
            'contact_phone': '123-456-7890',
            'hk_address': 'Test Address'
        },
        {
            'company_en': 'Test Company A',  # Duplicate
            'company_zh': '测试公司A',
            'status': 'Rumors',
            'date': '2026-04-01',
            'sector': 'Technology',
            'notes': 'Different notes',
            'source': 'https://example.com/test2',
            'contact_email': 'test2@example.com',
            'contact_phone': '987-654-3210',
            'hk_address': 'Different Address'
        }
    ]
    
    reporter = EnhancedIPOReporter()
    
    print("Testing deduplication:")
    dedup = reporter.deduplicate_data(test_data)
    print(f"Original: {len(test_data)} items")
    print(f"Deduplicated: {len(dedup)} items")
    
    print("\nTesting Markdown generation:")
    markdown = reporter.generate_markdown_string(test_data)
    print(markdown[:500])
    
    return True


if __name__ == "__main__":
    test_enhanced_reporter()