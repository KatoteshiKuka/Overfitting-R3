export type Provenance =
  | 'OBSERVED'
  | 'HISTORICAL'
  | 'OFFICIAL_FORECAST'
  | 'DERIVED'
  | 'SIMULATED'
  | 'SYNTHETIC'
  | 'UNAVAILABLE'
  | 'UNVERIFIED';

export type PressureLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH';

export type InboundWindow = {
  commitments: number;
  weighted: number;
};

export type CongestionSnapshot = {
  facility_id: number;
  queue: {
    rosso: number;
    giallo: number;
    verde: number;
    bianco: number;
    non_assegnato: number;
    totale: number;
  };
  in_treatment: number;
  in_observation: number;
  ratio: number;
  level: string;
  source: string;
  observed_at: string | null;
  updated_at: string;
};

export type CongestionDraft = {
  waiting_red: number;
  waiting_yellow: number;
  waiting_green: number;
  waiting_white: number;
  waiting_unassigned: number;
  in_treatment: number;
  in_observation: number;
};

export type IncomingPatient = {
  code: string;
  commitment_id: string;
  commitment_status: 'CONFIRMED' | 'EN_ROUTE' | 'ARRIVED';
  status: 'issued' | 'accepted' | 'expired';
  eta_minutes: number;
  expected_arrival_at: string;
  care_cluster: string;
  identity: {
    given_name: string;
    family_name: string;
    fiscal_code: string;
    birth_date: string;
    is_minor: boolean;
    email: string | null;
    mobile_phone: string | null;
  };
  clinical_context: {
    exemptions: { code: string; description: string }[];
    chronic_conditions: string[];
    gp: {
      given_name: string;
      family_name: string;
      relationship: string | null;
      phone: string | null;
    } | null;
  };
  user_input: Record<string, string | null>;
  triage_summary: {
    priority_code: 'bianco' | 'verde' | 'azzurro' | 'arancione' | 'rosso';
    reason: string;
    advice: string;
    provider: string;
    provisional: true;
  } | null;
  synthetic: boolean;
};

export type ConsoleOverview = {
  facility: { id: number; name: string; municipality: string | null };
  pressure: {
    level: string;
    ratio: number;
    waiting_total: number;
    in_treatment: number;
    provenance: Provenance;
    observed_at: string | null;
  };
  inbound: {
    next_30_min: InboundWindow;
    next_60_min: InboundWindow;
    next_4_hours: InboundWindow;
    provenance: Provenance;
    weight_formula: string;
  };
  care_mix: { cluster: string; label: string; count: number; weighted: number }[];
  expected_pressure_level: PressureLevel;
  readiness: { area: string; level: PressureLevel; reason: string }[];
  staffing: {
    on_shift: number;
    on_call: number;
    resting: number;
    total: number;
    deficit: {
      qualification: string;
      additional_shifts_suggested: number;
      candidates_available: number;
      reason: string;
    }[];
    excluded: { id: string; qualification: string; exclusion_reason: string }[];
    provenance: Provenance;
    policy: string;
    formula: string;
  };
  generated_at: string;
};
