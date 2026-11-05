using System.Diagnostics;
using System.IO;
using FileX.Core.Interfaces;

namespace FileX.Infrastructure.Converters;

public class NativeMediaConverter : IConversionEngine
{
    private static readonly HashSet<string> AudioExts = new(StringComparer.OrdinalIgnoreCase)
    {
        "mp3", "wav", "flac", "aac", "ogg", "m4a"
    };

    private static readonly HashSet<string> VideoExts = new(StringComparer.OrdinalIgnoreCase)
    {
        "mp4", "mkv", "avi", "mov", "webm", "gif"
    };

    public bool CanHandle(string sourceExtension, string targetExtension)
    {
        var src = sourceExtension.TrimStart('.').ToLowerInvariant();
        var tgt = targetExtension.TrimStart('.').ToLowerInvariant();

        bool isAudio = AudioExts.Contains(src) && AudioExts.Contains(tgt);
        bool isVideo = VideoExts.Contains(src) && (VideoExts.Contains(tgt) || AudioExts.Contains(tgt));

        return isAudio || isVideo;
    }

    public async Task<string> ConvertAsync(
        string sourcePath,
        string outputPath,
        string targetExtension,
        IProgress<int>? progress = null,
        CancellationToken cancellationToken = default)
    {
        var ffmpegExe = FindFfmpeg();
        if (string.IsNullOrEmpty(ffmpegExe))
        {
            throw new FileNotFoundException("FFmpeg executable not found. Please install FFmpeg on system PATH or bundle ffmpeg.exe.");
        }

        var dir = Path.GetDirectoryName(outputPath);
        if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);

        progress?.Report(10);

        var args = BuildFfmpegArguments(sourcePath, outputPath, targetExtension);

        var psi = new ProcessStartInfo
        {
            FileName = ffmpegExe,
            Arguments = args,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardError = true,
            RedirectStandardOutput = true
        };

        using var process = new Process { StartInfo = psi };
        process.Start();

        progress?.Report(40);

        // Read error stream for completion
        var errorOutput = await process.StandardError.ReadToEndAsync(cancellationToken);
        await process.WaitForExitAsync(cancellationToken);

        if (process.ExitCode != 0)
        {
            throw new InvalidOperationException($"FFmpeg conversion failed: {errorOutput.Take(400)}");
        }

        progress?.Report(100);
        return outputPath;
    }

    private static string BuildFfmpegArguments(string input, string output, string targetExt)
    {
        var tgt = targetExt.TrimStart('.').ToLowerInvariant();

        // Audio extraction or conversion
        if (tgt == "mp3")
            return $"-y -i \"{input}\" -vn -ar 44100 -ac 2 -b:a 192k \"{output}\"";
        if (tgt == "wav")
            return $"-y -i \"{input}\" -vn \"{output}\"";
        if (tgt == "aac")
            return $"-y -i \"{input}\" -vn -c:a aac -b:a 192k \"{output}\"";
        if (tgt == "flac")
            return $"-y -i \"{input}\" -vn -c:a flac \"{output}\"";
        if (tgt == "ogg")
            return $"-y -i \"{input}\" -vn -c:a libvorbis -q:a 5 \"{output}\"";
        if (tgt == "gif")
            return $"-y -i \"{input}\" -vf \"fps=12,scale=480:-1:flags=lanczos\" \"{output}\"";
        if (tgt == "mp4")
            return $"-y -i \"{input}\" -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k -movflags +faststart \"{output}\"";

        return $"-y -i \"{input}\" \"{output}\"";
    }

    private static string? FindFfmpeg()
    {
        // 1. Check application directory
        var appDir = AppDomain.CurrentDomain.BaseDirectory;
        var directFfmpeg = Path.Combine(appDir, "ffmpeg.exe");
        if (File.Exists(directFfmpeg)) return directFfmpeg;

        var binFfmpeg = Path.Combine(appDir, "bin", "ffmpeg.exe");
        if (File.Exists(binFfmpeg)) return binFfmpeg;

        // 2. Check parent directories (dev mode)
        var current = new DirectoryInfo(appDir);
        for (int i = 0; i < 4 && current.Parent != null; i++)
        {
            current = current.Parent;
            var devBin = Path.Combine(current.FullName, "bin", "ffmpeg.exe");
            if (File.Exists(devBin)) return devBin;
        }

        // 3. Check system PATH
        var pathEnv = Environment.GetEnvironmentVariable("PATH");
        if (!string.IsNullOrEmpty(pathEnv))
        {
            foreach (var p in pathEnv.Split(';', StringSplitOptions.RemoveEmptyEntries))
            {
                var candidate = Path.Combine(p.Trim(), "ffmpeg.exe");
                if (File.Exists(candidate)) return candidate;
            }
        }

        return null;
    }
}

