import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5173,
    // In ascolto su tutte le interfacce: serve per aprire l'app dal telefono sulla stessa
    // rete. È impostato qui e non solo da riga di comando perché `npm run dev --host` non
    // inoltra il flag a Vite (servirebbe `npm run dev -- --host`), e nessuno se lo ricorda.
    host: true,
    // Il proxy vive sul server di sviluppo, quindi funziona anche per il telefono: il
    // browser chiama sempre `/api` sul proprio indirizzo, non direttamente il backend.
    proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true } },
  },
  preview: {
    port: 4173,
    host: true,
  },
});
