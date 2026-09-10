import { AuthContext, type AuthContextValue } from '@/features/auth/AuthContext';
import { useContext } from 'react';

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (value === null) {
    throw new Error('useAuth va usato dentro <AuthProvider>.');
  }
  return value;
}
