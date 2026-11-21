package com.example.app;

import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Properties;
import java.util.Set;


public class PgRepo implements ItemRepo {

    private final String jdbcUrl;
    private final Properties props = new Properties();

    /** Acepta DATABASE_URL con forma postgresql://usuario:clave@host:5432/base. */
    public PgRepo(String databaseUrl) {
        URI uri = URI.create(databaseUrl);
        int port = uri.getPort() == -1 ? 5432 : uri.getPort();
        this.jdbcUrl = "jdbc:postgresql://" + uri.getHost() + ":" + port + uri.getPath();
        if (uri.getUserInfo() != null) {
            String[] user = uri.getUserInfo().split(":", 2);
            props.setProperty("user", user[0]);
            if (user.length > 1) {
                props.setProperty("password", user[1]);
            }
        }
        migrate();
    }

    private Connection connect() throws SQLException {
        return DriverManager.getConnection(jdbcUrl, props);
    }

    /** Aplica db/migrations/*.sql en orden, una sola vez cada una. El lock evita carreras entre replicas. */
    private void migrate() {
        try (Connection conn = connect()) {
            conn.setAutoCommit(false);
            try (Statement st = conn.createStatement()) {
                st.execute("SELECT pg_advisory_xact_lock(727274)");
                st.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)");
                Set<String> done = new HashSet<>();
                try (ResultSet rs = st.executeQuery("SELECT name FROM schema_migrations")) {
                    while (rs.next()) {
                        done.add(rs.getString(1));
                    }
                }
                for (String file : migrationNames()) {
                    if (done.contains(file)) {
                        continue;
                    }
                    st.execute(readResource("db/migrations/" + file));
                    String record = "INSERT INTO schema_migrations (name) VALUES (?)";
                    try (PreparedStatement ins = conn.prepareStatement(record)) {
                        ins.setString(1, file);
                        ins.executeUpdate();
                    }
                }
            }
            conn.commit();
        } catch (SQLException | IOException e) {
            throw new IllegalStateException("fallo la migracion de la base de datos", e);
        }
    }

    /** Las migraciones se listan en db/migrations/index.txt (una por linea, en orden). */
    private static List<String> migrationNames() throws IOException {
        return readResource("db/migrations/index.txt").lines().map(String::strip).filter(l -> !l.isEmpty()).toList();
    }

    private static String readResource(String path) throws IOException {
        try (InputStream in = Thread.currentThread().getContextClassLoader().getResourceAsStream(path)) {
            if (in == null) {
                throw new IOException("no existe el recurso " + path);
            }
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    @Override
    public Item add(String name, int quantity) {
        String sql = "INSERT INTO items (name, quantity) VALUES (?, ?) RETURNING id, name, quantity";
        try (Connection conn = connect(); PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, name);
            ps.setInt(2, quantity);
            try (ResultSet rs = ps.executeQuery()) {
                rs.next();
                return new Item(rs.getLong(1), rs.getString(2), rs.getInt(3));
            }
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }

    @Override
    public List<Item> list() {
        List<Item> out = new ArrayList<>();
        try (Connection conn = connect();
                Statement st = conn.createStatement();
                ResultSet rs = st.executeQuery("SELECT id, name, quantity FROM items ORDER BY id")) {
            while (rs.next()) {
                out.add(new Item(rs.getLong(1), rs.getString(2), rs.getInt(3)));
            }
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
        return out;
    }
}
