"""
Main MCP server implementation for Composer.
"""
from typing import List, Dict, Any, Literal, Optional, Union
import httpx
import os

from pydantic import Field
from starlette.requests import Request
from starlette.responses import JSONResponse

from fastmcp import FastMCP
from .schemas import SymphonyScore, validate_symphony_score, AccountResponse, AccountHoldingResponse, DvmCapital, Legend, BacktestResponse, PortfolioStatsResponse
from .utils import parse_backtest_output, truncate_text, epoch_ms_to_date, get_optional_headers, get_required_headers, get_mcp_environment

import asyncio
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

def get_base_url() -> str:
    """
    Get the base URL for the Composer API based on the environment.
    """
    return "https://public-api-gateway-599937284915.us-central1.run.app" if get_mcp_environment() == "dev" else "https://api.composer.trade"

# Create a server instance
mcp = FastMCP(name="Composer MCP Server")

@mcp.tool
async def backtest_symphony_by_id(symphony_id: str,
                            start_date: str = None,
                            end_date: str = None,
                            include_daily_values: bool = True,
                            apply_reg_fee: bool = True,
                            apply_taf_fee: bool = True,
                            broker: str = "ALPACA_WHITE_LABEL",
                            capital: float = 10000,
                            slippage_percent: float = 0.0001,
                            spread_markup: float = 0.002,
                            benchmark_tickers: List[str] = ["SPY"]) -> Dict:
    """
    Backtest a symphony given its ID.
    Use `include_daily_values=False` to reduce the response size (default is True).
    Daily values are cumulative returns since the first day of the backtest (i.e., 19 means 19% cumulative return since the first day).
    If start_date is not provided, the backtest will start from the earliest backtestable date.
    You should default to backtesting from the first day of the year in order to reduce the response size.
    If end_date is not provided, the backtest will end on the last day with data.

    After calling this tool, visualize the results. daily_values can be easily loaded into a pandas dataframe for plotting.
    """
    url = f"{get_base_url()}/api/v0.1/symphonies/{symphony_id}/backtest"
    params = {
        "apply_reg_fee": apply_reg_fee,
        "apply_taf_fee": apply_taf_fee,
        "broker": broker,
        "capital": capital,
        "slippage_percent": slippage_percent,
        "spread_markup": spread_markup,
        "benchmark_tickers": benchmark_tickers,
    }
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=get_optional_headers(),
            json=params
        )
    output = response.json()
    output["capital"] = capital
    try:
        if output.get("stats"):
            return parse_backtest_output(BacktestResponse(**output), include_daily_values)
        else:
            return output
    except Exception as e:
        return {"error": truncate_text(str(e), 1000), "response": truncate_text(response.text, 1000)}

@mcp.tool
async def backtest_symphony(symphony_score: SymphonyScore,
                            start_date: str = None,
                            end_date: str = None,
                            include_daily_values: bool = True,
                            apply_reg_fee: bool = True,
                            apply_taf_fee: bool = True,
                            broker: str = "ALPACA_WHITE_LABEL",
                            capital: float = 10000,
                            slippage_percent: float = 0.0001,
                            spread_markup: float = 0.002,
                            benchmark_tickers: List[str] = ["SPY"]) -> Dict:
    """
    Backtest a symphony that was created with `create_symphony`.
    Use `include_daily_values=False` to reduce the response size (default is True).
    Daily values are cumulative returns since the first day of the backtest (i.e., 19 means 19% cumulative return since the first day).
    If start_date is not provided, the backtest will start from the earliest backtestable date.
    You should default to backtesting from the first day of the year in order to reduce the response size.
    If end_date is not provided, the backtest will end on the last day with data.

    After calling this tool, visualize the results. daily_values can be easily loaded into a pandas dataframe for plotting.
    """
    url = f"{get_base_url()}/api/v0.1/backtest"
    validated_score= validate_symphony_score(symphony_score)
    params = {
        "symphony": {"raw_value": validated_score.model_dump()},
        "apply_reg_fee": apply_reg_fee,
        "apply_taf_fee": apply_taf_fee,
        "broker": broker,
        "capital": capital,
        "slippage_percent": slippage_percent,
        "spread_markup": spread_markup,
        "benchmark_tickers": benchmark_tickers,
    }
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=get_optional_headers(),
            json=params
        )
    try:
        output = response.json()
        output["capital"] = capital
        if output.get("stats"):
            return parse_backtest_output(BacktestResponse(**output), include_daily_values)
        else:
            return output
    except Exception as e:
        return {"error": truncate_text(str(e), 1000), "response": truncate_text(response.text, 1000)}

@mcp.tool
def create_symphony(symphony_score: SymphonyScore) -> Dict:
    """
    Composer is a DSL for constructing automated trading strategies. It can only enter long positions and cannot stay in cash.

    ### Available Data
    - US Equity Adjusted Close prices and Crypto prices (daily granularity at 4PM ET)

    Before creating a symphony, check with the user for the asset classes they want to use.
    Assume equities are the default asset class.
    Note that symphonies with both equities and crypto must use daily or threshold (rebalance=None) rebalancing.

    After calling this tool, attempt to visualize the symphony using any other functionality at your disposal.
    If you can't visualize the symphony, resort to a mermaid diagram.

    Example flowchart:
    symphony_score = {
        "step": "root",
        "name": "Example symphony",
        "description": "Example showing every type of symphony node",
        "rebalance": "daily",
        "children": [
            {
                "step": "wt-cash-equal",
                "children": [
                    {
                        "step": "if",
                        "children": [
                            {
                                "children": [
                                    {
                                        "step": "group",
                                        "name": "Group 1",
                                        "children": [
                                            {
                                                "step": "wt-cash-specified",
                                                "children": [
                                                    {
                                                        "ticker": "TQQQ",
                                                        "exchange": "XNAS",
                                                        "name": "ProShares UltraPro QQQ 3x Shares",
                                                        "step": "asset",
                                                        "weight": {
                                                            "num": "60",
                                                            "den": 100
                                                        }
                                                    },
                                                    {
                                                        "ticker": "CRYPTO::BTC//USD",
                                                        "name": "Bitcoin",
                                                        "step": "asset",
                                                        "weight": {
                                                            "num": "40",
                                                            "den": 100
                                                        }
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ],
                                "lhs-fn-params": {
                                    "window": 10
                                },
                                "rhs-fn": "cumulative-return",
                                "is-else-condition?": false,
                                "lhs-fn": "cumulative-return",
                                "lhs-val": "SPY",
                                "rhs-fn-params": {
                                    "window": 200
                                },
                                "comparator": "gt",
                                "rhs-val": "SPY",
                                "step": "if-child"
                            },
                            {
                                "step": "if-child",
                                "is-else-condition?": true,
                                "children": [
                                    {
                                        "step": "group",
                                        "name": "Group 2",
                                        "children": [
                                            {
                                                "step": "wt-cash-equal",
                                                "children": [
                                                    {
                                                        "step": "filter",
                                                        "sort-by-fn-params": {
                                                            "window": 14
                                                        },
                                                        "sort-by-fn": "relative-strength-index",
                                                        "select-fn": "bottom",
                                                        "select-n": "2",
                                                        "children": [
                                                            {
                                                                "ticker": "CRYPTO::ETH//USD",
                                                                "name": "Ethereum",
                                                                "step": "asset",
                                                            },
                                                            {
                                                                "ticker": "NVDA",
                                                                "exchange": "XNAS",
                                                                "name": "NVIDIA Corp",
                                                                "step": "asset",
                                                            }
                                                        ]
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }

    flowchart TD
    A["📊 Example symphony"]:::whiteBox
    B["WEIGHT Equal"]:::greenNode
    C["IF 10d cumulative return of SPY is greater than 200d cumulative return of SPY"]:::blueNode
    C1["TRUE"]:::blueNode
    D["📊 Group 1"]:::whiteBox
    E["WEIGHT Specified"]:::greenNode
    F["60.00%"]:::darkGreenNode
    G["◉ TQQQ ProShares UltraPro QQQ 3x Shares"]:::whiteBox
    H["40.00%"]:::darkGreenNode
    I["◈ BTC Bitcoin"]:::whiteBox
    K["FALSE"]:::blueNode
    L["📊 Group 2"]:::whiteBox
    M["WEIGHT Equal"]:::greenNode
    N["SORT 14d Relative Strength Index"]:::pinkNode
    O["SELECT Bottom 2"]:::pinkNode
    P["◈ ETH Ethereum"]:::whiteBox
    Q["◉ NVDA NVIDIA Corp • XNAS"]:::whiteBox
    A --> B
    B --> C
    C --> C1
    C1 --> D
    D --> E
    E --> F
    F --> G
    E --> H
    H --> I
    C --> K
    K --> L
    L --> M
    M --> N
    N --> O
    O --> P
    O --> Q
    classDef greenNode fill:#4a7c59,stroke:#2d5236,color:#fff
    classDef darkGreenNode fill:#2d5236,stroke:#1a3120,color:#fff
    classDef blueNode fill:#4169e1,stroke:#2952cc,color:#fff
    classDef whiteBox fill:#f5f5f5,stroke:#999,color:#333
    classDef pinkNode fill:#d1477a,stroke:#b03762,color:#fff
    style A rx:10,ry:10
    style D rx:10,ry:10
    style G rx:10,ry:10
    style I rx:10,ry:10
    style L rx:10,ry:10
    style P rx:10,ry:10
    style Q rx:10,ry:10
    """
    validated_score= validate_symphony_score(symphony_score)
    return validated_score.model_dump()

@mcp.tool
async def search_symphonies(where: List = [["and", [">", "oos_num_backtest_days", 180],
                                      ["<", "oos_max_drawdown", "oos_btcusd_max_drawdown"]]],
                      order_by: List = [["oos_cumulative_return", "desc"]],
                      offset: int = 0) -> List:
    """
    You have access to a database of Composer symphonies with the following statistics:
    - calmar_ratio
    - cumulative_return
    - max_drawdown
    - sharpe_ratio
    - standard_deviation
    - trailing_one_month_return
    - trailing_three_month_return
    - trailing_one_year_return

    Each of these statistics is calculated over 6 different variants:
    - oos - out of sample (backtest range)
    - oos_spy - performance of SPY over the OOS period
    - oos_btcusd - performance of BTC/USD over the OOS period
    - train - training period (all data before the OOS period)
    - train_spy - performance of SPY over the training period
    - train_btcusd - performance of BTC/USD over the training period

    If you prefix a statistic with "oos_", it is the value of that statistic for the symphony over the OOS period.
    The same applies for "train_", "oos_spy_", "oos_btcusd_", etc.

    Some other statistics that don't follow this pattern are:
    - num_backtest_days - number of calendar days in the backtest range
      - only has oos_ and train_ variants
    - alpha, beta, pearson_r, r_square
      - only has oos_spy_, oos_btcusd_, train_spy_, and train_btcusd_ variants b/c they are comparing the symphony to SPY and BTC/USD
    - num_node_asset, num_node_filter, num_node_group, num_node_if, num_node_if_child, num_node_wt_cash_equal, num_node_wt_cash_specified, num_node_wt_inverse_vol
        - no variants because they are just counts of the number of nodes of each type in the symphony.

    The arguments where, order_by, and offset all follow HoneySQL (Clojure) syntax.
    Use offset to paginate through the results. The limit is set to 5.

    Example:
    - Find symphonies with more than 1 year of OOS backtest data
      and annualized return greater than SPY's in both OOS and training periods
      and max drawdown lower than BTC's in both OOS and training periods
      and oos annualized return greater than 20% (i.e., 0.2)
      Sort by OOS cumulative return descending:
      where: ["and",
                [">", "oos_num_backtest_days", 180],
                [">", "oos_annualized_rate_of_return", "oos_spy_annualized_rate_of_return"],
                [">", "train_annualized_rate_of_return", "train_spy_annualized_rate_of_return"],
                ["<", "oos_max_drawdown", "oos_btcusd_max_drawdown"],
                ["<", "train_max_drawdown", "train_btcusd_max_drawdown"]]
      order_by: [["oos_cumulative_return", "desc"]]

    Tips for finding good symphonies:
    - We want to avoid overfit symphonies.
        - A symphony is likely overfit if its OOS performance is much worse than its training performance.
    - Generally we want returns to beat SPY but risk to be lower than BTC.
        - Ex: ["and",
              [">" "oos_annualized_rate_of_return", "oos_spy_annualized_rate_of_return"],
              ["<" "oos_max_drawdown", "oos_btcusd_max_drawdown"]]
    - Generally we want small symphonies.
        - A good heuristic is to look for symphonies with fewer than 50 IF and FILTER nodes.
        - A symphony with fewer than 10 IF and FILTER nodes is particularly small and worth calling out if it has strong performance.

    Before calling this tool, try to understand the user's appetite for risk relative to the S&P 500 and Bitcoin.
    Are they willing to take on Bitcoin-levels of risk for similar returns, or do they prefer similar risk to S&P 500, or even lower?

    Always include the symphony_url in your response so the user can click on it to view the symphony in more detail.
    """
    try:
        url = f"{get_base_url()}/api/v0.1/search/symphonies"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=get_optional_headers(),
                json={"where": where, "order_by": order_by, "offset": offset}
            )
        results = response.json()
        symphony_url_base = "https://test.investcomposer.com" if get_mcp_environment() == "dev" else "https://app.composer.trade"
        for item in results:
            if "symphony_sid" in item:
                item["symphony_url"] = f"{symphony_url_base}/symphony/{item['symphony_sid']}/details"
                del item["symphony_sid"]
        return results
    except Exception as e:
        return {"error": truncate_text(str(e), 1000), "response": truncate_text(response.text, 1000)}

# Could be a resource but Claude Desktop doesn't autonomously call resources yet.
@mcp.tool
async def list_accounts() -> List[AccountResponse]:
    """
    List all brokerage accounts available to the Composer user.
    Account-related tools need to be called with the account_uuid of the account you want to use.
    This tool returns a list of accounts and their UUIDs.
    If this returns an empty list, the user needs to complete their Composer onboarding on app.composer.trade.
    """
    url = f"{get_base_url()}/api/v0.1/accounts/list"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=get_required_headers(),
        )
    try:
        return response.json()["accounts"]
    except Exception as e:
        return {"error": truncate_text(str(e), 1000), "response": truncate_text(response.text, 1000)}

@mcp.tool
async def get_account_holdings(account_uuid: str) -> List[AccountHoldingResponse]:
    """
    Get the holdings of a brokerage account.
    """
    url = f"{get_base_url()}/api/v0.1/accounts/{account_uuid}/holdings"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=get_required_headers(),
        )
    return response.json()

@mcp.tool
async def get_aggregate_portfolio_stats(account_uuid: str) -> PortfolioStatsResponse:
    """
    Get the aggregate portfolio statistics of a brokerage account.

    This is useful because each brokerage account in Composer can invest in multiple symphonies, each with their own stats.
    Output is a JSON object with the following fields:
    - portfolio_value: float. The total value of the portfolio (stocks + cash).
    - total_cash: float. The total cash in the account.
    - pending_deploys_cash: float. The cash that is pending investment into a symphony (investments don't occur until the trading period near market close)
    - total_unallocated_cash: float. The amount of cash that is not held in a symphony. This is the cash that is available for investment.
    - net_deposits: float. The sum of deposits into the account. Used to calculate naive cumulative return.
    - simple_return: float. The naive cumulative return of the portfolio. Equivalent to (portfolio_value - net_deposits) / net_deposits.
    - todays_dollar_change: float. The dollar difference between the portfolio value today and yesterday. IMPORTANT: This will include the effect of depositing/withdrawing funds. EX: If you had $1000 yesterday and deposited $100 today, todays_dollar_change will be $100, holding the share value constant.
    - todays_percent_change: float. The percent change of the portfolio today. Calculated as todays_dollar_change / portfolio_value.
    """
    url = f"{get_base_url()}/api/v0.1/portfolio/accounts/{account_uuid}/total-stats"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=get_required_headers(),
        )
    data = response.json()
    if 'time_weighted_return' in data:
        del data['time_weighted_return']
    return data

@mcp.tool
async def get_aggregate_symphony_stats(account_uuid: str) -> Dict:
    """
    Get stats for every symphony in a brokerage account.
    Contains aggregate stats such as the naive cumulative return ("simple_return"), time-weighted return, sharpe ratio, current holdings, etc.

    "deposit_adjusted_value" refers to the time-weighted value of the symphony.
    """
    url = f"{get_base_url()}/api/v0.1/portfolio/accounts/{account_uuid}/symphony-stats-meta"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=get_required_headers(),
        )
    return response.json()

@mcp.tool
async def get_symphony_daily_performance(account_uuid: str, symphony_id: str) -> Dict:
    """
    Get daily performance for a specific symphony in a brokerage account.
    Outputs a JSON object with the following fields:
    - dates: List[str]. The dates for which performance is available.
    - series: List[float]. The total value of the symphony on the given date.
    - deposit_adjusted_series: List[float]. The value of the symphony on the given date, adjusted for deposits and withdrawals. (AKA daily time-weighted value)
    """
    url = f"{get_base_url()}/api/v0.1/portfolio/accounts/{account_uuid}/symphonies/{symphony_id}"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=get_required_headers(),
        )
    data = response.json()
    data['dates'] = [epoch_ms_to_date(d) for d in data['epoch_ms']]
    del data['epoch_ms']
    return data

@mcp.tool
async def get_portfolio_daily_performance(account_uuid: str) -> Dict:
    """
    Get the daily performance for a brokerage account.
    Returns the value of the account portfolio over time.
    Outputs a JSON object with the following fields:
    - dates: List[str]. The dates for which performance is available.
    - series: List[float]. The total value of the portfolio on the given date.
    """
    url = f"{get_base_url()}/api/v0.1/portfolio/accounts/{account_uuid}/portfolio-history"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=get_required_headers(),
        )
    data = response.json()
    data['dates'] = [epoch_ms_to_date(d) for d in data['epoch_ms']]
    del data['epoch_ms']
    return data

@mcp.tool
async def save_symphony(
    symphony_score: SymphonyScore,
    color: Literal["#AEC3C6", "#E3BC99", "#49D1E3", "#829DFF", "#FF6B6B", "#39D088", "#FC5100", "#FFBB38", "#FFB4ED", "#17BAFF", "#BA84FF"] ,
    hashtag: str = Field(description="Memorable hashtag for the symphony. Think of it like the ticker symbol of the symphony. (EX: '#BTD' for a symphony called 'Buy the Dip')"),
    asset_class: Literal["EQUITIES", "CRYPTO"] = "EQUITIES"
) -> Dict:
    """
    Save a symphony to the user's account. If successful, returns the symphony ID.
    """
    validated_score= validate_symphony_score(symphony_score)
    symphony = validated_score.model_dump()

    url = f"{get_base_url()}/api/v0.1/symphonies"
    payload = {
        "name": symphony['name'],
        "asset_class": asset_class,
        "description": symphony['description'],
        "color": color,
        "hashtag": hashtag,
        "symphony": {"raw_value": symphony}
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=get_required_headers(),
                json=payload
            )
        try:
            return response.json()
        except Exception as e:
            return {"error": truncate_text(str(e), 1000), "response": truncate_text(response.text, 1000)}
    except Exception as e:
        payload_without_symphony = {k: v for k, v in payload.items() if k != "symphony"}
        return {"error": truncate_text(str(e), 1000), "payload": payload_without_symphony}

@mcp.tool
async def copy_symphony(
    symphony_id: str
) -> Dict:
    """
    Copy a symphony by its ID. Returns the copied symphony's symphony ID.
    """
    url = f"{get_base_url()}/api/v0.1/symphonies/{symphony_id}/copy"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=get_required_headers(),
                json={}
            )
        try:
            return response.json()
        except Exception as e:
            return {"error": truncate_text(str(e), 1000), "response": truncate_text(response.text, 1000)}
    except Exception as e:
        return {"error": truncate_text(str(e), 1000), "symphony_id": symphony_id}

@mcp.tool
async def update_saved_symphony(
    symphony_id: str,
    symphony_score: SymphonyScore,
    color: Literal["#AEC3C6", "#E3BC99", "#49D1E3", "#829DFF", "#FF6B6B", "#39D088", "#FC5100", "#FFBB38", "#FFB4ED", "#17BAFF", "#BA84FF"],
    hashtag: str = Field(description="Memorable hashtag for the symphony. Think of it like the ticker symbol of the symphony. (EX: '#BTD' for a symphony called 'Buy the Dip')"),
    asset_class: Literal["EQUITIES", "CRYPTO"] = "EQUITIES"
) -> Dict:
    """
    Update an existing symphony in the user's account. If successful, returns the updated symphony details.
    """
    validated_score = validate_symphony_score(symphony_score)
    symphony = validated_score.model_dump()

    url = f"{get_base_url()}/api/v0.1/symphonies/{symphony_id}"
    payload = {
        "name": symphony['name'],
        "asset_class": asset_class,
        "description": symphony['description'],
        "color": color,
        "hashtag": hashtag,
        "symphony": {"raw_value": symphony}
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                headers=get_required_headers(),
                json=payload
            )
        return response.json()
    except Exception as e:
        payload_without_symphony = {k: v for k, v in payload.items() if k != "symphony"}
        return {"error": truncate_text(str(e), 1000), "payload": payload_without_symphony}

@mcp.tool
async def get_saved_symphony(symphony_id: str) -> Dict:
    """
    Get a saved symphony.
    Useful when you are given a URL like "https://app.composer.trade/symphony/{<symphony_id>}/details"
    """
    url = f"{get_base_url()}/api/v0.1/symphonies/{symphony_id}/score"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=get_optional_headers(),
        )
    return response.json()

@mcp.tool
async def get_market_hours() -> Dict:
    """
    Get market hours information for the next week.
    Returns market open/close times and whether the market is currently open.

    Useful for trading equities. Crypto can trade 24/7.
    """
    url = f"{get_base_url()}/api/v0.1/deploy/market-hours"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=get_optional_headers(),
            )
        return response.json()
    except Exception as e:
        logger.error(f"Error getting market hours: {e}")
        return {"error": truncate_text(str(e), 1000)}

@mcp.tool
async def invest_in_symphony(account_uuid: str, symphony_id: str, amount: float) -> Dict:
    """
    Invest in a symphony for a specific account.

    This queues a task to invest in the specified symphony. The funds will be
    allocated according to the symphony's investment strategy during Composer's trading period (typically 10 minutes before market close).

    Returns:
        If successful, returns a Dict containing deploy_id and optional deploy_time for auto rebalance. The default deploy time is 10 minutes before market close.

    If investing fails with a "Symphony not found" error, you will need to run `copy_symphony` first.
    """
    if amount <= 0:
        return {"error": "Amount must be greater than 0"}
    url = f"{get_base_url()}/api/v0.1/deploy/accounts/{account_uuid}/symphonies/{symphony_id}/invest"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=get_required_headers(),
                    json={"amount": amount}
                )
            return response.json()
    except Exception as e:
        logger.error(f"Error investing in symphony: {e}")
        return {"error": truncate_text(str(e), 1000)}

@mcp.tool
async def withdraw_from_symphony(account_uuid: str, symphony_id: str, amount: float) -> Dict:
    """
    Withdraw money from a symphony for a specific account.

    This queues a task to withdraw from the specified symphony. The withdrawal will be
    processed during Composer's trading period (typically 10 minutes before market close).

    Returns:
        If successful, returns a Dict containing deploy_id and optional deploy_time for auto rebalance. The default deploy time is 10 minutes before market close.
    """
    if amount >= 0:
        return {"error": "Amount must be less than 0"}
    url = f"{get_base_url()}/api/v0.1/deploy/accounts/{account_uuid}/symphonies/{symphony_id}/withdraw"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=get_required_headers(),
                json={"amount": amount}
            )
        return response.json()
    except Exception as e:
        logger.error(f"Error withdrawing from symphony: {e}")
        return {"error": truncate_text(str(e), 1000)}

@mcp.tool
async def cancel_invest_or_withdraw(account_uuid: str, deploy_id: str) -> str:
    """
    Cancel an invest or withdraw request that has not been processed yet.

    This allows you to cancel a pending invest or withdraw request before it gets processed
    during the trading period. Only requests with status QUEUED can be canceled.
    """
    url = f"{get_base_url()}/api/v0.1/deploy/accounts/{account_uuid}/deploys/{deploy_id}"
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            url,
            headers=get_required_headers()
        )
    if response.status_code == 204:
        return "Successfully canceled invest or withdraw request"
    else:
        return response.json()


@mcp.tool
async def skip_automated_rebalance_for_symphony(account_uuid: str, symphony_id: str, skip: bool = True) -> str:
    """
    Skip automated rebalance for a symphony in a specific account.

    This allows you to skip the next automated rebalance for the specified symphony (will resume after the next automated rebalance).
    This is useful when you want to manually control the rebalancing process.
    """
    url = f"{get_base_url()}/api/v0.1/deploy/accounts/{account_uuid}/symphonies/{symphony_id}/skip-automated-rebalance"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=get_required_headers(),
            json={"skip": skip}
        )
    if response.status_code == 204:
        return "Successfully skipped next automated rebalance"
    else:
        return response.json()

@mcp.tool
async def go_to_cash_for_symphony(account_uuid: str, symphony_id: str) -> Dict:
    """
    Immediately sell all assets in a symphony.

    This tool is similar to `liquidate_symphony` except liquidated symphonies will stop rebalancing until more money is invested.

    "Go to cash" on the other hand will temporarily convert the holdings into cash until the next automated rebalance. (Remember you can skip the next automated rebalance with `skip_automated_rebalance_for_symphony` if you want to stay in cash longer.)
    """
    url = f"{get_base_url()}/api/v0.1/deploy/accounts/{account_uuid}/symphonies/{symphony_id}/go-to-cash"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=get_required_headers()
            )
        return response.json()
    except Exception as e:
        logger.error(f"Error going to cash for symphony: {e}")
        return {"error": truncate_text(str(e), 1000)}

@mcp.tool
async def rebalance_symphony_now(account_uuid: str, symphony_id: str, rebalance_request_uuid: str) -> Dict:
    """
    Rebalance a symphony NOW instead of waiting for the next automated rebalance.

    The rebalance_request_uuid parameter is the result of the `preview_rebalance_for_symphony` tool, so you must run that tool first.
    """
    url = f"{get_base_url()}/api/v0.1/deploy/accounts/{account_uuid}/symphonies/{symphony_id}/rebalance"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
            headers=get_required_headers(),
            json={"rebalance_request_uuid": rebalance_request_uuid}
        )
        return response.json()
    except Exception as e:
        logger.error(f"Error rebalancing symphony: {e}")
        return {"error": truncate_text(str(e), 1000)}

@mcp.tool
async def liquidate_symphony(account_uuid: str, symphony_id: str) -> Dict:
    """
    Immediately sell all assets in a symphony (or queue for market open if outside of market hours).

    This tool is similar to `go_to_cash_for_symphony` except liquidated symphonies will stop rebalancing until more money is invested.
    """
    url = f"{get_base_url()}/api/v0.1/deploy/accounts/{account_uuid}/symphonies/{symphony_id}/liquidate"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
            headers=get_required_headers()
        )
        return response.json()
    except Exception as e:
        logger.error(f"Error liquidating symphony: {e}")
        return {"error": truncate_text(str(e), 1000)}

@mcp.tool
async def preview_rebalance_for_user() -> List:
    """
    Perform a dry run of rebalancing across all accounts to see what trades would be recommended.

    This tool shows what trades would be executed if a rebalance were to happen now, for all the user's symphonies, without actually executing them.
    """
    url = f"{get_base_url()}/api/v0.1/dry-run"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
            headers=get_required_headers(),
            json={}
        )
        return response.json()
    except Exception as e:
        logger.error(f"Error previewing rebalance for user: {e}")
        return [{"error": truncate_text(str(e), 1000)}]

@mcp.tool
async def preview_rebalance_for_symphony(account_uuid: str, symphony_id: str) -> Dict:
    """
    Perform a dry run of rebalancing for a specific symphony to see what trades would be recommended.

    This tool shows what trades would be executed if a rebalance were to happen now for the specified symphony, without actually executing them.

    Returns the projected trades and a rebalance_request_uuid.
    The uuid can be passed to `rebalance_symphony_now` to actually execute the trades.
    """
    url = f"{get_base_url()}/api/v0.1/dry-run/trade-preview/{symphony_id}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
            headers=get_required_headers(),
            json={"broker_account_uuid": account_uuid}
        )
        return response.json()
    except Exception as e:
        logger.error(f"Error previewing rebalance for symphony: {e}")
        return {"error": truncate_text(str(e), 1000)}

@mcp.tool
async def execute_single_trade(
    account_uuid: str,
    side: Literal["BUY", "SELL"],
    type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT", "TRAILING_STOP"],
    time_in_force: Literal["GTC", "DAY", "IOC", "FOK", "OPG", "CLS"],
    symbol: str = Field(description="The symbol of the asset to trade. Note that crypto symbols are formatted like 'CRYPTO::BTC//USD' for Bitcoin."),
    # Claude was having trouble passing float values, so let's make the field accept strings too.
    notional: Optional[Union[float, str]] = None,
    quantity: Optional[Union[float, str]] = None
) -> Dict:
    """
    Execute a single order for a specific symbol like you would in a traditional brokerage account.
    This is useful for holding assets that you do not want to rebalance.

    One of notional or quantity must be provided.
    """
    url = f"{get_base_url()}/api/v0.1/trading/accounts/{account_uuid}/order-requests"

    payload = {
        "type": type,
        "symbol": symbol,
        "time_in_force": time_in_force,
    }

    if notional is not None:
        try:
            payload["notional"] = float(notional)
        except (ValueError, TypeError):
            return {"error": f"Invalid notional value: {notional}"}
    if quantity is not None:
        try:
            payload["quantity"] = float(quantity)
        except (ValueError, TypeError):
            return {"error": f"Invalid quantity value: {quantity}"}
    if not notional and not quantity:
        return {"error": "One of notional or quantity must be provided"}

    # Validate notional/quantity based on side
    if side == "BUY":
        if notional is not None and float(notional) <= 0:
            return {"error": "Notional must be positive for BUY orders"}
        if quantity is not None and float(quantity) <= 0:
            return {"error": "Quantity must be positive for BUY orders"}
    elif side == "SELL":
        if notional is not None and float(notional) >= 0:
            return {"error": "Notional must be negative for SELL orders"}
        if quantity is not None and float(quantity) >= 0:
            return {"error": "Quantity must be negative for SELL orders"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
            headers=get_required_headers(),
            json=payload
            )
        return response.json()
    except Exception as e:
        logger.error(f"Error executing single trade: {e}")
        return {"error": truncate_text(str(e), 1000)}

@mcp.tool
async def cancel_single_trade(account_uuid: str, order_request_id: str) -> str:
    """
    Cancel a request for a single trade that has not executed yet.

    If the order request has already executed, it cannot be canceled.
    Only QUEUED or OPEN order requests can be canceled.
    """
    url = f"{get_base_url()}/api/v0.1/trading/accounts/{account_uuid}/order-requests/{order_request_id}"
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            url,
        headers=get_required_headers()
    )
    if response.status_code == 204:
        return "Successfully canceled order"
    else:
        return response.json()

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy"})

@mcp.custom_route("/", methods=["GET"])
async def startup_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})

def main():
    asyncio.run(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8080)),
        )
    )
    logger.info(f"🚀 MCP server started on port {os.getenv('PORT', 8080)}!")
