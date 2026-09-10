import { ErrorState } from '@/components/ErrorState';
import { PageHeader } from '@/components/PageHeader';
import { AddressForm } from '@/features/triage/AddressForm';
import { AssessmentPanel } from '@/features/triage/AssessmentPanel';
import { ChatBubble } from '@/features/triage/ChatBubble';
import { ChatComposer } from '@/features/triage/ChatComposer';
import { FacilityMap } from '@/features/triage/FacilityMap';
import { PlanOptionCard } from '@/features/triage/PlanOptionCard';
import { ProviderBadge } from '@/features/triage/ProviderBadge';
import { TypingBubble } from '@/features/triage/TypingBubble';
import type { Assessment, ChatMessage, PlanOption } from '@/features/triage/types';
import { usePlan, useSendMessage, useTriageStatus } from '@/features/triage/useTriage';
import { useEffect, useRef, useState } from 'react';

const OPENING: ChatMessage = {
  role: 'assistant',
  content:
    'Ciao. Raccontami cosa ti succede: che disturbo hai, da quanto tempo e quanto ti sembra forte. Poi ti dico dove conviene andare.',
};

const EXAMPLES = [
  'Ho mal di gola e un po’ di febbre da due giorni',
  'Mi sono tagliato una mano e sanguina',
  'Ho mal di schiena da una settimana',
];

export function TriagePage() {
  const [messages, setMessages] = useState<ChatMessage[]>([OPENING]);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [provider, setProvider] = useState<string>('');
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const status = useTriageStatus();
  const sendMessage = useSendMessage();
  const plan = usePlan();

  const scrollAnchor = useRef<HTMLDivElement>(null);
  useEffect(() => {
    scrollAnchor.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, sendMessage.isPending]);

  function handleSend(text: string) {
    const next: ChatMessage[] = [...messages, { role: 'user', content: text }];
    setMessages(next);

    // Il saluto iniziale è solo scenografia: al modello si mandano i turni veri.
    const forServer = next.filter((message, index) => index > 0 || message.role === 'user');

    sendMessage.mutate(forServer, {
      onSuccess: (response) => {
        setMessages((current) => [...current, { role: 'assistant', content: response.reply }]);
        setProvider(response.provider);
        if (response.assessment) setAssessment(response.assessment);
      },
      onError: (error) => {
        const detail = error instanceof Error ? error.message : 'Errore imprevisto.';
        setMessages((current) => [
          ...current,
          { role: 'assistant', content: `Non sono riuscito a rispondere: ${detail}` },
        ]);
      },
    });
  }

  function handlePlan(address: string) {
    if (!assessment) return;
    setSelectedId(null);
    plan.mutate({ address, code: assessment.code });
  }

  function restart() {
    setMessages([OPENING]);
    setAssessment(null);
    setProvider('');
    setSelectedId(null);
    plan.reset();
  }

  const offline = status.data?.providers.every((entry) => !entry.available) ?? false;
  const showMapStep = assessment !== null && assessment.code !== 'rosso';

  return (
    <>
      <PageHeader
        title="Assistente di triage"
        description="Rispondi a poche domande: capiamo quanto è urgente e dove conviene andare davvero."
        actions={
          assessment && (
            <button
              type="button"
              onClick={restart}
              className="min-h-11 rounded-xl border border-line px-4 text-sm text-muted transition-colors hover:text-ink"
            >
              Ricomincia
            </button>
          )
        }
      />

      {offline && (
        <p
          className="mb-4 rounded-xl px-4 py-3 text-sm"
          style={{
            backgroundColor: 'rgb(var(--triage-arancione) / 0.1)',
            color: 'rgb(var(--triage-arancione))',
          }}
        >
          Nessun modello linguistico raggiungibile: rispondo con le regole di sicurezza, che sono
          più prudenti ma non fanno domande di approfondimento.
        </p>
      )}

      <div className="rounded-2xl border border-line bg-raised p-3 sm:p-4">
        <div className="max-h-[420px] space-y-3 overflow-y-auto pr-1">
          {messages.map((message, index) => (
            <ChatBubble key={index} role={message.role} content={message.content} />
          ))}
          {sendMessage.isPending && <TypingBubble />}
          <div ref={scrollAnchor} />
        </div>

        <div className="mt-3 border-t border-line pt-3">
          <ChatComposer onSend={handleSend} disabled={sendMessage.isPending} />
          <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
            {provider ? <ProviderBadge provider={provider} /> : <span />}
            <p className="text-[11px] text-faint">Non è un servizio medico. Emergenze: 118.</p>
          </div>
        </div>
      </div>

      {messages.length === 1 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {EXAMPLES.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => handleSend(example)}
              className="rounded-full border border-line bg-surface px-3 py-2 text-xs text-muted transition-colors hover:border-accent/40 hover:text-ink"
            >
              {example}
            </button>
          ))}
        </div>
      )}

      {assessment && (
        <div className="mt-6">
          <AssessmentPanel assessment={assessment} />
        </div>
      )}

      {showMapStep && (
        <section className="mt-6" aria-label="Strutture consigliate">
          <div className="rounded-2xl border border-line bg-surface p-5">
            <AddressForm onSubmit={handlePlan} pending={plan.isPending} />
          </div>

          {plan.isError && (
            <div className="mt-4">
              <ErrorState error={plan.error} />
            </div>
          )}

          {plan.data && (
            <div className="mt-4 space-y-4">
              <div className="rounded-2xl border border-line bg-surface p-5">
                <p className="text-sm leading-relaxed text-ink">{plan.data.advice}</p>
                <div className="mt-2">
                  <ProviderBadge provider={plan.data.provider} />
                </div>
              </div>

              <FacilityMap
                plan={plan.data}
                selectedId={selectedId}
                onSelect={(option: PlanOption) => setSelectedId(option.facility_id)}
              />

              <ul className="space-y-3">
                {plan.data.options.map((option) => (
                  <li key={option.facility_id}>
                    <PlanOptionCard
                      option={option}
                      selected={option.facility_id === selectedId}
                      onSelect={() => setSelectedId(option.facility_id)}
                    />
                  </li>
                ))}
              </ul>

              <p className="text-xs text-faint">
                Tempi di viaggio calcolati su OpenStreetMap. L'affollamento è al momento una stima:
                sarà sostituito dai dati dichiarati dalle strutture.
              </p>
            </div>
          )}
        </section>
      )}
    </>
  );
}
