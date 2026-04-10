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
            word-break: break-all;
            display: inline-block; /* Helps with clickability */
        }}
        a:hover {{
            text-decoration: underline;
        }}
        /* Make the table cell relative so we can potentially stretch the link */
        table td {{
            position: relative;
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
    <script>
    // Wait for content to be fully loaded
    window.onload = function() {{
        const tables = document.querySelectorAll("table");
        tables.forEach(table => {{
            const rows = table.querySelectorAll("tr");
            rows.forEach(row => {{
                const cells = row.querySelectorAll("td");
                if (cells.length > 0) {{
                    const lastCell = cells[cells.length - 1];
                    // Clean up potential markdown formatting remnants
                    const text = lastCell.textContent.trim();
                    
                    // Check if the cell text looks like a URL but isn't wrapped in <a>
                    if (text.startsWith("http") && !lastCell.querySelector("a")) {{
                        const url = text;
                        lastCell.innerHTML = `<a href="${{url}}">${{url}}</a>`;
                    }}
                    
                    const link = lastCell.querySelector("a");
                    if (link) {{
                        // Ensure the link is block-level to fill the cell
                        link.style.display = "block";
                        link.style.width = "100%";
                        link.style.minHeight = "100%"; 
                        link.style.wordBreak = "break-all";
                        link.style.textDecoration = "none";
                        link.style.color = "#0366d6";
                        
                        // Remove padding from cell and add it to link to maximize clickable area
                        lastCell.style.padding = "0";
                        link.style.padding = "2px 4px"; // Match original cell padding
                        link.style.boxSizing = "border-box";
                    }}
                }}
            }});
        }});
    }};
    </script>
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
    md_file = r"/Users/austin/Desktop/HK_IPO_Monitor_Agent/output/Combined_HK_IPO_Report_2026-04-09_173800.md"
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
