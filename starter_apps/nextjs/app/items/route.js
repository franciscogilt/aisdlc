import { validateItem } from "../../lib/items.js";

export async function POST(request) {
  let body;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "JSON invalido" }, { status: 400 });
  }
  const { errors, item } = validateItem(body);
  if (errors) return Response.json({ errors }, { status: 422 });
  return Response.json(item, { status: 201 });
}
