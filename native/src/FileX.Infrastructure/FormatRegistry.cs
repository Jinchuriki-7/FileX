using FileX.Core.Enums;
using FileX.Core.Interfaces;
using FileX.Core.Models;

namespace FileX.Infrastructure;

public class FormatRegistry : IFormatRegistry
{
    private readonly Dictionary<string, FormatDefinition> _formats = new(StringComparer.OrdinalIgnoreCase);
    private readonly Dictionary<string, List<string>> _outputMap = new(StringComparer.OrdinalIgnoreCase);
    private readonly List<CategoryInfo> _categories = new();

    public FormatRegistry()
    {
        InitializeFormats();
        InitializeOutputMap();
        InitializeCategories();
    }

    private void InitializeFormats()
    {
        var list = new List<FormatDefinition>
        {
            // Images
            new("jpg",  "JPEG Image",        FileCategory.Image,        "image/jpeg"),
            new("jpeg", "JPEG Image",        FileCategory.Image,        "image/jpeg"),
            new("png",  "PNG Image",         FileCategory.Image,        "image/png"),
            new("bmp",  "Bitmap Image",      FileCategory.Image,        "image/bmp"),
            new("gif",  "GIF Image",         FileCategory.Image,        "image/gif"),
            new("tiff", "TIFF Image",        FileCategory.Image,        "image/tiff"),
            new("tif",  "TIFF Image",        FileCategory.Image,        "image/tiff"),
            new("webp", "WebP Image",        FileCategory.Image,        "image/webp"),
            new("ico",  "Icon File",         FileCategory.Image,        "image/x-icon"),

            // PDF
            new("pdf",  "PDF Document",      FileCategory.Pdf,          "application/pdf"),

            // Documents
            new("docx", "Word Document",     FileCategory.Document,     "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            new("doc",  "Word 97-2003",      FileCategory.Document,     "application/msword", CanOutput: false),
            new("txt",  "Plain Text",        FileCategory.Document,     "text/plain"),
            new("html", "HTML File",         FileCategory.Document,     "text/html"),
            new("htm",  "HTML File",         FileCategory.Document,     "text/html"),
            new("md",   "Markdown",          FileCategory.Document,     "text/markdown"),
            new("rtf",  "Rich Text",         FileCategory.Document,     "application/rtf"),

            // Spreadsheets
            new("xlsx", "Excel Workbook",    FileCategory.Spreadsheet,  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            new("xls",  "Excel 97-2003",     FileCategory.Spreadsheet,  "application/vnd.ms-excel", CanOutput: false),
            new("csv",  "CSV Document",      FileCategory.Spreadsheet,  "text/csv"),

            // Presentations
            new("pptx", "PowerPoint Deck",   FileCategory.Presentation, "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
            new("ppt",  "PowerPoint 97-2003",FileCategory.Presentation, "application/vnd.ms-powerpoint", CanOutput: false),

            // Audio
            new("mp3",  "MP3 Audio",         FileCategory.Audio,        "audio/mpeg"),
            new("wav",  "WAV Audio",         FileCategory.Audio,        "audio/wav"),
            new("flac", "FLAC Lossless",     FileCategory.Audio,        "audio/flac"),
            new("aac",  "AAC Audio",         FileCategory.Audio,        "audio/aac"),
            new("ogg",  "OGG Vorbis",        FileCategory.Audio,        "audio/ogg"),
            new("m4a",  "M4A Audio",         FileCategory.Audio,        "audio/mp4"),

            // Video
            new("mp4",  "MP4 Video",         FileCategory.Video,        "video/mp4"),
            new("mkv",  "MKV Video",         FileCategory.Video,        "video/x-matroska"),
            new("avi",  "AVI Video",         FileCategory.Video,        "video/x-msvideo"),
            new("mov",  "QuickTime Video",   FileCategory.Video,        "video/quicktime"),
            new("webm", "WebM Video",        FileCategory.Video,        "video/webm")
        };

        foreach (var f in list)
        {
            _formats[f.Extension] = f;
        }
    }

    private void InitializeOutputMap()
    {
        // Image conversions
        var imageOutputs = new List<string> { "png", "jpg", "bmp", "gif", "tiff", "ico", "pdf" };
        _outputMap["jpg"]  = new List<string> { "png", "bmp", "gif", "tiff", "ico", "pdf" };
        _outputMap["jpeg"] = new List<string> { "png", "bmp", "gif", "tiff", "ico", "pdf" };
        _outputMap["png"]  = new List<string> { "jpg", "bmp", "gif", "tiff", "ico", "pdf" };
        _outputMap["bmp"]  = new List<string> { "png", "jpg", "gif", "tiff", "pdf" };
        _outputMap["gif"]  = new List<string> { "png", "jpg", "bmp", "tiff" };
        _outputMap["tiff"] = new List<string> { "png", "jpg", "bmp", "gif", "pdf" };
        _outputMap["tif"]  = new List<string> { "png", "jpg", "bmp", "gif", "pdf" };
        _outputMap["webp"] = new List<string> { "png", "jpg", "bmp", "gif" };
        _outputMap["ico"]  = new List<string> { "png", "jpg", "bmp" };

        // PDF
        _outputMap["pdf"] = new List<string> { "docx", "txt", "png", "jpg" };

        // Documents
        _outputMap["docx"] = new List<string> { "pdf", "txt", "html", "md" };
        _outputMap["doc"]  = new List<string> { "docx", "pdf", "txt", "html" };
        _outputMap["txt"]  = new List<string> { "pdf", "docx", "html", "md" };
        _outputMap["html"] = new List<string> { "pdf", "docx", "txt", "md" };
        _outputMap["htm"]  = new List<string> { "pdf", "docx", "txt", "md" };
        _outputMap["md"]   = new List<string> { "html", "pdf", "docx", "txt" };
        _outputMap["rtf"]  = new List<string> { "pdf", "docx", "txt" };

        // Spreadsheets
        _outputMap["xlsx"] = new List<string> { "csv", "pdf" };
        _outputMap["xls"]  = new List<string> { "xlsx", "csv", "pdf" };
        _outputMap["csv"]  = new List<string> { "xlsx", "pdf" };

        // Presentations
        _outputMap["pptx"] = new List<string> { "pdf" };
        _outputMap["ppt"]  = new List<string> { "pdf" };

        // Audio
        _outputMap["mp3"] = new List<string> { "wav", "aac", "flac", "ogg" };
        _outputMap["wav"] = new List<string> { "mp3", "aac", "flac", "ogg" };
        _outputMap["aac"] = new List<string> { "mp3", "wav", "flac", "ogg" };
        _outputMap["flac"]= new List<string> { "mp3", "wav", "aac", "ogg" };
        _outputMap["ogg"] = new List<string> { "mp3", "wav", "aac", "flac" };
        _outputMap["m4a"] = new List<string> { "mp3", "wav", "aac", "flac" };

        // Video
        _outputMap["mp4"]  = new List<string> { "avi", "mkv", "mov", "webm", "gif", "mp3" };
        _outputMap["avi"]  = new List<string> { "mp4", "mkv", "mov", "webm", "gif", "mp3" };
        _outputMap["mkv"]  = new List<string> { "mp4", "avi", "mov", "webm", "gif", "mp3" };
        _outputMap["mov"]  = new List<string> { "mp4", "avi", "mkv", "webm", "gif", "mp3" };
        _outputMap["webm"] = new List<string> { "mp4", "avi", "mkv", "gif", "mp3" };
    }

    private void InitializeCategories()
    {
        _categories.Add(new CategoryInfo(FileCategory.Image, "Image", "🖼️", _formats.Values.Where(f => f.Category == FileCategory.Image).ToList()));
        _categories.Add(new CategoryInfo(FileCategory.Pdf, "PDF", "📄", _formats.Values.Where(f => f.Category == FileCategory.Pdf).ToList()));
        _categories.Add(new CategoryInfo(FileCategory.Document, "Document", "📝", _formats.Values.Where(f => f.Category == FileCategory.Document).ToList()));
        _categories.Add(new CategoryInfo(FileCategory.Spreadsheet, "Spreadsheet", "📊", _formats.Values.Where(f => f.Category == FileCategory.Spreadsheet).ToList()));
        _categories.Add(new CategoryInfo(FileCategory.Presentation, "Presentation", "📽️", _formats.Values.Where(f => f.Category == FileCategory.Presentation).ToList()));
        _categories.Add(new CategoryInfo(FileCategory.Audio, "Audio", "🎵", _formats.Values.Where(f => f.Category == FileCategory.Audio).ToList()));
        _categories.Add(new CategoryInfo(FileCategory.Video, "Video", "🎬", _formats.Values.Where(f => f.Category == FileCategory.Video).ToList()));
    }

    public FormatDefinition? GetFormat(string extension)
    {
        var clean = extension.TrimStart('.').ToLowerInvariant();
        return _formats.TryGetValue(clean, out var fmt) ? fmt : null;
    }

    public FileCategory GetCategory(string extension)
    {
        var fmt = GetFormat(extension);
        return fmt?.Category ?? FileCategory.Unknown;
    }

    public IReadOnlyList<string> GetOutputFormats(string sourceExtension)
    {
        var clean = sourceExtension.TrimStart('.').ToLowerInvariant();
        return _outputMap.TryGetValue(clean, out var list) ? list : Array.Empty<string>();
    }

    public IReadOnlyList<FormatDefinition> GetOutputFormatDefinitions(string sourceExtension)
    {
        return GetOutputFormats(sourceExtension)
            .Select(GetFormat)
            .Where(f => f != null)
            .Cast<FormatDefinition>()
            .ToList();
    }

    public IReadOnlyList<CategoryInfo> GetAllCategories() => _categories;

    public bool IsSupported(string extension)
    {
        var clean = extension.TrimStart('.').ToLowerInvariant();
        return _formats.ContainsKey(clean);
    }
}

