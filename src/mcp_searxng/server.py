"""云智AI本地搜 - MCP Server
为 Claude Code 等 AI 助手提供本地联网搜索能力 (SSE模式)

技术架构：
- SearXNG: 搜索引擎聚合器 (默认 localhost:18888)
- MCP Server: 协议适配层 (默认 localhost:19000)

开源地址：
- GitHub: https://github.com/TheDigestif/YZ_AI_LocalSearch
- Gitee: https://gitee.com/yungantech/YZ_AI_LocalSearch

Powered by 云感数字科技 (https://www.yungantech.com)
"""

import os
import sys
import json
import requests

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import Response
import uvicorn

# SearXNG 服务地址（从环境变量读取，支持自定义端口）
SEARXNG_PORT = int(os.environ.get("SEARXNG_PORT", 18888))
SEARXNG_URL = os.environ.get("SEARXNG_URL", f"http://localhost:{SEARXNG_PORT}")
MCP_PORT = int(os.environ.get("MCP_PORT", 19000))

# 创建MCP服务器实例
server = Server("yz-local-search")
sse = SseServerTransport("/messages/")


def search_web(query: str, count: int = 5, engines: str = None) -> dict:
    """调用SearXNG API进行网页搜索"""
    try:
        params = {"q": query, "format": "json", "language": "zh-CN"}
        if engines:
            params["engines"] = engines

        response = requests.get(f"{SEARXNG_URL}/search", params=params, timeout=15)
        data = response.json()

        results = []
        for item in data.get("results", [])[:count]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", "")[:500] if item.get("content") else "",
                "engine": item.get("engine", "")
            })

        return {
            "query": query,
            "total": len(results),
            "results": results,
            "engines_used": engines if engines else "all enabled engines",
            "failed_engines": [e[0] for e in data.get("unresponsive_engines", [])]
        }
    except Exception as e:
        return {"query": query, "total": 0, "results": [], "failed_engines": [str(e)]}


def search_images(query: str, count: int = 5) -> dict:
    """搜索图片"""
    try:
        response = requests.get(
            f"{SEARXNG_URL}/search",
            params={"q": query, "format": "json", "categories": "images", "language": "zh-CN"},
            timeout=30
        )
        data = response.json()

        results = []
        for item in data.get("results", [])[:count]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "thumbnail": item.get("thumbnail", ""),
                "source": item.get("img_src", "")
            })

        return {"query": query, "total": len(results), "results": results}
    except Exception as e:
        return {"query": query, "total": 0, "results": [], "error": str(e)}


@server.list_tools()
async def list_tools():
    """列出可用的MCP工具"""
    return [
        Tool(
            name="web_search",
            description="搜索互联网获取信息。返回搜索结果的标题、URL和摘要。支持 Google、Bing、Baidu、Sogou 等多引擎。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "count": {"type": "integer", "description": "返回数量", "default": 5},
                    "engines": {"type": "string", "description": "指定引擎（可选）: google, bing, baidu, sogou"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="image_search",
            description="搜索图片。返回图片的标题、URL和缩略图。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "图片搜索关键词"},
                    "count": {"type": "integer", "description": "返回数量", "default": 5}
                },
                "required": ["query"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """执行工具调用"""
    try:
        if name == "web_search":
            result = search_web(arguments["query"], arguments.get("count", 5), arguments.get("engines"))
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        elif name == "image_search":
            result = search_images(arguments["query"], arguments.get("count", 5))
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_sse(request):
    """处理SSE连接"""
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())
    return Response()


def main():
    """启动 MCP Server"""
    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
        ]
    )

    print(f"YZ Local Search MCP Server 启动中...")
    print(f"  SearXNG 地址: {SEARXNG_URL}")
    print(f"  MCP 端口: {MCP_PORT}")
    print(f"  SSE 端点: http://localhost:{MCP_PORT}/sse")
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
