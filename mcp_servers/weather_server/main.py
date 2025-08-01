from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Weather MCP Server",
    description="A simple weather service that provides stubbed weather data for a given city.",
    version="1.0.0",
)

class WeatherRequest(BaseModel):
    city: str

class WeatherResponse(BaseModel):
    city: str
    temperature: float
    description: str
    humidity: int

# Stubbed weather data
STUB_WEATHER_DATA = {
    "New York": {"temperature": 15.5, "description": "Cloudy with a chance of rain", "humidity": 70},
    "London": {"temperature": 12.0, "description": "Light drizzle and overcast", "humidity": 85},
    "Tokyo": {"temperature": 22.3, "description": "Sunny and pleasant", "humidity": 60},
    "Sydney": {"temperature": 25.0, "description": "Clear skies and warm", "humidity": 55},
}

@app.post("/get_weather", response_model=WeatherResponse)
async def get_weather(request: WeatherRequest):
    """
    Returns stubbed weather information for a specified city.
    If the city is not in the stub data, it returns a random weather condition.
    """
    city = request.city
    logger.info(f"Received weather request for city: {city}")

    if city in STUB_WEATHER_DATA:
        weather = STUB_WEATHER_DATA[city]
        response = WeatherResponse(city=city, **weather)
    else:
        logger.warning(f"City '{city}' not found in stub data. Returning random weather.")
        # Generate random weather for unknown cities
        response = WeatherResponse(
            city=city,
            temperature=round(random.uniform(5.0, 35.0), 1),
            description="Random weather condition",
            humidity=random.randint(40, 90)
        )
        
    logger.info(f"Returning weather for {city}: {response.dict()}")
    return response

@app.get("/health")
async def health_check():
    """
    A simple health check endpoint to confirm the server is running.
    """
    return {"status": "ok"}
