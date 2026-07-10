export interface ChangelogEntry {
  title: string;
  detail: string;
  date: string;
}

export const whatsNew: ChangelogEntry[] = [
  {
    title: 'Upgraded GPT Backend to GPT-5.4-mini',
    detail:
      'On July 10th, we migrated the GPT comparison backend from GPT-4o-mini to GPT-5.4-mini, as the GPT-4o model family reached end-of-life and was deprecated. This update brings:\n' +
      '• A newer, more capable model for BGP analysis code generation\n' +
      '• Continued head-to-head comparison against BGP-LLaMA\n' +
      '• A configurable model id (via the OPENAI_MODEL environment variable) for easier future upgrades.',
    date: '2026-07-10',
  },
  {
    title: 'Frontend Rebuilt with a New Design System',
    detail:
      'On July 10th, we rebuilt the web frontend from the ground up for a faster, cleaner, and more maintainable experience. Key updates include:\n' +
      '• Migrated from Create React App to Vite with full TypeScript support\n' +
      '• Redesigned the interface with Tailwind CSS and a dark, control-plane visual theme\n' +
      '• Reworked the chat, dataset, and fine-tuning pages with clearer navigation and richer dataset detail views.',
    date: '2026-07-10',
  },
  {
    title: 'Backend Refactored with SSE Integration',
    detail:
      'On March 26th, we completed a full backend refactoring to enhance performance and maintainability. Key updates include:\n' +
      '• Replaced WebSocket-based LLM interaction with Server-Sent Events (SSE) via FastAPI\n' +
      '• Modularized backend architecture, isolating the LLM service from the main ASGI (Django Daphne) application\n' +
      '• Improved scalability and clearer separation of concerns in the overall backend design.',
    date: '2025-03-26',
  },
  {
    title: 'Updated Home Page UI',
    detail:
      'On March 13th, we revamped the home page design to improve user experience. New changes include:\n' +
      "• Full-width 'What's New' carousel\n" +
      '• Improved navigation with clearer calls to action\n' +
      '• Better separation of content sections for enhanced readability and accessibility.',
    date: '2025-03-13',
  },
  {
    title: 'Enhanced Chat Experience',
    detail:
      'On February 28th, we upgraded our chat functionality by integrating WebSocket support for real-time messaging. Key improvements:\n' +
      '• Smoother, faster real-time communication\n' +
      '• Instant notifications for new messages\n' +
      '• A more interactive user experience overall.',
    date: '2025-02-28',
  },
  {
    title: 'Upgraded BGP-LLaMA Model',
    detail:
      'On February 10th, BGP-LLaMA was upgraded to a LLaMA 3.1 8B model. This update brings:\n' +
      '• A more lightweight model for faster processing\n' +
      '• Enhanced accuracy in BGP routing data analysis\n' +
      '• Improved overall performance.',
    date: '2025-02-10',
  },
  {
    title: 'Optimized BGP Analysis Code',
    detail:
      'On January 15th, we introduced an automated code generation feature for processing local BGP update files. The optimizations include:\n' +
      '• Significant reduction in data collection and processing time\n' +
      '• More efficient routing analysis workflows\n' +
      '• Streamlined generation of analysis code.',
    date: '2025-01-15',
  },
  {
    title: 'Added GPT-4o-mini for Comparison',
    detail:
      'On December 20th, we integrated a prompt engineered GPT-4o-mini option, enabling performance comparisons with BGP-LLaMA. This update offers:\n' +
      '• A valuable benchmark for evaluating model efficiency\n' +
      '• Direct performance comparison between GPT-4o-mini and BGP-LLaMA\n' +
      '• Additional insights into model accuracy and scalability.',
    date: '2024-12-20',
  },
];
