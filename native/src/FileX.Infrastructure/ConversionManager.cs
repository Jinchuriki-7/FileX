using System.IO;
using FileX.Core.Enums;
using FileX.Core.Interfaces;
using FileX.Core.Models;
using FileX.Infrastructure.Converters;

namespace FileX.Infrastructure;

public class ConversionManager
{
    private readonly ISettingsService _settingsService;
    private readonly IHistoryRepository _historyRepository;
    private readonly IFormatRegistry _formatRegistry;
    private readonly IFileDetector _fileDetector;
    private readonly List<IConversionEngine> _engines = new();

    public event Action<ConversionTask>? ConversionStarted;
    public event Action<ConversionTask, int>? ConversionProgress;
    public event Action<ConversionTask>? ConversionCompleted;
    public event Action<ConversionTask, string>? ConversionFailed;

    public ConversionManager(
        ISettingsService settingsService,
        IHistoryRepository historyRepository,
        IFormatRegistry formatRegistry,
        IFileDetector fileDetector)
    {
        _settingsService = settingsService;
        _historyRepository = historyRepository;
        _formatRegistry = formatRegistry;
        _fileDetector = fileDetector;

        // Register all native engines
        _engines.Add(new NativeImageConverter());
        _engines.Add(new NativeDocumentConverter());
        _engines.Add(new NativePdfConverter());
        _engines.Add(new NativeSpreadsheetConverter());
        _engines.Add(new NativeMediaConverter());
    }

    public async Task<ConversionTask> ConvertAsync(
        string sourcePath,
        string targetFormat,
        string? outputDir = null,
        CancellationToken cancellationToken = default)
    {
        var task = new ConversionTask
        {
            SourcePath = sourcePath,
            TargetFormat = targetFormat.TrimStart('.').ToLowerInvariant(),
            FileSizeIn = File.Exists(sourcePath) ? new FileInfo(sourcePath).Length : 0,
            Status = ConversionStatus.Converting,
            Progress = 5
        };

        ConversionStarted?.Invoke(task);

        var stopwatch = System.Diagnostics.Stopwatch.StartNew();

        // Add pending record in history
        var historyRecord = new HistoryRecord
        {
            SourcePath = task.SourcePath,
            SourceFormat = task.SourceExtension,
            OutputPath = string.Empty,
            OutputFormat = task.TargetFormat,
            Status = "pending",
            FileSizeIn = task.FileSizeIn,
            CreatedAt = DateTime.Now
        };

        long historyId = 0;
        try
        {
            historyId = await _historyRepository.AddAsync(historyRecord, cancellationToken);
        }
        catch { /* Non-fatal */ }

        try
        {
            var srcExt = task.SourceExtension;
            var tgtExt = task.TargetFormat;

            var engine = _engines.FirstOrDefault(e => e.CanHandle(srcExt, tgtExt));
            if (engine == null)
            {
                throw new NotSupportedException($"No conversion engine available for {srcExt.ToUpperInvariant()} → {tgtExt.ToUpperInvariant()}");
            }

            // Determine output directory
            var targetDir = !string.IsNullOrEmpty(outputDir)
                ? outputDir
                : _settingsService.Settings.OutputFolder;

            Directory.CreateDirectory(targetDir);

            // Determine unique output path
            var outPath = BuildOutputPath(sourcePath, tgtExt, targetDir, _settingsService.Settings.OverwriteExisting);
            task.OutputPath = outPath;

            var progressReporter = new Progress<int>(pct =>
            {
                task.Progress = pct;
                ConversionProgress?.Invoke(task, pct);
            });

            var resultPath = await engine.ConvertAsync(sourcePath, outPath, tgtExt, progressReporter, cancellationToken);

            stopwatch.Stop();
            task.Duration = stopwatch.Elapsed;
            task.Status = ConversionStatus.Completed;
            task.Progress = 100;
            task.FileSizeOut = File.Exists(resultPath) ? new FileInfo(resultPath).Length : 0;

            if (historyId > 0)
            {
                await _historyRepository.UpdateStatusAsync(
                    historyId,
                    "success",
                    "",
                    task.FileSizeOut,
                    (long)task.Duration.TotalMilliseconds,
                    cancellationToken
                );
            }

            ConversionCompleted?.Invoke(task);
            return task;
        }
        catch (Exception ex)
        {
            stopwatch.Stop();
            task.Duration = stopwatch.Elapsed;
            task.Status = ConversionStatus.Failed;
            task.ErrorMessage = ex.Message;

            if (historyId > 0)
            {
                await _historyRepository.UpdateStatusAsync(
                    historyId,
                    "failed",
                    ex.Message,
                    0,
                    (long)task.Duration.TotalMilliseconds,
                    cancellationToken
                );
            }

            ConversionFailed?.Invoke(task, ex.Message);
            return task;
        }
    }

    private static string BuildOutputPath(string sourcePath, string targetExt, string outputDir, bool overwrite)
    {
        var stem = Path.GetFileNameWithoutExtension(sourcePath);
        var ext = targetExt.TrimStart('.').ToLowerInvariant();
        var candidate = Path.Combine(outputDir, $"{stem}.{ext}");

        if (overwrite || !File.Exists(candidate))
        {
            return candidate;
        }

        int count = 1;
        while (File.Exists(Path.Combine(outputDir, $"{stem}_{count}.{ext}")))
        {
            count++;
        }

        return Path.Combine(outputDir, $"{stem}_{count}.{ext}");
    }
}

