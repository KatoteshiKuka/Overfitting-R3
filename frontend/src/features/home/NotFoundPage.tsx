import { EmptyState } from '@/components/EmptyState';
import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <EmptyState
      title="Pagina non trovata"
      description="L'indirizzo che hai aperto non corrisponde a nessuna sezione dell'app."
      action={
        <Link
          to="/"
          className="inline-flex min-h-11 items-center rounded-xl bg-accent px-5 text-sm font-medium text-white transition-opacity hover:opacity-90"
        >
          Torna alla home
        </Link>
      }
    />
  );
}
