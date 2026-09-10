import type { TriageCode } from '@/lib/triage';

export type ChatRole = 'user' | 'assistant';

export type ChatMessage = {
  role: ChatRole;
  content: string;
};

export type Assessment = {
  code: TriageCode;
  reason: string;
  care_setting: string;
  advice: string;
  /** `true` se le regole di sicurezza hanno alzato il codice deciso dal modello. */
  escalated: boolean;
  red_flags: string[];
};

export type ChatResponse = {
  reply: string;
  done: boolean;
  assessment: Assessment | null;
  /** `locale`, `groq` o `regole`. */
  provider: string;
};

export type PlanOption = {
  facility_id: number;
  name: string;
  type: string;
  address: string | null;
  municipality: string | null;
  latitude: number;
  longitude: number;
  distance_km: number;
  travel_minutes: number;
  waiting_minutes: number;
  total_minutes: number;
  congestion_level: 'basso' | 'medio' | 'alto';
  congestion_ratio: number;
  route_source: 'osrm' | 'stimato';
  recommended: boolean;
};

export type PlanResponse = {
  origin: { label: string; latitude: number; longitude: number };
  options: PlanOption[];
  advice: string;
  provider: string;
};

export type ProviderStatus = {
  name: string;
  model: string;
  available: boolean;
};

export type TriageStatus = {
  providers: ProviderStatus[];
  fallback_ready: boolean;
};
