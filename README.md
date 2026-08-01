# Claude + Tavily Search Agent Demo

This project demonstrates a powerful AI agent using **Claude 3.5 Sonnet** via AWS Bedrock with **Tavily search** capabilities for real-time web intelligence.

## Features

- **Claude 3.5 Reasoning**: Advanced AI via AWS Bedrock with superior reasoning capabilities
- **Real-time Web Search**: Live internet search powered by Tavily API
- **Intelligent Tool Selection**: Claude automatically decides when and how to search
- **Interactive Jupyter Notebook**: Easy-to-follow demo with step-by-step execution
- **Production-Ready**: Enterprise-grade AWS infrastructure with robust error handling
- **Direct API Integration**: No middleware - direct Claude + Tavily integration
- **Conversation Memory**: Maintains context for follow-up questions

## How to Run the Demo

### Prerequisites

- Python 3.8+
- AWS account with Bedrock access (Claude 3.5 Sonnet enabled)
- AWS credentials configured in your environment  
- Tavily API key from [tavily.com](https://tavily.com)

### 1. Set Up Your Environment

First, clone this repository to your local machine:

```bash
git clone <your-repo-url>
cd <repository-name>
```

Next, create a virtual environment and install the required Python packages:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\\Scripts\\activate`
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the root of the project by copying the example:

```bash
cp env.example .env
```

Now, open the `.env` file and add your credentials:

```
# AWS Bedrock Configuration (for Claude 3.5 Sonnet)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Tavily Search API
TAVILY_API_KEY=tvly-YOUR_TAVILY_API_KEY_HERE
```

*Note: Your AWS credentials should already be configured if you're using AWS services.*

### 3. Run the Demo

Start the Jupyter Notebook to run the Claude + Tavily search agent:

```bash
source venv/bin/activate
jupyter notebook agent_demo.ipynb
```

This will open the notebook in your web browser. Execute the cells one by one to see Claude in action with real-time web search capabilities.

### 4. Try the Interactive Demo

The notebook includes:
- **Setup verification**: Check that your AWS and Tavily credentials are working
- **Live examples**: See Claude search for current events and factual information  
- **Interactive chat**: Have natural conversations with web-powered responses

### 5. Example Queries to Try

- "What are the latest developments in AI in 2024?"
- "What is the current price of Bitcoin?"
- "Who won the latest Nobel Prize in Physics?"
- "What are the current trends in renewable energy?"

## Blender MCP (Cursor)

This workspace includes project-scoped [Blender MCP](https://github.com/ahujasid/blender-mcp) configuration so Cursor can control a local Blender session.

- **Cursor config**: [`.cursor/mcp.json`](.cursor/mcp.json)
- **Blender addon**: [`blender/addon.py`](blender/addon.py)
- **Setup guide**: [`docs/blender-mcp-setup.md`](docs/blender-mcp-setup.md)

Quick start:

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
2. Install the addon in Blender from `blender/addon.py`
3. In Blender, open the BlenderMCP sidebar panel and click **Connect to Claude**
4. Restart Cursor and confirm `blender` is green under **Settings → MCP**

See the [full setup guide](docs/blender-mcp-setup.md) for Windows config, remote hosts, and troubleshooting.

## Project Structure

```
agentMCPDemo/
├── .cursor/
│   └── mcp.json            # Cursor MCP servers (Blender)
├── agent_demo.ipynb        # Main demo: Claude + Tavily search agent
├── blender/
│   └── addon.py            # BlenderMCP addon for local Blender install
├── docs/
│   └── blender-mcp-setup.md
├── mcp_servers/            # Legacy MCP servers (optional)
│   ├── tavily_server/      # Tavily MCP server implementation
│   ├── calculator_server/  # Calculator tool server
│   └── weather_server/     # Weather tool server
├── requirements.txt        # Python dependencies
├── env.example             # Environment configuration template
├── docker-compose.yml      # Container management (optional)
├── README.md               # This documentation
└── plan.md                 # Project implementation plan
```

## Key Components

- **`agent_demo.ipynb`**: The main interactive demo featuring Claude 3.5 Sonnet with Tavily search
- **AWS Bedrock Integration**: Direct API calls to Claude via boto3
- **Tavily Search**: Real-time web search capabilities  
- **Blender MCP**: Cursor integration for controlling a local Blender session
- **Legacy MCP Servers**: Optional containerized tools (not required for main demo)

## Why This Architecture?

- **🧠 Claude 3.5 Reasoning**: Superior reasoning and tool selection capabilities
- **☁️ AWS Infrastructure**: Enterprise-grade reliability and performance  
- **🔍 Real-time Search**: Current, accurate information via Tavily
- **💡 Intelligent Tool Use**: Claude decides when and how to search automatically
- **🚀 Production-Ready**: Built for scale with proper error handling
