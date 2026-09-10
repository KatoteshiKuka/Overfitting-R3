/** Attributi SPID, con i nomi dello standard. */
export type SpidProfile = {
  spidCode: string;
  name: string;
  familyName: string;
  fiscalNumber: string;
  dateOfBirth: string;
  placeOfBirth: string;
  countyOfBirth: string;
  gender: string;
  email: string | null;
  mobilePhone: string | null;
};

export type CitizenSession = {
  authenticated: true;
  provider: string;
  synthetic: boolean;
  profile: SpidProfile;
  expires_at: string;
};

export type HospitalRole =
  | 'HOSPITAL_ADMIN'
  | 'PS_COORDINATOR'
  | 'DEPARTMENT_LEAD'
  | 'OPERATOR_READONLY';

export type Operator = {
  username: string;
  display_name: string;
  role: HospitalRole;
  facility_id: number;
  facility_name: string | null;
};

export type HospitalSession = {
  authenticated: true;
  provider: string;
  synthetic: boolean;
  operator: Operator;
  expires_at: string;
};

export type DemoIdentity = {
  username: string;
  display_name: string;
  hero: string | null;
  care_intent: string;
  note: string | null;
};

export type DemoDirectory = {
  citizens: DemoIdentity[];
  operators: string[];
  synthetic: boolean;
};

/**
 * Stato dell'accesso.
 *
 * `loading` esiste perché la sessione si verifica sul server: senza, l'app mostrerebbe
 * per un istante la schermata di login a chi è già autenticato.
 */
export type AuthState =
  | { status: 'loading' }
  | { status: 'anonymous' }
  | { status: 'citizen'; session: CitizenSession }
  | { status: 'operator'; session: HospitalSession };
