export interface HomeCard {
  title: string;
  description: string;
  buttonText: string;
  link: string;
}

export const homeCards: HomeCard[] = [
  {
    title: 'BGP-LLaMA documentation',
    description: 'Learn how to interact with BGP-LLaMA.',
    buttonText: 'Coming soon',
    link: '',
  },
  {
    title: 'Web app source code',
    description:
      'Visit the GitHub repo to see the entire web app source code and star it if you find it useful.',
    buttonText: 'View on GitHub',
    link: 'https://github.com/hyonbokan/BGP-LLaMA-webservice',
  },
  {
    title: 'LLM research repository',
    description:
      'Our GitHub repository with self-instruct data generation and finetuning tutorial.',
    buttonText: 'Learn more',
    link: 'https://github.com/hyonbokan/LLM-research',
  },
];
