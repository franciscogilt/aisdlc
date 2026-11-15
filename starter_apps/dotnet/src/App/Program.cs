var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));

app.MapPost("/items", (ItemIn item) =>
{
    var errors = new Dictionary<string, string>();
    if (string.IsNullOrEmpty(item.Name) || item.Name.Length > 80)
    {
        errors["name"] = "texto de 1 a 80 caracteres";
    }

    if (item.Quantity is null or < 1 or > 1000)
    {
        errors["quantity"] = "entero de 1 a 1000";
    }

    return errors.Count > 0
        ? Results.Json(new { errors }, statusCode: StatusCodes.Status422UnprocessableEntity)
        : Results.Json(new { name = item.Name, quantity = item.Quantity }, statusCode: StatusCodes.Status201Created);
});

app.Run();

public record ItemIn(string? Name, int? Quantity);

// Necesario para que las pruebas puedan arrancar la app con WebApplicationFactory<Program>.
public partial class Program;
