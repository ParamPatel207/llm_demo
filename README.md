# LangChain Agent with Bedrock and MCP Servers Demo - MLflow Edition

This project demonstrates how to build a LangChain agent that uses AWS Bedrock for its language model and interacts with external tools hosted as MCP (Model Context Protocol) servers. The entire demonstration is contained within a Jupyter Notebook for easy, step-by-step execution, with comprehensive tracking using MLflow.

## Features

- **Jupyter Notebook-driven**: The main logic is presented in a clear, interactive notebook.
- **AWS Bedrock Integration**: Leverages powerful models like Claude from AWS Bedrock.
- **Dockerized MCP Servers**: External tools (like a calculator and a weather service) run in isolated Docker containers.
- **MLflow Tracking**: Comprehensive experiment tracking, metrics logging, and model management.
- **Performance Analytics**: Real-time monitoring of agent execution times, response quality, and tool usage.
- **Model Versioning**: Track different agent configurations and their performance over time.
- **FastAPI Framework**: The MCP servers are built using FastAPI, a modern, fast web framework for Python.

## How to Run the Demo

### Prerequisites

- [Docker](https://www.docker.com/get-started) and Docker Compose
- Python 3.8+
- An AWS account with access to Bedrock models.
- MLflow for experiment tracking (included in requirements.txt)

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
# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# MLflow Configuration
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=LangChain-Bedrock-MCP-Agent
```

*Note: MLflow will automatically create a local SQLite database for tracking if no specific backend is configured.*

### 3. Start the MCP Servers

With Docker running, start the calculator and weather MCP servers using Docker Compose:

```bash
docker-compose up --build
```

This command will build the Docker images for the two servers and run them in the background. You should see logs indicating that both servers are running. The calculator will be available at `http://localhost:8001` and the weather service at `http://localhost:8002`.

### 4. Start MLflow Tracking Server (Optional)

For a better tracking experience, start the MLflow UI server:

```bash
source venv/bin/activate
mlflow ui --host 0.0.0.0 --port 5000
```

This will start the MLflow UI at http://localhost:5000 where you can view experiment results, metrics, and model artifacts.

### 5. Run the Jupyter Notebook

Now you can start the Jupyter Notebook to run the agent:

```bash
source venv/bin/activate
jupyter notebook agent_demo.ipynb
```

This will open the notebook in your web browser. You can then execute the cells one by one to see the agent in action with comprehensive MLflow tracking.

### 6. Shut Down the Servers

Once you are finished with the demo, you can stop the MCP servers with:

```bash
docker-compose down
```

## Project Structure

```
agentMCPDemo/
├── mcp_servers/
│   ├── calculator_server/  # Dockerized calculator tool
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── weather_server/     # Dockerized weather tool
│       ├── main.py
│       ├── Dockerfile
│       └── requirements.txt
├── agent_demo.ipynb        # The main notebook for the demo
├── docker-compose.yml      # Manages the MCP server containers
├── requirements.txt        # Python dependencies for the notebook
├── .env.example            # Example environment file
├── README.md               # This file
└── plan.md                 # The project plan
```
