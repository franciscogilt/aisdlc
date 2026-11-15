import { TestBed } from '@angular/core/testing';

import { App } from './app';

describe('App', () => {
  async function render() {
    await TestBed.configureTestingModule({ imports: [App] }).compileComponents();
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    return fixture;
  }

  async function submit(fixture: Awaited<ReturnType<typeof render>>, name: string, quantity: string) {
    const root = fixture.nativeElement as HTMLElement;
    root.querySelector<HTMLInputElement>('input[name=name]')!.value = name;
    root.querySelector<HTMLInputElement>('input[name=quantity]')!.value = quantity;
    root.querySelector('form')!.dispatchEvent(new Event('submit', { cancelable: true }));
    await fixture.whenStable();
    return root;
  }

  it('agrega un item valido', async () => {
    const root = await submit(await render(), 'cafe', '2');
    expect(root.querySelector('li')?.textContent).toContain('cafe x 2');
  });

  it('rechaza una cantidad invalida', async () => {
    const root = await submit(await render(), 'cafe', '0');
    expect(root.querySelector('[role=alert]')?.textContent).toContain('entero de 1 a 1000');
    expect(root.querySelector('li')).toBeNull();
  });

  it('rechaza un nombre vacio', async () => {
    const root = await submit(await render(), '', '2');
    expect(root.querySelector('[role=alert]')?.textContent).toContain('texto de 1 a 80');
  });
});
