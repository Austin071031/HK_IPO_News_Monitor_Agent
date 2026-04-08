#!/usr/bin/env python3
"""
Convert Markdown to PDF using ReportLab (fallback method when Playwright is not available).
This provides a reliable PDF generation without browser dependencies.
"""

import os
import re
import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch, mm

class MarkdownToPDFConverter:
    """Convert Markdown files to PDF using ReportLab."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.register_fonts()
        
    def register_fonts(self):
        """Register Chinese fonts for ReportLab."""
        try:
            # Try to register a common Chinese font
            # SimHei is standard on many Windows systems
            font_path = "C:\\Windows\\Fonts\\simhei.ttf"
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('SimHei', font_path))
                self.font_name = 'SimHei'
            else:
                # Fallback or try another
                font_path = "C:\\Windows\\Fonts\\msyh.ttc"
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('MicrosoftYaHei', font_path))
                    self.font_name = 'MicrosoftYaHei'
                else:
                    print("Warning: Chinese font not found. Using Helvetica.")
                    self.font_name = 'Helvetica' # Fallback
        except Exception as e:
            print(f"Error registering font: {e}")
            self.font_name = 'Helvetica'
    
    def parse_markdown_tables(self, content):
        """Parse markdown tables from content."""
        tables = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Check for markdown table header
            if '|' in line and not line.startswith('#'):
                # Found a potential table start
                table_lines = []
                
                # Get header row
                table_lines.append(line)
                i += 1
                
                # Get separator row
                if i < len(lines) and '|' in lines[i] and '---' in lines[i]:
                    table_lines.append(lines[i])
                    i += 1
                
                # Get data rows
                while i < len(lines) and '|' in lines[i] and not lines[i].startswith('#'):
                    table_lines.append(lines[i])
                    i += 1
                
                if len(table_lines) >= 3:  # At least header, separator, and one data row
                    tables.append(table_lines)
                continue
            i += 1
        
        return tables
    
    def markdown_table_to_data(self, table_lines):
        """Convert markdown table lines to table data for ReportLab."""
        if not table_lines:
            return []
        
        # Parse header
        header_line = table_lines[0]
        headers = [cell.strip() for cell in header_line.split('|') if cell.strip()]
        
        # Parse data rows (skip separator line at index 1)
        data = [headers]
        for line in table_lines[2:]:
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if len(cells) == len(headers):
                data.append(cells)
        
        return data
    
    def convert_links_in_text(self, text):
        """Convert markdown links [text](url) to clickable links in PDF."""
        # Simple link conversion: [text](url) -> text (url)
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        return re.sub(pattern, r'\1 (\2)', text)
    
    def create_title_style(self):
        """Create title style for the PDF."""
        return ParagraphStyle(
            'Title',
            parent=self.styles['Heading1'],
            fontName=self.font_name,
            fontSize=16,
            alignment=1,  # Center
            spaceAfter=12
        )
    
    def create_heading_style(self, level):
        """Create heading style for different levels."""
        sizes = {1: 14, 2: 12, 3: 10, 4: 9, 5: 8, 6: 8}
        return ParagraphStyle(
            f'Heading{level}',
            parent=self.styles[f'Heading{level}'],
            fontName=self.font_name,
            fontSize=sizes.get(level, 10),
            spaceBefore=10,
            spaceAfter=6
        )
    
    def create_normal_style(self):
        """Create normal text style."""
        return ParagraphStyle(
            'Normal',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=9,
            leading=11
        )
    
    def create_table_style(self, num_cols):
        """Create table style."""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F81BD')),  # Blue header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 9),  # Header font size
            ('FONTSIZE', (0, 1), (-1, -1), 8),  # Data font size
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ])
    
    def process_markdown_content(self, content):
        """Process markdown content and extract sections."""
        elements = []
        
        # Parse markdown
        lines = content.split('\n')
        current_paragraph = []
        in_list = False
        
        for line in lines:
            stripped = line.strip()
            
            # Check for headings
            if stripped.startswith('# '):
                if current_paragraph:
                    elements.append(Paragraph(' '.join(current_paragraph), self.create_normal_style()))
                    current_paragraph = []
                elements.append(Paragraph(stripped[2:], self.create_title_style()))
            
            elif stripped.startswith('## '):
                if current_paragraph:
                    elements.append(Paragraph(' '.join(current_paragraph), self.create_normal_style()))
                    current_paragraph = []
                elements.append(Paragraph(stripped[3:], self.create_heading_style(2)))
            
            elif stripped.startswith('### '):
                if current_paragraph:
                    elements.append(Paragraph(' '.join(current_paragraph), self.create_normal_style()))
                    current_paragraph = []
                elements.append(Paragraph(stripped[4:], self.create_heading_style(3)))
            
            # Check for horizontal rule
            elif stripped.startswith('---'):
                if current_paragraph:
                    elements.append(Paragraph(' '.join(current_paragraph), self.create_normal_style()))
                    current_paragraph = []
                elements.append(Spacer(1, 12))
            
            # Check for table
            elif '|' in stripped and not stripped.startswith('#'):
                # Handle table separately
                if current_paragraph:
                    elements.append(Paragraph(' '.join(current_paragraph), self.create_normal_style()))
                    current_paragraph = []
                
                # Find the complete table
                table_lines = []
                idx = lines.index(line)
                while idx < len(lines) and '|' in lines[idx]:
                    table_lines.append(lines[idx])
                    idx += 1
                
                # Convert table
                table_data = self.markdown_table_to_data(table_lines)
                if table_data and len(table_data) > 1:
                    # Calculate column widths
                    col_widths = [min(2*inch, max(1*inch, len(max(col, key=len)) * 3.5)) for col in zip(*table_data)]
                    
                    # Create table
                    table = Table(table_data, colWidths=col_widths)
                    table.setStyle(self.create_table_style(len(table_data[0])))
                    elements.append(table)
                    elements.append(Spacer(1, 12))
            
            # Normal text
            elif stripped:
                # Convert links in text
                converted_line = self.convert_links_in_text(stripped)
                current_paragraph.append(converted_line)
            
            # Empty line - end of paragraph
            elif current_paragraph:
                elements.append(Paragraph(' '.join(current_paragraph), self.create_normal_style()))
                current_paragraph = []
                elements.append(Spacer(1, 6))
        
        # Add any remaining paragraph
        if current_paragraph:
            elements.append(Paragraph(' '.join(current_paragraph), self.create_normal_style()))
        
        return elements
    
    def convert(self, md_file_path, pdf_file_path):
        """Convert markdown file to PDF."""
        try:
            # Read markdown file
            with open(md_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_file_path,
                pagesize=landscape(A4),
                rightMargin=20*mm,
                leftMargin=20*mm,
                topMargin=20*mm,
                bottomMargin=20*mm
            )
            
            # Process content
            elements = self.process_markdown_content(content)
            
            # Add generation timestamp
            timestamp = Paragraph(
                f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ParagraphStyle(
                    'Timestamp',
                    parent=self.styles['Normal'],
                    fontName=self.font_name,
                    fontSize=8,
                    alignment=2,  # Right
                    textColor=colors.grey
                )
            )
            elements.insert(0, timestamp)
            elements.insert(0, Spacer(1, 10))
            
            # Build PDF
            doc.build(elements)
            
            print(f"Successfully converted {md_file_path} to {pdf_file_path}")
            return True
            
        except Exception as e:
            print(f"Error converting markdown to PDF: {e}")
            import traceback
            traceback.print_exc()
            return False

def convert_md_to_pdf_reportlab(md_file_path, pdf_file_path):
    """Main conversion function."""
    converter = MarkdownToPDFConverter()
    return converter.convert(md_file_path, pdf_file_path)

if __name__ == "__main__":
    # Test conversion
    import sys
    if len(sys.argv) != 3:
        print("Usage: python convert_md_to_pdf_reportlab.py <input.md> <output.pdf>")
        sys.exit(1)
    
    input_md = sys.argv[1]
    output_pdf = sys.argv[2]
    
    if convert_md_to_pdf_reportlab(input_md, output_pdf):
        print(f"PDF created: {output_pdf}")
    else:
        print("Conversion failed.")