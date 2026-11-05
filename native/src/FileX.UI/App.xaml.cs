using System.Windows;
using FileX.Core.Interfaces;
using FileX.Infrastructure;
using FileX.Infrastructure.Persistence;
using FileX.UI.Windows;

namespace FileX.UI;

public partial class App : Application
{
    public static ISettingsService SettingsService { get; private set; } = null!;
    public static IHistoryRepository HistoryRepository { get; private set; } = null!;
    public static IFormatRegistry FormatRegistry { get; private set; } = null!;
    public static IFileDetector FileDetector { get; private set; } = null!;
    public static ConversionManager ConversionManager { get; private set; } = null!;

    public static FloatingWidgetWindow? FloatingWidget { get; private set; }
    public static MainWindow? AppMainWindow { get; private set; }

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        // Initialize Core & Infrastructure Services
        SettingsService = new JsonSettingsService();
        HistoryRepository = new SqliteHistoryRepository();
        FormatRegistry = new FormatRegistry();
        FileDetector = new FileDetector(FormatRegistry);
        ConversionManager = new ConversionManager(SettingsService, HistoryRepository, FormatRegistry, FileDetector);

        // Apply saved theme
        if (SettingsService.Settings.Theme.Equals("light", StringComparison.OrdinalIgnoreCase))
        {
            Wpf.Ui.Appearance.ApplicationThemeManager.Apply(Wpf.Ui.Appearance.ApplicationTheme.Light);
        }
        else
        {
            Wpf.Ui.Appearance.ApplicationThemeManager.Apply(Wpf.Ui.Appearance.ApplicationTheme.Dark);
        }

        // Create and show Main Window
        AppMainWindow = new MainWindow();
        MainWindow = AppMainWindow;

        if (!SettingsService.Settings.StartMinimised)
        {
            AppMainWindow.Show();
        }

        // Create Floating Widget
        FloatingWidget = new FloatingWidgetWindow();
        if (SettingsService.Settings.ShowFloatingWidget)
        {
            FloatingWidget.Show();
        }
    }

    protected override void OnExit(ExitEventArgs e)
    {
        FloatingWidget?.Close();
        base.OnExit(e);
    }
}

