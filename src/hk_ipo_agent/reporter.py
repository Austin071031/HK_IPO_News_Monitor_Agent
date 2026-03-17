# from reportlab.lib import colors
# from reportlab.lib.pagesizes import A4, landscape
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.pdfbase import pdfmetrics
# from reportlab.pdfbase.ttfonts import TTFont
import os
import datetime

# Renamed from PDFReporter to IPOReporter to reflect the change in functionality
class IPOReporter:
    def __init__(self):
        # self.register_fonts()
        pass

    # def register_fonts(self):
    #     """
    #     Registers Chinese fonts for ReportLab.
    #     """
    #     try:
    #         # Try to register a common Chinese font
    #         # SimHei is standard on many Windows systems
    #         font_path = "C:\\Windows\\Fonts\\simhei.ttf"
    #         if os.path.exists(font_path):
    #             pdfmetrics.registerFont(TTFont('SimHei', font_path))
    #             self.font_name = 'SimHei'
    #         else:
    #             # Fallback or try another
    #             font_path = "C:\\Windows\\Fonts\\msyh.ttc"
    #             if os.path.exists(font_path):
    #                 pdfmetrics.registerFont(TTFont('MicrosoftYaHei', font_path))
    #                 self.font_name = 'MicrosoftYaHei'
    #             else:
    #                 print("Warning: Chinese font not found. Text may not display correctly.")
    #                 self.font_name = 'Helvetica' # Fallback
    #     except Exception as e:
    #         print(f"Error registering font: {e}")
    #         self.font_name = 'Helvetica'

    def generate_markdown_string(self, data):
        """
        Generates the Markdown report content as a string.
        """
        # Sort data by date (latest to oldest)
        def get_date_object(item):
            date_str = item.get('date', '')
            if not date_str or date_str == 'N/A':
                return datetime.datetime.min
            try:
                # Attempt to parse YYYY-MM-DD (most common)
                # If date_str is longer (e.g. ISO timestamp), taking first 10 chars usually works for date
                return datetime.datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
            except (ValueError, TypeError):
                return datetime.datetime.min

        # Sort in descending order (latest first)
        data = sorted(data, key=get_date_object, reverse=True)
        
        output = []
        
        # Table Header
        headers = ["Company (EN)", "Company (ZH)", "Status", "Date", "Sector", "Notes", "Email", "Phone", "Address"]
        output.append("| " + " | ".join(headers) + " |")
        output.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # Table Rows
        for item in data:
            # Format notes as clickable link if source is available
            notes_val = str(item.get('notes', '')).strip()
            source_url = str(item.get('source', '')).strip()
            if source_url.startswith('http') and notes_val:
                notes_val = f"[{notes_val}]({source_url})"
            
            # Format Company (ZH) as clickable link if website is available
            company_zh_val = str(item.get('company_zh', '')).strip()
            website_val = str(item.get('website_url', '')).strip()
            
            if website_val.startswith('http') and company_zh_val:
                    company_zh_val = f"[{company_zh_val}]({website_val})"
            elif website_val.startswith('http') and not company_zh_val:
                # If no Chinese name, use English name or "Website"
                company_zh_val = f"[Website]({website_val})"

            row = [
                str(item.get('company_en', '')).replace('|', '\\|').replace('\n', ' '),
                company_zh_val.replace('|', '\\|').replace('\n', ' '),
                str(item.get('status', '')).replace('|', '\\|').replace('\n', ' '),
                str(item.get('date', '')).replace('|', '\\|').replace('\n', ' '),
                str(item.get('sector', '')).replace('|', '\\|').replace('\n', ' '),
                notes_val.replace('|', '\\|').replace('\n', ' '),
                str(item.get('contact_email', '')).replace('|', '\\|').replace('\n', ' '),
                str(item.get('contact_phone', '')).replace('|', '\\|').replace('\n', ' '),
                str(item.get('hk_address', '')).replace('|', '\\|').replace('\n', ' '),
            ]
            output.append("| " + " | ".join(row) + " |")
            
        return "\n".join(output)

    def generate_markdown_report(self, data, filename=None):
        """
        Generates a Markdown report from the enriched data.
        """
        # Sort data by date (latest to oldest)
        def get_date_object(item):
            date_str = item.get('date', '')
            if not date_str or date_str == 'N/A':
                return datetime.datetime.min
            try:
                # Attempt to parse YYYY-MM-DD (most common)
                # If date_str is longer (e.g. ISO timestamp), taking first 10 chars usually works for date
                return datetime.datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
            except (ValueError, TypeError):
                return datetime.datetime.min

        # Sort in descending order (latest first)
        # We sort a copy to avoid side effects if data is used elsewhere, 
        # though in this app it's the final step.
        data = sorted(data, key=get_date_object, reverse=True)

        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
            # Create output directory if it doesn't exist
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            filename = os.path.join(output_dir, f"Hong_Kong_IPO_Analysis_{timestamp}.md")
            
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# Hong Kong IPO Analysis Report\n\n")
                f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Table Header
                headers = ["Company (EN)", "Company (ZH)", "Status", "Date", "Sector", "Notes", "Email", "Phone", "Address"]
                f.write("| " + " | ".join(headers) + " |\n")
                f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
                
                # Table Rows
                for item in data:
                    # Format notes as clickable link if source is available
                    notes_val = str(item.get('notes', '')).strip()
                    source_url = str(item.get('source', '')).strip()
                    if source_url.startswith('http') and notes_val:
                        notes_val = f"[{notes_val}]({source_url})"
                    
                    # Format Company (ZH) as clickable link if website is available
                    company_zh_val = str(item.get('company_zh', '')).strip()
                    website_val = str(item.get('website_url', '')).strip()
                    
                    if website_val.startswith('http') and company_zh_val:
                         company_zh_val = f"[{company_zh_val}]({website_val})"
                    elif website_val.startswith('http') and not company_zh_val:
                        # If no Chinese name, use English name or "Website"
                        company_zh_val = f"[Website]({website_val})"

                    row = [
                        str(item.get('company_en', '')).replace('|', '\\|').replace('\n', ' '),
                        company_zh_val.replace('|', '\\|').replace('\n', ' '),
                        str(item.get('status', '')).replace('|', '\\|').replace('\n', ' '),
                        str(item.get('date', '')).replace('|', '\\|').replace('\n', ' '),
                        str(item.get('sector', '')).replace('|', '\\|').replace('\n', ' '),
                        notes_val.replace('|', '\\|').replace('\n', ' '),
                        str(item.get('contact_email', '')).replace('|', '\\|').replace('\n', ' '),
                        str(item.get('contact_phone', '')).replace('|', '\\|').replace('\n', ' '),
                        str(item.get('hk_address', '')).replace('|', '\\|').replace('\n', ' '),
                    ]
                    f.write("| " + " | ".join(row) + " |\n")
            
            print(f"Markdown report generated: {filename}")        
            return filename
        except Exception as e:
            print(f"Error generating Markdown report: {e}")
            return None

    # def generate_report(self, data, filename=None):
    #     if not filename:
    #         timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    #         filename = f"Hong_Kong_IPO_Analysis_{timestamp}.pdf"
    #
    #     doc = SimpleDocTemplate(filename, pagesize=landscape(A4))
    #     elements = []
    #
    #     # Title
    #     styles = getSampleStyleSheet()
    #     title_style = ParagraphStyle(
    #         'Title',
    #         parent=styles['Heading1'],
    #         fontName=self.font_name,
    #         fontSize=16,
    #         alignment=1,
    #         spaceAfter=20
    #     )
    #     elements.append(Paragraph("Hong Kong IPO Analysis Report", title_style))
    #     elements.append(Spacer(1, 20))
    #
    #     # Table Data
    #     headers = [
    #         "Company (EN)", "Company (ZH)", "Status", "Notes", 
    #         "Source", "Email", "Phone", "Address", "Website"
    #     ]
    #     
    #     table_data = [headers]
    #     
    #     # Style for table cells
    #     cell_style = ParagraphStyle(
    #         'Cell',
    #         parent=styles['Normal'],
    #         fontName=self.font_name,
    #         fontSize=8,
    #         leading=10
    #     )
    #
    #     for item in data:
    #         row = [
    #             Paragraph(str(item.get('company_en', '')), cell_style),
    #             Paragraph(str(item.get('company_zh', '')), cell_style),
    #             Paragraph(str(item.get('status', '')), cell_style),
    #             Paragraph(str(item.get('notes', '')), cell_style),
    #             Paragraph(str(item.get('source', '')), cell_style),
    #             Paragraph(str(item.get('contact_email', '')), cell_style),
    #             Paragraph(str(item.get('contact_phone', '')), cell_style),
    #             Paragraph(str(item.get('hk_address', '')), cell_style),
    #             Paragraph(str(item.get('website_url', '')), cell_style),
    #         ]
    #         table_data.append(row)
    #
    #     # Table Style
    #     table = Table(table_data, colWidths=[80, 60, 60, 150, 80, 80, 80, 100, 80])
    #     table.setStyle(TableStyle([
    #         ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    #         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    #         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    #         ('FONTNAME', (0, 0), (-1, -1), self.font_name),
    #         ('FONTSIZE', (0, 0), (-1, 0), 10),
    #         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    #         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    #         ('GRID', (0, 0), (-1, -1), 1, colors.black),
    #         ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    #     ]))
    #
    #     elements.append(table)
    #     
    #     try:
    #         doc.build(elements)
    #         return filename
    #     except Exception as e:
    #         print(f"Error generating PDF: {e}")
    #         return None
