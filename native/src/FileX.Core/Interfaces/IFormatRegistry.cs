using FileX.Core.Enums;
using FileX.Core.Models;

namespace FileX.Core.Interfaces;

public interface IFormatRegistry
{
    FormatDefinition? GetFormat(string extension);
    FileCategory GetCategory(string extension);
    IReadOnlyList<string> GetOutputFormats(string sourceExtension);
    IReadOnlyList<FormatDefinition> GetOutputFormatDefinitions(string sourceExtension);
    IReadOnlyList<CategoryInfo> GetAllCategories();
    bool IsSupported(string extension);
}

