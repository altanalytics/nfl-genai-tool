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
  {
    id: 'us.anthropic.claude-3-5-haiku-20241022-v1:0',
    name: 'Claude Haiku 3.5',
    description: 'Quick advanced reasoning and analysis'
  },
  {
    id: 'us.anthropic.claude-sonnet-4-20250514-v1:0',
    name: 'Claude Sonnet 4',
    description: 'Advanced reasoning and analysis'
  }
];

export const PERSONALITY_OPTIONS: PersonalityOption[] = [
  {
    id: 'game_recap',
    name: 'Game Recap Expert',
    description: 'Specializes in creating detailed game recaps and summaries'
  },
  {
    id: 'nfl_stats',
    name: 'NFL Stats Analyst',
    description: 'Deep statistical knowledge with access to NFL knowledge base'
  }
];

export const DEFAULT_MODEL = 'us.amazon.nova-pro-v1:0';
export const DEFAULT_PERSONALITY = 'game_recap';
