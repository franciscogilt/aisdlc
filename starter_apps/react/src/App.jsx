import { useState } from "react";

import { validateItem } from "./validate.js";

export default function App() {
  const [items, setItems] = useState([]);
  const [errors, setErrors] = useState({});

  function onSubmit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const item = { name: form.get("name"), quantity: Number(form.get("quantity")) };
    const found = validateItem(item);
    setErrors(found);
    if (Object.keys(found).length === 0) {
      setItems((current) => [...current, item]);
      event.currentTarget.reset();
    }
  }

  return (
    <main>
      <h1>Starter React</h1>
      <form onSubmit={onSubmit}>
        <label>
          Nombre <input name="name" />
        </label>
        {errors.name && <p role="alert">{errors.name}</p>}
        <label>
          Cantidad <input name="quantity" type="number" />
        </label>
        {errors.quantity && <p role="alert">{errors.quantity}</p>}
        <button type="submit">Agregar</button>
      </form>
      <ul>
        {items.map((item, i) => (
          <li key={i}>
            {item.name} x {item.quantity}
          </li>
        ))}
      </ul>
    </main>
  );
}
