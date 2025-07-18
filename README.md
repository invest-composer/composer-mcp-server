[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/invest-composer-composer-trade-mcp-badge.png)](https://mseep.ai/app/invest-composer-composer-trade-mcp)

![composermcpheader](https://github.com/user-attachments/assets/786b71f3-78a3-48f3-a4ee-f42f85a52949)

<div class="title-block" style="text-align: center;" align="center">

  [![Twitter](https://img.shields.io/badge/Twitter-@ComposerTrade-000000.svg?style=for-the-badge&logo=x&labelColor=000)](https://x.com/composertrade)
  [![PyPI](https://img.shields.io/badge/PyPI-composer--mcp-000000.svg?style=for-the-badge&logo=pypi&labelColor=000)](https://pypi.org/project/composer-trade-mcp)
  [![Reddit Community](https://img.shields.io/badge/reddit-r/ComposerTrade-000000.svg?style=for-the-badge&logo=reddit&labelColor=000)](https://www.reddit.com/r/ComposerTrade)

</div>

<p align="center">
  <strong>Vibe Trading is here!</strong>
</p>
<p align="center">
  Official <a href="https://www.composer.trade">Composer</a> Model Context Protocol (MCP) server that allows MCP-enabled LLMs like Claude to validate investment ideas via backtests and even trade multiple strategies (called "symphonies") in parallel to compare their live performance.
</p>

## Features
- **Create automated investing strategies**
  - Use indicators like Relative Strength Index (RSI), Moving Average (MA), and Exponential Moving Average (EMA) with a diverse range of equity and crypto offerings to build your ideal portfolio.
  - Don't just make one-off trades. Composer symphonies constantly monitor the market and rebalance accordingly.
  - Try asking Claude: "_Build me a crypto strategy with a maximum drawdown of 30% or less._"
- **Backtest your ideas**
  - Our Backtesting API provides a fast feedback loop for AI to iterate and validate its hypotheses.
  - Try asking Claude: "_Compare the strategy's performance against the S&P 500. Plot the results._"
- **Find a strategy tailored for you**
  - Provide your criteria to the AI and it will search through our database of 1000+ strategies to find one that suits your needs.
  - Try asking Claude: "_Find me a strategy with better risk-reward characteristics than Bitcoin._"
- **Monitor performance** (requires [API Key](https://github.com/invest-composer/composer-trade-mcp?tab=readme-ov-file#getting-your-api-key))
  - View performance statistics for your overall account as well as for individual symphonies.
  - Try asking Claude: "_Identify my best-performing symphonies. Analyze why they are working._"
- **Control your investments** (requires API Key + [Composer subscription](https://www.composer.trade/pricing))
  - Ask AI to analyze your investments and adjust your exposure accordingly!
  - Try asking Claude: "_Research the latest trends and news. Analyze my symphonies and determine whether I should increase / decrease my investments._"

‼️ **WARNING: Composer's symphony schema takes up nearly all of the available context window on Claude's free plan. Please upgrade your Anthropic plan to get the full benefit of the MCP server.** ‼️

## Quickstart with Claude Desktop
This section will get you started with creating symphonies and backtesting them. You don't even need a Composer account to use these features! Note that more advanced features will require an [API Key](https://github.com/invest-composer/composer-trade-mcp?tab=readme-ov-file#getting-your-api-key).

**To use the Composer MCP, you’ll need the Claude Pro or Max [plan](https://www.anthropic.com/pricing).**

1. Make sure you have [Claude Desktop](https://claude.ai/download) installed.
1. Make sure you have [Python 3.10](https://www.python.org/downloads/) (or higher).
   - Check your version by running `python3 --version` in the terminal.
1. Install `uv` (Python package manager) with `curl -LsSf https://astral.sh/uv/install.sh | sh` or see the `uv` [repo](https://github.com/astral-sh/uv) for additional install methods.
1. Download [composer-trade-mcp.dxt](https://storage.googleapis.com/www.investcomposer.com/downloads/composer-trade-mcp.dxt)
1. Go to Claude > Settings > Extensions then drag the `composer-trade-mcp.dxt` file into the window.

<div align="center">
 <img src="https://github.com/user-attachments/assets/e5ffe326-41ec-4f8c-8b6f-e2abf3340622" alt="CleanShot 2025-06-25 at 14 35 15@2x" width="500">
</div>

6. Click "Install"
    - You can choose to add your [API Key](https://github.com/invest-composer/composer-trade-mcp?tab=readme-ov-file#getting-your-api-key) here for more advanced features but it's not necessary for backtesting.
1. That's it. Your MCP client can now interact with Composer! Try asking Claude something like, "_Create and backtest a basic 60-40 strategy._"

## Manual install
If the approach above did not work or your AI client doesn't support DXT, you can try the following:

1. Make sure you have [Python 3.10](https://www.python.org/downloads/) (or higher).
   - Check your version by running `python3 --version` in the terminal.
1. Install `uv` (Python package manager) with `curl -LsSf https://astral.sh/uv/install.sh | sh` or see the `uv` [repo](https://github.com/astral-sh/uv) for additional install methods.
1. Open your Terminal and run `which uvx`
1. Go to Claude > Settings > Developer > Edit Config > claude_desktop_config.json to include the following:

```
{
  "mcpServers": {
    "composer": {
      "command": "uvx",  <--------- Replace "uvx" with the result of `which uvx` in the prior step
      "args": [
        "composer-trade-mcp"
      ]
    }
  }
}
```
5. Close and re-open Claude and you can now interact with Composer!

## Getting your API Key

An API key will be necessary to interact with your Composer account. For example, saving a Composer Symphony for later or viewing statistics about your portfolio.

Trading a symphony will require a paid subscription, although you can always liquidate a position regardless of your subscription status. Composer also includes a 14-day free trial so you can try without any commitment.

Get your API key from [Composer](https://app.composer.trade) by following these steps:

1. If you haven't already done so, [create an account](https://app.composer.trade/register).
1. Open your "Accounts & Funding" page
   ![CleanShot 2025-06-25 at 14 28 12@2x](https://github.com/user-attachments/assets/7821f9f8-07ad-4fa9-87e0-24b29e6bbd87)
1. Request an API key
   <div align="center">
     <img src="https://github.com/user-attachments/assets/df6d8f23-de5a-44fb-a1c7-0bffa7e3173f" alt="CleanShot 2025-06-25 at 14 35 15@2x" width="500">
   </div>
1. Save your API key and secret
   <div align="center">
     <img src="https://github.com/user-attachments/assets/dd4d2828-6bfd-4db5-9fe0-6a78694f87c6" alt="CleanShot 2025-06-25 at 14 35 15@2x" width="500">
   </div>
1. Depending on how you installed the Composer MCP server, do the following:
    1. If you installed via `composer-trade-mcp.dxt`:
        - Go to Claude > Settings > Extensions > Composer MCP Server > Configure
        - Add your API Key and Secret
    1. If you installed via `claude_desktop_config.json`:
        - Modify your `claude_desktop_config.json` to include your API key and secret:
```
{
  "mcpServers": {
    "composer": {
      "command": "uvx",
      "args": [
        "composer-trade-mcp"
      ],
      "env": {
        "COMPOSER_API_KEY": "<insert-your-api-key-here>",
        "COMPOSER_SECRET_KEY": "<insert-your-api-secret-here>"
      }
    }
  }
}
```
6. Quit and re-open Claude to apply your changes.

## Available tools
Once your LLM is connected to the Composer MCP Server, it will have access to the following tools:

- `create_symphony` - Define an automated strategy using Composer's system.
- `backtest_symphony` - Backtest a symphony that was created with `create_symphony`
- `search_symphonies` - Search through a database of existing Composer symphonies.
- `backtest_symphony_by_id` - Backtest an existing symphony given its ID
- `save_symphony` - Save a symphony to the user's account
- `copy_symphony` - Copy an existing symphony to the user's account
- `update_saved_symphony` - Update a saved symphony
- `list_accounts` - List all brokerage accounts available to the Composer user
- `get_account_holdings` - Get the holdings of a brokerage account
- `get_aggregate_portfolio_stats` - Get the aggregate portfolio statistics of a brokerage account
- `get_aggregate_symphony_stats` - Get stats for every symphony in a brokerage account
- `get_symphony_daily_performance` - Get daily performance for a specific symphony in a brokerage account
- `get_portfolio_daily_performance` - Get the daily performance for a brokerage account
- `get_saved_symphony` - Get the definition about an existing symphony given its ID.
- `get_market_hours` - Get market hours for the next week
- `invest_in_symphony` - Invest in a symphony for a specific account
- `withdraw_from_symphony` - Withdraw money from a symphony for a specific account
- `cancel_invest_or_withdraw` - Cancel an invest or withdraw request that has not been processed yet
- `skip_automated_rebalance_for_symphony` - Skip automated rebalance for a symphony in a specific account
- `go_to_cash_for_symphony` - Immediately sell all assets in a symphony
- `liquidate_symphony` - Immediately sell all assets in a symphony (or queue for market open if outside of market hours)
- `preview_rebalance_for_user` - Perform a dry run of rebalancing across all accounts to see what trades would be recommended
- `preview_rebalance_for_symphony` - Perform a dry run of rebalancing for a specific symphony to see what trades would be recommended
- `rebalance_symphony_now` - Rebalance a symphony NOW instead of waiting for the next automated rebalance
- `execute_single_trade` - Execute a single order for a specific symbol like you would in a traditional brokerage account
- `cancel_single_trade` - Cancel a request for a single trade that has not executed yet

## Recommendations
We recommend the following for the best experience with Composer:
- Use Claude Opus 4 instead of Sonnet. Opus is much better at tool use.
- Turn on Claude's Research mode if you need the latest financial data and news.
- Tools that execute trades or affect your funds should only be allowed once. Do not set them to "Always Allow".
  - The following tools should be handled with care: `invest_in_symphony`, `withdraw_from_symphony`, `skip_automated_rebalance_for_symphony`, `go_to_cash_for_symphony`, `liquidate_symphony`, `rebalance_symphony_now`, `execute_single_trade`

## Troubleshooting

Logs when running with Claude Desktop can be found at:

- **Windows**: `%APPDATA%\Claude\logs\mcp-server-composer.log`
- **macOS**: `~/Library/Logs/Claude/mcp-server-composer.log`

---
_Please review the [API & MCP Server Disclosure](https://storage.googleapis.com/www.investcomposer.com/docs/COM%20sh%20-%20API%20%26%20MCP%20Server%20Disclosure.pdf) before using the API_
