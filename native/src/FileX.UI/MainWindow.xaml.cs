using System.ComponentModel;
using System.Windows;
using System.Windows.Media;
using FileX.UI.Services;
using FileX.UI.Views;
using Wpf.Ui.Controls;

namespace FileX.UI;

public partial class MainWindow : FluentWindow
{
    private readonly DashboardPage _dashboardPage = new();
    private readonly ConvertPage _convertPage = new();
    private readonly HistoryPage _historyPage = new();
    private readonly SettingsPage _settingsPage = new();

    private NativeTrayIcon? _trayIcon;

    public MainWindow()
    {
        InitializeComponent();
        Loaded += MainWindow_Loaded;
        _trayIcon = new NativeTrayIcon(this, "FileX — Universal File Converter");
        _trayIcon.DoubleClicked += RestoreAndShow;
    }

    private void MainWindow_Loaded(object sender, RoutedEventArgs e)
    {
        NavigateToDashboard();
        UpdateWidgetButtonText();
    }

    public void RestoreAndShow()
    {
        Show();
        WindowState = WindowState.Normal;
        Activate();
    }

    protected override void OnClosing(CancelEventArgs e)
    {
        // Minimize to tray instead of full termination to keep floating widget active
        e.Cancel = true;
        Hide();
    }

    public void NavigateToDashboard()
    {
        RootFrame.Navigate(_dashboardPage);
        HighlightNav(NavDashboard);
    }

    public void NavigateToConvert()
    {
        RootFrame.Navigate(_convertPage);
        HighlightNav(NavConvert);
    }

    public void NavigateToHistory()
    {
        RootFrame.Navigate(_historyPage);
        HighlightNav(NavHistory);
        _ = _historyPage.RefreshHistoryAsync();
    }

    public void NavigateToSettings()
    {
        RootFrame.Navigate(_settingsPage);
        HighlightNav(NavSettings);
    }

    private void HighlightNav(Wpf.Ui.Controls.Button activeButton)
    {
        NavDashboard.Background = Brushes.Transparent;
        NavConvert.Background = Brushes.Transparent;
        NavHistory.Background = Brushes.Transparent;
        NavSettings.Background = Brushes.Transparent;

        activeButton.Background = new SolidColorBrush(Color.FromRgb(38, 39, 63));
        activeButton.Foreground = new SolidColorBrush(Color.FromRgb(255, 255, 255));
    }

    private void NavDashboard_Click(object sender, RoutedEventArgs e) => NavigateToDashboard();
    private void NavConvert_Click(object sender, RoutedEventArgs e) => NavigateToConvert();
    private void NavHistory_Click(object sender, RoutedEventArgs e) => NavigateToHistory();
    private void NavSettings_Click(object sender, RoutedEventArgs e) => NavigateToSettings();

    private void ToggleWidget_Click(object sender, RoutedEventArgs e)
    {
        if (App.FloatingWidget == null) return;

        if (App.FloatingWidget.IsVisible)
        {
            App.FloatingWidget.Hide();
            App.SettingsService.Set<bool>(s => s.ShowFloatingWidget = false);
        }
        else
        {
            App.FloatingWidget.Show();
            App.SettingsService.Set<bool>(s => s.ShowFloatingWidget = true);
        }
        UpdateWidgetButtonText();
    }

    private void UpdateWidgetButtonText()
    {
        if (App.FloatingWidget != null && App.FloatingWidget.IsVisible)
        {
            BtnToggleWidget.Content = "Hide Widget";
        }
        else
        {
            BtnToggleWidget.Content = "Show Widget";
        }
    }
}
