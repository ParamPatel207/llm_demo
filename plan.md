# LangChain Agent Demo Plan

## Project Overview
This project aims to create a demonstration of a LangChain-based agent using AWS Bedrock. The agent will be developed in a Jupyter Notebook for clarity and ease of presentation. It will integrate with external tools provided by MCP (Model Context Protocol) servers, each running in a separate Docker container. The demonstration will also include tracing and monitoring capabilities using LangSmith.

## Architecture Components

### 1. LangChain Agent (Jupyter Notebook)
- **Notebook Environment**: The core logic will be in a Jupyter Notebook.
- **LangChain Agent**: Orchestrates the interaction between the LLM and tools.
- **AWS Bedrock Integration**: Connects to AWS Bedrock to use models like Claude.
- **Tool Integration**: The agent will be equipped with tools to interact with the MCP servers.
- **Tracing**: LangSmith will be used for comprehensive experiment tracking and monitoring.

### 2. MCP Servers
- **Framework**: Servers will be built using the `fast-mcp` library.
- **Containerization**: Each MCP server will be containerized using Docker for isolation and scalability.
- **Functionality**: We will create 1-2 example MCP servers (e.g., a simple calculator or a weather service).
- **Stub Responses**: The servers will provide stubbed JSON responses for the demo.

## Implementation Checklist

### Phase 1: Project & Environment Setup
- [ ] Initialize project structure.
- [ ] Create `requirements.txt` with necessary libraries (`langchain`, `boto3`, `jupyter`, `fast-mcp`, `docker`).
- [ ] Set up a `.env` file for environment variables (AWS keys).
- [ ] Create a `Dockerfile` for the main environment if needed, or just rely on a local virtual environment.

### Phase 2: Develop MCP Servers
- [ ] Create a directory `mcp_servers`.
- [ ] Implement a simple `calculator_server` using `fast-mcp`.
    - [ ] Create `mcp_servers/calculator_server/main.py`.
    - [ ] Create `mcp_servers/calculator_server/Dockerfile`.
- [ ] Implement a `weather_server` with stubbed data.
    - [ ] Create `mcp_servers/weather_server/main.py`.
    - [ ] Create `mcp_servers/weather_server/Dockerfile`.
- [ ] Create a `docker-compose.yml` to manage and run the MCP servers.

### Phase 3: Develop the LangChain Agent in Jupyter Notebook
- [ ] Create the main `agent_demo.ipynb` notebook.
- [ ] Inside the notebook:
    - [ ] Load environment variables.
    - [ ] Set up LangSmith for tracing.
    - [ ] Initialize the Bedrock LLM.
    - [ ] Define custom tools to communicate with the running MCP servers.
    - [ ] Create and initialize the LangChain agent with the LLM and tools.
    - [ ] Provide example prompts to demonstrate the agent's capabilities.
    - [ ] Show how to inspect traces in LangSmith.

### Phase 4: Integration and Documentation
- [ ] Ensure the agent notebook can successfully call the dockerized MCP servers.
- [ ] Update `README.md` with instructions on:
    - [ ] Setting up the environment.
    - [ ] Running the MCP servers using Docker Compose.
    - [ ] Running the Jupyter Notebook.
- [ ] Clean up code and add comments.

## Updated File Structure
```
agentMCPDemo/
├── mcp_servers/
│   ├── calculator_server/
│   │   ├── main.py
│   │   └── Dockerfile
│   └── weather_server/
│       ├── main.py
│       └── Dockerfile
├── agent_demo.ipynb
├── docker-compose.yml
├── requirements.txt
├── .env
├── README.md
└── plan.md
```

## Dependencies
- langchain
- langchain-community
- langchain-aws
- langsmith
- boto3
- jupyter
- python-dotenv
- docker
- fast-mcp (assuming this is the package name)

## Environment Variables
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=mcp-agent-demo
```
