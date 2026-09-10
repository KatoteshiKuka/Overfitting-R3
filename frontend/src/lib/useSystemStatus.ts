import { apiGet } from '@/api/client';
import type { SystemStatus } from '@/api/types';
import { useQuery } from '@tanstack/react-query';

/** Stato dei dataset caricati: serve alla top bar e alla home, quindi sta in `lib/`. */
export function useSystemStatus() {
  return useQuery({
    queryKey: ['system-status'],
    queryFn: () => apiGet<SystemStatus>('/system-status'),
  });
}
