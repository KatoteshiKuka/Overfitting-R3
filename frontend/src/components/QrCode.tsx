import { useEffect, useState } from 'react';
import QRCode from 'qrcode';

type QrCodeProps = {
  value: string;
  size?: number;
  label?: string;
};

/**
 * QR del codice di pre-accettazione, da mostrare all'accettazione.
 *
 * Nel QR c'è **solo il codice**, non i dati della persona: chi lo inquadra senza avere
 * accesso al sistema non ottiene niente di utile. È la stessa ragione per cui il codice
 * scade dopo poche ore ed è monouso.
 *
 * Reso come SVG perché deve restare nitido a qualunque dimensione e su qualunque
 * densità di schermo — un QR sgranato non si legge.
 */
export function QrCode({ value, size = 176, label }: QrCodeProps) {
  const [svg, setSvg] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    QRCode.toString(value, {
      type: 'svg',
      errorCorrectionLevel: 'M',
      margin: 1,
      width: size,
      // Nero su bianco anche in tema scuro: le fotocamere si aspettano questo contrasto.
      color: { dark: '#000000', light: '#ffffff' },
    })
      .then((result) => {
        if (active) setSvg(result);
      })
      .catch(() => {
        if (active) setFailed(true);
      });
    return () => {
      active = false;
    };
  }, [value, size]);

  if (failed) {
    // Il codice testuale resta leggibile e dettabile: la demo non si ferma sul QR.
    return (
      <p className="text-xs text-faint">
        QR non disponibile. Comunica il codice: <strong className="text-ink">{value}</strong>
      </p>
    );
  }

  return (
    <figure className="flex flex-col items-center gap-2">
      <div
        className="rounded-xl bg-white p-2 shadow-card"
        style={{ width: size + 16, height: size + 16 }}
        role="img"
        aria-label={label ?? `Codice ${value}`}
        dangerouslySetInnerHTML={svg ? { __html: svg } : undefined}
      />
      <figcaption className="tabular text-sm font-semibold tracking-wider text-ink">
        {value}
      </figcaption>
    </figure>
  );
}
