import type { ChatModel } from '@/types';

/** The pre-processed data window the backend serves queries from. */
export const DATA_WINDOW = {
  collector: 'RIPE RIS · rrc00',
  range: 'October 2024',
};

export const MODEL_LABELS: Record<ChatModel, string> = {
  bgp_llama: 'BGP-LLaMA',
  gpt_4o_mini: 'BGP-GPT',
};

export interface ExampleQuery {
  title: string;
  prompt: string;
}

export const EXAMPLE_QUERIES: ExampleQuery[] = [
  {
    title: 'Prefix & origin analysis',
    prompt:
      'Provide a summary of unique prefixes and origin ASes associated with AS4766 from Oct 28 13:00 to 13:15, 2024. Track the count of unique prefixes and changes in origin ASes, if any.',
  },
  {
    title: 'AS-path analysis',
    prompt:
      'Summarize the AS paths for each prefix associated with ASN AS4766 over the period Oct 28 13:00 to 13:15, 2024. Provide minimum, maximum, and median AS path lengths.',
  },
];
