using FileX.Core.Models;

namespace FileX.Core.Interfaces;

public interface IHistoryRepository
{
    Task<long> AddAsync(HistoryRecord record, CancellationToken cancellationToken = default);
    Task UpdateStatusAsync(long id, string status, string errorMsg = "", long fileSizeOut = 0, long durationMs = 0, CancellationToken cancellationToken = default);
    Task<IReadOnlyList<HistoryRecord>> GetAllAsync(int limit = 500, int offset = 0, CancellationToken cancellationToken = default);
    Task<IReadOnlyList<HistoryRecord>> SearchAsync(string query, int limit = 200, CancellationToken cancellationToken = default);
    Task DeleteAsync(long id, CancellationToken cancellationToken = default);
    Task ClearAllAsync(CancellationToken cancellationToken = default);
    Task<(long Total, long SuccessCount, long FailCount, long BytesIn, long BytesOut)> GetStatsAsync(CancellationToken cancellationToken = default);
}

