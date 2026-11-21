package com.example.app;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;

class RepoTests {

    private void roundTrip(ItemRepo repo) {
        int before = repo.list().size();
        Item saved = repo.add("cafe", 2);
        assertEquals("cafe", saved.name());
        assertEquals(before + 1, repo.list().size());
        assertTrue(repo.list().contains(saved));
    }

    @Test
    void memoriaGuardaYLista() {
        roundTrip(new MemoryRepo());
    }

    @Test
    @EnabledIfEnvironmentVariable(named = "DATABASE_URL", matches = ".+")
    void postgresGuardaYLista() {
        roundTrip(new PgRepo(System.getenv("DATABASE_URL")));
    }

    @Test
    @EnabledIfEnvironmentVariable(named = "DATABASE_URL", matches = ".+")
    void migracionesSonIdempotentes() {
        String url = System.getenv("DATABASE_URL");
        new PgRepo(url);
        new PgRepo(url);
    }
}
