import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { Bot, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ChatMessage as ChatMessageType } from '@/types';
import 'highlight.js/styles/github-dark.css';

export function ChatMessage({
  message,
  streaming,
}: {
  message: ChatMessageType;
  streaming?: boolean;
}) {
  const isUser = message.sender === 'user';

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      <div
        className={cn(
          'mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md border',
          isUser
            ? 'border-primary/30 bg-primary/10 text-primary'
            : 'border-border bg-card text-muted-foreground'
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div
        className={cn(
          'max-w-[85%] rounded-lg border px-4 py-3 md:max-w-[75%]',
          isUser ? 'border-primary/20 bg-primary/10' : 'border-border bg-card'
        )}
      >
        {typeof message.text === 'string' ? (
          <div className="markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
              {message.text}
            </ReactMarkdown>
            {streaming && (
              <span className="ml-0.5 inline-block h-4 w-2 translate-y-0.5 animate-caret-blink bg-primary" />
            )}
          </div>
        ) : (
          message.text
        )}
      </div>
    </div>
  );
}
