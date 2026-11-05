using FileX.Core.Models;

namespace FileX.Core.Interfaces;

public interface IConversionEngine
{
    bool CanHandle(string sourceExtension, string targetExtension);
    Task<string> ConvertAsync(
        string sourcePath,
        string outputPath,
        string targetExtension,
        IProgress<int>? progress = null,
        CancellationToken cancellationToken = default
    );
}

