/**
 * Marchio in stile SPID per il pulsante di accesso.
 *
 * È una resa grafica per la demo, non il logo ufficiale: l'ambiente è di test e non c'è
 * nessun Identity Provider reale dietro. Per questo ogni schermata che lo usa porta
 * sempre accanto l'etichetta «ambiente di test».
 */
export function SpidMark({ className = 'h-5 w-5' }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true" fill="currentColor">
      <path d="M3.2 5.4c0-.5.5-.9 1-.8 2.9.5 5.7 1.4 8.3 2.8.2.1.2.4 0 .5-.5.3-1 .5-1.6.7a.5.5 0 0 1-.4 0A24 24 0 0 0 3.9 6.6a.6.6 0 0 1-.7-.6v-.6Z" />
      <path d="M3.2 10.1c0-.5.5-.9 1-.8 1.7.3 3.4.8 5 1.4.3.1.3.5 0 .6-.5.3-1 .6-1.4 1a.5.5 0 0 1-.4.1c-1.2-.4-2.4-.7-3.6-.9a.6.6 0 0 1-.6-.6v-.8Z" />
      <path d="M20.8 5.4v.6a.6.6 0 0 1-.7.6c-4.9.8-9.2 3.4-11.8 7.3a.6.6 0 0 1-.8.2l-.6-.4a.6.6 0 0 1-.2-.8C9.5 8.5 14.4 5.5 19.8 4.6c.5-.1 1 .3 1 .8Z" />
      <path d="M20.8 10.4c0 .4-.3.8-.7.9-3.2.7-6 2.6-7.8 5.4a.6.6 0 0 1-.9.1l-.5-.5a.6.6 0 0 1-.1-.7 13 13 0 0 1 9-6.1c.5-.1 1 .3 1 .9Z" />
      <path d="M20.8 15.5c0 .4-.3.8-.7.9-1.7.4-3.2 1.5-4.1 3a.6.6 0 0 1-.9.2l-.6-.4a.6.6 0 0 1-.2-.8 8.4 8.4 0 0 1 5.5-3.8c.5-.1 1 .3 1 .9Z" />
    </svg>
  );
}
