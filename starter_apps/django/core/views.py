import json

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


@require_POST
def create_item(request):
    """Valida la entrada a mano. Sin sesiones ni cookies, por eso no hace falta CSRF en esta API."""
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON invalido"}, status=400)
    name, quantity = data.get("name"), data.get("quantity")
    errors = {}
    if not isinstance(name, str) or not 1 <= len(name) <= 80:
        errors["name"] = "texto de 1 a 80 caracteres"
    if isinstance(quantity, bool) or not isinstance(quantity, int) or not 1 <= quantity <= 1000:
        errors["quantity"] = "entero de 1 a 1000"
    if errors:
        return JsonResponse({"errors": errors}, status=422)
    return JsonResponse({"name": name, "quantity": quantity}, status=201)
