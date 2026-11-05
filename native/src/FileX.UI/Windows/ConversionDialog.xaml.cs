using System.IO;
using System.Windows;
using FileX.Core.Enums;
using FileX.Core.Models;

namespace FileX.UI.Windows;

public partial class ConversionDialog : Window
{
    private readonly List<string> _files;
    public string SelectedFormat { get; private set; } = string.Empty;

    public ConversionDialog(List<string> files)
    {
        InitializeComponent();
        _files = files;
        LoadFileInfo();
    }

    private void LoadFileInfo()
    {
        if (_files.Count == 0) return;

        var first = _files[0];
        TxtFileName.Text = Path.GetFileName(first);

        long size = File.Exists(first) ? new FileInfo(first).Length : 0;
        var (ext, category, _) = App.FileDetector.Detect(first);

        TxtCategoryIcon.Text = category switch
        {
            FileCategory.Image => "🖼️",
            FileCategory.Pdf => "📄",
            FileCategory.Document => "📝",
            FileCategory.Spreadsheet => "📊",
            FileCategory.Presentation => "📽️",
            FileCategory.Audio => "🎵",
            FileCategory.Video => "🎬",
            _ => "📁"
        };

        TxtFileMeta.Text = $"{HistoryRecord.FormatBytes(size)} • {category} ({ext.ToUpperInvariant()})";
        if (_files.Count > 1)
        {
            TxtFileMeta.Text += $"  (+{_files.Count - 1} more files)";
        }

        var targets = App.FormatRegistry.GetOutputFormatDefinitions(ext);
        ComboFormats.ItemsSource = targets;
        ComboFormats.DisplayMemberPath = "Label";
        ComboFormats.SelectedValuePath = "Extension";

        if (targets.Count > 0)
        {
            ComboFormats.SelectedIndex = 0;
            BtnConvert.IsEnabled = true;
        }
        else
        {
            BtnConvert.IsEnabled = false;
        }
    }

    private void Convert_Click(object sender, RoutedEventArgs e)
    {
        if (ComboFormats.SelectedValue is string target)
        {
            SelectedFormat = target;
            DialogResult = true;
            Close();
        }
    }

    private void Cancel_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}

