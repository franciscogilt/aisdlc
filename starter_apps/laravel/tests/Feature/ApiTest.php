<?php

namespace Tests\Feature;

use Tests\TestCase;

class ApiTest extends TestCase
{
    public function test_health_responde(): void
    {
        $this->getJson('/health')->assertOk()->assertExactJson(['status' => 'ok']);
    }

    public function test_crea_un_item(): void
    {
        $this->postJson('/items', ['name' => 'cafe', 'quantity' => 2])
            ->assertCreated()
            ->assertExactJson(['name' => 'cafe', 'quantity' => 2]);
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
