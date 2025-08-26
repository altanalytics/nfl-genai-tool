# NFL GenAI Tool

A comprehensive AI-powered NFL analysis platform featuring two specialized AI personalities with distinct architectures. Built as a custom solution using Amazon Bedrock AgentCore, this system provides both narrative game analysis and statistical insights through an advanced dual-personality approach.

## 🏈 What This System Provides

### **Two Specialized AI Personalities**

#### **🎯 Game Recap Specialist (`nfl_game_recap`)**
- **Purpose**: Creates engaging, narrative-driven game recaps and analysis
- **Architecture**: Direct tool integration optimized for workflow-heavy processes
- **Strengths**: Context-aware storytelling, game flow analysis, player narratives
- **Tools**: 4 specialized tools for comprehensive game analysis
- **Use Cases**: Game recaps, matchup analysis, storytelling

#### **📊 NFL Analyst (`nfl_analyst`)**  
- **Purpose**: Provides database-driven statistical analysis and insights
- **Architecture**: MCP Gateway with Lambda microservices for scalable data access
- **Strengths**: Complex SQL queries, trend analysis, schema-aware database interactions
- **Tools**: 3 MCP services with knowledge base integration
- **Use Cases**: Statistical analysis, player comparisons, trend identification

### **Production-Ready Infrastructure**
- 🔐 **Cognito Authentication** - Secure user management with signup notifications
- 💬 **React Chat Interface** - Mobile-responsive UI with real-time streaming
- 📧 **SNS Integration** - Automated user signup alerts
- ⚡ **Lambda Microservices** - Auto-scaling backend with proper dependency management
- 🗄️ **Athena Database** - Serverless SQL queries against comprehensive NFL datasets
- 🧠 **Knowledge Base Integration** - Database schemas and Sample Queries
- 🌐 **MCP Gateway** - Model Context Protocol for microservices architecture
- 📱 **Mobile-Optimized** - Responsive navigation and mobile-friendly design

## 🏗️ System Architecture

### **Frontend (React + Amplify)**
```
React Chat App → Cognito Auth → Lambda Function URL → Bedrock AgentCore
```

### **Backend - Dual Architecture**

#### **Game Recap Specialist Flow:**
```
User Input → Bedrock AgentCore → Direct Tools → S3 Data → Game Recap
```

#### **NFL Analyst Flow:**
```
User Input → Bedrock AgentCore → MCP Gateway → Lambda Services → Data Sources → Analysis
```

### **Data Sources**
- **S3 Bucket** (`alt-nfl-bucket`): Game data, schedules, knowledge base files
- **Athena Database** (`nfl_stats_database`): Queryable NFL statistics
- **Knowledge Base** (`ZJOYGGYSJM`): NFL rules and historical context

## 🚀 Quick Start

### **Step 1: Deploy Frontend Infrastructure**

1. **Clone and setup repository**
```bash
git clone https://github.com/your-repo/nfl-genai-tool.git
cd nfl-genai-tool
```

2. **Deploy through Amplify Console**
   - Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify/home)
   - Connect your git repository
   - Add environment variables:
     - `AGENTCORE_RUNTIME_ARN` = Your agent runtime ARN (get after Step 3)
     - `NOTIFICATION_EMAIL` = Your email for notifications

### **Step 2: Enable Bedrock Models**
Go to AWS Bedrock Console and enable **Nova Micro Model** and **CLaude 4 Sonnet**.

### **Step 3: Build and Deploy Custom AI Agent**

```bash
cd genai

# Install dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh

# Test locally (optional)
export AWS_PROFILE=nfl
uv run uvicorn agent:app --host 0.0.0.0 --port 8080

# Build and push Docker image
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text --profile $AWS_PROFILE)

aws ecr create-repository --repository-name my-strands-agent --region us-east-1 --profile $AWS_PROFILE

aws ecr get-login-password --region us-east-1 --profile $AWS_PROFILE | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com 

docker buildx build --platform linux/arm64 -t $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/my-strands-agent:latest --push .

# Deploy to Bedrock Agent Core
uv run agent_deploy.py

# Update Bedrock Agent Core
uv run agent_update.py
```

### **Step 4: Deploy MCP Infrastructure (for NFL Analyst)**

```bash
# Deploy Lambda functions
uv run ../agent_core_config/deploy_lambdas.py

# Deploy MCP Gateway (first time)
AWS_PROFILE=nfl uv run ../agent_core_config/gateway_deploy.py

# Test MCP services
AWS_PROFILE=nfl uv run ../agent_core_config/test_mcp_gateway.py
```

### **Step 5: Update Environment Variables**
Update the `AGENTCORE_RUNTIME_ARN` in Amplify with the ARN from Step 3.

## 🛠️ Detailed Tool Breakdown

### **Game Recap Specialist Tools**

#### **`get_schedules`**
- **Purpose**: Find NFL games by team, season, week, or matchup
- **Use Cases**: "Show me all Cowboys games" or "Find Patriots vs Bills matchups"

#### **`get_context`**  
- **Purpose**: Get team performance context before a specific game
- **Returns**: Recent games for each team plus head-to-head history
- **Use Cases**: Understanding team momentum and historical matchups

#### **`get_game_inputs`**
- **Purpose**: Retrieve detailed game data (play-by-play, stats, summaries)
- **Use Cases**: Deep game analysis, creating comprehensive recaps

#### **`get_game_outputs`**
- **Purpose**: Retrieve existing game recaps and analysis
- **Use Cases**: Learning writing styles, understanding narrative approaches

### **NFL Analyst MCP Services**

#### **`nfl-data-service___nfl_data_service`**
- **Purpose**: Execute SQL queries against Athena database
- **Database**: `nfl_stats_database` with comprehensive NFL statistics
- **Safety**: Only SELECT queries allowed, 100-row limit
- **Use Cases**: Statistical analysis, trend queries, performance comparisons

#### **`nfl-game-service___nfl_game_service`**
- **Purpose**: Retrieve complete game data (inputs + outputs)
- **Data**: Play-by-play, player stats, team stats, existing recaps
- **Use Cases**: Deep game analysis, understanding data relationships

#### **`nfl-knowledge-service___nfl_knowledge_service`**
- **Purpose**: Search NFL knowledge base for rules and context
- **Knowledge Base**: `ZJOYGGYSJM` with NFL rules and historical facts
- **Use Cases**: Rule clarifications, historical context, league information

## 📊 Database Schema

The system includes comprehensive NFL data tables accessible via Athena:

- **`clean_schedule`** - Game schedules and results
- **`team_mapping`** - Team information and abbreviations  
- **`play_by_play`** - Detailed play-by-play data
- **`player_stats`** - Individual player statistics
- **`team_stats`** - Team-level performance metrics
- **`drive_report`** - Drive summaries and scoring
- **`pbp_stats_*`** - Specialized play-by-play statistics

Schema files are automatically deployed to S3 at: `s3://alt-nfl-bucket/knowledge_base_sql_ddl/`

## 🎯 Usage Examples

### **Game Recap Specialist**
```
"Create a recap for the Washington vs Chicago game from week 8"
→ Follows structured workflow: confirms game → asks for context → gathers data → creates engaging narrative
```

### **NFL Analyst**  
```
"Show me the top 5 rushing performances this season"
→ Executes: SELECT player, team, rushing_yards FROM player_stats WHERE season=2024 ORDER BY rushing_yards DESC LIMIT 5

"What are the playoff seeding rules?"
→ Searches knowledge base for NFL playoff information

"Analyze the Bears vs Washington game data"
→ Retrieves complete game inputs and outputs for statistical analysis
```

## 🔧 Configuration Files

### **Core Agent Configuration**
- **`genai/agent_config.py`** - Personality and tool configuration
- **`genai/prompts/nfl_tools.md`** - Game Recap Specialist prompt
- **`genai/prompts/nfl_analyst.md`** - NFL Analyst prompt
- **`genai/prompts/rules.md`** - Shared behavioral rules

### **MCP Infrastructure**
- **`agent_core_config/deploy_lambdas.py`** - Lambda deployment automation
- **`agent_core_config/gateway_deploy.py`** - MCP Gateway setup
- **`agent_core_config/gateway_update.py`** - Gateway updates
- **`agent_core_config/test_mcp_gateway.py`** - Service testing

### **Frontend Configuration**
- **`amplify/backend.ts`** - Infrastructure as code
- **`src/components/Navigation/`** - Mobile-friendly navigation
- **Auto-deployment** - DDL files sync to S3 on deployment

## 🔐 Security & Permissions

### **IAM Roles Created**
- **`bedrock-agent-core-role`** - For Python agent execution
- **`nfl-mcp-lambda-role`** - For MCP Lambda functions

### **Required Permissions**
- **S3**: Read/write access to `alt-nfl-bucket`
- **Athena**: Query execution and results access
- **Bedrock**: Model invocation and agent runtime access
- **Knowledge Base**: Document retrieval access

## 🚀 Deployment Architecture

### **Amplify Frontend**
- **React application** with Cognito authentication
- **Lambda Function URL** for direct agent access
- **S3 integration** for session management
- **SNS notifications** for user events

### **Bedrock AgentCore Backend**
- **Docker container** with Python agent
- **ECR repository** for container storage
- **Streaming responses** via Function URL
- **Session persistence** in S3

### **MCP Microservices**
- **Three Lambda functions** for specialized data access
- **API Gateway integration** via MCP Gateway
- **Cognito authorization** for secure access
- **Auto-scaling** based on demand

## 📈 Benefits of This Architecture

### **Separation of Concerns**
- **Game Recap Specialist**: Optimized for narrative workflows and storytelling
- **NFL Analyst**: Optimized for data analysis and statistical queries

### **Scalability**
- **Lambda-based microservices** scale independently based on demand
- **MCP Gateway** handles routing and load balancing automatically
- **Athena** provides serverless query processing without infrastructure management

### **Maintainability**  
- **Clear tool boundaries** between personalities prevent feature creep
- **Modular Lambda functions** allow independent updates and testing
- **Infrastructure as code** ensures reproducible deployments

### **User Experience**
- **Specialized interfaces** tailored for different analytical needs
- **Mobile-friendly design** with responsive navigation components
- **Real-time streaming** responses for immediate engagement
- **Schema-aware queries** prevent database errors through knowledge base integration

## 🧪 Testing

### **Local Testing**
```bash
# Test agent locally
uv run uvicorn agent:app --host 0.0.0.0 --port 8080

# Test MCP services
AWS_PROFILE=yourprofile uv run ../agent_core_config/test_mcp_gateway.py

# Test individual tools
uv run agent_cli.py
```

### **Production Testing**
- **Amplify deployment** automatically tests frontend
- **MCP Gateway testing** validates all microservices
- **End-to-end testing** through chat interface

## 🎉 What You Get

- ✅ **Two specialized AI personalities** for different NFL analysis needs
- ✅ **Complete chat application** with authentication and streaming
- ✅ **Scalable microservices architecture** with MCP Gateway
- ✅ **Comprehensive NFL database** with SQL query capabilities
- ✅ **Knowledge base integration** for rules and context
- ✅ **Mobile-friendly interface** with responsive design
- ✅ **Production-ready infrastructure** on AWS
- ✅ **Easy customization** and extension capabilities

Your NFL GenAI Tool provides both narrative storytelling and analytical insights, making it the complete solution for NFL data analysis and game coverage! 🏈🚀
