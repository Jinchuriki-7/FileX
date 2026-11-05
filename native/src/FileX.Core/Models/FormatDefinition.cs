using FileX.Core.Enums;

namespace FileX.Core.Models;

public record FormatDefinition(
    string Extension,
    string Label,
    FileCategory Category,
    string MimeType,
    bool CanInput = true,
    bool CanOutput = true
);

