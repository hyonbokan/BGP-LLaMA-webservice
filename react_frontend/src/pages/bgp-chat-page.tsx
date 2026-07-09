import { useEffect, useRef } from 'react';
import { MessageSquarePlus } from 'lucide-react';
import { useBgpChat } from '@/hooks/use-bgp-chat';
import { ChatSidebar } from '@/components/chat/chat-sidebar';
import { ChatMessage } from '@/components/chat/chat-message';
import { ChatComposer } from '@/components/chat/chat-composer';
import { ChatEmptyState } from '@/components/chat/chat-empty-state';
import { CodePanel } from '@/components/chat/code-panel';
import { ModelSwitch } from '@/components/chat/model-switch';
import { Button } from '@/components/ui/button';

export function BgpChatPage() {
  const chat = useBgpChat();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Keep the latest message in view as tokens stream in.
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [chat.messages, chat.generatedCode]);

  const hasMessages = chat.messages.length > 0;

  return (
    <div className="flex h-full">
      <div className="hidden md:flex">
        <ChatSidebar
          tabs={chat.tabs}
          currentTab={chat.currentTab}
          onSelect={chat.selectTab}
          onNewChat={chat.newChat}
          onRename={chat.renameTab}
          onDelete={chat.deleteTab}
        />
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between gap-2 border-b border-border px-4 py-2.5">
          <Button
            variant="ghost"
            size="sm"
            className="gap-2 font-mono md:hidden"
            onClick={chat.newChat}
          >
            <MessageSquarePlus className="h-4 w-4" /> New
          </Button>
          <div className="flex flex-1 items-center justify-center md:justify-start">
            <ModelSwitch
              value={chat.selectedModel}
              onChange={chat.setSelectedModel}
              disabled={chat.isGenerating}
            />
          </div>
        </header>

        <div ref={scrollRef} className="flex-1 overflow-y-auto">
          {hasMessages ? (
            <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-6">
              {chat.messages.map((message, index) => {
                const isLast = index === chat.messages.length - 1;
                return (
                  <ChatMessage
                    key={index}
                    message={message}
                    streaming={
                      chat.isGenerating && isLast && message.sender === 'system' && !message.final
                    }
                  />
                );
              })}
              {chat.generatedCode && (
                <div className="px-0">
                  <CodePanel code={chat.generatedCode} />
                </div>
              )}
            </div>
          ) : (
            <ChatEmptyState model={chat.selectedModel} onPick={chat.setInput} />
          )}
        </div>

        <ChatComposer
          value={chat.input}
          onChange={chat.setInput}
          onSend={chat.sendMessage}
          onStop={chat.stopGenerating}
          isGenerating={chat.isGenerating}
        />
      </div>
    </div>
  );
}
