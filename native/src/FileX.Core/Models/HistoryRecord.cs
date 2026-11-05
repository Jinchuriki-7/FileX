namespace FileX.Core.Models;

public class HistoryRecord
{
    public long Id { get; set; }
    public string SourcePath { get; set; } = string.Empty;
    public string SourceFileName => System.IO.Path.GetFileName(SourcePath);
    public string SourceFormat { get; set; } = string.Empty;
    public string OutputPath { get; set; } = string.Empty;
    public string OutputFormat { get; set; } = string.Empty;
    public string Status { get; set; } = "success";
    public string ErrorMessage { get; set; } = string.Empty;
    public long FileSizeIn { get; set; }
    public long FileSizeOut { get; set; }
    public long DurationMs { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.Now;

    public string FormattedSizeIn => FormatBytes(FileSizeIn);
    public string FormattedSizeOut => FormatBytes(FileSizeOut);

    public static string FormatBytes(long bytes)
    {
        string[] suffixes = { "B", "KB", "MB", "GB", "TB" };
        int counter = 0;
        decimal number = bytes;
        while (Math.Round(number / 1024) >= 1)
        {
            number /= 1024;
            counter++;
        }
        return $"{number:n1} {suffixes[counter]}";
    }
}

