using System.Windows;
using System.Windows.Controls;
using FileX.Core.Models;
using FileX.UI.Services;

namespace FileX.UI.Views;

public partial class HistoryPage : Page
{
    public HistoryPage()
    {
        InitializeComponent();
        Loaded += async (_, _) => await RefreshHistoryAsync();
    }

    public async Task RefreshHistoryAsync()
    {
        var query = SearchBox?.Text?.Trim();
        IReadOnlyList<HistoryRecord> records;

        if (!string.IsNullOrEmpty(query))
        {
            records = await App.HistoryRepository.SearchAsync(query);
        }
        else
        {
            records = await App.HistoryRepository.GetAllAsync(limit: 250);
        }

        HistoryGrid.ItemsSource = records;
    }

    private async void SearchBox_TextChanged(object sender, TextChangedEventArgs e)
    {
        await RefreshHistoryAsync();
    }

    private async void ClearHistory_Click(object sender, RoutedEventArgs e)
    {
        var result = MessageBox.Show(
            "Are you sure you want to clear your conversion history? (Your files will not be deleted)",
            "Clear History",
            MessageBoxButton.YesNo,
            MessageBoxImage.Question
        );

        if (result == MessageBoxResult.Yes)
        {
            await App.HistoryRepository.ClearAllAsync();
            await RefreshHistoryAsync();
        }
    }

    private void OpenRecordFile_Click(object sender, RoutedEventArgs e)
    {
        if (sender is FrameworkElement { DataContext: HistoryRecord record })
        {
            WindowsIntegrationService.OpenFile(record.OutputPath);
        }
    }

    private void OpenRecordFolder_Click(object sender, RoutedEventArgs e)
    {
        if (sender is FrameworkElement { DataContext: HistoryRecord record })
        {
            WindowsIntegrationService.OpenContainingFolder(record.OutputPath);
        }
    }

    private async void DeleteRecord_Click(object sender, RoutedEventArgs e)
    {
        if (sender is FrameworkElement { DataContext: HistoryRecord record })
        {
            await App.HistoryRepository.DeleteAsync(record.Id);
            await RefreshHistoryAsync();
        }
    }
}

