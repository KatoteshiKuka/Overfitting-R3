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
