using System.Reflection;
using Npgsql;

public record Item(long Id, string Name, int Quantity);

/// <summary>Almacenamiento de items: Postgres si hay DATABASE_URL, memoria si no.</summary>
public interface IItemRepo
{
    Task<Item> AddAsync(string name, int quantity);

    Task<IReadOnlyList<Item>> ListAsync();
}

public sealed class MemoryRepo : IItemRepo
{
    private readonly List<Item> items = [];
    private readonly object gate = new();

    public Task<Item> AddAsync(string name, int quantity)
    {
        lock (gate)
        {
            var item = new Item(items.Count + 1L, name, quantity);
            items.Add(item);
            return Task.FromResult(item);
        }
    }

    public Task<IReadOnlyList<Item>> ListAsync()
    {
        lock (gate)
        {
            return Task.FromResult<IReadOnlyList<Item>>(items.ToList());
        }
    }
}

public sealed class PgRepo : IItemRepo
{
    private readonly NpgsqlDataSource db;

    public PgRepo(string databaseUrl)
    {
        db = NpgsqlDataSource.Create(ToConnectionString(databaseUrl));
        Migrate();
    }

    /// <summary>Acepta DATABASE_URL con forma postgresql://usuario:clave@host:5432/base.</summary>
    public static string ToConnectionString(string url)
    {
        var uri = new Uri(url);
        var user = uri.UserInfo.Split(':', 2);
        var builder = new NpgsqlConnectionStringBuilder
        {
            Host = uri.Host,
            Port = uri.Port > 0 ? uri.Port : 5432,
            Database = uri.AbsolutePath.TrimStart('/'),
            Username = Uri.UnescapeDataString(user[0]),
            Password = user.Length > 1 ? Uri.UnescapeDataString(user[1]) : null,
        };
        return builder.ConnectionString;
    }

    /// <summary>Aplica Migrations/*.sql en orden, una sola vez cada una. El lock evita carreras entre replicas.</summary>
    private void Migrate()
    {
        using var conn = db.OpenConnection();
        using var tx = conn.BeginTransaction();
        Run(conn, tx, "SELECT pg_advisory_xact_lock(727274)");
        Run(conn, tx, "CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)");

        var done = new HashSet<string>();
        using (var cmd = new NpgsqlCommand("SELECT name FROM schema_migrations", conn, tx))
        using (var reader = cmd.ExecuteReader())
        {
            while (reader.Read())
            {
                done.Add(reader.GetString(0));
            }
        }

        var assembly = Assembly.GetExecutingAssembly();
        var scripts = assembly.GetManifestResourceNames()
            .Where(n => n.EndsWith(".sql", StringComparison.Ordinal))
            .OrderBy(n => n, StringComparer.Ordinal);
        foreach (var resource in scripts)
        {
            var name = resource[(resource.IndexOf("Migrations.", StringComparison.Ordinal) + "Migrations.".Length)..];
            if (done.Contains(name))
            {
                continue;
            }

            using var stream = assembly.GetManifestResourceStream(resource)!;
            using var text = new StreamReader(stream);
            Run(conn, tx, text.ReadToEnd());
            using var record = new NpgsqlCommand("INSERT INTO schema_migrations (name) VALUES (@n)", conn, tx);
            record.Parameters.AddWithValue("n", name);
            record.ExecuteNonQuery();
        }

        tx.Commit();
    }

    private static void Run(NpgsqlConnection conn, NpgsqlTransaction tx, string sql)
    {
        using var cmd = new NpgsqlCommand(sql, conn, tx);
        cmd.ExecuteNonQuery();
    }

    public async Task<Item> AddAsync(string name, int quantity)
    {
        await using var cmd = db.CreateCommand("INSERT INTO items (name, quantity) VALUES ($1, $2) RETURNING id, name, quantity");
        cmd.Parameters.AddWithValue(name);
        cmd.Parameters.AddWithValue(quantity);
        await using var reader = await cmd.ExecuteReaderAsync();
        await reader.ReadAsync();
        return new Item(reader.GetInt64(0), reader.GetString(1), reader.GetInt32(2));
    }

    public async Task<IReadOnlyList<Item>> ListAsync()
    {
        var items = new List<Item>();
        await using var cmd = db.CreateCommand("SELECT id, name, quantity FROM items ORDER BY id");
        await using var reader = await cmd.ExecuteReaderAsync();
        while (await reader.ReadAsync())
        {
            items.Add(new Item(reader.GetInt64(0), reader.GetString(1), reader.GetInt32(2)));
        }

        return items;
    }
}
