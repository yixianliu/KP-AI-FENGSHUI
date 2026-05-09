def get_exporter(format_type):
    if format_type == 'csv':
        from ui.export.csv_exporter import CsvExporter
        return CsvExporter
    elif format_type == 'excel':
        from ui.export.excel_exporter import ExcelExporter
        return ExcelExporter
    elif format_type == 'pdf':
        from ui.export.pdf_exporter import PdfExporter
        return PdfExporter
    else:
        from ui.export.csv_exporter import CsvExporter
        return CsvExporter

__all__ = ['get_exporter']
