using FileX.Core.Enums;
using FileX.Core.Models;

namespace FileX.Core.Interfaces;

public interface IFileDetector
{
    (string extension, FileCategory category, FormatDefinition? format) Detect(string filePath);
}

