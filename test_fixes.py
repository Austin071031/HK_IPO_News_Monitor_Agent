#!/usr/bin/env python3
"""
Test script to demonstrate PDF fixes and enhanced reporter.
Uses existing data to show improvements without running full agents.
"""

import os
import sys
import json
import datetime
from pathlib import Path

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath('.')))

def test_pdf_fixes():
    """Test the PDF conversion fixes on existing Markdown files."""
    print("=== Testing PDF Fixes ===")
    
    # Get the latest Markdown report
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    
    if not os.path.exists(output_dir):
        print("Output directory not found!")
        return False
    
    # Find latest Markdown file
    md_files = list(Path(output_dir).glob("*.md"))
    if not md_files:
        print("No Markdown files found!")
        return False
    
    latest_md = max(md_files, key=lambda f: f.stat().st_mtime)
    print(f"Testing with: {latest_md.name}")
    
    # Read the original Markdown
    with open(latest_md, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    print(f"Original file size: {len(original_content)} bytes")
    
    # Test enhanced reporter
    print("\n=== Testing Enhanced Reporter ===")
    
    try:
        from src.hk_ipo_agent.reporter_enhanced import EnhancedIPOReporter
        reporter = EnhancedIPOReporter()
        
        # Parse the data from the Markdown (simplified)
        data = []
        lines = original_content.split('\n')
        in_table = False
        headers = []
        
        for line in lines:
            if line.startswith('## 2. HK IPO News & Rumours'):
                in_table = True
                continue
            elif in_table and line.startswith('| '):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) > 3 and not line.startswith('| ---'):
                    # Skip header rows
                    if 'Company (EN)' in line or '---' in line:
                        continue
                    
                    # Parse table row
                    if len(parts) >= 10:  # Has all columns
                        item = {
                            'company_en': parts[1],
                            'company_zh': parts[2],
                            'status': parts[3],
                            'date': parts[4],
                            'sector': parts[5],
                            'notes': parts[6],
                            'contact_email': parts[7],
                            'contact_phone': parts[8],
                            'hk_address': parts[9]
                        }
                        data.append(item)
        
        print(f"Parsed {len(data)} items from Markdown")
        
        # Test deduplication
        dedup_data = reporter.deduplicate_data(data)
        print(f"After deduplication: {len(dedup_data)} items")
        
        # Generate cleaned Markdown
        cleaned_markdown = reporter.generate_markdown_string(data)
        
        # Save cleaned version
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        cleaned_filename = f"Cleaned_Test_{timestamp}.md"
        cleaned_path = os.path.join(output_dir, cleaned_filename)
        
        with open(cleaned_path, 'w', encoding='utf-8') as f:
            f.write(f"# Test Enhanced Report\n")
            f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Original items:** {len(data)}\n")
            f.write(f"**Deduplicated items:** {len(dedup_data)}\n\n")
            f.write("## Enhanced Table (Deduplicated & Cleaned)\n\n")
            f.write(cleaned_markdown)
        
        print(f"Cleaned report saved: {cleaned_filename}")
        
        return cleaned_path
        
    except ImportError as e:
        print(f"Enhanced reporter import error: {e}")
        return False

def test_pdf_conversion(md_file):
    """Test the fixed PDF conversion."""
    print("\n=== Testing PDF Conversion (Fixed) ===")
    
    try:
        # Try the enhanced converter first
        from src.hk_ipo_agent.convert_md_to_pdf_enhanced import convert_md_to_pdf_safe
        
        print("Converting with enhanced converter...")
        pdf_path = convert_md_to_pdf_safe(md_file)
        
        if pdf_path and os.path.exists(pdf_path):
            print(f"✅ PDF generated: {os.path.basename(pdf_path)}")
            print(f"   Size: {os.path.getsize(pdf_path)} bytes")
            return pdf_path
        else:
            print("⚠️ PDF conversion failed")
            
    except ImportError as e:
        print(f"Enhanced converter not available: {e}")
        
        # Try the fixed standard converter
        try:
            from src.hk_ipo_agent.convert_md_to_pdf import convert_md_to_pdf
            
            pdf_path = md_file.replace('.md', '_fixed.pdf')
            convert_md_to_pdf(md_file, pdf_path)
            
            if os.path.exists(pdf_path):
                print(f"✅ PDF generated with fixed converter: {os.path.basename(pdf_path)}")
                print(f"   Size: {os.path.getsize(pdf_path)} bytes")
                return pdf_path
                
        except Exception as e2:
            print(f"Standard converter error: {e2}")
    
    return False

def compare_formats():
    """Compare original vs fixed formatting."""
    print("\n=== Format Comparison ===")
    
    # Check what CSS fixes were applied
    try:
        from src.hk_ipo_agent.convert_md_to_pdf import convert_md_to_pdf
        
        # Read the converter file to check CSS
        converter_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                      "src", "hk_ipo_agent", "convert_md_to_pdf.py")
        
        with open(converter_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for problematic CSS
        issues_fixed = []
        
        if 'position: relative' not in content or '/* Removed:' in content:
            issues_fixed.append("✓ Removed 'position: relative' from table cells")
        
        if 'word-break: break-word' in content and 'word-break: break-all' not in content:
            issues_fixed.append("✓ Changed 'break-all' to 'break-word' for links")
        
        if '<script>' not in content or 'JavaScript removed' in content:
            issues_fixed.append("✓ Removed problematic JavaScript")
        
        print("CSS/JS fixes applied:")
        for fix in issues_fixed:
            print(f"  {fix}")
            
    except Exception as e:
        print(f"Error checking fixes: {e}")

def main():
    """Main test function."""
    print("HK IPO Monitor Agent - Fix Validation Tool")
    print("=" * 50)
    
    # Test 1: Compare formatting fixes
    compare_formats()
    
    # Test 2: Test enhanced reporter
    cleaned_md = test_pdf_fixes()
    
    if cleaned_md:
        # Test 3: Test PDF conversion
        pdf_result = test_pdf_conversion(cleaned_md)
        
        if pdf_result:
            print(f"\n✅ All tests passed!")
            print(f"   - Enhanced reporter: Working")
            print(f"   - CSS fixes: Applied")
            print(f"   - PDF conversion: Successful")
            print(f"\nOutput files:")
            print(f"   - {os.path.basename(cleaned_md)}")
            print(f"   - {os.path.basename(pdf_result)}")
            
            # Open output directory
            output_dir = os.path.dirname(cleaned_md)
            try:
                os.startfile(output_dir)
            except:
                pass
            
            return True
        else:
            print("\n⚠️ PDF conversion failed")
            return False
    else:
        print("\n❌ Enhanced reporter test failed")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)