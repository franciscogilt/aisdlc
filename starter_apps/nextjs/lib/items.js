// Validacion pura (sin Next): se prueba con `node --test` sin levantar el servidor.
export function validateItem(body) {
  const { name, quantity } = body ?? {};
  const errors = {};
  if (typeof name !== "string" || name.length < 1 || name.length > 80) {
    errors.name = "texto de 1 a 80 caracteres";
  }
  if (!Number.isInteger(quantity) || quantity < 1 || quantity > 1000) {
    errors.quantity = "entero de 1 a 1000";
  }
  return Object.keys(errors).length > 0 ? { errors } : { item: { name, quantity } };
}
