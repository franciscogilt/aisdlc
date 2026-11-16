package com.example.app;

import java.util.List;

/** Almacenamiento de items: Postgres si hay DATABASE_URL, memoria si no. */
public interface ItemRepo {

    Item add(String name, int quantity);

    List<Item> list();
}
