import { HospitalLogin } from '@/features/auth/HospitalLogin';
import { SpidLoginPanel } from '@/features/auth/SpidLoginPanel';
import { DemoProfileCard } from '@/features/home/DemoProfileCard';
import { NearbyCarePreview } from '@/features/home/NearbyCarePreview';
import { TriageScale } from '@/features/home/TriageScale';
import { BRANDING } from '@/lib/branding';
import { useRole } from '@/lib/useRole';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

/** Apertura della demo: prima il ruolo, poi l'identità o la struttura sintetica. */
export function HomePage() {
  const { setRole } = useRole();
  const navigate = useNavigate();
  const [selectedRole, setSelectedRole] = useState<
    'citizen-preview' | 'citizen-login' | 'operator' | null
  >(null);

  function enterCitizen() {
    setRole('paziente');
    navigate('/paziente');
  }

  function enterOperator() {
    setRole('operatore');
    navigate('/operatore');
  }

  if (selectedRole === 'citizen-preview') {
    return (
      <NearbyCarePreview
        onContinue={() => setSelectedRole('citizen-login')}
        onBack={() => setSelectedRole(null)}
      />
    );
  }

  if (selectedRole === 'citizen-login') {
    return (
      <div className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center py-10">
        <SpidLoginPanel
          title="Scegli il paziente mock"
          description="Seleziona liberamente uno dei profili sintetici per provare il percorso cittadino. Non serve alcuna password."
          onDone={enterCitizen}
          onBack={() => setSelectedRole('citizen-preview')}
        />
      </div>
    );
  }

  if (selectedRole === 'operator') {
    return <HospitalLogin onDone={enterOperator} onBack={() => setSelectedRole(null)} />;
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col justify-center py-6">
      <section className="animate-fade-up text-center">
        <p className="text-sm font-medium text-accent">{BRANDING.tagline}</p>
        <h1 className="mx-auto mt-2 max-w-2xl text-[2rem] font-semibold leading-[1.15] tracking-tight text-ink sm:text-4xl">
          {BRANDING.claim}
        </h1>
        <p className="mx-auto mt-3 max-w-xl text-[15px] leading-relaxed text-muted">
          {BRANDING.subclaim}
        </p>
      </section>

      <section aria-label="Scegli come entrare" className="mt-10 grid gap-4 sm:grid-cols-2">
        <DemoProfileCard
          accent
          name="Paziente"
          role="Percorso cittadino"
          initials="PA"
          badge="15 profili mock"
          description="Scegli un paziente sintetico, prova il triage intelligente e confronta viaggio, attesa e afflusso previsto."
          cta="Entra come paziente"
          onSelect={() => setSelectedRole('citizen-preview')}
        />

        <DemoProfileCard
          name="Operatore pronto soccorso"
          role="Console ospedaliera"
          initials="PS"
          badge="Ospedali registrati"
          description="Scegli il pronto soccorso, osserva gli arrivi confermati e aggiorna la coda per alimentare il ranking predittivo."
          cta="Entra come operatore pronto soccorso"
          onSelect={() => setSelectedRole('operator')}
        />
      </section>

      <TriageScale />

      <p className="mt-10 rounded-xl border border-line bg-raised px-4 py-3 text-xs leading-relaxed text-muted">
        HealthPulse non è un servizio medico e non sostituisce una diagnosi. In caso di emergenza
        chiama sempre il <strong className="text-ink">118</strong>.
      </p>
    </div>
  );
}
