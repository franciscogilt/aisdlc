export interface Item {
  name: string;
  quantity: number;
}

export function validateItem(item: Item): Record<string, string> {
  const errors: Record<string, string> = {};
  if (item.name.length < 1 || item.name.length > 80) {
    errors['name'] = 'texto de 1 a 80 caracteres';
  }
  if (!Number.isInteger(item.quantity) || item.quantity < 1 || item.quantity > 1000) {
    errors['quantity'] = 'entero de 1 a 1000';
  }
  return errors;
}
