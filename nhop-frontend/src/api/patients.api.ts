export async function createPatient(name: string) {
  const response = await fetch("http://localhost:3000/patients", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name }),
  });

  return response.json();
}
