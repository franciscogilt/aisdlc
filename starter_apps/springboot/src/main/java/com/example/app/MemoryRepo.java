package com.example.app;

import java.util.ArrayList;
import java.util.List;

public class MemoryRepo implements ItemRepo {

    private final List<Item> items = new ArrayList<>();

    @Override
    public synchronized Item add(String name, int quantity) {
        Item item = new Item(items.size() + 1L, name, quantity);
        items.add(item);
        return item;
    }

    @Override
    public synchronized List<Item> list() {
        return List.copyOf(items);
    }
}
