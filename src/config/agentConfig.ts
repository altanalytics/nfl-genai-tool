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
    id: 'nfl_native_analyst',
    name: 'NFL Analyst Local Tools',
    description: 'Database-driven statistical analysis and insights using local toold for complex queries and trends'
  },
    {
    id: 'nfl_analyst',
    name: 'NFL Analyst MCP',
    description: 'Database-driven statistical analysis and insights using MCP microservices for complex queries and trends'
  },
  {
    id: 'nfl_game_recap',
    name: 'Game Recap Specialist',
    description: 'Narrative-driven game recaps and analysis with context-aware storytelling and player narratives'
  }
];

export const DEFAULT_MODEL = 'us.amazon.nova-pro-v1:0';
export const DEFAULT_PERSONALITY = 'nfl_native_analyst';
