using System.IO;
using System.Text;
using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using FileX.Core.Interfaces;
using Markdig;

namespace FileX.Infrastructure.Converters;

public class NativeDocumentConverter : IConversionEngine
{
    private static readonly HashSet<string> DocumentExts = new(StringComparer.OrdinalIgnoreCase)
    {
        "docx", "doc", "txt", "html", "htm", "md", "rtf"
    };

    public bool CanHandle(string sourceExtension, string targetExtension)
    {
        var src = sourceExtension.TrimStart('.').ToLowerInvariant();
        var tgt = targetExtension.TrimStart('.').ToLowerInvariant();
        return DocumentExts.Contains(src) && (DocumentExts.Contains(tgt) || tgt == "pdf");
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

            // Read source text or extract from docx
            string textContent;
            if (src == "docx")
            {
                textContent = ExtractTextFromDocx(sourcePath);
            }
            else if (src == "md")
            {
                var md = File.ReadAllText(sourcePath);
                if (tgt == "html")
                {
                    var pipeline = new MarkdownPipelineBuilder().UseAdvancedExtensions().Build();
                    var html = Markdown.ToHtml(md, pipeline);
                    var fullHtml = $"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Converted Document</title><style>body {{ font-family: Segoe UI, sans-serif; margin: 40px; line-height: 1.6; color: #333; }}</style></head><body>{html}</body></html>";
                    File.WriteAllText(outputPath, fullHtml, Encoding.UTF8);
                    progress?.Report(100);
                    return outputPath;
                }
                textContent = md;
            }
            else
            {
                textContent = File.ReadAllText(sourcePath);
            }

            progress?.Report(50);

            // Output writing
            if (tgt == "txt")
            {
                File.WriteAllText(outputPath, textContent, Encoding.UTF8);
            }
            else if (tgt == "html")
            {
                var body = System.Net.WebUtility.HtmlEncode(textContent).Replace("\n", "<br/>\n");
                var html = $"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Document</title><style>body {{ font-family: Segoe UI, sans-serif; margin: 40px; line-height: 1.6; }}</style></head><body>{body}</body></html>";
                File.WriteAllText(outputPath, html, Encoding.UTF8);
            }
            else if (tgt == "md")
            {
                File.WriteAllText(outputPath, textContent, Encoding.UTF8);
            }
            else if (tgt == "docx")
            {
                CreateDocxFromText(textContent, outputPath);
            }
            else if (tgt == "pdf")
            {
                NativePdfConverter.CreateSimplePdfFromText(textContent, outputPath);
            }

            progress?.Report(100);
            return outputPath;
        }, cancellationToken);
    }

    private static string ExtractTextFromDocx(string docxPath)
    {
        var sb = new StringBuilder();
        using var doc = WordprocessingDocument.Open(docxPath, false);
        var body = doc.MainDocumentPart?.Document?.Body;
        if (body != null)
        {
            foreach (var para in body.Elements<Paragraph>())
            {
                sb.AppendLine(para.InnerText);
            }
        }
        return sb.ToString();
    }

    private static void CreateDocxFromText(string text, string outputPath)
    {
        using var doc = WordprocessingDocument.Create(outputPath, WordprocessingDocumentType.Document);
        var mainPart = doc.AddMainDocumentPart();
        mainPart.Document = new Document();
        var body = mainPart.Document.AppendChild(new Body());

        foreach (var line in text.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None))
        {
            var p = body.AppendChild(new Paragraph());
            var r = p.AppendChild(new Run());
            r.AppendChild(new Text(line));
        }
        doc.Save();
    }
}

