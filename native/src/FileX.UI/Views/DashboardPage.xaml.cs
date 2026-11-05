using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using FileX.Core.Models;

namespace FileX.UI.Views;

public partial class DashboardPage : Page
{
    public DashboardPage()
    {
        InitializeComponent();
        Loaded += OnLoaded;
    }

    private async void OnLoaded(object sender, RoutedEventArgs e)
    {
        await LoadStatsAsync();
        LoadCategories();
    }

    private async Task LoadStatsAsync()
    {
        var stats = await App.HistoryRepository.GetStatsAsync();
        TxtTotal.Text = stats.Total.ToString();

        if (stats.Total > 0)
        {
            var rate = (int)((double)stats.SuccessCount / stats.Total * 100);
            TxtSuccessRate.Text = $"{rate}%";
        }
        else
        {
            TxtSuccessRate.Text = "100%";
        }

        TxtVolume.Text = HistoryRecord.FormatBytes(stats.BytesIn + stats.BytesOut);
    }

    private void LoadCategories()
    {
        CategoryPanel.Children.Clear();
        var categories = App.FormatRegistry.GetAllCategories();

        foreach (var cat in categories)
        {
            var card = new Wpf.Ui.Controls.Card
            {
                Margin = new Thickness(6),
                Padding = new Thickness(14),
                Background = new SolidColorBrush(Color.FromRgb(26, 27, 43)),
                BorderBrush = new SolidColorBrush(Color.FromRgb(40, 42, 68))
            };

            var sp = new StackPanel();

            var icon = new TextBlock
            {
                Text = cat.IconEmoji,
                FontSize = 24
            };

            var title = new TextBlock
            {
                Text = cat.DisplayName,
                FontSize = 14,
                FontWeight = FontWeights.Bold,
                Foreground = new SolidColorBrush(Color.FromRgb(241, 245, 249))
            };

            var exts = string.Join(", ", cat.Formats.Take(3).Select(f => f.Extension.ToUpperInvariant())) + "…";
            var desc = new TextBlock
            {
                Text = exts,
                FontSize = 11,
                Foreground = new SolidColorBrush(Color.FromRgb(148, 163, 184))
            };

            sp.Children.Add(icon);
            sp.Children.Add(title);
            sp.Children.Add(desc);
            card.Content = sp;

            CategoryPanel.Children.Add(card);
        }
    }

    private void StartConverting_Click(object sender, RoutedEventArgs e)
    {
        App.AppMainWindow?.NavigateToConvert();
    }
}
