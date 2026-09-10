import { ApiError, apiGet, apiPost } from '@/api/client';
import type {
  AuthState,
  CitizenSession,
  HospitalSession,
} from '@/features/auth/types';
import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';

export type AuthContextValue = {
  state: AuthState;
  loginCitizen: (username: string) => Promise<void>;
  loginOperator: (username: string, facilityId: number) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
};

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext<AuthContextValue | null>(null);

/** Una sessione assente non è un errore: è semplicemente lo stato anonimo. */
async function readSession(): Promise<AuthState> {
  try {
    const citizen = await apiGet<CitizenSession>('/auth/session');
    return { status: 'citizen', session: citizen };
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 401) throw error;
  }

  try {
    const operator = await apiGet<HospitalSession>('/auth/hospital/session');
    return { status: 'operator', session: operator };
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 401) throw error;
  }

  return { status: 'anonymous' };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: 'loading' });

  const refresh = useCallback(async () => {
    try {
      setState(await readSession());
    } catch {
      // Backend irraggiungibile: si resta anonimi, la schermata di accesso lo dirà.
      setState({ status: 'anonymous' });
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const loginCitizen = useCallback(async (username: string) => {
    const session = await apiPost<CitizenSession>('/auth/test-spid/login', { username });
    setState({ status: 'citizen', session });
  }, []);

  const loginOperator = useCallback(async (username: string, facilityId: number) => {
    const session = await apiPost<HospitalSession>('/auth/hospital/login', {
      username,
      facility_id: facilityId,
    });
    setState({ status: 'operator', session });
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiPost<void>('/auth/logout', {});
    } finally {
      // Anche se la chiamata fallisce, localmente si torna anonimi.
      setState({ status: 'anonymous' });
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ state, loginCitizen, loginOperator, logout, refresh }),
    [state, loginCitizen, loginOperator, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
