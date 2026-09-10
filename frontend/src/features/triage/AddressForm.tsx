import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';

type AddressFormProps = {
  onSubmit: (address: string) => void;
  pending: boolean;
  autoLocate?: boolean;
};

export function AddressForm({ onSubmit, pending, autoLocate = false }: AddressFormProps) {
  const [address, setAddress] = useState('');
  const [locating, setLocating] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const autoLocateStarted = useRef(false);
  const locationAvailable =
    typeof navigator !== 'undefined' && 'geolocation' in navigator && window.isSecureContext;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = address.trim();
    if (trimmed && !pending) onSubmit(trimmed);
  }

  const requestCurrentLocation = useCallback(() => {
    if (!locationAvailable || pending || locating) return;

    setLocating(true);
    setLocationError(null);
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setLocating(false);
        onSubmit(`geo:${coords.latitude.toFixed(6)},${coords.longitude.toFixed(6)}`);
      },
      (error) => {
        setLocating(false);
        if (error.code === error.PERMISSION_DENIED) {
          setLocationError(
            'Permesso negato. Abilita la posizione nel browser oppure usa l’indirizzo manuale.',
          );
          return;
        }
        if (error.code === error.TIMEOUT) {
          setLocationError('La posizione non ha risposto in tempo. Riprova o usa l’indirizzo.');
          return;
        }
        setLocationError('Posizione non disponibile. Riprova o usa l’indirizzo manuale.');
      },
      { enableHighAccuracy: true, timeout: 12_000, maximumAge: 60_000 },
    );
  }, [locating, locationAvailable, onSubmit, pending]);

  useEffect(() => {
    if (!autoLocate || autoLocateStarted.current) return;
    autoLocateStarted.current = true;
    requestCurrentLocation();
  }, [autoLocate, requestCurrentLocation]);

  return (
    <div className="space-y-3">
      <div>
        <h3 className="text-sm font-medium text-ink">Da dove parti?</h3>
        <p className="mt-1 text-xs leading-relaxed text-muted">
          Usa la posizione del dispositivo per trovare la struttura davvero più conveniente.
        </p>
      </div>

      <button
        type="button"
        onClick={requestCurrentLocation}
        disabled={!locationAvailable || pending || locating}
        className="min-h-11 w-full rounded-xl bg-accent px-5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
      >
        {locating
          ? 'Rilevo la posizione…'
          : pending
            ? 'Calcolo il percorso…'
            : 'Usa la mia posizione'}
      </button>

      {!locationAvailable && (
        <p className="rounded-xl bg-raised px-3 py-2 text-xs leading-relaxed text-muted">
          La posizione richiede HTTPS oppure <strong className="text-ink">localhost</strong>. Apri
          l’app da localhost o usa l’indirizzo manuale.
        </p>
      )}
      {locationError && (
        <p className="text-xs leading-relaxed text-red-700" role="alert">
          {locationError}
        </p>
      )}

      <details className="rounded-xl border border-line bg-raised px-3 py-2.5">
        <summary className="cursor-pointer text-xs font-medium text-muted">
          Inserisci un indirizzo invece
        </summary>
        <form onSubmit={handleSubmit} className="mt-3 flex flex-col gap-2 sm:flex-row">
          <label htmlFor="address" className="sr-only">
            Indirizzo di partenza
          </label>
          <input
            id="address"
            type="text"
            value={address}
            disabled={pending}
            onChange={(event) => setAddress(event.target.value)}
            placeholder="Via Nazionale 100, Roma"
            className="min-h-11 flex-1 rounded-xl border border-line bg-surface px-4 text-sm text-ink placeholder:text-faint focus:border-accent disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={pending || !address.trim()}
            className="min-h-11 shrink-0 rounded-xl border border-line bg-surface px-5 text-sm font-medium text-ink transition-colors hover:border-accent/50 disabled:opacity-40"
          >
            {pending ? 'Calcolo…' : 'Usa indirizzo'}
          </button>
        </form>
      </details>

      <p className="text-xs text-faint">
        La posizione serve solo a calcolare il tragitto e non viene salvata.
      </p>
    </div>
  );
}
