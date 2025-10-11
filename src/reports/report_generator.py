"""
Report Generator Module
Creates visualizations and exports data to various formats
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import io
import os


class ReportGenerator:
    """Generate reports, charts, and exports from query results"""

    def __init__(self):
        """Initialize report generator"""
        self.current_figure = None
        print("✓ Report Generator initialized")

    def create_chart(self, df, chart_type='auto', title='Query Results'):
        """
        Create a chart from DataFrame

        Args:
            df: pandas DataFrame with query results
            chart_type: 'auto', 'bar', 'line', 'pie'
            title: Chart title

        Returns:
            matplotlib Figure object or None
        """
        if df is None or df.empty:
            print("⚠️  No data to visualize")
            return None

        try:
            fig = Figure(figsize=(10, 6))
            ax = fig.add_subplot(111)

            # Auto-detect chart type if needed
            if chart_type == 'auto':
                if len(df.columns) == 2:
                    chart_type = 'bar'
                elif 'date' in df.columns[0].lower():
                    chart_type = 'line'
                else:
                    chart_type = 'bar'

            # Create appropriate chart
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
                # Default to bar chart
                df.plot(kind='bar', ax=ax, legend=True)

            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            fig.tight_layout()

            self.current_figure = fig
            return fig

        except Exception as e:
            print(f"❌ Chart creation error: {e}")
            return None

    def save_chart(self, filename, dpi=300):
        """Save current chart to file"""
        if self.current_figure is None:
            print("⚠️  No chart to save")
            return False

        try:
            self.current_figure.savefig(filename, dpi=dpi, bbox_inches='tight')
            print(f"✓ Chart saved to {filename}")
            return True
        except Exception as e:
            print(f"❌ Error saving chart: {e}")
            return False

    def export_to_csv(self, df, filename):
        """Export DataFrame to CSV"""
        try:
            df.to_csv(filename, index=False)
            print(f"✓ Data exported to {filename}")
            return True
        except Exception as e:
            print(f"❌ CSV export error: {e}")
            return False

    def export_to_excel(self, df, filename):
        """Export DataFrame to Excel"""
        try:
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"✓ Data exported to {filename}")
            return True
        except Exception as e:
            print(f"❌ Excel export error: {e}")
            return False

    def export_to_pdf(self, df, filename):
        """Export DataFrame to PDF using reportlab"""
        try:
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors

            doc = SimpleDocTemplate(filename, pagesize=landscape(letter))
            elements = []

            # Add title
            styles = getSampleStyleSheet()
            title = Paragraph("Query Results", styles['Title'])
            elements.append(title)

            # Convert DataFrame to list for table
            data = [df.columns.tolist()] + df.values.tolist()

            # Create table
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

            print(f"✓ PDF exported to {filename}")
            return True
        except Exception as e:
            print(f"❌ PDF export error: {e}")
            return False


# Test function
def test_report_generator():
    """Test report generation"""
    print("Testing Report Generator...")

    # Create sample data
    df = pd.DataFrame({
        'Product': ['Widget', 'Gadget', 'Gizmo', 'Tool', 'Device'],
        'Sales': [1500, 2300, 1800, 2100, 1900]
    })

    rg = ReportGenerator()

    # Test chart creation
    fig = rg.create_chart(df, chart_type='bar', title='Sales by Product')
    if fig:
        print("✓ Chart created successfully")

    # Test exports
    rg.export_to_csv(df, 'test_export.csv')

    print("✓ Report Generator tests complete")


if __name__ == "__main__":
    test_report_generator()

