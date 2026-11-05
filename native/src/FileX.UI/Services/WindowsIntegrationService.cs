using System.Diagnostics;
using System.IO;
using Microsoft.Win32;

namespace FileX.UI.Services;

public static class WindowsIntegrationService
{
    private const string AppName = "FileX";
    private const string RunKeyPath = @"Software\Microsoft\Windows\CurrentVersion\Run";

    public static void OpenFile(string filePath)
    {
        if (!File.Exists(filePath)) return;
        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = filePath,
                UseShellExecute = true
            });
        }
        catch
        {
            // Fallback via explorer
            Process.Start("explorer.exe", $"\"{filePath}\"");
        }
    }

    public static void OpenContainingFolder(string filePath)
    {
        if (string.IsNullOrEmpty(filePath)) return;
        try
        {
            if (File.Exists(filePath))
            {
                Process.Start("explorer.exe", $"/select,\"{filePath}\"");
            }
            else if (Directory.Exists(filePath))
            {
                Process.Start("explorer.exe", $"\"{filePath}\"");
            }
            else
            {
                var dir = Path.GetDirectoryName(filePath);
                if (Directory.Exists(dir))
                {
                    Process.Start("explorer.exe", $"\"{dir}\"");
                }
            }
        }
        catch
        {
            // Non-fatal
        }
    }

    public static bool IsInStartup()
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(RunKeyPath, false);
            return key?.GetValue(AppName) != null;
        }
        catch
        {
            return false;
        }
    }

    public static void SetStartup(bool enable)
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(RunKeyPath, true);
            if (key == null) return;

            if (enable)
            {
                var exePath = Process.GetCurrentProcess().MainModule?.FileName
                              ?? Environment.ProcessPath
                              ?? string.Empty;

                if (!string.IsNullOrEmpty(exePath))
                {
                    key.SetValue(AppName, $"\"{exePath}\"");
                }
            }
            else
            {
                key.DeleteValue(AppName, false);
            }
        }
        catch
        {
            // Non-fatal
        }
    }
}

