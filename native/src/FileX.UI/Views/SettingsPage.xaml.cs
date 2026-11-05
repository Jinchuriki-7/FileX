using System.Windows;
using System.Windows.Controls;
using FileX.UI.Services;
using Microsoft.Win32;

namespace FileX.UI.Views;

public partial class SettingsPage : Page
{
    private bool _initialized;

    public SettingsPage()
    {
        InitializeComponent();
        Loaded += (_, _) => LoadSettings();
    }

    private void LoadSettings()
    {
        var s = App.SettingsService.Settings;

        ChkShowFloatingWidget.IsChecked = s.ShowFloatingWidget;
        ChkAlwaysOnTop.IsChecked = s.AlwaysOnTop;
        SliderOpacity.Value = s.WidgetOpacity * 100;
        TxtOpacityValue.Text = $"{(int)SliderOpacity.Value}%";

        TxtOutputFolder.Text = s.OutputFolder;
        ChkOpenAfter.IsChecked = s.OpenOutputAfterConversion;
        ChkOverwrite.IsChecked = s.OverwriteExisting;

        ChkNotifications.IsChecked = s.ShowNotifications;
        ChkStartMinimised.IsChecked = s.StartMinimised;
        ChkStartup.IsChecked = WindowsIntegrationService.IsInStartup();

        _initialized = true;
    }

    private void ChkShowFloatingWidget_Changed(object sender, RoutedEventArgs e)
    {
        if (!_initialized) return;
        var isChecked = ChkShowFloatingWidget.IsChecked == true;
        App.SettingsService.Set<bool>(s => s.ShowFloatingWidget = isChecked);

        if (isChecked) App.FloatingWidget?.Show();
        else App.FloatingWidget?.Hide();
    }

    private void ChkAlwaysOnTop_Changed(object sender, RoutedEventArgs e)
    {
        if (!_initialized) return;
        var isChecked = ChkAlwaysOnTop.IsChecked == true;
        App.SettingsService.Set<bool>(s => s.AlwaysOnTop = isChecked);
        if (App.FloatingWidget != null)
        {
            App.FloatingWidget.Topmost = isChecked;
        }
    }

    private void SliderOpacity_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
    {
        if (!_initialized) return;
        int pct = (int)SliderOpacity.Value;
        TxtOpacityValue.Text = $"{pct}%";
        var opacity = pct / 100.0;
        App.SettingsService.Set<double>(s => s.WidgetOpacity = opacity);
        if (App.FloatingWidget != null)
        {
            App.FloatingWidget.Opacity = opacity;
        }
    }

    private void BrowseOutputFolder_Click(object sender, RoutedEventArgs e)
    {
        var dlg = new OpenFolderDialog
        {
            Title = "Select Default Output Directory",
            InitialDirectory = App.SettingsService.Settings.OutputFolder
        };

        if (dlg.ShowDialog() == true && !string.IsNullOrEmpty(dlg.FolderName))
        {
            TxtOutputFolder.Text = dlg.FolderName;
            App.SettingsService.Set<string>(s => s.OutputFolder = dlg.FolderName);
        }
    }

    private void ChkOpenAfter_Changed(object sender, RoutedEventArgs e)
    {
        if (!_initialized) return;
        App.SettingsService.Set<bool>(s => s.OpenOutputAfterConversion = ChkOpenAfter.IsChecked == true);
    }

    private void ChkOverwrite_Changed(object sender, RoutedEventArgs e)
    {
        if (!_initialized) return;
        App.SettingsService.Set<bool>(s => s.OverwriteExisting = ChkOverwrite.IsChecked == true);
    }

    private void ChkStartup_Changed(object sender, RoutedEventArgs e)
    {
        if (!_initialized) return;
        var isChecked = ChkStartup.IsChecked == true;
        App.SettingsService.Set<bool>(s => s.RunAtStartup = isChecked);
        WindowsIntegrationService.SetStartup(isChecked);
    }

    private void ChkNotifications_Changed(object sender, RoutedEventArgs e)
    {
        if (!_initialized) return;
        App.SettingsService.Set<bool>(s => s.ShowNotifications = ChkNotifications.IsChecked == true);
    }

    private void ChkStartMinimised_Changed(object sender, RoutedEventArgs e)
    {
        if (!_initialized) return;
        App.SettingsService.Set<bool>(s => s.StartMinimised = ChkStartMinimised.IsChecked == true);
    }
}

