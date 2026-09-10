import { useState, type FormEvent } from 'react';

type AddressFormProps = {
  onSubmit: (address: string) => void;
  pending: boolean;
};

export function AddressForm({ onSubmit, pending }: AddressFormProps) {
  const [address, setAddress] = useState('');

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = address.trim();
    if (trimmed && !pending) onSubmit(trimmed);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <label htmlFor="address" className="block text-sm font-medium text-ink">
        Da dove parti?
      </label>
      <div className="flex flex-col gap-2 sm:flex-row">
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
          className="min-h-11 shrink-0 rounded-xl bg-accent px-5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          {pending ? 'Calcolo…' : 'Trova le strutture'}
        </button>
      </div>
      <p className="text-xs text-faint">
        L'indirizzo serve solo a calcolare il tragitto e non viene salvato.
      </p>
    </form>
  );
}
