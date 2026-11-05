namespace FileX.Core.Models;

public class AppSettings
{
    public string Theme { get; set; } = "dark";
    public bool AlwaysOnTop { get; set; } = true;
    public bool StartMinimised { get; set; } = false;
    public bool RunAtStartup { get; set; } = false;
    public bool ShowNotifications { get; set; } = true;

    public string OutputFolder { get; set; } = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
        "Downloads",
        "FileX"
    );

    public bool OpenOutputAfterConversion { get; set; } = false;
    public bool OverwriteExisting { get; set; } = false;

    public double WidgetOpacity { get; set; } = 0.95;
    public double WidgetX { get; set; } = 100;
    public double WidgetY { get; set; } = 150;
    public bool ShowFloatingWidget { get; set; } = true;

    public int MaxHistoryEntries { get; set; } = 500;
}

