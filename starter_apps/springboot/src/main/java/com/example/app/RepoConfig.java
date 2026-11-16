package com.example.app;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RepoConfig {

    @Bean
    public ItemRepo itemRepo() {
        String url = System.getenv("DATABASE_URL");
        return url == null || url.isBlank() ? new MemoryRepo() : new PgRepo(url);
    }
}
