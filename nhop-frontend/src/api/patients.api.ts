import api from "./client";

export async function createPatient(name: string) {
  const response = await api.post("/doctor/patients", { name });
  return response.data;
}
