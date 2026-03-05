
export function render(root: HTMLElement) {

  root.innerHTML = `
    <h1>🧪 Laboratory Module</h1>
    <p>Lab system ready.</p>
  `;

  return () => console.log("Labs cleanup");
}
