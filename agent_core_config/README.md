# NFL Agent Core Configuration

This folder contains Lambda functions and MCP Gateway configuration for the NFL GenAI system. The MCP (Model Context Protocol) architecture enables the NFL Analyst personality to access database queries, game data, and knowledge base search through Lambda-based microservices.

## Quick Deployment

### Prerequisites
1. **Deploy main application** first to create S3 bucket with NFL data
2. **Install dependencies** - The `bedrock-agentcore-starter-toolkit` should be added to your uv project
3. **AWS Profile** - Ensure you have proper AWS credentials configured

### Automated Deployment
```bash
# Run from the genai directory using uv
cd ../genai

# Deploy Lambda functions
uv run ../agent_core_config/deploy_lambdas.py

# FIRST TIME: Deploy MCP Gateway (creates Cognito resources)
AWS_PROFILE=your-profile uv run ../agent_core_config/gateway_deploy.py

# UPDATES: Update existing gateway targets
AWS_PROFILE=your-profile uv run ../agent_core_config/gateway_update.py

# Test the deployment
AWS_PROFILE=your-profile uv run ../agent_core_config/test_mcp_gateway.py
```

## NFL MCP Services

The system provides three specialized Lambda-based MCP services:

### 1. NFL Data Service (`nfl-data-service`)
**Purpose**: Execute SQL queries against the NFL Athena database
- **Database**: `nfl_stats_database`
- **Safety**: Only SELECT queries allowed
- **Usage**: Statistical analysis, trend queries, performance comparisons

### 2. NFL Game Service (`nfl-game-service`)
**Purpose**: Retrieve complete game data from S3
- **Inputs**: Play-by-play data, player stats, team stats, drive reports
- **Outputs**: Game recaps and analysis (for learning writing styles)
- **Usage**: Deep game analysis, understanding game narratives

### 3. NFL Knowledge Service (`nfl-knowledge-service`)
**Purpose**: Search NFL knowledge base for rules and context
- **Knowledge Base ID**: `DO11YJUJMC`
- **Usage**: NFL rules, historical context, league information

## Architecture Benefits

### Unified Tool Interface
The NFL Analyst personality uses MCP services through the gateway:
- **Simpler for Agent** - Clean tool interface
- **Flexible Operations** - Database queries, game data, knowledge search
- **Consistent Responses** - Standardized JSON response format
- **Better Performance** - Direct Lambda invocation through MCP Gateway

### Separation of Concerns
- **Game Recap Specialist** - Uses direct tools for workflow-heavy game recaps
- **NFL Analyst** - Uses MCP services for database-driven analytics
- **Clean Architecture** - Each personality optimized for its use case
