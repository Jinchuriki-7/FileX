using System.IO;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using FileX.Core.Interfaces;

namespace FileX.Infrastructure.Converters;

public class NativeImageConverter : IConversionEngine
{
    private static readonly HashSet<string> Supported = new(StringComparer.OrdinalIgnoreCase)
    {
        "png", "jpg", "jpeg", "bmp", "gif", "tiff", "tif", "ico"
    };

    public bool CanHandle(string sourceExtension, string targetExtension)
    {
        var src = sourceExtension.TrimStart('.').ToLowerInvariant();
        var tgt = targetExtension.TrimStart('.').ToLowerInvariant();
        return Supported.Contains(src) && (Supported.Contains(tgt) || tgt == "pdf");
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
            progress?.Report(15);
            var tgt = targetExtension.TrimStart('.').ToLowerInvariant();

            using var inputStream = new FileStream(sourcePath, FileMode.Open, FileAccess.Read, FileShare.Read);
            var decoder = BitmapDecoder.Create(inputStream, BitmapCreateOptions.PreservePixelFormat, BitmapCacheOption.OnLoad);

            if (decoder.Frames.Count == 0)
                throw new InvalidOperationException("Image contains no valid frames.");

            var frame = decoder.Frames[0];
            progress?.Report(40);

            var dir = Path.GetDirectoryName(outputPath);
            if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);

            if (tgt == "pdf")
            {
                // Simple Image-to-PDF embedding
                ConvertImageToPdf(frame, outputPath);
                progress?.Report(100);
                return outputPath;
            }

            BitmapEncoder encoder = tgt switch
            {
                "png" => new PngBitmapEncoder(),
                "jpg" or "jpeg" => new JpegBitmapEncoder { QualityLevel = 92 },
                "bmp" => new BmpBitmapEncoder(),
                "gif" => new GifBitmapEncoder(),
                "tiff" or "tif" => new TiffBitmapEncoder(),
                "ico" => new PngBitmapEncoder(), // Windows icons wrap PNG frames
                _ => new PngBitmapEncoder()
            };

            progress?.Report(70);

            // If encoding to JPEG, ensure frame does not have transparent alpha
            BitmapFrame frameToSave = frame;
            if ((tgt == "jpg" || tgt == "jpeg" || tgt == "bmp") &&
                (frame.Format == PixelFormats.Bgra32 || frame.Format == PixelFormats.Rgba64 || frame.Format == PixelFormats.Pbgra32))
            {
                var formattedBitmap = new FormatConvertedBitmap();
                formattedBitmap.BeginInit();
                formattedBitmap.Source = frame;
                formattedBitmap.DestinationFormat = PixelFormats.Bgr32;
                formattedBitmap.EndInit();
                frameToSave = BitmapFrame.Create(formattedBitmap);
            }

            encoder.Frames.Add(frameToSave);

            using var outputStream = new FileStream(outputPath, FileMode.Create, FileAccess.Write, FileShare.None);
            encoder.Save(outputStream);

            progress?.Report(100);
            return outputPath;
        }, cancellationToken);
    }

    private static void ConvertImageToPdf(BitmapSource image, string outputPath)
    {
        // Simple minimal native PDF generation with embedded image
        // Converts image to JPEG byte array and embeds into a valid standard PDF stream
        using var ms = new MemoryStream();
        var jpegEncoder = new JpegBitmapEncoder { QualityLevel = 90 };
        jpegEncoder.Frames.Add(BitmapFrame.Create(image));
        jpegEncoder.Save(ms);
        var jpgBytes = ms.ToArray();

        int width = (int)image.PixelWidth;
        int height = (int)image.PixelHeight;

        using var fs = new FileStream(outputPath, FileMode.Create, FileAccess.Write);
        using var writer = new StreamWriter(fs, System.Text.Encoding.ASCII);

        var offsets = new List<long>();

        writer.WriteLine("%PDF-1.4");
        writer.Flush();

        // 1 0 obj: Catalog
        offsets.Add(fs.Position);
        writer.WriteLine("1 0 obj");
        writer.WriteLine("<< /Type /Catalog /Pages 2 0 R >>");
        writer.WriteLine("endobj");
        writer.Flush();

        // 2 0 obj: Pages
        offsets.Add(fs.Position);
        writer.WriteLine("2 0 obj");
        writer.WriteLine("<< /Type /Pages /Kids [3 0 R] /Count 1 >>");
        writer.WriteLine("endobj");
        writer.Flush();

        // 3 0 obj: Page
        offsets.Add(fs.Position);
        writer.WriteLine("3 0 obj");
        writer.WriteLine($"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] /Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >>");
        writer.WriteLine("endobj");
        writer.Flush();

        // 4 0 obj: Image XObject
        offsets.Add(fs.Position);
        writer.WriteLine("4 0 obj");
        writer.WriteLine($"<< /Type /XObject /Subtype /Image /Width {width} /Height {height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length {jpgBytes.Length} >>");
        writer.WriteLine("stream");
        writer.Flush();
        fs.Write(jpgBytes, 0, jpgBytes.Length);
        writer.WriteLine();
        writer.WriteLine("endstream");
        writer.WriteLine("endobj");
        writer.Flush();

        // 5 0 obj: Content stream (drawing the image full page)
        string content = $"q {width} 0 0 {height} 0 0 cm /Im0 Do Q";
        byte[] contentBytes = System.Text.Encoding.ASCII.GetBytes(content);
        offsets.Add(fs.Position);
        writer.WriteLine("5 0 obj");
        writer.WriteLine($"<< /Length {contentBytes.Length} >>");
        writer.WriteLine("stream");
        writer.Flush();
        fs.Write(contentBytes, 0, contentBytes.Length);
        writer.WriteLine();
        writer.WriteLine("endstream");
        writer.WriteLine("endobj");
        writer.Flush();

        // Cross-reference table
        long xrefPos = fs.Position;
        writer.WriteLine("xref");
        writer.WriteLine($"0 {offsets.Count + 1}");
        writer.WriteLine("0000000000 65535 f ");
        foreach (var offset in offsets)
        {
            writer.WriteLine($"{offset:D10} 00000 n ");
        }

        // Trailer
        writer.WriteLine("trailer");
        writer.WriteLine($"<< /Size {offsets.Count + 1} /Root 1 0 R >>");
        writer.WriteLine("startxref");
        writer.WriteLine(xrefPos);
        writer.WriteLine("%%EOF");
        writer.Flush();
    }
}

