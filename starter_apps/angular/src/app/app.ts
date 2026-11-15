import { Component, signal } from '@angular/core';

import { Item, validateItem } from './validate';

@Component({
  selector: 'app-root',
  template: `
    <main>
      <h1>Starter Angular</h1>
      <form (submit)="add($event, name.value, quantity.value)">
        <label>Nombre <input #name name="name" /></label>
        @if (errors()['name']) {
          <p role="alert">{{ errors()['name'] }}</p>
        }
        <label>Cantidad <input #quantity name="quantity" type="number" /></label>
        @if (errors()['quantity']) {
          <p role="alert">{{ errors()['quantity'] }}</p>
        }
        <button type="submit">Agregar</button>
      </form>
      <ul>
        @for (item of items(); track $index) {
          <li>{{ item.name }} x {{ item.quantity }}</li>
        }
      </ul>
    </main>
  `,
})
export class App {
  protected readonly items = signal<Item[]>([]);
  protected readonly errors = signal<Record<string, string>>({});

  protected add(event: Event, name: string, quantity: string): void {
    event.preventDefault();
    const item: Item = { name, quantity: Number(quantity) };
    const found = validateItem(item);
    this.errors.set(found);
    if (Object.keys(found).length === 0) {
      this.items.update((current) => [...current, item]);
    }
  }
}
