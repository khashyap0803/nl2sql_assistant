# report_generator.py - Export and Reporting Module

## File Location
```
nl2sql_assistant/src/reports/report_generator.py
```

## Purpose
This module handles exporting query results to various formats:
- CSV (Comma-Separated Values)
- Excel (.xlsx)
- PDF (with optional charts)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ReportGenerator                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐                                       │
│  │ pandas DataFrame│──┬──> export_to_csv()  ──> .csv file  │
│  │ (Query Results) │  │                                    │
│  │                 │  ├──> export_to_excel() ──> .xlsx file│
│  │                 │  │                                    │
│  │                 │  └──> export_to_pdf()   ──> .pdf file │
│  └─────────────────┘                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Dependencies

```python
import pandas as pd          # DataFrame operations
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import openpyxl              # Excel export
import matplotlib.pyplot as plt  # Charts for PDF
```

---

## Class: ReportGenerator

### Method: `export_to_csv(df, filename)`

Exports DataFrame to CSV format.

```python
def export_to_csv(self, df, filename):
    df.to_csv(filename, index=False)
    return True
```

#### Output Format:
```csv
region,total_revenue
North,12500.00
South,11200.00
East,10800.00
West,9500.00
```

---

### Method: `export_to_excel(df, filename)`

Exports DataFrame to Excel with formatting.

```python
def export_to_excel(self, df, filename):
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Query Results')
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Query Results']
        for column in worksheet.columns:
            max_length = max(
                len(str(cell.value)) for cell in column
            )
            worksheet.column_dimensions[column[0].column_letter].width = max_length + 2
```

#### Features:
- Automatic column width adjustment
- No index column
- Sheet named "Query Results"

---

### Method: `export_to_pdf(df, filename, title)`

Exports DataFrame to PDF with optional chart.

```python
def export_to_pdf(self, df, filename, title="Query Results"):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    
    # Convert DataFrame to table data
    data = [df.columns.tolist()] + df.values.tolist()
    
    # Create table with styling
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    doc.build([table])
```

#### PDF Features:
- Professional table formatting
- Header row styling (purple background)
- Grid lines
- Letter page size

---

### Method: `generate_chart(df, chart_type, x_col, y_col, filename)`

Generates chart image for inclusion in reports.

```python
def generate_chart(self, df, chart_type, x_col, y_col, filename):
    plt.figure(figsize=(10, 6))
    
    if chart_type == 'bar':
        plt.bar(df[x_col], df[y_col])
    elif chart_type == 'line':
        plt.plot(df[x_col], df[y_col], marker='o')
    elif chart_type == 'pie':
        plt.pie(df[y_col], labels=df[x_col], autopct='%1.1f%%')
    
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(f'{y_col} by {x_col}')
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
```

#### Supported Chart Types:
- `bar`: Bar chart (vertical)
- `line`: Line chart with markers
- `pie`: Pie chart with percentages

---

## Usage in Application

### In main_window.py:

```python
from src.reports.report_generator import ReportGenerator

report_gen = ReportGenerator()

# After query execution
if current_df is not None:
    # User clicks "Export CSV"
    report_gen.export_to_csv(current_df, "sales_report.csv")
    
    # User clicks "Export Excel"
    report_gen.export_to_excel(current_df, "sales_report.xlsx")
    
    # User clicks "Export PDF"
    report_gen.export_to_pdf(current_df, "sales_report.pdf", 
                             title="Sales by Region")
```

---

## File Relationships

```
report_generator.py
    │
    ├──> External: pandas (DataFrame to file)
    │
    ├──> External: openpyxl (Excel export)
    │
    ├──> External: reportlab (PDF generation)
    │
    ├──> External: matplotlib (Charts)
    │
    └──> used by src/gui/main_window.py
```

---

## Design Decisions

| Decision | Why |
|----------|-----|
| pandas for CSV | Simple, handles edge cases |
| openpyxl for Excel | Pure Python, no Excel needed |
| reportlab for PDF | Professional output, no deps |
| matplotlib for charts | Standard Python charting |
| index=False | Cleaner output |
