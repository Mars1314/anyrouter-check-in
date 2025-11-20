# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-account auto check-in system for AnyRouter and compatible NewAPI/OneAPI platforms. It uses Playwright for WAF bypass, supports multiple notification channels, and runs on GitHub Actions.

## Development Commands

### Environment Setup
```bash
# Install all dependencies (including dev dependencies)
uv sync --dev

# Install Playwright browser (required for WAF bypass)
uv run playwright install chromium
```

### Running the Application
```bash
# Create .env file with configuration (JSON must be single-line format)
# ANYROUTER_ACCOUNTS=[{"name":"账号1","cookies":{"session":"xxx"},"api_user":"12345"}]
# PROVIDERS={"agentrouter":{"domain":"https://agentrouter.org"}}

# Run check-in script
uv run checkin.py
```

### Testing
```bash
# Run all tests
uv run pytest tests/

# Run with coverage
uv run pytest --cov tests/
```

### Code Quality
```bash
# Format and lint code (ruff configured in pyproject.toml)
uv run ruff check .
uv run ruff format .
```

## Architecture

### Core Components

**checkin.py** - Main orchestration script that:
- Loads account and provider configurations from environment variables
- Uses Playwright to bypass WAF protection (when required)
- Executes check-in requests with proper headers and cookies
- Tracks balance changes using hash-based detection
- Sends notifications on failures or balance changes

**utils/config.py** - Configuration management:
- `ProviderConfig`: Platform configuration (domain, API paths, WAF bypass method)
- `AppConfig`: Manages multiple providers, includes built-in configs for `anyrouter` and `agentrouter`
- `AccountConfig`: Individual account settings (cookies, api_user, provider, name)
- Built-in providers: `anyrouter` (needs WAF bypass), `agentrouter` (no WAF bypass)

**utils/notify.py** - Notification system with support for:
- Email (SMTP)
- DingTalk, Feishu, WeChat Work webhooks
- PushPlus, Server酱 push services
- Telegram Bot

### Key Architectural Patterns

**WAF Bypass Strategy**:
- Providers with `bypass_method: "waf_cookies"` launch a headless Chromium browser via Playwright to obtain WAF cookies (`acw_tc`, `cdn_sec_tc`, `acw_sc__v2`)
- These cookies are merged with user cookies before making API requests
- Providers without `bypass_method` use user cookies directly

**Balance Change Detection**:
- Generates SHA-256 hash of all account balances (quota values only)
- Stores hash in `balance_hash.txt` (cached in GitHub Actions)
- Triggers notifications when hash changes (balance updates)
- First run always triggers notification

**Provider Configuration System**:
- Default providers (`anyrouter`, `agentrouter`) are built-in
- Custom providers can be added via `PROVIDERS` environment variable
- Each provider specifies: `domain`, API paths, `api_user_key` header name, and `bypass_method`
- Some providers auto-complete check-in on user info request (set `sign_in_path: None`)

**Notification Logic**:
- Only notifies when: (1) any account fails, (2) balance changes detected, or (3) first run
- Includes detailed account status and balance information
- Attempts all configured notification methods independently

### GitHub Actions Workflow

The workflow (`.github/workflows/checkin.yml`):
- Runs on Windows 2025 runner every 6 hours
- Uses UV for fast dependency management with caching
- Caches Playwright browsers by version
- Caches `balance_hash.txt` to track balance changes across runs
- Accesses secrets from `production` environment
- Exits with code 0 if any account succeeds (partial success allowed)

### Important Implementation Details

**Provider auto-detect**: If `sign_in_path` is `None`, the system assumes check-in happens automatically when fetching user info (like `agentrouter`)

**Account naming**: Accounts can have optional `name` field for custom display names, otherwise defaults to "Account 1", "Account 2", etc.

**Error handling**: Partial failures are allowed - task succeeds if at least one account checks in successfully

**Cookie parsing**: Supports both dict format `{"session": "value"}` and string format `"key1=value1; key2=value2"`

## Configuration Schema

### ANYROUTER_ACCOUNTS (required)
JSON array of account objects:
```json
[
  {
    "name": "账号显示名称",
    "provider": "anyrouter",
    "cookies": {"session": "cookie_value"},
    "api_user": "12345"
  }
]
```
- `cookies` and `api_user` are required
- `provider` defaults to "anyrouter" if not specified
- `name` is optional for display purposes

### PROVIDERS (optional)
JSON object defining custom providers:
```json
{
  "customrouter": {
    "domain": "https://custom.example.com",
    "login_path": "/login",
    "sign_in_path": "/api/user/sign_in",
    "user_info_path": "/api/user/self",
    "api_user_key": "new-api-user",
    "bypass_method": "waf_cookies"
  }
}
```
- Only `domain` is required, others use defaults
- `bypass_method` can be "waf_cookies" or null
- Set `sign_in_path: null` for platforms that auto-complete check-in

## Testing Notes

Tests use pytest with mocking. The notification tests mock external services (SMTP, HTTP requests). Set `ENABLE_REAL_TEST=true` in `.env` to run actual integration tests with real services.

## Python Environment

- Requires Python 3.11+
- Uses UV for dependency management (faster than pip)
- Uses Ruff for linting and formatting (tabs, single quotes, 120 line length)
