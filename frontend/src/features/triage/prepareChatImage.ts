import type { ChatImage } from '@/features/triage/types';

const MAX_SOURCE_BYTES = 12_000_000;
const MAX_UPLOAD_BYTES = 2_000_000;

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const source = URL.createObjectURL(file);
    const image = new window.Image();
    image.onload = () => {
      URL.revokeObjectURL(source);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(source);
      reject(new Error('Formato immagine non leggibile dal browser. Usa JPEG, PNG o WebP.'));
    };
    image.src = source;
  });
}

function renderJpeg(image: HTMLImageElement, maxEdge: number, quality: number): Promise<Blob> {
  const scale = Math.min(1, maxEdge / Math.max(image.naturalWidth, image.naturalHeight));
  const canvas = document.createElement('canvas');
  canvas.width = Math.max(1, Math.round(image.naturalWidth * scale));
  canvas.height = Math.max(1, Math.round(image.naturalHeight * scale));

  const context = canvas.getContext('2d');
  if (!context) throw new Error('Il browser non riesce a preparare la foto.');
  context.drawImage(image, 0, 0, canvas.width, canvas.height);

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error('Impossibile comprimere la foto.'))),
      'image/jpeg',
      quality,
    );
  });
}

function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error('Impossibile leggere la foto.'));
    reader.readAsDataURL(blob);
  });
}

export async function prepareChatImage(file: File): Promise<ChatImage> {
  if (!file.type.startsWith('image/')) throw new Error('Seleziona un file immagine.');
  if (file.size > MAX_SOURCE_BYTES) throw new Error('La foto originale non può superare 12 MB.');

  const image = await loadImage(file);
  let blob = await renderJpeg(image, 1600, 0.82);
  if (blob.size > MAX_UPLOAD_BYTES) blob = await renderJpeg(image, 1200, 0.68);
  if (blob.size > MAX_UPLOAD_BYTES) {
    throw new Error('La foto resta troppo grande. Prova a ritagliarla o scegline un’altra.');
  }

  const baseName = file.name.replace(/\.[^.]+$/, '').slice(0, 110) || 'foto';
  return { name: `${baseName}.jpg`, data_url: await blobToDataUrl(blob) };
}
