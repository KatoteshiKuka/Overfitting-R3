import type { ChatRole } from '@/features/triage/types';

type ChatBubbleProps = {
  role: ChatRole;
  content: string;
};

export function ChatBubble({ role, content }: ChatBubbleProps) {
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
        {content}
      </div>
    </div>
  );
}
