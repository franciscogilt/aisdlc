<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

Route::get('/health', fn () => response()->json(['status' => 'ok']));

Route::post('/items', function (Request $request) {
    $data = json_decode($request->getContent(), true);
    if (! is_array($data)) {
        return response()->json(['error' => 'JSON invalido'], 400);
    }

    $errors = [];
    $name = $data['name'] ?? null;
    if (! is_string($name) || strlen($name) < 1 || strlen($name) > 80) {
        $errors['name'] = 'texto de 1 a 80 caracteres';
    }
    $quantity = $data['quantity'] ?? null;
    if (! is_int($quantity) || $quantity < 1 || $quantity > 1000) {
        $errors['quantity'] = 'entero de 1 a 1000';
    }
    if ($errors !== []) {
        return response()->json(['errors' => $errors], 422);
    }

    return response()->json(['name' => $name, 'quantity' => $quantity], 201);
});
