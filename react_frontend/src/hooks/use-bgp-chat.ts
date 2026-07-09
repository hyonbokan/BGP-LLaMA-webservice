import { useCallback, useRef, useState } from 'react';
import { agentUrl } from '@/config';
import type { ChatMessage, ChatModel, ChatTab, SseEvent } from '@/types';

let nextTabId = 2;

const INITIAL_TABS: ChatTab[] = [{ id: 1, label: 'Chat 1', messages: [] }];

/**
 * Owns chat state and the SSE stream to the FastAPI agent. Streaming semantics
 * mirror the original: `generating` appends tokens to the open system message,
 * `code_ready` finalizes it and surfaces the extracted code, and terminal
 * statuses stop the spinner.
 */
export function useBgpChat() {
  const [tabs, setTabs] = useState<ChatTab[]>(INITIAL_TABS);
  const [currentTab, setCurrentTab] = useState(0);
  const [selectedModel, setSelectedModel] = useState<ChatModel>('bgp_llama');
  const [input, setInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedCode, setGeneratedCode] = useState('');

  const eventSourceRef = useRef<EventSource | null>(null);

  const closeStream = useCallback(() => {
    eventSourceRef.current?.close();
    eventSourceRef.current = null;
  }, []);

  const appendMessage = useCallback(
    (message: ChatMessage) => {
      setTabs((prev) =>
        prev.map((tab, i) =>
          i === currentTab ? { ...tab, messages: [...tab.messages, message] } : tab
        )
      );
    },
    [currentTab]
  );

  const patchCurrentMessages = useCallback(
    (updater: (messages: ChatMessage[]) => ChatMessage[]) => {
      setTabs((prev) =>
        prev.map((tab, i) => (i === currentTab ? { ...tab, messages: updater(tab.messages) } : tab))
      );
    },
    [currentTab]
  );

  const sendMessage = useCallback(() => {
    const query = input.trim();
    if (!query || isGenerating) return;

    appendMessage({ text: query, sender: 'user' });
    setInput('');
    setIsGenerating(true);
    setGeneratedCode('');
    closeStream();

    const endpoint = selectedModel === 'bgp_llama' ? 'bgp_llama' : 'bgp_gpt';
    const source = new EventSource(agentUrl(`${endpoint}?query=${encodeURIComponent(query)}`));
    eventSourceRef.current = source;

    source.onmessage = (event) => {
      let data: SseEvent;
      try {
        data = JSON.parse(event.data);
      } catch (err) {
        console.error('Failed to parse SSE message:', err);
        return;
      }

      switch (data.status) {
        case 'generating':
          patchCurrentMessages((messages) => {
            const last = messages[messages.length - 1];
            if (last && last.sender === 'system' && !last.final) {
              const updated = [...messages];
              updated[updated.length - 1] = {
                ...last,
                text: (last.text as string) + (data.generated_text ?? ''),
              };
              return updated;
            }
            return [
              ...messages,
              { text: data.generated_text ?? '', sender: 'system', final: false },
            ];
          });
          break;

        case 'code_ready':
          patchCurrentMessages((messages) => {
            const last = messages[messages.length - 1];
            if (last && last.sender === 'system') {
              const updated = [...messages];
              updated[updated.length - 1] = { ...last, final: true };
              return updated;
            }
            return messages;
          });
          setGeneratedCode(data.code ?? '');
          break;

        case 'no_code_found':
          appendMessage({
            text: 'No code block was found in the response.',
            sender: 'system',
            final: true,
          });
          break;

        case 'error':
          console.error('Agent error:', data.message);
          appendMessage({ text: `⚠️ Error: ${data.message}`, sender: 'system', final: true });
          setIsGenerating(false);
          closeStream();
          break;

        case 'complete':
          setIsGenerating(false);
          closeStream();
          break;
      }
    };

    source.onerror = (err) => {
      console.error('SSE error:', err);
      setIsGenerating(false);
      closeStream();
    };
  }, [input, isGenerating, selectedModel, appendMessage, patchCurrentMessages, closeStream]);

  const stopGenerating = useCallback(() => {
    setIsGenerating(false);
    closeStream();
  }, [closeStream]);

  const newChat = useCallback(() => {
    const id = nextTabId++;
    setTabs((prev) => [...prev, { id, label: `Chat ${prev.length + 1}`, messages: [] }]);
    setCurrentTab((prev) => prev + 1);
    closeStream();
  }, [closeStream]);

  const selectTab = useCallback(
    (index: number) => {
      setCurrentTab(index);
      closeStream();
    },
    [closeStream]
  );

  const deleteTab = useCallback(
    (id: number) => {
      setTabs((prev) => {
        if (prev.length === 1) return prev;
        const filtered = prev.filter((t) => t.id !== id);
        setCurrentTab((cur) => Math.min(cur, filtered.length - 1));
        return filtered;
      });
      closeStream();
    },
    [closeStream]
  );

  const renameTab = useCallback((id: number, label: string) => {
    setTabs((prev) => prev.map((t) => (t.id === id ? { ...t, label } : t)));
  }, []);

  return {
    tabs,
    currentTab,
    messages: tabs[currentTab]?.messages ?? [],
    selectedModel,
    setSelectedModel,
    input,
    setInput,
    isGenerating,
    generatedCode,
    sendMessage,
    stopGenerating,
    newChat,
    selectTab,
    deleteTab,
    renameTab,
  };
}
