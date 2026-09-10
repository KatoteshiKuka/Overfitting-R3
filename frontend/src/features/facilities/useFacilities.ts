import { apiGet } from '@/api/client';
import type { Facility, FacilityList, FacilityQuery, FacilitySummary } from '@/api/types';
import { useQuery } from '@tanstack/react-query';

export function useFacilities(query: FacilityQuery) {
  return useQuery({
    queryKey: ['facilities', query],
    queryFn: () => apiGet<FacilityList>('/facilities', { ...query }),
  });
}

export function useFacilitySummary() {
  return useQuery({
    queryKey: ['facilities', 'summary'],
    queryFn: () => apiGet<FacilitySummary>('/facilities/summary'),
  });
}

export function useFacility(facilityId: number) {
  return useQuery({
    queryKey: ['facilities', facilityId],
    queryFn: () => apiGet<Facility>(`/facilities/${facilityId}`),
    enabled: Number.isFinite(facilityId),
  });
}
