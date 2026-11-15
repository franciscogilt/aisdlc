import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";

import App from "./App.jsx";

afterEach(cleanup);

function submit(name, quantity) {
  fireEvent.change(screen.getByLabelText(/nombre/i), { target: { value: name } });
  fireEvent.change(screen.getByLabelText(/cantidad/i), { target: { value: quantity } });
  fireEvent.click(screen.getByRole("button", { name: /agregar/i }));
}

test("agrega un item valido", () => {
  render(<App />);
  submit("cafe", "2");
  expect(screen.getByText("cafe x 2")).toBeTruthy();
});

test("rechaza una cantidad invalida", () => {
  render(<App />);
  submit("cafe", "0");
  expect(screen.getByRole("alert").textContent).toContain("entero de 1 a 1000");
  expect(screen.queryByText("cafe x 0")).toBeNull();
});

test("rechaza un nombre vacio", () => {
  render(<App />);
  submit("", "2");
  expect(screen.getByRole("alert").textContent).toContain("texto de 1 a 80");
});
