
export function createLayout(): HTMLElement {

  const root = document.createElement("div");

  root.innerHTML = `
    <div style="
      display:flex;
      min-height:100vh;
      font-family:system-ui;
      background:#0f172a;
      color:white;
    ">
     
      <aside style="
        width:220px;
        background:#020617;
        padding:20px;
        border-right:1px solid #1e293b;
      ">
        <h2>NHOP</h2>

        <button data-route="dashboard">Dashboard</button>
<button data-route="patients">Patients</button>
      </aside>

      <main id="app-view" style="
        flex:1;
        padding:30px;
      ">
      </main>

    </div>
  `;

  return root;
}
