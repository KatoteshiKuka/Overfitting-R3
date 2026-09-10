import { useState, type FormEvent, type KeyboardEvent } from 'react';

type ChatComposerProps = {
  onSend: (text: string) => void;
  disabled: boolean;
  placeholder?: string;
};

export function ChatComposer({ onSend, disabled, placeholder }: ChatComposerProps) {
  const [text, setText] = useState('');

  function submit(event?: FormEvent) {
    event?.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    // Invio manda, Shift+Invio va a capo: è quello che la gente si aspetta da una chat.
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <form onSubmit={submit} className="flex items-end gap-2">
      <label htmlFor="chat-input" className="sr-only">
        Descrivi il tuo problema
      </label>
      <textarea
        id="chat-input"
        rows={1}
        value={text}
        disabled={disabled}
        onChange={(event) => setText(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder ?? 'Scrivi qui cosa ti succede…'}
        className="max-h-32 min-h-11 flex-1 resize-none rounded-xl border border-line bg-surface px-4 py-3 text-sm text-ink placeholder:text-faint focus:border-accent disabled:opacity-60"
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        aria-label="Invia"
        className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-accent text-white transition-opacity hover:opacity-90 disabled:opacity-40"
      >
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="m4 12 16-8-6 8 6 8-16-8Z" />
        </svg>
      </button>
    </form>
  );
}
