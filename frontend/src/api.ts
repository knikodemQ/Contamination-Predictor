export const API_BASE = 'http://127.0.0.1:8000/api';

type RequestOptions = RequestInit;

async function requestJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  const payload: unknown = await response.json();
  if (!response.ok) {
    const detail = typeof payload === 'object' && payload !== null && 'detail' in payload
      ? String((payload as { detail?: unknown }).detail ?? 'Wystąpił błąd API')
      : 'Wystąpił błąd API';
    throw new Error(detail);
  }

  return payload as T;
}

export interface UserSession {
  id: number;
  username: string;
  createdAt?: string;
}

export interface RunSummary {
  id: number;
  created_at: string;
  source_lat: number;
  source_lon: number;
  initial_oil_mass: number;
  temperature_c: number;
  steps: number;
  total_mass: number;
  max_cell_mass: number;
}

export interface SimulationResult {
  source_lat: number;
  source_lon: number;
  initial_oil_mass: number;
  temperature_c: number;
  steps: number;
  total_mass: number;
  max_cell_mass: number;
  snapshots: Array<{ step: number; totalMass: number; maxCellMass: number }>;
  final_grid: number[][];
}

export interface SimulationResponse {
  run: { id: number; username: string; created_at: string };
  result: SimulationResult;
}

export function registerUser(username: string, password: string) {
  return requestJson<UserSession>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export function loginUser(username: string, password: string) {
  return requestJson<UserSession>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export function getUserRuns(username: string) {
  return requestJson<RunSummary[]>(`/users/${username}/runs`);
}

export function runSimulation(payload: {
  username: string;
  sourceLat: number;
  sourceLon: number;
  initialOilMass: number;
  temperatureC: number;
  days: number;
  stepsPerDay: number;
}) {
  return requestJson<SimulationResponse>('/simulations/run', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}