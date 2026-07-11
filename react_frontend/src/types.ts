/** The two chat backends the user can toggle between. */
export type ChatModel = 'bgp_llama' | 'gpt_5_4_mini';

/** Who/what produced a chat message. */
export type MessageSender = 'user' | 'system' | 'tutorial';

export interface ChatMessage {
  /** Rendered as markdown for system/user; tutorials pass a React node instead. */
  text: string | React.ReactNode;
  sender: MessageSender;
  /** True once the model has finished streaming this message. */
  final?: boolean;
  /** A `notice` is a centered status line (e.g. compaction / code warnings), not a chat bubble. */
  kind?: 'notice';
}

export interface ChatTab {
  id: number;
  label: string;
  messages: ChatMessage[];
}

/** SSE payload shape emitted by the FastAPI agent. */
export interface SseEvent {
  status:
    | 'generating_started'
    | 'generating'
    | 'compacted'
    | 'code_ready'
    | 'no_code_found'
    | 'error'
    | 'complete';
  generated_text?: string;
  code?: string;
  message?: string;
  /** `code_ready`: set when the generated script failed a syntax check. */
  warning?: string;
  /** `compacted`: how many earlier turns were folded away, and whether summarized. */
  dropped?: number;
  summarized?: boolean;
}

// ---- Datasets ----

export interface DatasetItem {
  id: string;
  title: string;
  fileUrl: string;
  promptUrl?: string;
  fileCount: number;
  size: string;
  fileType: string;
  promptType?: string;
  description: string;
  categories?: Record<string, string>;
  jsonSnapshot: unknown;
}

export interface DatasetSection {
  id: string;
  title: string;
  datasets: DatasetItem[];
}
