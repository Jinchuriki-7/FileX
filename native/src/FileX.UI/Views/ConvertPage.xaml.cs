using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using FileX.Core.Models;
using FileX.UI.Services;
using FileX.UI.Windows;
using Microsoft.Win32;

namespace FileX.UI.Views;

public partial class ConvertPage : Page
{
    private readonly Dictionary<string, ProgressBar> _activeBars = new();

    public ConvertPage()
    {
        InitializeComponent();
        App.ConversionManager.ConversionProgress += OnConversionProgress;
        App.ConversionManager.ConversionCompleted += OnConversionCompleted;
        App.ConversionManager.ConversionFailed += OnConversionFailed;
    }

    private void DropZone_DragEnter(object sender, DragEventArgs e)
    {
        if (e.Data.GetDataPresent(DataFormats.FileDrop))
        {
            e.Effects = DragDropEffects.Copy;
            DropZoneBorder.Background = new SolidColorBrush(Color.FromArgb(40, 124, 77, 255));
            DropZoneBorder.BorderBrush = new SolidColorBrush(Color.FromRgb(124, 77, 255));
            TxtDropTitle.Text = "Release to select output format!";
        }
    }

    private void DropZone_DragLeave(object sender, DragEventArgs e)
    {
        ResetDropZoneStyle();
    }

    private void DropZone_Drop(object sender, DragEventArgs e)
    {
        ResetDropZoneStyle();
        if (e.Data.GetDataPresent(DataFormats.FileDrop))
        {
            var files = (string[])e.Data.GetData(DataFormats.FileDrop);
            if (files != null && files.Length > 0)
            {
                ProcessFiles(files);
            }
        }
    }

    private void DropZone_MouseDown(object sender, MouseButtonEventArgs e)
    {
        if (e.LeftButton == MouseButtonState.Pressed)
        {
            var dlg = new OpenFileDialog
            {
                Multiselect = true,
                Title = "Select Files to Convert"
            };

            if (dlg.ShowDialog() == true && dlg.FileNames.Length > 0)
            {
                ProcessFiles(dlg.FileNames);
            }
        }
    }

    private void ResetDropZoneStyle()
    {
        DropZoneBorder.Background = new SolidColorBrush(Color.FromRgb(22, 23, 38));
        DropZoneBorder.BorderBrush = new SolidColorBrush(Color.FromRgb(61, 64, 102));
        TxtDropTitle.Text = "Drop files here to convert";
    }

    public void ProcessFiles(IEnumerable<string> filePaths)
    {
        var list = filePaths.Where(File.Exists).ToList();
        if (list.Count == 0) return;

        var dialog = new ConversionDialog(list);
        dialog.Owner = Window.GetWindow(this);
        if (dialog.ShowDialog() == true && !string.IsNullOrEmpty(dialog.SelectedFormat))
        {
            var targetFormat = dialog.SelectedFormat;
            foreach (var file in list)
            {
                StartConversion(file, targetFormat);
            }
        }
    }

    private async void StartConversion(string filePath, string targetFormat)
    {
        AddTaskCard(filePath, targetFormat);
        await App.ConversionManager.ConvertAsync(filePath, targetFormat);
    }

    private void AddTaskCard(string filePath, string targetFormat)
    {
        var card = new Wpf.Ui.Controls.Card
        {
            Tag = filePath,
            Padding = new Thickness(14),
            Background = new SolidColorBrush(Color.FromRgb(26, 27, 43)),
            BorderBrush = new SolidColorBrush(Color.FromRgb(40, 42, 68)),
            Margin = new Thickness(0, 0, 0, 8)
        };

        var sp = new StackPanel();

        var topRow = new Grid();
        topRow.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        topRow.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        var fileInfo = new StackPanel();
        fileInfo.Children.Add(new TextBlock
        {
            Text = Path.GetFileName(filePath),
            FontWeight = FontWeights.Bold,
            Foreground = new SolidColorBrush(Color.FromRgb(241, 245, 249))
        });

        var srcExt = Path.GetExtension(filePath).TrimStart('.').ToUpperInvariant();
        fileInfo.Children.Add(new TextBlock
        {
            Text = $"{srcExt} → {targetFormat.ToUpperInvariant()}",
            FontSize = 11,
            Foreground = new SolidColorBrush(Color.FromRgb(148, 163, 184))
        });

        var statusBadge = new Border
        {
            Name = "Badge",
            Background = new SolidColorBrush(Color.FromArgb(50, 56, 189, 248)),
            CornerRadius = new CornerRadius(6),
            Padding = new Thickness(8, 4, 8, 4),
            Child = new TextBlock
            {
                Text = "Converting…",
                FontSize = 11,
                FontWeight = FontWeights.SemiBold,
                Foreground = new SolidColorBrush(Color.FromRgb(56, 189, 248))
            }
        };

        Grid.SetColumn(fileInfo, 0);
        Grid.SetColumn(statusBadge, 1);
        topRow.Children.Add(fileInfo);
        topRow.Children.Add(statusBadge);

        var pbar = new ProgressBar
        {
            Height = 6,
            Value = 10,
            Foreground = new SolidColorBrush(Color.FromRgb(124, 77, 255)),
            Background = new SolidColorBrush(Color.FromRgb(35, 37, 56)),
            Margin = new Thickness(0, 4, 0, 0)
        };

        _activeBars[filePath] = pbar;

        sp.Children.Add(topRow);
        sp.Children.Add(pbar);
        card.Content = sp;

        TaskQueuePanel.Children.Insert(0, card);
    }

    private void OnConversionProgress(ConversionTask task, int progress)
    {
        Dispatcher.Invoke(() =>
        {
            if (_activeBars.TryGetValue(task.SourcePath, out var bar))
            {
                bar.Value = progress;
            }
        });
    }

    private void OnConversionCompleted(ConversionTask task)
    {
        Dispatcher.Invoke(() =>
        {
            foreach (Wpf.Ui.Controls.Card card in TaskQueuePanel.Children)
            {
                if (card.Tag as string == task.SourcePath && card.Content is StackPanel sp)
                {
                    if (_activeBars.TryGetValue(task.SourcePath, out var bar))
                    {
                        bar.Value = 100;
                        bar.Foreground = new SolidColorBrush(Color.FromRgb(16, 185, 129));
                    }

                    // Add Open File & Open Folder buttons
                    var actionRow = new StackPanel
                    {
                        Orientation = Orientation.Horizontal,
                        HorizontalAlignment = HorizontalAlignment.Right,
                        Margin = new Thickness(0, 6, 0, 0)
                    };

                    var btnOpenFile = new Wpf.Ui.Controls.Button
                    {
                        Content = "Open File",
                        Appearance = Wpf.Ui.Controls.ControlAppearance.Primary,
                        Padding = new Thickness(12, 4, 12, 4),
                        Margin = new Thickness(0, 0, 8, 0),
                        FontSize = 11
                    };
                    btnOpenFile.Click += (_, _) => WindowsIntegrationService.OpenFile(task.OutputPath);

                    var btnOpenFolder = new Wpf.Ui.Controls.Button
                    {
                        Content = "Open Folder",
                        Appearance = Wpf.Ui.Controls.ControlAppearance.Secondary,
                        Padding = new Thickness(12, 4, 12, 4),
                        FontSize = 11
                    };
                    btnOpenFolder.Click += (_, _) => WindowsIntegrationService.OpenContainingFolder(task.OutputPath);

                    actionRow.Children.Add(btnOpenFile);
                    actionRow.Children.Add(btnOpenFolder);
                    sp.Children.Add(actionRow);
                    break;
                }
            }
        });
    }

    private void OnConversionFailed(ConversionTask task, string error)
    {
        Dispatcher.Invoke(() =>
        {
            if (_activeBars.TryGetValue(task.SourcePath, out var bar))
            {
                bar.Value = 100;
                bar.Foreground = new SolidColorBrush(Color.FromRgb(239, 68, 68));
            }
        });
    }
}
