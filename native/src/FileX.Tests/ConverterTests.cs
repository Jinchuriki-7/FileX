using System.IO;
using System.Text;
using FileX.Core.Enums;
using FileX.Core.Models;
using FileX.Infrastructure;
using FileX.Infrastructure.Converters;
using FileX.Infrastructure.Persistence;
using Xunit;

namespace FileX.Tests;

public class ConverterTests
{
    private readonly string _testDir;

    public ConverterTests()
    {
        _testDir = Path.Combine(Path.GetTempPath(), "FileX_Tests_" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(_testDir);
    }

    [Fact]
    public void FormatRegistry_ContainsAllRequiredCategories()
    {
        var reg = new FormatRegistry();
        Assert.True(reg.IsSupported("png"));
        Assert.True(reg.IsSupported("docx"));
        Assert.True(reg.IsSupported("pdf"));
        Assert.True(reg.IsSupported("xlsx"));
        Assert.True(reg.IsSupported("mp3"));
        Assert.True(reg.IsSupported("mp4"));

        Assert.Equal(FileCategory.Image, reg.GetCategory("jpg"));
        Assert.Equal(FileCategory.Pdf, reg.GetCategory("pdf"));
        Assert.Equal(FileCategory.Document, reg.GetCategory("docx"));
        Assert.Equal(FileCategory.Spreadsheet, reg.GetCategory("xlsx"));
        Assert.Equal(FileCategory.Audio, reg.GetCategory("mp3"));
        Assert.Equal(FileCategory.Video, reg.GetCategory("mp4"));
    }

    [Fact]
    public async Task DocumentConverter_ConvertsTxtToDocxAndPdf()
    {
        var docConverter = new NativeDocumentConverter();
        var txtPath = Path.Combine(_testDir, "test.txt");
        await File.WriteAllTextAsync(txtPath, "Hello Native FileX!\nThis is a C# .NET 10 document conversion test.");

        // Convert TXT -> DOCX
        var docxPath = Path.Combine(_testDir, "test.docx");
        var resDocx = await docConverter.ConvertAsync(txtPath, docxPath, "docx");
        Assert.True(File.Exists(resDocx));
        Assert.True(new FileInfo(resDocx).Length > 0);

        // Convert TXT -> PDF
        var pdfPath = Path.Combine(_testDir, "test.pdf");
        var resPdf = await docConverter.ConvertAsync(txtPath, pdfPath, "pdf");
        Assert.True(File.Exists(resPdf));
        Assert.True(new FileInfo(resPdf).Length > 0);
    }

    [Fact]
    public async Task SpreadsheetConverter_ConvertsCsvToXlsx()
    {
        var sheetConverter = new NativeSpreadsheetConverter();
        var csvPath = Path.Combine(_testDir, "data.csv");
        await File.WriteAllTextAsync(csvPath, "ID,Product,Price\n1,Widget,19.99\n2,Gadget,29.99\n");

        var xlsxPath = Path.Combine(_testDir, "data.xlsx");
        var resXlsx = await sheetConverter.ConvertAsync(csvPath, xlsxPath, "xlsx");
        Assert.True(File.Exists(resXlsx));
        Assert.True(new FileInfo(resXlsx).Length > 0);
    }

    [Fact]
    public async Task SqliteHistory_CrudOperations_WorkCorrectly()
    {
        var dbPath = Path.Combine(_testDir, "history_test.db");
        var repo = new SqliteHistoryRepository(dbPath);

        var id = await repo.AddAsync(new HistoryRecord
        {
            SourcePath = @"C:\dummy\file.png",
            SourceFormat = "png",
            OutputPath = @"C:\dummy\file.jpg",
            OutputFormat = "jpg",
            FileSizeIn = 1024,
            Status = "pending"
        });

        Assert.True(id > 0);

        await repo.UpdateStatusAsync(id, "success", fileSizeOut: 2048, durationMs: 120);

        var all = await repo.GetAllAsync();
        Assert.Single(all);
        Assert.Equal("success", all[0].Status);
        Assert.Equal(2048, all[0].FileSizeOut);

        var stats = await repo.GetStatsAsync();
        Assert.Equal(1, stats.Total);
        Assert.Equal(1, stats.SuccessCount);
    }
}

