using FileX.Core.Models;

namespace FileX.Core.Interfaces;

public interface ISettingsService
{
    AppSettings Settings { get; }
    Task LoadAsync();
    Task SaveAsync();
    void Set<T>(Action<AppSettings> updateAction);
}

