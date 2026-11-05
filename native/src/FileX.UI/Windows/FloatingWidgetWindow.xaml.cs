using System.IO;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using FileX.Core.Models;

namespace FileX.UI.Windows;

public partial class FloatingWidgetWindow : Window
{
    public FloatingWidgetWindow()
    {
        InitializeComponent();

        // Restore saved coordinates
        var s = App.SettingsService.Settings;
        Left = s.WidgetX;
        Top = s.WidgetY;
        Opacity = s.WidgetOpacity;
        Topmost = s.AlwaysOnTop;

        App.ConversionManager.ConversionStarted += OnConversionStarted;
        App.ConversionManager.ConversionProgress += OnConversionProgress;
        App.ConversionManager.ConversionCompleted += OnConversionCompleted;
        App.ConversionManager.ConversionFailed += OnConversionFailed;
    }

    private void Window_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (e.ButtonState == MouseButtonState.Pressed)
        {
            DragMove();
            // Save new position
            App.SettingsService.Set<double>(s =>
            {
                s.WidgetX = Left;
                s.WidgetY = Top;
            });
        }
    }

    private void Window_MouseDoubleClick(object sender, MouseButtonEventArgs e)
    {
        App.AppMainWindow?.RestoreAndShow();
    }

    private void Window_DragEnter(object sender, DragEventArgs e)
    {
        if (e.Data.GetDataPresent(DataFormats.FileDrop))
        {
            e.Effects = DragDropEffects.Copy;
            SetDraggingHover(true);
        }
    }

    private void Window_DragLeave(object sender, DragEventArgs e)
    {
        SetDraggingHover(false);
    }

    private void Window_Drop(object sender, DragEventArgs e)
    {
        SetDraggingHover(false);
        if (e.Data.GetDataPresent(DataFormats.FileDrop))
        {
            var files = (string[])e.Data.GetData(DataFormats.FileDrop);
            if (files != null && files.Length > 0)
            {
                HandleDroppedFiles(files.Where(File.Exists).ToList());
            }
        }
    }

    private void SetDraggingHover(bool active)
    {
        if (active)
        {
            IdleState.Visibility = Visibility.Collapsed;
            ProcessingState.Visibility = Visibility.Collapsed;
            DragState.Visibility = Visibility.Visible;

            OuterCircle.BorderBrush = new SolidColorBrush(Color.FromRgb(56, 189, 248));
            CircleShadow.Color = Color.FromRgb(56, 189, 248);
        }
        else
        {
            DragState.Visibility = Visibility.Collapsed;
            IdleState.Visibility = Visibility.Visible;

            OuterCircle.BorderBrush = new SolidColorBrush(Color.FromRgb(124, 77, 255));
            CircleShadow.Color = Color.FromRgb(124, 77, 255);
        }
    }

    private async void HandleDroppedFiles(List<string> filePaths)
    {
        if (filePaths.Count == 0) return;

        var dialog = new ConversionDialog(filePaths);
        dialog.Owner = this;
        if (dialog.ShowDialog() == true && !string.IsNullOrEmpty(dialog.SelectedFormat))
        {
            var targetFormat = dialog.SelectedFormat;
            foreach (var file in filePaths)
            {
                await App.ConversionManager.ConvertAsync(file, targetFormat);
            }
        }
    }

    private void OnConversionStarted(ConversionTask task)
    {
        Dispatcher.Invoke(() =>
        {
            IdleState.Visibility = Visibility.Collapsed;
            DragState.Visibility = Visibility.Collapsed;
            ProcessingState.Visibility = Visibility.Visible;
            TxtProgressPct.Text = "5%";
        });
    }

    private void OnConversionProgress(ConversionTask task, int progress)
    {
        Dispatcher.Invoke(() =>
        {
            TxtProgressPct.Text = $"{progress}%";
        });
    }

    private void OnConversionCompleted(ConversionTask task)
    {
        Dispatcher.Invoke(() =>
        {
            ProcessingState.Visibility = Visibility.Collapsed;
            DragState.Visibility = Visibility.Collapsed;
            IdleState.Visibility = Visibility.Visible;
        });
    }

    private void OnConversionFailed(ConversionTask task, string error)
    {
        Dispatcher.Invoke(() =>
        {
            ProcessingState.Visibility = Visibility.Collapsed;
            DragState.Visibility = Visibility.Collapsed;
            IdleState.Visibility = Visibility.Visible;
        });
    }

    private void OpenDashboard_Click(object sender, RoutedEventArgs e)
    {
        App.AppMainWindow?.RestoreAndShow();
    }

    private void ToggleTopmost_Click(object sender, RoutedEventArgs e)
    {
        Topmost = !Topmost;
        MenuAlwaysOnTop.IsChecked = Topmost;
        App.SettingsService.Set<bool>(s => s.AlwaysOnTop = Topmost);
    }

    private void HideWidget_Click(object sender, RoutedEventArgs e)
    {
        Hide();
        App.SettingsService.Set<bool>(s => s.ShowFloatingWidget = false);
    }

    private void ExitApp_Click(object sender, RoutedEventArgs e)
    {
        Application.Current.Shutdown();
    }
}

