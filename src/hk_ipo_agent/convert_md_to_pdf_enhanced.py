#!/usr/bin/env python3
"""
Enhanced Markdown to PDF converter with fallback mechanisms.
Tries Playwright first, falls back to ReportLab if browser not available.
"""

import os
import sys
import traceback

def convert_md_to_pdf(md_file_path, output_pdf_path, use_reportlab_fallback=True):
    """
    Convert markdown file to PDF with fallback support.
    
    Args:
        md_file_path: Path to input markdown file
        output_pdf_path: Path to output PDF file
        use_reportlab_fallback: If True, fall back to ReportLab if Playwright fails
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"Converting {md_file_path} to {output_pdf_path}")
    
    # Try Playwright method first (higher quality output)
    try:
        print("Attempting PDF conversion with Playwright...")
        from .convert_md_to_pdf import convert_md_to_pdf as playwright_convert
        playwright_convert(md_file_path, output_pdf_path)
        
        if os.path.exists(output_pdf_path) and os.path.getsize(output_pdf_path) > 0:
            print(f"[SUCCESS] Playwright PDF conversion successful: {output_pdf_path}")
            return True
        else:
            print("[ERROR] Playwright conversion produced empty file")
            
    except ImportError as e:
        print(f"[WARNING] Playwright dependencies not available: {e}")
        print("  Install with: pip install markdown-it-py playwright && playwright install chromium")
    except Exception as e:
        print(f"[WARNING] Playwright conversion failed: {e}")
        if "Executable doesn't exist" in str(e) or "Browsers not installed" in str(e):
            print("  Browser not installed. Run: playwright install chromium")
    
    # If Playwright failed and fallback is enabled, try ReportLab
    if use_reportlab_fallback:
        try:
            print("Falling back to ReportLab conversion...")
            from .convert_md_to_pdf_reportlab import convert_md_to_pdf_reportlab
            
            success = convert_md_to_pdf_reportlab(md_file_path, output_pdf_path)
            if success and os.path.exists(output_pdf_path) and os.path.getsize(output_pdf_path) > 0:
                print(f"[SUCCESS] ReportLab PDF conversion successful: {output_pdf_path}")
                return True
            else:
                print("[ERROR] ReportLab conversion failed")
                return False
                
        except ImportError as e:
            print(f"[ERROR] ReportLab dependencies not available: {e}")
            print("  Install with: pip install reportlab")
            return False
        except Exception as e:
            print(f"[ERROR] ReportLab conversion error: {e}")
            traceback.print_exc()
            return False
    else:
        print("[ERROR] No PDF conversion method available")
        return False

def convert_md_to_pdf_safe(md_file_path, output_pdf_path=None):
    """
    Safe conversion with automatic output path generation.
    
    Args:
        md_file_path: Path to input markdown file
        output_pdf_path: Optional output path (defaults to same name with .pdf extension)
    
    Returns:
        str: Path to generated PDF file, or None if failed
    """
    if output_pdf_path is None:
        output_pdf_path = md_file_path.replace('.md', '.pdf')
        # Ensure unique filename if it already exists
        counter = 1
        while os.path.exists(output_pdf_path):
            output_pdf_path = md_file_path.replace('.md', f'_{counter}.pdf')
            counter += 1
    
    success = convert_md_to_pdf(md_file_path, output_pdf_path)
    
    if success and os.path.exists(output_pdf_path):
        return output_pdf_path
    else:
        return None

if __name__ == "__main__":
    # Command line interface
    if len(sys.argv) < 2:
        print("Usage: python convert_md_to_pdf_enhanced.py <input.md> [output.pdf]")
        print("  If output.pdf is not specified, uses input.pdf")
        sys.exit(1)
    
    input_md = sys.argv[1]
    output_pdf = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_md):
        print(f"Error: Input file not found: {input_md}")
        sys.exit(1)
    
    result = convert_md_to_pdf_safe(input_md, output_pdf)
    
    if result:
        print(f"✅ PDF successfully created: {result}")
        sys.exit(0)
    else:
        print("❌ PDF creation failed")
        sys.exit(1)