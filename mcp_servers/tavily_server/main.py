#!/usr/bin/env python3
"""
Tavily Search MCP Server

This server provides internet search capabilities using the Tavily API.
It offers multiple search methods including general search, Q&A search, and context search.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult, 
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)
from tavily import TavilyClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Tavily client
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    logger.error("TAVILY_API_KEY environment variable is required")
    raise ValueError("TAVILY_API_KEY environment variable is required")

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# Create MCP server
server = Server("tavily-search")

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available Tavily search tools."""
    return [
        Tool(
            name="tavily_search",
            description=(
                "Perform a comprehensive web search using Tavily API. "
                "Returns search results with URLs, titles, and content snippets. "
                "Use this for general web searches when you need multiple sources of information."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to execute"
                    },
                    "max_results": {
                        "type": "integer", 
                        "description": "Maximum number of results to return (default: 5, max: 20)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    },
                    "include_domains": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of domains to search within (optional)"
                    },
                    "exclude_domains": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "List of domains to exclude from search (optional)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="tavily_qna_search",
            description=(
                "Get a direct, concise answer to a specific question using Tavily's Q&A search. "
                "This is optimized for factual questions where you need a single, accurate answer "
                "rather than multiple search results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question to get an answer for"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="tavily_get_context",
            description=(
                "Get comprehensive context about a topic for RAG (Retrieval-Augmented Generation) applications. "
                "Returns a formatted context string that contains relevant information from multiple sources. "
                "Use this when you need detailed background information on a topic."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The topic to get context about"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum number of tokens in the context (default: 4000)",
                        "default": 4000,
                        "minimum": 100,
                        "maximum": 8000
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="tavily_extract_content",
            description=(
                "Extract raw content from specific URLs using Tavily's extraction API. "
                "Useful for getting clean, formatted content from web pages. "
                "Can handle multiple URLs simultaneously (up to 20)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of URLs to extract content from (max 20)",
                        "maxItems": 20
                    },
                    "include_images": {
                        "type": "boolean",
                        "description": "Whether to include image URLs in the response (default: false)",
                        "default": False
                    }
                },
                "required": ["urls"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for Tavily search operations."""
    
    try:
        if name == "tavily_search":
            return await handle_search(arguments)
        elif name == "tavily_qna_search":
            return await handle_qna_search(arguments)
        elif name == "tavily_get_context":
            return await handle_get_context(arguments)
        elif name == "tavily_extract_content":
            return await handle_extract_content(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Error in {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def handle_search(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle general web search requests."""
    query = arguments["query"]
    max_results = arguments.get("max_results", 5)
    include_domains = arguments.get("include_domains")
    exclude_domains = arguments.get("exclude_domains")
    
    logger.info(f"Performing search for: {query}")
    
    try:
        # Prepare search parameters
        search_params = {
            "query": query,
            "max_results": max_results
        }
        
        if include_domains:
            search_params["include_domains"] = include_domains
        if exclude_domains:
            search_params["exclude_domains"] = exclude_domains
            
        # Execute search
        response = tavily_client.search(**search_params)
        
        # Format response
        results = []
        if "results" in response:
            for i, result in enumerate(response["results"][:max_results], 1):
                formatted_result = f"""
**Result {i}:**
**Title:** {result.get('title', 'N/A')}
**URL:** {result.get('url', 'N/A')}
**Content:** {result.get('content', 'N/A')}
**Score:** {result.get('score', 'N/A')}
---
"""
                results.append(formatted_result)
        
        if not results:
            return [TextContent(type="text", text="No search results found.")]
            
        formatted_response = f"""
# Tavily Search Results for: "{query}"

Found {len(results)} results:

{"".join(results)}

**Search completed successfully.**
"""
        
        return [TextContent(type="text", text=formatted_response)]
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return [TextContent(type="text", text=f"Search failed: {str(e)}")]

async def handle_qna_search(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle Q&A search requests for direct answers."""
    query = arguments["query"]
    
    logger.info(f"Performing Q&A search for: {query}")
    
    try:
        # Execute Q&A search
        answer = tavily_client.qna_search(query=query)
        
        formatted_response = f"""
# Tavily Q&A Result for: "{query}"

**Answer:** {answer}

**Note:** This answer is generated from web sources and optimized for factual accuracy.
"""
        
        return [TextContent(type="text", text=formatted_response)]
        
    except Exception as e:
        logger.error(f"Q&A search error: {str(e)}")
        return [TextContent(type="text", text=f"Q&A search failed: {str(e)}")]

async def handle_get_context(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle context retrieval for RAG applications."""
    query = arguments["query"]
    max_tokens = arguments.get("max_tokens", 4000)
    
    logger.info(f"Getting context for: {query}")
    
    try:
        # Get search context
        context = tavily_client.get_search_context(
            query=query,
            max_tokens=max_tokens
        )
        
        formatted_response = f"""
# Tavily Context for: "{query}"

## Generated Context:

{context}

---
**Context Length:** ~{len(context.split())} words
**Max Tokens Requested:** {max_tokens}

**Note:** This context is compiled from multiple web sources and formatted for RAG applications.
"""
        
        return [TextContent(type="text", text=formatted_response)]
        
    except Exception as e:
        logger.error(f"Context retrieval error: {str(e)}")
        return [TextContent(type="text", text=f"Context retrieval failed: {str(e)}")]

async def handle_extract_content(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle content extraction from URLs."""
    urls = arguments["urls"]
    include_images = arguments.get("include_images", False)
    
    logger.info(f"Extracting content from {len(urls)} URLs")
    
    try:
        # Execute extraction
        response = tavily_client.extract(
            urls=urls,
            include_images=include_images
        )
        
        # Format successful results
        results = []
        if "results" in response:
            for i, result in enumerate(response["results"], 1):
                content_preview = result.get('raw_content', '')[:500]
                if len(result.get('raw_content', '')) > 500:
                    content_preview += "..."
                    
                formatted_result = f"""
**Extract {i}:**
**URL:** {result.get('url', 'N/A')}
**Content Preview:** {content_preview}
**Full Content Length:** {len(result.get('raw_content', ''))} characters
"""
                if include_images and result.get('images'):
                    formatted_result += f"**Images Found:** {len(result['images'])} images\n"
                    
                formatted_result += "---\n"
                results.append(formatted_result)
        
        # Format failed results
        failed_results = []
        if "failed_results" in response and response["failed_results"]:
            for failed in response["failed_results"]:
                failed_results.append(f"- {failed.get('url', 'Unknown URL')}: {failed.get('error', 'Unknown error')}")
        
        formatted_response = f"""
# Tavily Content Extraction Results

## Successfully Extracted ({len(results)} URLs):

{"".join(results) if results else "No content successfully extracted."}

## Failed Extractions ({len(failed_results)} URLs):

{chr(10).join(failed_results) if failed_results else "No failed extractions."}

**Extraction completed.**
"""
        
        return [TextContent(type="text", text=formatted_response)]
        
    except Exception as e:
        logger.error(f"Content extraction error: {str(e)}")
        return [TextContent(type="text", text=f"Content extraction failed: {str(e)}")]

async def main():
    """Run the Tavily search MCP server."""
    logger.info("Starting Tavily Search MCP Server...")
    
    # Test connection
    try:
        test_response = tavily_client.qna_search("test")
        logger.info("Tavily API connection successful")
    except Exception as e:
        logger.warning(f"Tavily API test failed: {e}")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())