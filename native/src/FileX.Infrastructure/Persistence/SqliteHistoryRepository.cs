using System.IO;
using FileX.Core.Interfaces;
using FileX.Core.Models;
using Microsoft.Data.Sqlite;

namespace FileX.Infrastructure.Persistence;

public class SqliteHistoryRepository : IHistoryRepository
{
    private readonly string _connectionString;

    public SqliteHistoryRepository(string? dbPath = null)
    {
        if (string.IsNullOrEmpty(dbPath))
        {
            var appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            var dir = Path.Combine(appData, "FileX");
            Directory.CreateDirectory(dir);
            dbPath = Path.Combine(dir, "history.db");
        }

        _connectionString = new SqliteConnectionStringBuilder
        {
            DataSource = dbPath,
            Mode = SqliteOpenMode.ReadWriteCreate
        }.ToString();

        InitializeDatabase();
    }

    private void InitializeDatabase()
    {
        using var connection = new SqliteConnection(_connectionString);
        connection.Open();

        var sql = @"
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_path TEXT NOT NULL,
                source_format TEXT NOT NULL,
                output_path TEXT NOT NULL,
                output_format TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'success',
                error_msg TEXT NOT NULL DEFAULT '',
                file_size_in INTEGER NOT NULL DEFAULT 0,
                file_size_out INTEGER NOT NULL DEFAULT 0,
                duration_ms INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_history_created_at ON history(created_at DESC);
        ";

        using var cmd = new SqliteCommand(sql, connection);
        cmd.ExecuteNonQuery();
    }

    public async Task<long> AddAsync(HistoryRecord record, CancellationToken cancellationToken = default)
    {
        using var connection = new SqliteConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        var sql = @"
            INSERT INTO history (source_path, source_format, output_path, output_format, status, error_msg, file_size_in, file_size_out, duration_ms, created_at)
            VALUES (@src, @srcFmt, @out, @outFmt, @status, @err, @sizeIn, @sizeOut, @dur, @created);
            SELECT last_insert_rowid();
        ";

        using var cmd = new SqliteCommand(sql, connection);
        cmd.Parameters.AddWithValue("@src", record.SourcePath);
        cmd.Parameters.AddWithValue("@srcFmt", record.SourceFormat);
        cmd.Parameters.AddWithValue("@out", record.OutputPath);
        cmd.Parameters.AddWithValue("@outFmt", record.OutputFormat);
        cmd.Parameters.AddWithValue("@status", record.Status);
        cmd.Parameters.AddWithValue("@err", record.ErrorMessage);
        cmd.Parameters.AddWithValue("@sizeIn", record.FileSizeIn);
        cmd.Parameters.AddWithValue("@sizeOut", record.FileSizeOut);
        cmd.Parameters.AddWithValue("@dur", record.DurationMs);
        cmd.Parameters.AddWithValue("@created", record.CreatedAt.ToString("yyyy-MM-dd HH:mm:ss"));

        var result = await cmd.ExecuteScalarAsync(cancellationToken);
        return Convert.ToInt64(result);
    }

    public async Task UpdateStatusAsync(long id, string status, string errorMsg = "", long fileSizeOut = 0, long durationMs = 0, CancellationToken cancellationToken = default)
    {
        using var connection = new SqliteConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        var sql = @"
            UPDATE history
            SET status = @status, error_msg = @err, file_size_out = @sizeOut, duration_ms = @dur
            WHERE id = @id;
        ";

        using var cmd = new SqliteCommand(sql, connection);
        cmd.Parameters.AddWithValue("@id", id);
        cmd.Parameters.AddWithValue("@status", status);
        cmd.Parameters.AddWithValue("@err", errorMsg);
        cmd.Parameters.AddWithValue("@sizeOut", fileSizeOut);
        cmd.Parameters.AddWithValue("@dur", durationMs);

        await cmd.ExecuteNonQueryAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<HistoryRecord>> GetAllAsync(int limit = 500, int offset = 0, CancellationToken cancellationToken = default)
    {
        var records = new List<HistoryRecord>();
        using var connection = new SqliteConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        var sql = "SELECT * FROM history ORDER BY id DESC LIMIT @limit OFFSET @offset";
        using var cmd = new SqliteCommand(sql, connection);
        cmd.Parameters.AddWithValue("@limit", limit);
        cmd.Parameters.AddWithValue("@offset", offset);

        using var reader = await cmd.ExecuteReaderAsync(cancellationToken);
        while (await reader.ReadAsync(cancellationToken))
        {
            records.Add(MapRecord(reader));
        }

        return records;
    }

    public async Task<IReadOnlyList<HistoryRecord>> SearchAsync(string query, int limit = 200, CancellationToken cancellationToken = default)
    {
        var records = new List<HistoryRecord>();
        using var connection = new SqliteConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        var sql = @"
            SELECT * FROM history
            WHERE source_path LIKE @q OR output_path LIKE @q OR source_format LIKE @q OR output_format LIKE @q
            ORDER BY id DESC LIMIT @limit
        ";

        using var cmd = new SqliteCommand(sql, connection);
        cmd.Parameters.AddWithValue("@q", $"%{query}%");
        cmd.Parameters.AddWithValue("@limit", limit);

        using var reader = await cmd.ExecuteReaderAsync(cancellationToken);
        while (await reader.ReadAsync(cancellationToken))
        {
            records.Add(MapRecord(reader));
        }

        return records;
    }

    public async Task DeleteAsync(long id, CancellationToken cancellationToken = default)
    {
        using var connection = new SqliteConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        using var cmd = new SqliteCommand("DELETE FROM history WHERE id = @id", connection);
        cmd.Parameters.AddWithValue("@id", id);
        await cmd.ExecuteNonQueryAsync(cancellationToken);
    }

    public async Task ClearAllAsync(CancellationToken cancellationToken = default)
    {
        using var connection = new SqliteConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        using var cmd = new SqliteCommand("DELETE FROM history", connection);
        await cmd.ExecuteNonQueryAsync(cancellationToken);
    }

    public async Task<(long Total, long SuccessCount, long FailCount, long BytesIn, long BytesOut)> GetStatsAsync(CancellationToken cancellationToken = default)
    {
        using var connection = new SqliteConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        var sql = @"
            SELECT
                COUNT(*),
                COALESCE(SUM(CASE WHEN status='success' THEN 1 ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END), 0),
                COALESCE(SUM(file_size_in), 0),
                COALESCE(SUM(file_size_out), 0)
            FROM history;
        ";

        using var cmd = new SqliteCommand(sql, connection);
        using var reader = await cmd.ExecuteReaderAsync(cancellationToken);
        if (await reader.ReadAsync(cancellationToken))
        {
            return (
                reader.GetInt64(0),
                reader.GetInt64(1),
                reader.GetInt64(2),
                reader.GetInt64(3),
                reader.GetInt64(4)
            );
        }

        return (0, 0, 0, 0, 0);
    }

    private static HistoryRecord MapRecord(SqliteDataReader reader)
    {
        DateTime.TryParse(reader["created_at"]?.ToString(), out var dt);
        return new HistoryRecord
        {
            Id = Convert.ToInt64(reader["id"]),
            SourcePath = reader["source_path"]?.ToString() ?? string.Empty,
            SourceFormat = reader["source_format"]?.ToString() ?? string.Empty,
            OutputPath = reader["output_path"]?.ToString() ?? string.Empty,
            OutputFormat = reader["output_format"]?.ToString() ?? string.Empty,
            Status = reader["status"]?.ToString() ?? "success",
            ErrorMessage = reader["error_msg"]?.ToString() ?? string.Empty,
            FileSizeIn = Convert.ToInt64(reader["file_size_in"]),
            FileSizeOut = Convert.ToInt64(reader["file_size_out"]),
            DurationMs = Convert.ToInt64(reader["duration_ms"]),
            CreatedAt = dt == default ? DateTime.Now : dt
        };
    }
}
