using FileX.Core.Enums;

namespace FileX.Core.Models;

public record CategoryInfo(
    FileCategory Category,
    string DisplayName,
    string IconEmoji,
    IReadOnlyList<FormatDefinition> Formats
);

