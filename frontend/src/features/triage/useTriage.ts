import { apiGet, apiPost } from '@/api/client';
import type {
  ChatMessage,
  ChatResponse,
  NearbyResponse,
  PlanResponse,
  TriageStatus,
} from '@/features/triage/types';
import type { TriageCode } from '@/lib/triage';
import { useMutation, useQuery } from '@tanstack/react-query';

export function useTriageStatus() {
  return useQuery({
    queryKey: ['triage', 'status'],
    queryFn: () => apiGet<TriageStatus>('/triage/status'),
    // Il modello locale può essere acceso o spento durante la sessione.
    staleTime: 10_000,
  });
}

export function useSendMessage() {
  return useMutation({
    mutationFn: (messages: ChatMessage[]) =>
      apiPost<ChatResponse>('/triage/messages', { messages }),
  });
}

export function usePlan() {
  return useMutation({
    mutationFn: (input: { address: string; code: TriageCode }) =>
      apiPost<PlanResponse>('/triage/plan', { ...input, limit: 5 }),
  });
}

export function useNearbyFacilities() {
  return useMutation({
    mutationFn: (address: string) =>
      apiPost<NearbyResponse>('/triage/nearby', { address, limit: 8 }),
  });
}
