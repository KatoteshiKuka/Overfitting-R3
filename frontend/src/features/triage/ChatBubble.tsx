import type { ChatImage, ChatRole } from '@/features/triage/types';

type ChatBubbleProps = {
  role: ChatRole;
  content: string;
  image?: ChatImage;
};

export function ChatBubble({ role, content, image }: ChatBubbleProps) {
  const isUser = role === 'user';

  return (
    <div className={`flex animate-fade-up ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] whitespace-pre-line rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isUser
            ? 'rounded-br-md bg-accent text-white'
            : 'rounded-bl-md border border-line bg-surface text-ink'
        }`}
      >
        {image && (
          <img
            src={image.data_url}
            alt={`Foto allegata: ${image.name}`}
            className="mb-2 max-h-56 w-full rounded-xl object-cover"
          />
        )}
        {content}
      </div>
    </div>
  );
}
