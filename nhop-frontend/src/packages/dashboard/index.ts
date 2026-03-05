
export function render(root: HTMLElement) {

  root.innerHTML = `
    <h1>📊 Dashboard</h1>
    <p>System operational.</p>
  `;

  console.log("Dashboard loaded");

  return () => console.log("Dashboard unloaded");
}
