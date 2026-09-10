import { useCallback, useEffect, useState } from 'react';

export type Role = 'paziente' | 'operatore';

const STORAGE_KEY = 'presidio-role';

function readStoredRole(): Role | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === 'paziente' || stored === 'operatore' ? stored : null;
  } catch {
    // Storage bloccato: si riparte dalla scelta del ruolo, che non è un errore.
    return null;
  }
}

/** Ruolo scelto all'apertura. Ricordato tra le sessioni, ma sempre cambiabile. */
export function useRole() {
  const [role, setRoleState] = useState<Role | null>(readStoredRole);

  useEffect(() => {
    try {
      if (role) localStorage.setItem(STORAGE_KEY, role);
      else localStorage.removeItem(STORAGE_KEY);
    } catch {
      // La scelta vale solo per questa sessione.
    }
  }, [role]);

  const setRole = useCallback((next: Role) => setRoleState(next), []);
  const clearRole = useCallback(() => setRoleState(null), []);

  return { role, setRole, clearRole };
}
