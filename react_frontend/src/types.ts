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

// ---- BGP Agent (autonomous run-and-observe) ----

/** How a single agent run is progressing. */
export type AgentRunStatus = 'running' | 'done' | 'error';

/** The terminal outcome of a run: the answer plus run metadata. */
export interface AgentRunResult {
  text: string;
  isError: boolean;
  subtype: string | null;
  costUsd: number | null;
  durationMs: number | null;
  numTurns: number | null;
  structuredOutput: unknown;
}

/** One question posed to the agent and the run it kicked off. */
export interface AgentRun {
  id: number;
  query: string;
  status: AgentRunStatus;
  /** Wall-clock start (ms), used to show a live elapsed timer while running. */
  startedAt: number;
  result?: AgentRunResult;
  error?: string;
}

/** SSE payload shape the agent endpoint emits (`/api/agent/run`). */
export interface AgentSseEvent {
  status: 'agent_started' | 'running' | 'result' | 'error';
  text?: string;
  is_error?: boolean;
  subtype?: string | null;
  cost_usd?: number | null;
  duration_ms?: number | null;
  num_turns?: number | null;
  structured_output?: unknown;
  message?: string;
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
