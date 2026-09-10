/** Tipi speculari agli schemi Pydantic del backend. Il contratto vive in STATE.md. */

export type FacilityType =
  | 'pronto-soccorso'
  | 'ospedale'
  | 'casa-comunita'
  | 'farmacia'
  | 'ambulatorio'
  | 'altro';

export type Facility = {
  id: number;
  name: string;
  type: FacilityType;
  asl: string | null;
  municipality: string | null;
  province: string | null;
  address: string | null;
  postal_code: string | null;
  latitude: number | null;
  longitude: number | null;
  beds: number | null;
  phone: string | null;
  source: string;
};

export type FacilityList = {
  items: Facility[];
  total: number;
  limit: number;
  offset: number;
};

export type FacilitySummary = {
  total: number;
  by_type: { type: FacilityType; count: number }[];
  by_asl: { asl: string; count: number }[];
  municipalities: number;
};

export type DatasetStatus = {
  name: string;
  files: number;
  records: number;
  last_loaded_at: string | null;
};

export type SystemStatus = {
  status: string;
  version: string;
  data_loaded: boolean;
  facilities_count: number;
  asl_count: number;
  datasets: DatasetStatus[];
};

export type FacilityQuery = {
  q?: string;
  type?: FacilityType | '';
  asl?: string;
  limit?: number;
  offset?: number;
};
