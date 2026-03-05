export function render(root: HTMLElement) {

  root.innerHTML = `
    <h1>🧍 Patients Module</h1>
    <p>Hot-swapped successfully.</p>
  `;

  return () => console.log("Patients cleanup");
}
