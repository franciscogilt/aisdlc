<?php

namespace Tests\Feature;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class ApiTest extends TestCase
{
    use RefreshDatabase;

    public function test_health_responde(): void
    {
        $this->getJson('/health')->assertOk()->assertExactJson(['status' => 'ok']);
    }

    public function test_crea_un_item(): void
    {
        $this->postJson('/items', ['name' => 'cafe', 'quantity' => 2])
            ->assertCreated()
            ->assertJsonPath('name', 'cafe')
            ->assertJsonPath('quantity', 2);
    }

    public function test_crea_y_lista_items(): void
    {
        $this->postJson('/items', ['name' => 'listado', 'quantity' => 3])->assertCreated();
        $this->getJson('/items')->assertOk()->assertJsonPath('0.name', 'listado');
    }

    public function test_rechaza_cantidad_invalida(): void
    {
        $this->postJson('/items', ['name' => 'cafe', 'quantity' => 0])->assertStatus(422);
    }

    public function test_rechaza_json_invalido(): void
    {
        $this->call('POST', '/items', [], [], [], ['CONTENT_TYPE' => 'application/json'], 'no-json')
            ->assertStatus(400);
    }
}
