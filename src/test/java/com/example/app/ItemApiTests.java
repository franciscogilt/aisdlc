package com.example.app;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class ItemApiTests {

    @Value("${local.server.port}")
    private int port;

    private final HttpClient client = HttpClient.newHttpClient();

    private HttpResponse<String> send(HttpRequest.Builder request) throws Exception {
        return client.send(request.build(), HttpResponse.BodyHandlers.ofString());
    }

    private HttpResponse<String> post(String body) throws Exception {
        return send(HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/items"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(body)));
    }

    @Test
    void healthResponde() throws Exception {
        HttpResponse<String> r = send(HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/health")));
        assertEquals(200, r.statusCode());
        assertTrue(r.body().contains("\"status\":\"ok\""));
    }

    @Test
    void creaUnItem() throws Exception {
        HttpResponse<String> r = post("{\"name\":\"cafe\",\"quantity\":2}");
        assertEquals(201, r.statusCode());
        assertTrue(r.body().contains("\"name\":\"cafe\""));
    }

    @Test
    void rechazaCantidadInvalida() throws Exception {
        assertEquals(422, post("{\"name\":\"cafe\",\"quantity\":0}").statusCode());
    }

    @Test
    void rechazaJsonInvalido() throws Exception {
        assertEquals(400, post("no-json").statusCode());
    }
}
