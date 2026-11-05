using System.IO;
using FileX.Core.Enums;
using FileX.Core.Interfaces;
using FileX.Core.Models;

namespace FileX.Infrastructure;

public class FileDetector : IFileDetector
{
    private readonly IFormatRegistry _formatRegistry;

    public FileDetector(IFormatRegistry formatRegistry)
    {
        _formatRegistry = formatRegistry;
    }

    public (string extension, FileCategory category, FormatDefinition? format) Detect(string filePath)
    {
        if (string.IsNullOrWhiteSpace(filePath) || !File.Exists(filePath))
        {
            return (string.Empty, FileCategory.Unknown, null);
        }

        string detectedExt = Path.GetExtension(filePath).TrimStart('.').ToLowerInvariant();

        // Verify magic bytes for major formats
        try
        {
            using var stream = new FileStream(filePath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
            var header = new byte[16];
            int bytesRead = stream.Read(header, 0, header.Length);

            if (bytesRead >= 4)
            {
                // PDF: %PDF
                if (header[0] == 0x25 && header[1] == 0x50 && header[2] == 0x44 && header[3] == 0x46)
                {
                    detectedExt = "pdf";
                }
                // PNG: 89 50 4E 47
                else if (header[0] == 0x89 && header[1] == 0x50 && header[2] == 0x4E && header[3] == 0x47)
                {
                    detectedExt = "png";
                }
                // JPEG: FF D8 FF
                else if (header[0] == 0xFF && header[1] == 0xD8 && header[2] == 0xFF)
                {
                    detectedExt = "jpg";
                }
                // GIF: GIF87a or GIF89a
                else if (header[0] == 0x47 && header[1] == 0x49 && header[2] == 0x46)
                {
                    detectedExt = "gif";
                }
                // BMP: 42 4D
                else if (header[0] == 0x42 && header[1] == 0x4D)
                {
                    detectedExt = "bmp";
                }
            }
        }
        catch
        {
            // Fall back to extension if stream cannot be read
        }

        var format = _formatRegistry.GetFormat(detectedExt);
        var category = format?.Category ?? FileCategory.Unknown;

        return (detectedExt, category, format);
    }
}
