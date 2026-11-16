package com.example.app;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.hasItem;
import static org.hamcrest.Matchers.is;

import io.quarkus.test.junit.QuarkusTest;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;

@QuarkusTest
class ItemResourceTest {

    @Test
    void healthResponde() {
        given().when().get("/health").then().statusCode(200).body("status", is("ok"));
    }

    @Test
    void creaUnItem() {
        given().contentType(ContentType.JSON).body("{\"name\":\"cafe\",\"quantity\":2}")
                .when().post("/items").then().statusCode(201).body("name", is("cafe"));
    }

    @Test
    void creaYListaItems() {
        given().contentType(ContentType.JSON).body("{\"name\":\"listado\",\"quantity\":3}")
                .when().post("/items").then().statusCode(201);
        given().when().get("/items").then().statusCode(200).body("name", hasItem("listado"));
    }

    @Test
    void rechazaCantidadInvalida() {
        given().contentType(ContentType.JSON).body("{\"name\":\"cafe\",\"quantity\":0}")
                .when().post("/items").then().statusCode(422);
    }

    @Test
    void rechazaJsonInvalido() {
        given().contentType(ContentType.JSON).body("no-json")
                .when().post("/items").then().statusCode(400);
    }
}
