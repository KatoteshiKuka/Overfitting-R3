import { ErrorState } from '@/components/ErrorState';
import { AddressForm } from '@/features/triage/AddressForm';
import { ArrivalConfirm } from '@/features/triage/ArrivalConfirm';
import { AssessmentPanel } from '@/features/triage/AssessmentPanel';
import { ChatBubble } from '@/features/triage/ChatBubble';
import { ChatComposer } from '@/features/triage/ChatComposer';
import { FacilityMap } from '@/features/triage/FacilityMap';
import { PlanOptionCard } from '@/features/triage/PlanOptionCard';
import { ProviderBadge } from '@/features/triage/ProviderBadge';
import { RouteSummary } from '@/features/triage/RouteSummary';
import { TypingBubble } from '@/features/triage/TypingBubble';
import type { Assessment, ChatImage, ChatMessage } from '@/features/triage/types';
import { usePlan, useSendMessage, useTriageStatus } from '@/features/triage/useTriage';
import { Link } from 'react-router-dom';
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

  function handleSend(text: string, image?: ChatImage) {
    const next: ChatMessage[] = [...messages, { role: 'user', content: text, image }];
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
  const selected =
    plan.data?.options.find((option) => option.facility_id === selectedId) ?? plan.data?.options[0];

  return (
    <div className="flex w-full flex-1 flex-col">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-ink">Assistente di triage</h1>
          <p className="mt-0.5 text-sm text-muted">
            Rispondi a poche domande: capiamo quanto è urgente e dove conviene andare davvero.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to="/"
            className="min-h-11 rounded-xl border border-line px-4 text-sm leading-[2.75rem] text-muted transition-colors hover:text-ink"
          >
            Cambia ruolo
          </Link>
          {assessment && (
            <button
              type="button"
              onClick={restart}
              className="min-h-11 rounded-xl border border-line px-4 text-sm text-muted transition-colors hover:text-ink"
            >
              Ricomincia
            </button>
          )}
        </div>
      </div>

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

      {/* Due colonne su schermi larghi: la conversazione a sinistra, il risultato a destra. */}
      <div className="grid flex-1 gap-5 lg:grid-cols-[minmax(0,7fr)_minmax(0,9fr)]">
        <section aria-label="Conversazione" className="flex min-h-[26rem] flex-col">
          <div className="flex flex-1 flex-col rounded-2xl border border-line bg-raised p-3 sm:p-4">
            <div className="flex-1 space-y-3 overflow-y-auto pr-1" style={{ maxHeight: '58vh' }}>
              {messages.map((message, index) => (
                <ChatBubble
                  key={index}
                  role={message.role}
                  content={message.content}
                  image={message.image}
                />
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
        </section>

        <section aria-label="Esito e strutture" className="flex flex-col gap-4">
          {!assessment && (
            <div className="flex flex-1 items-center justify-center rounded-2xl border border-dashed border-line px-6 py-16 text-center">
              <p className="max-w-xs text-sm leading-relaxed text-faint">
                Qui compariranno il tuo codice di priorità e la struttura più adatta, con il
                tragitto e l’attesa stimata.
              </p>
            </div>
          )}

          {assessment && <AssessmentPanel assessment={assessment} />}

          {showMapStep && !plan.data && (
            <div className="rounded-2xl border border-line bg-surface p-5">
              <AddressForm onSubmit={handlePlan} pending={plan.isPending} />
            </div>
          )}

          {plan.isError && <ErrorState error={plan.error} />}

          {plan.data && selected && assessment && (
            <>
              <div className="h-[300px] shrink-0 lg:h-[340px]">
                <FacilityMap
                  plan={plan.data}
                  selectedId={selected.facility_id}
                  onSelect={(option) => setSelectedId(option.facility_id)}
                />
              </div>

              <RouteSummary option={selected} crowdingNote={plan.data.crowding_note} />

              {/* Conferma esplicita: la struttura viene avvisata solo se lo decide la persona. */}
              <ArrivalConfirm
                key={selected.facility_id}
                option={selected}
                assessment={assessment}
                provider={provider}
              />

              <div className="rounded-2xl border border-line bg-surface p-4">
                <p className="text-sm leading-relaxed text-ink">{plan.data.advice}</p>
                <div className="mt-2">
                  <ProviderBadge provider={plan.data.provider} />
                </div>
              </div>

              {plan.data.options.length > 1 && (
                <div>
                  <p className="mb-2 text-xs font-medium uppercase tracking-wide text-faint">
                    Altre opzioni
                  </p>
                  <ul className="space-y-2">
                    {plan.data.options
                      .filter((option) => option.facility_id !== selected.facility_id)
                      .map((option) => (
                        <li key={option.facility_id}>
                          <PlanOptionCard
                            option={option}
                            selected={false}
                            onSelect={() => setSelectedId(option.facility_id)}
                          />
                        </li>
                      ))}
                  </ul>
                </div>
              )}

              <button
                type="button"
                onClick={() => plan.reset()}
                className="min-h-11 self-start rounded-xl border border-line px-4 text-sm text-muted transition-colors hover:text-ink"
              >
                Cambia indirizzo
              </button>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
