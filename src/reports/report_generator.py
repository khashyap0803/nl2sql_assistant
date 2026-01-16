import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import io
import os


class ReportGenerator:

    def __init__(self):
        self.current_figure = None
        print("[OK] Report Generator initialized")

    def create_chart(self, df, chart_type='auto', title='Query Results'):
        if df is None or df.empty:
            print("[WARNING] No data to visualize")
            return None

        try:
            fig = Figure(figsize=(10, 6))
            ax = fig.add_subplot(111)

            if chart_type == 'auto':
                if len(df.columns) == 2:
                    chart_type = 'bar'
                elif 'date' in df.columns[0].lower():
                    chart_type = 'line'
                else:
                    chart_type = 'bar'

            if chart_type == 'bar' and len(df.columns) >= 2:
                df.plot(kind='bar', ax=ax, x=df.columns[0], y=df.columns[1], legend=False)
                ax.set_xlabel(df.columns[0])
                ax.set_ylabel(df.columns[1] if len(df.columns) > 1 else 'Value')

            elif chart_type == 'line' and len(df.columns) >= 2:
                df.plot(kind='line', ax=ax, x=df.columns[0], y=df.columns[1], legend=False)
                ax.set_xlabel(df.columns[0])
                ax.set_ylabel(df.columns[1] if len(df.columns) > 1 else 'Value')

            elif chart_type == 'pie' and len(df) <= 10 and len(df.columns) >= 2:
                ax.pie(df[df.columns[1]], labels=df[df.columns[0]], autopct='%1.1f%%')
                ax.axis('equal')
            else:
                df.plot(kind='bar', ax=ax, legend=True)

            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            fig.tight_layout()

            self.current_figure = fig
            return fig

        except Exception as e:
            print(f"[ERROR] Chart creation error: {e}")
            return None

    def save_chart(self, filename, dpi=300):
        if self.current_figure is None:
            print("[WARNING] No chart to save")
            return False

        try:
            self.current_figure.savefig(filename, dpi=dpi, bbox_inches='tight')
            print(f"[OK] Chart saved to {filename}")
            return True
        except Exception as e:
            print(f"[ERROR] Error saving chart: {e}")
            return False

    def export_to_csv(self, df, filename):
        try:
            df.to_csv(filename, index=False)
            print(f"[OK] Data exported to {filename}")
            return True
        except Exception as e:
            print(f"[ERROR] CSV export error: {e}")
            return False

    def export_to_excel(self, df, filename):
        try:
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"[OK] Data exported to {filename}")
            return True
        except Exception as e:
            print(f"[ERROR] Excel export error: {e}")
            return False

    def export_to_pdf(self, df, filename):
        try:
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors

            doc = SimpleDocTemplate(filename, pagesize=landscape(letter))
            elements = []

            styles = getSampleStyleSheet()
            title = Paragraph("Query Results", styles['Title'])
            elements.append(title)

            data = [df.columns.tolist()] + df.values.tolist()

            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            elements.append(table)
            doc.build(elements)

            print(f"[OK] PDF exported to {filename}")
            return True
        except Exception as e:
            print(f"[ERROR] PDF export error: {e}")
            return False


def test_report_generator():
    print("Testing Report Generator...")

    df = pd.DataFrame({
        'Product': ['Widget', 'Gadget', 'Gizmo', 'Tool', 'Device'],
        'Sales': [1500, 2300, 1800, 2100, 1900]
    })

    rg = ReportGenerator()

    fig = rg.create_chart(df, chart_type='bar', title='Sales by Product')
    if fig:
        print("[OK] Chart created successfully")

    rg.export_to_csv(df, 'test_export.csv')

    print("[OK] Report Generator tests complete")


if __name__ == "__main__":
    test_report_generator()
