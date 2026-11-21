package com.example.app;

/** Punto unico de acceso al almacenamiento: Postgres si hay DATABASE_URL, memoria si no. */
public final class Repos {

    private static ItemRepo instance;

    private Repos() {
    }

    public static synchronized ItemRepo get() {
        if (instance == null) {
            String url = System.getenv("DATABASE_URL");
            instance = url == null || url.isBlank() ? new MemoryRepo() : new PgRepo(url);
        }
        return instance;
    }
}
