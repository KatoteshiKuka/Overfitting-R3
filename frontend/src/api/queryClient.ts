import { ApiError } from '@/api/client';
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      // Ritentare quando il backend è spento o la risorsa non esiste è solo attesa sprecata.
      retry: (failureCount, error) => {
        if (error instanceof ApiError && (error.status === 0 || error.status === 404)) return false;
        return failureCount < 2;
      },
    },
  },
});
