using System.Net;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.Mvc.Testing;

namespace App.Tests;

public class ApiTests(WebApplicationFactory<Program> factory) : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient client = factory.CreateClient();

    [Fact]
    public async Task HealthResponde()
    {
        var response = await client.GetAsync("/health");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var body = await response.Content.ReadFromJsonAsync<JsonElement>();
        Assert.Equal("ok", body.GetProperty("status").GetString());
    }

    [Fact]
    public async Task CreaUnItem()
    {
        var response = await client.PostAsJsonAsync("/items", new { name = "cafe", quantity = 2 });

        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        var body = await response.Content.ReadFromJsonAsync<JsonElement>();
        Assert.Equal("cafe", body.GetProperty("name").GetString());
    }

    [Fact]
    public async Task CreaYListaItems()
    {
        await client.PostAsJsonAsync("/items", new { name = "listado", quantity = 3 });

        var body = await client.GetFromJsonAsync<JsonElement>("/items");

        Assert.Contains(body.EnumerateArray(), i => i.GetProperty("name").GetString() == "listado");
    }

    [Fact]
    public async Task RechazaCantidadInvalida()
    {
        var response = await client.PostAsJsonAsync("/items", new { name = "cafe", quantity = 0 });

        Assert.Equal(HttpStatusCode.UnprocessableEntity, response.StatusCode);
    }

    [Fact]
    public async Task RechazaJsonInvalido()
    {
        using var content = new StringContent("no-json", Encoding.UTF8, "application/json");

        var response = await client.PostAsync("/items", content);

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
    }
}
