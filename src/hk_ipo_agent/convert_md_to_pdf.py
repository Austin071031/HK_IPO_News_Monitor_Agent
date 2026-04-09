import sys
import os
from markdown_it import MarkdownIt
from playwright.sync_api import sync_playwright

def convert_md_to_pdf(md_file_path, output_pdf_path):
    # Read Markdown content
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert to HTML
    # Enable tables which are part of GFM (GitHub Flavored Markdown)
    # Enable linkify to convert raw URLs to clickable links
    # Note: 'commonmark' preset in markdown-it-py is strict and might ignore linkify in some contexts.
    # We use 'default' preset or explicitly enable linkify rules if needed, 
    # but simplest is to switch to 'gfm-like' config if possible or ensure linkify is active.
    # Actually, 'commonmark' with linkify=True SHOULD work, but let's try 'default' or 'gfm' if available.
    # However, to be safe and ensure links are created, we can use a custom renderer or just 'default' preset which is more feature-rich.
    md = MarkdownIt("gfm-like", {'linkify': True, 'html': True})
    html_content = md.render(md_content)

    # Add CSS for styling (GitHub-like style)
    html_with_style = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
            font-size: 14px;
            line-height: 1.5;
            word-wrap: break-word;
            padding: 40px;
        }}
        a {{
            color: #0366d6;
            text-decoration: none;
            word-break: break-word; /* Fix: break-word instead of break-all */
        }}
        a:hover {{
            text-decoration: underline;
        }}
        /* Clean table cell styling - remove problematic positioning */
        table td {{
            /* Removed: position: relative; */
        }}
        table {{
            border-spacing: 0;
            border-collapse: collapse;
            margin-top: 0;
            margin-bottom: 16px;
            display: table;
            width: 100%;
            font-size: 11px;
        }}
        table th, table td {{
            padding: 2px 4px;
            border: 1px solid #dfe2e5;
            word-wrap: break-word;
            word-break: break-all;
            max-width: 200px;
            font-size: 10px;
        }}
        table th {{
            font-weight: 600;
            background-color: #f6f8fa;
        }}
        table tr {{
            background-color: #fff;
            border-top: 1px solid #c6cbd1;
        }}
        table tr:nth-child(2n) {{
            background-color: #f6f8fa;
        }}
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
        }}
        h1 {{ font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }}
        h2 {{ font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }}
        blockquote {{
            padding: 0 1em;
            color: #6a737d;
            border-left: 0.25em solid #dfe2e5;
        }}
        code {{
            padding: .2em .4em;
            margin: 0;
            font-size: 85%;
            background-color: rgba(27,31,35,.05);
            border-radius: 3px;
        }}
    </style>
    </head>
    <body>
    {html_content}
     <!-- JavaScript removed to fix layout issues -->
    </body>
    </html>
    """

    # Generate PDF using Playwright
    with sync_playwright() as p:
        try:
            print("Launching browser...")
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html_with_style)
            # Use A4 format with landscape orientation, reduced margins, and scaling
            page.pdf(
                path=output_pdf_path,
                format="A4",
                landscape=True,
                margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"},
                scale=0.8
            )
            browser.close()
            print(f"Successfully converted {md_file_path} to {output_pdf_path}")
        except Exception as e:
            print(f"Error during PDF generation: {e}")
            if "Executable doesn't exist" in str(e):
                print("Browsers not installed. Please run 'playwright install'.")

if __name__ == "__main__":
    md_file = r"D:\05-automation_project\HK_IPO_Info_Analysis_Agent\output\Hong_Kong_IPO_Analysis_2026-03-02.md"
    pdf_file = md_file.replace(".md", ".pdf")
    try:
        convert_md_to_pdf(md_file, pdf_file)
    except Exception as e:
        if "Permission denied" in str(e):
             # Try adding a timestamp to ensure uniqueness
             import time
             ts = int(time.time())
             print(f"Could not write to {pdf_file}, trying a new filename with timestamp {ts}...")
             pdf_file = md_file.replace(".md", f"_v{ts}.pdf")
             convert_md_to_pdf(md_file, pdf_file)
        else:
            raise e
