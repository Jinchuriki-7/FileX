using FileX.Core.Enums;

namespace FileX.Core.Models;

public class ConversionTask
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string SourcePath { get; set; } = string.Empty;
    public string SourceFileName => Path.GetFileName(SourcePath);
    public string SourceExtension => Path.GetExtension(SourcePath).TrimStart('.').ToLowerInvariant();
    public string TargetFormat { get; set; } = string.Empty;
    public string OutputPath { get; set; } = string.Empty;
    public long FileSizeIn { get; set; }
    public long FileSizeOut { get; set; }
    public int Progress { get; set; }
    public ConversionStatus Status { get; set; } = ConversionStatus.Pending;
    public string ErrorMessage { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public TimeSpan Duration { get; set; } = TimeSpan.Zero;
}

