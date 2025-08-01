from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Calculator MCP Server",
    description="A simple calculator service that supports add, subtract, multiply, and divide.",
    version="1.0.0",
)

class CalculationRequest(BaseModel):
    operation: str
    a: float
    b: float

class CalculationResponse(BaseModel):
    result: float
    detail: str

@app.post("/calculate", response_model=CalculationResponse)
async def calculate(request: CalculationRequest):
    """
    Performs a calculation based on the provided operation and operands.
    """
    logger.info(f"Received calculation request: {request.dict()}")
    
    op = request.operation.lower()
    a = request.a
    b = request.b
    
    if op == "add":
        result = a + b
    elif op == "subtract":
        result = a - b
    elif op == "multiply":
        result = a * b
    elif op == "divide":
        if b == 0:
            logger.error("Division by zero attempted.")
            raise HTTPException(status_code=400, detail="Division by zero is not allowed.")
        result = a / b
    else:
        logger.warning(f"Invalid operation requested: {request.operation}")
        raise HTTPException(status_code=400, detail=f"Invalid operation: {request.operation}. Supported operations are add, subtract, multiply, divide.")
        
    response_detail = f"Successfully performed {op} on {a} and {b}."
    logger.info(response_detail)
    
    return CalculationResponse(result=result, detail=response_detail)

@app.get("/health")
async def health_check():
    """
    A simple health check endpoint to confirm the server is running.
    """
    return {"status": "ok"}
