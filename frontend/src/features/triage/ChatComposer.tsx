import { prepareChatImage } from '@/features/triage/prepareChatImage';
import type { ChatImage } from '@/features/triage/types';
import { useRef, useState, type ChangeEvent, type FormEvent, type KeyboardEvent } from 'react';

type ChatComposerProps = {
  onSend: (text: string, image?: ChatImage) => void;
  disabled: boolean;
  placeholder?: string;
};

export function ChatComposer({ onSend, disabled, placeholder }: ChatComposerProps) {
  const [text, setText] = useState('');
  const [image, setImage] = useState<ChatImage | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);
  const [processingImage, setProcessingImage] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  function submit(event?: FormEvent) {
    event?.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled || processingImage) return;
    onSend(trimmed, image ?? undefined);
    setText('');
    setImage(null);
    setImageError(null);
  }

  async function selectImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;

    setProcessingImage(true);
    setImageError(null);
    try {
      setImage(await prepareChatImage(file));
    } catch (error) {
      setImage(null);
      setImageError(error instanceof Error ? error.message : 'Impossibile preparare la foto.');
    } finally {
      setProcessingImage(false);
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    // Invio manda, Shift+Invio va a capo: è quello che la gente si aspetta da una chat.
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <form onSubmit={submit} className="space-y-2">
      {image && (
        <div className="flex items-center gap-3 rounded-xl border border-line bg-surface p-2">
          <img
            src={image.data_url}
            alt="Anteprima della foto allegata"
            className="h-14 w-14 rounded-lg object-cover"
          />
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-ink">{image.name}</p>
            <p className="mt-0.5 text-[11px] leading-relaxed text-faint">
              Temporanea: non sarà inclusa nella scheda paziente.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setImage(null)}
            disabled={disabled}
            className="min-h-10 rounded-lg px-3 text-xs text-muted hover:text-ink disabled:opacity-40"
          >
            Rimuovi
          </button>
        </div>
      )}

      {imageError && (
        <p role="alert" className="text-xs leading-relaxed text-red-700">
          {imageError}
        </p>
      )}

      <div className="flex items-end gap-2">
        <input
          ref={fileInput}
          type="file"
          accept="image/*"
          className="sr-only"
          onChange={selectImage}
          disabled={disabled || processingImage}
        />
        <button
          type="button"
          onClick={() => fileInput.current?.click()}
          disabled={disabled || processingImage}
          aria-label="Allega una foto"
          title="Allega una foto temporanea"
          className="grid h-11 w-11 shrink-0 place-items-center rounded-xl border border-line bg-surface text-muted transition-colors hover:border-accent/50 hover:text-ink disabled:opacity-40"
        >
          {processingImage ? (
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          ) : (
            <svg
              viewBox="0 0 24 24"
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M15.5 7.5 8.8 14.2a2.1 2.1 0 0 0 3 3l7.4-7.4a4 4 0 1 0-5.7-5.7L5.4 12.2a5.8 5.8 0 0 0 8.2 8.2l6.1-6.1" />
            </svg>
          )}
        </button>
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
          disabled={disabled || processingImage || !text.trim()}
          aria-label="Invia"
          className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-accent text-white transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="m4 12 16-8-6 8 6 8-16-8Z" />
          </svg>
        </button>
      </div>
      <p className="text-[11px] leading-relaxed text-faint">
        La foto aiuta solo la valutazione preliminare: aggiungi sempre una breve descrizione.
      </p>
    </form>
  );
}
