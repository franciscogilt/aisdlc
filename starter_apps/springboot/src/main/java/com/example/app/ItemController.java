package com.example.app;

import java.util.LinkedHashMap;
import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ItemController {

    public record ItemIn(String name, Integer quantity) {
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "ok");
    }

    @PostMapping("/items")
    public ResponseEntity<Object> create(@RequestBody ItemIn item) {
        Map<String, String> errors = new LinkedHashMap<>();
        if (item.name() == null || item.name().isEmpty() || item.name().length() > 80) {
            errors.put("name", "texto de 1 a 80 caracteres");
        }
        if (item.quantity() == null || item.quantity() < 1 || item.quantity() > 1000) {
            errors.put("quantity", "entero de 1 a 1000");
        }
        if (!errors.isEmpty()) {
            return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY).body(Map.of("errors", errors));
        }
        return ResponseEntity.status(HttpStatus.CREATED).body(item);
    }
}
