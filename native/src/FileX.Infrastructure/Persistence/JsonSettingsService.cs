using System.IO;
using System.Text.Json;
using FileX.Core.Interfaces;
using FileX.Core.Models;

namespace FileX.Infrastructure.Persistence;

public class JsonSettingsService : ISettingsService
{
    private readonly string _filePath;
    private readonly JsonSerializerOptions _jsonOptions = new() { WriteIndented = true };

    public AppSettings Settings { get; private set; } = new();

    public JsonSettingsService(string? configPath = null)
    {
        if (string.IsNullOrEmpty(configPath))
        {
            var appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            var dir = Path.Combine(appData, "FileX");
            Directory.CreateDirectory(dir);
            _filePath = Path.Combine(dir, "settings.json");
        }
        else
        {
            _filePath = configPath;
        }

        LoadSynchronous();
    }

    private void LoadSynchronous()
    {
        try
        {
            if (File.Exists(_filePath))
            {
                var json = File.ReadAllText(_filePath);
                Settings = JsonSerializer.Deserialize<AppSettings>(json) ?? new AppSettings();
            }
            else
            {
                Settings = new AppSettings();
                SaveSynchronous();
            }
        }
        catch
        {
            Settings = new AppSettings();
        }
    }

    private void SaveSynchronous()
    {
        try
        {
            var dir = Path.GetDirectoryName(_filePath);
            if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
            var json = JsonSerializer.Serialize(Settings, _jsonOptions);
            File.WriteAllText(_filePath, json);
        }
        catch
        {
            // Non-fatal
        }
    }

    public async Task LoadAsync()
    {
        if (!File.Exists(_filePath)) return;
        try
        {
            var json = await File.ReadAllTextAsync(_filePath);
            Settings = JsonSerializer.Deserialize<AppSettings>(json) ?? new AppSettings();
        }
        catch
        {
            // Fall back to default
        }
    }

    public async Task SaveAsync()
    {
        try
        {
            var dir = Path.GetDirectoryName(_filePath);
            if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
            var json = JsonSerializer.Serialize(Settings, _jsonOptions);
            await File.WriteAllTextAsync(_filePath, json);
        }
        catch
        {
            // Non-fatal
        }
    }

    public void Set<T>(Action<AppSettings> updateAction)
    {
        updateAction(Settings);
        SaveSynchronous();
    }
}
