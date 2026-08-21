const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://localhost:8000";

export async function fetchIncidentStats() {
  const response = await fetch(
    `${API_URL}/api/v1/incidents/stats`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch incident statistics"
    );
  }

  return response.json();
}

export async function fetchIncidents() {
  const response = await fetch(
    `${API_URL}/api/v1/incidents`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch incidents"
    );
  }

  return response.json();
}

export async function fetchIncident(id) {
  const response = await fetch(
    `${API_URL}/api/v1/incidents/${id}`
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch incident ${id}`
    );
  }

  return response.json();
}

export async function fetchIncidentMemory(id) {
  const response = await fetch(
    `${API_URL}/api/v1/incidents/${id}/memory`
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch incident memory ${id}`
    );
  }

  return response.json();
}