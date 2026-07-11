import { useCallback, useRef, useState } from 'react';
import { apiUrl } from '@/config';
import type { ChatMessage, ChatModel, ChatTab, SseEvent } from '@/types';

let nextTabId = 2;

const INITIAL_TABS: ChatTab[] = [{ id: 1, label: 'Chat 1', messages: [] }];

/** A conversation turn as the backend expects it in the request body. */
type HistoryTurn = { role: 'user' | 'assistant'; content: string };

/**
 * Distill the visible messages into the role-tagged history the backend threads
 * back into the model. User bubbles map to `user`, finished assistant bubbles to
 * `assistant`; notices, tutorials, and still-streaming text are skipped.
 */
function toHistory(messages: ChatMessage[]): HistoryTurn[] {
  return messages
    .filter(
      (m) =>
        typeof m.text === 'string' &&
        m.kind !== 'notice' &&
        (m.sender === 'user' || m.sender === 'system')
    )
    .map((m) => ({
      role: m.sender === 'user' ? 'user' : 'assistant',
      content: m.text as string,
    }));
}

/**
 * Owns chat state and the streamed connection to the FastAPI agent. The request
 * is a POST carrying the query plus prior turns (so the model refines across the
 * conversation); the SSE body is read with fetch + a stream reader. `generating`
 * appends tokens to the open system message, `compacted` drops in a status
 * notice, `code_ready` finalizes the message and surfaces the script (with an
 * optional syntax warning), and the stream ending stops the spinner.
 */
export function useBgpChat() {
  const [tabs, setTabs] = useState<ChatTab[]>(INITIAL_TABS);
  const [currentTab, setCurrentTab] = useState(0);
  const [selectedModel, setSelectedModel] = useState<ChatModel>('bgp_llama');
  const [input, setInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedCode, setGeneratedCode] = useState('');

  const abortRef = useRef<AbortController | null>(null);

  const closeStream = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
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

  const handleEvent = useCallback(
    (data: SseEvent) => {
      switch (data.status) {
        case 'generating':
          patchCurrentMessages((messages) => {
            const last = messages[messages.length - 1];
            if (last && last.sender === 'system' && last.kind !== 'notice' && !last.final) {
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

        case 'compacted': {
          const dropped = data.dropped ?? 0;
          const how = data.summarized ? 'into a summary' : 'to stay within context';
          appendMessage({
            text: `Compacted ${dropped} earlier message${dropped === 1 ? '' : 's'} ${how}.`,
            sender: 'system',
            final: true,
            kind: 'notice',
          });
          break;
        }

        case 'code_ready':
          patchCurrentMessages((messages) => {
            const last = messages[messages.length - 1];
            if (last && last.sender === 'system' && last.kind !== 'notice') {
              const updated = [...messages];
              updated[updated.length - 1] = { ...last, final: true };
              return updated;
            }
            return messages;
          });
          setGeneratedCode(data.code ?? '');
          if (data.warning) {
            appendMessage({ text: data.warning, sender: 'system', final: true, kind: 'notice' });
          }
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
          break;
      }
    },
    [appendMessage, patchCurrentMessages]
  );

  const sendMessage = useCallback(() => {
    const query = input.trim();
    if (!query || isGenerating) return;

    const history = toHistory(tabs[currentTab]?.messages ?? []);
    appendMessage({ text: query, sender: 'user' });
    setInput('');
    setIsGenerating(true);
    setGeneratedCode('');
    closeStream();

    const endpoint = selectedModel === 'bgp_llama' ? 'bgp_llama' : 'bgp_gpt';
    const controller = new AbortController();
    abortRef.current = controller;

    // EventSource can't POST, so read the SSE body off a fetch stream, splitting
    // on the blank-line frame boundary and parsing each `data:` payload.
    (async () => {
      try {
        const res = await fetch(apiUrl(`chat/${endpoint}`), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, history }),
          signal: controller.signal,
        });
        if (!res.ok || !res.body) throw new Error(`Request failed (${res.status})`);

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          let boundary: number;
          while ((boundary = buffer.indexOf('\n\n')) !== -1) {
            const frame = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 2);
            const line = frame.split('\n').find((l) => l.startsWith('data:'));
            if (!line) continue; // skip `: flush` keep-alive comments
            try {
              handleEvent(JSON.parse(line.slice(5).trim()));
            } catch (err) {
              console.error('Failed to parse SSE message:', err);
            }
          }
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          console.error('SSE error:', err);
          appendMessage({
            text: `⚠️ Error: ${(err as Error).message}`,
            sender: 'system',
            final: true,
          });
        }
      } finally {
        if (abortRef.current === controller) abortRef.current = null;
        setIsGenerating(false);
      }
    })();
  }, [
    input,
    isGenerating,
    selectedModel,
    tabs,
    currentTab,
    appendMessage,
    handleEvent,
    closeStream,
  ]);

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
