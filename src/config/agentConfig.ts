export interface ModelOption {
  id: string;
  name: string;
  description: string;
}

export interface PersonalityOption {
  id: string;
  name: string;
  description: string;
}

export const MODEL_OPTIONS: ModelOption[] = [
  {
    id: 'us.amazon.nova-micro-v1:0',
    name: 'Amazon Nova Micro',
    description: 'Fast and efficient for simple tasks'
  },
  {
    id: 'us.amazon.nova-pro-v1:0',
    name: 'Amazon Nova Pro',
    description: 'Balanced performance and capability'
  },
  {
    id: 'us.amazon.nova-premier-v1:0',
    name: 'Amazon Nova Premier',
    description: 'Most capable Nova model'
  },
  // {
  //   id: 'us.anthropic.claude-sonnet-4-20250514-v1:0',
  //   name: 'Claude Sonnet 4',
  //   description: 'Advanced reasoning and analysis'
  // }
];

export const PERSONALITY_OPTIONS: PersonalityOption[] = [
  {
    id: 'basic',
    name: 'Helpful Assistant',
    description: 'Balanced and professional'
  },
  {
    id: 'creative',
    name: 'Creative Thinker',
    description: 'Imaginative and innovative'
  },
  {
    id: 'analytical',
    name: 'Analytical Expert',
    description: 'Logical and detailed responses'
  },
  {
    id: 'friendly',
    name: 'Friendly Companion',
    description: 'Warm and conversational'
  },
  {
    id: 'silly',
    name: 'Silly Trickster',
    description: 'Tells jokes and gives silly responses'
  }
];

export const DEFAULT_MODEL = 'us.amazon.nova-micro-v1:0';
export const DEFAULT_PERSONALITY = 'basic';
