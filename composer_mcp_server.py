"""
Main entry point for the composer-mcp-server application.
"""
from typing import List, Dict
from fastmcp import FastMCP
from fastmcp.server.openapi import (
    HTTPRoute, 
    OpenAPITool, 
    OpenAPIResource, 
    OpenAPIResourceTemplate,
)
import httpx
import os
from datetime import datetime
import json

# Internal
from src.schemas.symphony_score_schema import SymphonyScore, validate_symphony_score
from src.schemas.asset_classes_schema import AssetClasses
from src.schemas.api import AccountResponse, AccountHoldingResponse

BASE_URL = "https://public-api-gateway-599937284915.us-central1.run.app"
# BASE_URL = "https://api.composer.trade"
client = httpx.AsyncClient(
    base_url=BASE_URL,
    headers={
        "x-api-key-id": os.getenv("COMPOSER_API_KEY"),
        "Authorization": f"Bearer {os.getenv('COMPOSER_SECRET_KEY')}"
    }
)
try:
    openapi_spec = httpx.get("https://converter.swagger.io/api/convert?url=https%3A%2F%2Fapi.composer.trade%2Fdocs%2Fswagger.json").json()
except:
    with open("src/schemas/openapi.json", "r") as f:
        openapi_spec = json.loads(f.read())

def customize_components(
    route: HTTPRoute, 
    component: OpenAPITool | OpenAPIResource | OpenAPIResourceTemplate,
) -> None:
    """
    Modify the default implementation of OpenAPI integration with FastMCP.
    (Usually by modifying the names, descriptions, and arguements to make them more LLM-friendly)
    """    
    if isinstance(component, OpenAPITool):
        if route.path == "/api/v0.1/accounts/list":
            component.name = "list_accounts"
            component.description = """
            List all brokerage accounts available to the Composer user.
            Account-related tools need to be called with the account_uuid of the account you want to use.
            This tool returns a list of accounts and their UUIDs.
            """
        elif route.path == "/api/v0.1/accounts/{account-id}/holdings":
            component.name = "get_account_holdings"
            component.description = "Get the holdings of a brokerage account."
        # elif route.path == "/api/v0.1/symphonies/{symphony-id}/backtest":
        elif route.path == "/api/v0.1/backtest":
            component.name = "backtest_symphony"
            component.description = """
            Backtest a symphony that was created with `create_symphony`.
            """
            component.parameters.append(
                {
                    "name": "symphony_score",
                    "type": "object",
                    "description": "The symphony to backtest.",
                }
            )


# Create a server instance
mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    name="Composer MCP Server",
    timeout=30.0,
    mcp_component_fn=customize_components
)


# TODO: Use Tool Transformation to adapt the OpenAPI spec to the MCP server.

def parse_stats(stats: Dict) -> Dict:
    """
    Parse the stats of a symphony backtest.
    """
    parsed_stats = {
        "annualized_rate_of_return": f"{round(stats.get('annualized_rate_of_return', 0) * 100, 2)}%",
        "benchmarks": {
            benchmark: parse_stats(benchmark_stats) for benchmark, benchmark_stats in stats.get("benchmarks", {}).items()
        },
        "calmar_ratio": round(stats.get("calmar_ratio", 0), 4),
        "sharpe_ratio": round(stats.get("sharpe_ratio", 0), 4),
        "cumulative_return": f"{round(stats.get('cumulative_return', 0) * 100, 2)}%",
        "trailing_one_year_return": f"{round(stats.get('trailing_one_year_return', 0) * 100, 2)}%",
        "trailing_one_month_return": f"{round(stats.get('trailing_one_month_return', 0) * 100, 2)}%",
        "trailing_three_month_return": f"{round(stats.get('trailing_three_month_return', 0) * 100, 2)}%",
        "max_drawdown": f"{round(stats.get('max_drawdown', 0) * 100, 2)}%",
        "standard_deviation": f"{round(stats.get('standard_deviation', 0) * 100, 2)}%",
    }
    # Process alpha and beta from percent section
    percent_stats = stats.get("percent", {})
    if percent_stats:
        parsed_stats["alpha"] = round(percent_stats.get("alpha", 0), 4)
        parsed_stats["beta"] = round(percent_stats.get("beta", 0), 4)
        parsed_stats["r_square"] = round(percent_stats.get("r_square", 0), 4)
        parsed_stats["pearson_r"] = round(percent_stats.get("pearson_r", 0), 4)
    return parsed_stats

def parse_backtest_output(output: Dict) -> Dict:
    """
    Parse the output of a symphony backtest.
    """
    return {
        "data_warnings": output.get("data_warnings"),
        "first_day": datetime.fromtimestamp(output.get("first_day") * 86400).strftime("%Y-%m-%d") if output.get("first_day") else None,
        "first_day_value": f"${output.get('capital', 0):,.2f}",
        "last_market_day": datetime.fromtimestamp(output.get("last_market_day") * 86400).strftime("%Y-%m-%d") if output.get("last_market_day") else None,
        "last_market_days_shares": {
            k: v for k, v in output.get("last_market_days_holdings", {}).items() 
            if k != "$USD" and v != 0.0
        },
        "last_market_days_value": f"${output.get('last_market_days_value', 0):,.2f}" if output.get('last_market_days_value') else None,
        "stats": parse_stats(output.get("stats", {}))
    }

@mcp.tool
def backtest_symphony_by_id(symphony_id: str,
                            apply_reg_fee: bool = True,
                            apply_taf_fee: bool = True,
                            broker: str = "ALPACA_WHITE_LABEL",
                            capital: float = 10000,
                            slippage_percent: float = 0.0001,
                            spread_markup: float = 0.002,
                            benchmark_tickers: List[str] = ["SPY"]) -> Dict:
    """
    Backtest a symphony given its ID.
    """
    url = f"{BASE_URL}/api/v0.1/symphonies/{symphony_id}/backtest"
    response = httpx.post(
        url,
        headers={
            "x-api-key-id": os.getenv("COMPOSER_API_KEY"),
            "Authorization": f"Bearer {os.getenv('COMPOSER_SECRET_KEY')}"
        },
        json={
            "apply_reg_fee": apply_reg_fee,
            "apply_taf_fee": apply_taf_fee,
            "broker": broker,
            "capital": capital,
            "slippage_percent": slippage_percent,
            "spread_markup": spread_markup,
            "benchmark_tickers": benchmark_tickers,
        }
    )
    output = response.json()
    try:
        return parse_backtest_output(output)
    except Exception as e:
        return response.text

@mcp.tool
def backtest_symphony(symphony_score: SymphonyScore,
                            apply_reg_fee: bool = True,
                            apply_taf_fee: bool = True,
                            broker: str = "ALPACA_WHITE_LABEL",
                            capital: float = 10000,
                            slippage_percent: float = 0.0001,
                            spread_markup: float = 0.002,
                            benchmark_tickers: List[str] = ["SPY"]) -> Dict:
    """
    Backtest a symphony that was created with `create_symphony`.
    """
    url = f"{BASE_URL}/api/v0.1/backtest"
    validated_score= validate_symphony_score(symphony_score)
    response = httpx.post(
        url,
        headers={
            "x-api-key-id": os.getenv("COMPOSER_API_KEY"),
            "Authorization": f"Bearer {os.getenv('COMPOSER_SECRET_KEY')}"
        },
        json={
            "symphony": {"raw_value": validated_score.model_dump()},
            "apply_reg_fee": apply_reg_fee,
            "apply_taf_fee": apply_taf_fee,
            "broker": broker,
            "capital": capital,
            "slippage_percent": slippage_percent,
            "spread_markup": spread_markup,
            "benchmark_tickers": benchmark_tickers,
        }
    )
    try:
        return parse_backtest_output(response.json())
    except Exception as e:
        return response.text

@mcp.tool
def create_symphony(symphony_score: SymphonyScore) -> SymphonyScore:
    """
    Composer is a DSL for constructing automated trading strategies. It can only enter long positions and cannot stay in cash.

    ### Available Data
    - US Equity Adjusted Close prices and Crypto prices (daily granularity at 4PM ET)

    Before creating a symphony, check with the user for the asset classes they want to use.
    Assume equities are the default asset class.
    Note that symphonies with both equities and crypto must use daily or threshold (rebalance=None) rebalancing.

    After calling this tool, attempt to visualize the symphony using any other functionality at your disposal.
    If you can't visualize the symphony, resort to a mermaid diagram.
    """
    validated_score= validate_symphony_score(symphony_score)
    return validated_score.model_dump_json()

# Could be a resource but Claude Desktop doesn't autonomously call resources yet.
@mcp.tool
def list_accounts() -> List[AccountResponse]:
    """
    List all brokerage accounts available to the Composer user.
    Account-related tools need to be called with the account_uuid of the account you want to use.
    This tool returns a list of accounts and their UUIDs.
    """
    url = f"{BASE_URL}/api/v0.1/accounts/list"
    response = httpx.get(
        url,
        headers={
            "x-api-key-id": os.getenv("COMPOSER_API_KEY"),
            "Authorization": f"Bearer {os.getenv('COMPOSER_SECRET_KEY')}"
        }
    )
    return response.json()["accounts"]

@mcp.tool
def get_account_holdings(account_uuid: str) -> List[AccountHoldingResponse]:
    """
    Get the holdings of a brokerage account.
    """
    url = f"{BASE_URL}/api/v0.1/accounts/{account_uuid}/holdings"
    response = httpx.get(
        url,
        headers={
            "x-api-key-id": os.getenv("COMPOSER_API_KEY"),
            "Authorization": f"Bearer {os.getenv('COMPOSER_SECRET_KEY')}"
        }
    )
    return response.json()

if __name__ == "__main__":
    mcp.run()
