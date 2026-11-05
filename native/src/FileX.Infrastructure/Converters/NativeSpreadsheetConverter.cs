using System.IO;
using System.Text;
using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Spreadsheet;
using FileX.Core.Interfaces;

namespace FileX.Infrastructure.Converters;

public class NativeSpreadsheetConverter : IConversionEngine
{
    public bool CanHandle(string sourceExtension, string targetExtension)
    {
        var src = sourceExtension.TrimStart('.').ToLowerInvariant();
        var tgt = targetExtension.TrimStart('.').ToLowerInvariant();
        return (src == "csv" || src == "xlsx") && (tgt == "csv" || tgt == "xlsx" || tgt == "pdf");
    }

    public Task<string> ConvertAsync(
        string sourcePath,
        string outputPath,
        string targetExtension,
        IProgress<int>? progress = null,
        CancellationToken cancellationToken = default)
    {
        return Task.Run(() =>
        {
            progress?.Report(10);
            var src = Path.GetExtension(sourcePath).TrimStart('.').ToLowerInvariant();
            var tgt = targetExtension.TrimStart('.').ToLowerInvariant();

            var dir = Path.GetDirectoryName(outputPath);
            if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);

            if (src == "csv" && tgt == "xlsx")
            {
                ConvertCsvToXlsx(sourcePath, outputPath);
            }
            else if (src == "xlsx" && tgt == "csv")
            {
                ConvertXlsxToCsv(sourcePath, outputPath);
            }
            else if (tgt == "pdf")
            {
                var text = src == "csv" ? File.ReadAllText(sourcePath) : ExtractTextFromXlsx(sourcePath);
                NativePdfConverter.CreateSimplePdfFromText(text, outputPath);
            }

            progress?.Report(100);
            return outputPath;
        }, cancellationToken);
    }

    private static void ConvertCsvToXlsx(string csvPath, string xlsxPath)
    {
        using var document = SpreadsheetDocument.Create(xlsxPath, SpreadsheetDocumentType.Workbook);
        var workbookPart = document.AddWorkbookPart();
        workbookPart.Workbook = new Workbook();

        var worksheetPart = workbookPart.AddNewPart<WorksheetPart>();
        var sheetData = new SheetData();
        worksheetPart.Worksheet = new Worksheet(sheetData);

        var sheets = workbookPart.Workbook.AppendChild(new Sheets());
        var sheet = new Sheet
        {
            Id = workbookPart.GetIdOfPart(worksheetPart),
            SheetId = 1,
            Name = "Sheet1"
        };
        sheets.Append(sheet);

        uint rowIndex = 1;
        foreach (var line in File.ReadLines(csvPath, Encoding.UTF8))
        {
            var row = new Row { RowIndex = rowIndex };
            var cols = line.Split(',');
            for (int i = 0; i < cols.Length; i++)
            {
                var cell = new Cell
                {
                    DataType = CellValues.String,
                    CellValue = new CellValue(cols[i].Trim('\"'))
                };
                row.Append(cell);
            }
            sheetData.Append(row);
            rowIndex++;
        }

        workbookPart.Workbook.Save();
    }

    private static void ConvertXlsxToCsv(string xlsxPath, string csvPath)
    {
        var text = ExtractTextFromXlsx(xlsxPath);
        File.WriteAllText(csvPath, text, Encoding.UTF8);
    }

    private static string ExtractTextFromXlsx(string xlsxPath)
    {
        var sb = new StringBuilder();
        using var doc = SpreadsheetDocument.Open(xlsxPath, false);
        var workbookPart = doc.WorkbookPart;
        if (workbookPart == null) return string.Empty;

        var sharedStringPart = workbookPart.SharedStringTablePart;
        var strings = sharedStringPart?.SharedStringTable.Elements<SharedStringItem>().Select(s => s.InnerText).ToList();

        var worksheetPart = workbookPart.WorksheetParts.FirstOrDefault();
        if (worksheetPart != null)
        {
            var sheetData = worksheetPart.Worksheet.Elements<SheetData>().FirstOrDefault();
            if (sheetData != null)
            {
                foreach (var row in sheetData.Elements<Row>())
                {
                    var values = new List<string>();
                    foreach (var cell in row.Elements<Cell>())
                    {
                        var val = cell.CellValue?.Text ?? string.Empty;
                        if (cell.DataType != null && cell.DataType.Value == CellValues.SharedString)
                        {
                            if (int.TryParse(val, out int idx) && strings != null && idx < strings.Count)
                            {
                                val = strings[idx];
                            }
                        }
                        values.Add($"\"{val.Replace("\"", "\"\"")}\"");
                    }
                    sb.AppendLine(string.Join(",", values));
                }
            }
        }

        return sb.ToString();
    }
}

