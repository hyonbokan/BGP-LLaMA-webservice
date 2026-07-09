export type HomeCardKind = 'docs' | 'code' | 'research';

export interface HomeCard {
  kind: HomeCardKind;
  title: string;
  description: string;
  buttonText: string;
  link: string;
}

export const homeCards: HomeCard[] = [
  {
    kind: 'docs',
    title: 'BGP-LLaMA documentation',
    description: 'Learn how to interact with BGP-LLaMA and get the most out of each query.',
    buttonText: 'Coming soon',
    link: '',
  },
  {
    kind: 'code',
    title: 'Web app source code',
    description:
      'The full source for this web app — Django, FastAPI, and the React frontend. Star it if you find it useful.',
    buttonText: 'View on GitHub',
    link: 'https://github.com/hyonbokan/BGP-LLaMA-webservice',
  },
  {
    kind: 'research',
    title: 'LLM research repository',
    description:
      'Self-instruct data generation and the fine-tuning pipeline behind the BGP-LLaMA model.',
    buttonText: 'Learn more',
    link: 'https://github.com/hyonbokan/LLM-research',
  },
];
