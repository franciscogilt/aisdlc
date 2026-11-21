package com.example.app;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

@Path("/")
@Produces(MediaType.APPLICATION_JSON)
public class ItemResource {

    public record ItemIn(String name, Integer quantity) {
    }

    @GET
    @Path("/health")
    public Map<String, String> health() {
        return Map.of("status", "ok");
    }

    @GET
    @Path("/items")
    public List<Item> list() {
        return Repos.get().list();
    }

    @POST
    @Path("/items")
    @Consumes(MediaType.APPLICATION_JSON)
    public Response create(ItemIn item) {
        Map<String, String> errors = new LinkedHashMap<>();
        if (item == null || item.name() == null || item.name().isEmpty() || item.name().length() > 80) {
            errors.put("name", "texto de 1 a 80 caracteres");
        }
        if (item == null || item.quantity() == null || item.quantity() < 1 || item.quantity() > 1000) {
            errors.put("quantity", "entero de 1 a 1000");
        }
        if (!errors.isEmpty()) {
            return Response.status(422).entity(Map.of("errors", errors)).build();
        }
        return Response.status(Response.Status.CREATED).entity(Repos.get().add(item.name(), item.quantity())).build();
    }
}
