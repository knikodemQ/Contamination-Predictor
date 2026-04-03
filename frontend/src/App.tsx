import { useEffect, useState } from 'react';

import { API_BASE, getUserRuns, loginUser, registerUser, runSimulation, type RunSummary, type SimulationResult, type UserSession } from './api';
import HeatmapCanvas from './components/HeatmapCanvas';
import { StatCard } from './components/InfoCard';

type AuthMode = 'login' | 'register';
type ViewTab = 'simulation' | 'account';

type AuthFormState = {
  username: string;
  password: string;
};

type SimFormState = {
  sourceLat: number;
  sourceLon: number;
  initialOilMass: number;
  temperatureC: number;
  days: number;
  stepsPerDay: number;
};

const DEFAULT_AUTH: AuthFormState = { username: '', password: '' };
const DEFAULT_SIM: SimFormState = {
  sourceLat: 28.7,
  sourceLon: -88.3,
  initialOilMass: 100,
  temperatureC: 20,
  days: 4,
  stepsPerDay: 3,
};

function formatNumber(value: number) {
  return Number(value).toLocaleString('pl-PL', { maximumFractionDigits: 2 });
}

function loadStoredUser(): UserSession | null {
  try {
    const stored = localStorage.getItem('contamination-user');
    if (!stored) {
      return null;
    }

    const parsed = JSON.parse(stored) as UserSession;
    if (!parsed.username || parsed.username.trim().toLowerCase() === 'demo') {
      return null;
    }

    return parsed;
  } catch {
    return null;
  }
}

export default function App() {
  const [activeTab, setActiveTab] = useState<ViewTab>('simulation');
  const [mode, setMode] = useState<AuthMode>('login');
  const [authForm, setAuthForm] = useState<AuthFormState>(DEFAULT_AUTH);
  const [simForm, setSimForm] = useState<SimFormState>(DEFAULT_SIM);
  const [currentUser, setCurrentUser] = useState<UserSession | null>(loadStoredUser);
  const [history, setHistory] = useState<RunSummary[]>([]);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [message, setMessage] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [authLoading, setAuthLoading] = useState(false);
  const [simulationLoading, setSimulationLoading] = useState(false);

  useEffect(() => {
    if (currentUser) {
      localStorage.setItem('contamination-user', JSON.stringify(currentUser));
      return;
    }

    localStorage.removeItem('contamination-user');
  }, [currentUser]);

  useEffect(() => {
    let cancelled = false;

    async function loadHistory() {
      if (!currentUser?.username) {
        setHistory([]);
        return;
      }

      try {
        const runs = await getUserRuns(currentUser.username);
        if (!cancelled) {
          setHistory(runs);
        }
      } catch {
        if (!cancelled) {
          setHistory([]);
        }
      }
    }

    loadHistory();

    return () => {
      cancelled = true;
    };
  }, [currentUser]);

  async function submitAuth(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthLoading(true);
    setError('');
    setMessage('');

    try {
      const action = mode === 'register' ? registerUser : loginUser;
      const payload = await action(authForm.username, authForm.password);
      setCurrentUser(payload);
      setMessage(mode === 'register' ? 'Konto utworzone.' : 'Zalogowano pomyślnie.');
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : 'Wystąpił błąd logowania');
    } finally {
      setAuthLoading(false);
    }
  }

  async function submitSimulation(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!currentUser?.username) {
      setError('Najpierw zaloguj użytkownika.');
      return;
    }

    setSimulationLoading(true);
    setError('');
    setMessage('');

    try {
      const payload = await runSimulation({
        username: currentUser.username,
        ...simForm,
      });

      setResult(payload.result);
      setMessage('Symulacja zakończona.');
      setHistory(await getUserRuns(currentUser.username));
    } catch (simulationError) {
      setError(simulationError instanceof Error ? simulationError.message : 'Wystąpił błąd symulacji');
    } finally {
      setSimulationLoading(false);
    }
  }

  function handleAuthChange(field: keyof AuthFormState, value: string) {
    setAuthForm((current) => ({ ...current, [field]: value }));
  }

  function handleSimChange(field: keyof SimFormState, value: string) {
    const numericFields: Array<keyof SimFormState> = ['sourceLat', 'sourceLon', 'temperatureC', 'initialOilMass', 'days', 'stepsPerDay'];
    setSimForm((current) => ({
      ...current,
      [field]: numericFields.includes(field) ? Number(value) : value,
    }));
  }

  const totalMass = result ? formatNumber(result.total_mass) : '—';
  const maxCellMass = result ? formatNumber(result.max_cell_mass) : '—';
  const steps = result ? result.steps : '—';
  const mapBackgroundUrl = `${API_BASE}/map-background`;

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Contamination Predictor</p>
          <h1>Wyniki symulacji skażenia morskiego</h1>
          <p className="hero-copy">Parametry uruchomienia, statystyki i mapa rozkładu masy ropy.</p>
        </div>

        <div className="hero-status">
          <span>Aktywny użytkownik</span>
          <strong>{currentUser?.username || 'brak'}</strong>
          <p>{message || 'Uruchom symulację po zalogowaniu.'}</p>
          {error ? <p className="error-box">{error}</p> : null}
        </div>
      </header>

      <div className="main-tabs" role="tablist" aria-label="Zakladki aplikacji">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'simulation'}
          className={activeTab === 'simulation' ? 'active' : ''}
          onClick={() => setActiveTab('simulation')}
        >
          Symulacja
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'account'}
          className={activeTab === 'account' ? 'active' : ''}
          onClick={() => setActiveTab('account')}
        >
          Użytkownik
        </button>
      </div>

      {activeTab === 'simulation' ? (
        <main className="layout-grid">
          <section className="panel sim-panel wide-panel">
            <div className="panel-header">
              <div>
                <p className="section-label">1. Parametry</p>
                <h2>Uruchomienie symulacji</h2>
              </div>
            </div>

            {!currentUser ? (
              <div className="empty-state">
                Żeby uruchomić symulację, przejdź do zakładki Użytkownik i zaloguj się.
                <button type="button" className="inline-link" onClick={() => setActiveTab('account')}>
                  Przejdź do zakładki Użytkownik
                </button>
              </div>
            ) : null}

            <form className="stack-form" onSubmit={submitSimulation}>
              <div className="form-grid">
                <label>
                  Szerokość geograficzna
                  <input type="number" step="0.1" value={simForm.sourceLat} onChange={(event) => handleSimChange('sourceLat', event.target.value)} />
                </label>
                <label>
                  Długość geograficzna
                  <input type="number" step="0.1" value={simForm.sourceLon} onChange={(event) => handleSimChange('sourceLon', event.target.value)} />
                </label>
                <label>
                  Masa początkowa
                  <input type="number" step="1" value={simForm.initialOilMass} onChange={(event) => handleSimChange('initialOilMass', event.target.value)} />
                </label>
                <label>
                  Temperatura C
                  <input type="number" step="1" value={simForm.temperatureC} onChange={(event) => handleSimChange('temperatureC', event.target.value)} />
                </label>
                <label>
                  Dni symulacji
                  <input type="number" min="1" max="10" value={simForm.days} onChange={(event) => handleSimChange('days', event.target.value)} />
                </label>
                <label>
                  Kroków na dzień
                  <input type="number" min="1" max="12" value={simForm.stepsPerDay} onChange={(event) => handleSimChange('stepsPerDay', event.target.value)} />
                </label>
              </div>
              <button className="primary-button" type="submit" disabled={simulationLoading || !currentUser}>
                {simulationLoading ? 'Przetwarzanie...' : 'Uruchom symulację'}
              </button>
            </form>
          </section>

          <section className="panel stats-panel">
            <div className="panel-header">
              <div>
                <p className="section-label">2. Statystyki</p>
                <h2>Podsumowanie wyniku</h2>
              </div>
            </div>
            <div className="stats-grid">
              <StatCard label="Łączna masa" value={totalMass} hint="wartość z ostatniego kroku" />
              <StatCard label="Maks. komórka" value={maxCellMass} hint="najmocniejszy punkt" />
              <StatCard label="Liczba kroków" value={steps} hint="iteracje backendu" />
            </div>
          </section>

          <section className="panel heatmap-panel">
            <div className="panel-header">
              <div>
                <p className="section-label">3. Mapa</p>
                <h2>Rozkład masy ropy</h2>
              </div>
            </div>
            {result ? (
              <div className="heatmap-wrap">
                <HeatmapCanvas grid={result.final_grid} backgroundUrl={mapBackgroundUrl} />
                <p className="caption">Jaśniejsze obszary oznaczają większą koncentrację masy.</p>
              </div>
            ) : (
              <div className="empty-state">Uruchom symulację, aby wyświetlić mapę wynikową.</div>
            )}
          </section>

          <section className="panel history-panel">
            <div className="panel-header">
              <div>
                <p className="section-label">4. Historia</p>
                <h2>Ostatnie uruchomienia</h2>
              </div>
            </div>
            {history.length > 0 ? (
              <div className="history-list">
                {history.map((run) => (
                  <article key={run.id} className="history-item">
                    <strong>Uruchomienie {run.id}</strong>
                    <p>{run.created_at}</p>
                    <p>
                      start: {run.source_lat}, {run.source_lon}
                    </p>
                    <p>masa: {formatNumber(run.total_mass)}</p>
                  </article>
                ))}
              </div>
            ) : (
              <div className="empty-state">Brak zapisanych uruchomień dla bieżącego użytkownika.</div>
            )}
          </section>
        </main>
      ) : (
        <main className="layout-grid">
          <section className="panel auth-panel wide-panel">
            <div className="panel-header">
              <div>
                <p className="section-label">Konto</p>
                <h2>Logowanie i rejestracja</h2>
              </div>
              <div className="tab-switcher">
                <button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')} type="button">
                  Logowanie
                </button>
                <button className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')} type="button">
                  Rejestracja
                </button>
              </div>
            </div>

            <form className="stack-form" onSubmit={submitAuth}>
              <label>
                Nazwa użytkownika
                <input value={authForm.username} onChange={(event) => handleAuthChange('username', event.target.value)} placeholder="np. operator1" />
              </label>
              <label>
                Hasło
                <input
                  type="password"
                  value={authForm.password}
                  onChange={(event) => handleAuthChange('password', event.target.value)}
                  placeholder="minimum 4 znaki"
                />
              </label>
              <button className="primary-button" type="submit" disabled={authLoading}>
                {authLoading ? 'Przetwarzanie...' : mode === 'login' ? 'Zaloguj' : 'Utwórz konto'}
              </button>
            </form>

            <div className="mini-note">Po poprawnym logowaniu wróć do zakładki Symulacja, żeby uruchomić obliczenia.</div>
          </section>
        </main>
      )}
    </div>
  );
}