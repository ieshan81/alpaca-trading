#!/usr/bin/env python3
"""
Headless auto-trader for Railway / Docker.

Runs analyze → trade loops without clicking the Web UI. Configured via env vars.
This is the fastest mode AlpacaTradingAgent supports (still LLM-bound, not HFT).
"""

from __future__ import annotations

import os
import sys
import time


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    try:
        return max(minimum, int(os.getenv(name, str(default))))
    except ValueError:
        return default


def _parse_analysts() -> dict[str, bool]:
    raw = os.getenv("ANALYSTS", "market,news").lower()
    chosen = {part.strip() for part in raw.split(",") if part.strip()}
    return {
        "market": "market" in chosen,
        "social": "social" in chosen,
        "news": "news" in chosen,
        "fundamentals": "fundamentals" in chosen,
        "macro": "macro" in chosen,
    }


def main() -> int:
    if not _env_bool("AUTOTRADER_ENABLED", True):
        print("[autotrader] AUTOTRADER_ENABLED=false — exiting")
        return 0

    # Import after env/bootstrap from tradingagents.config
    from webui.components.analysis import start_analysis
    from webui.utils.market_hours import is_market_open
    from webui.utils.state import app_state

    symbols = [
        s.strip().upper()
        for s in os.getenv("TRADING_SYMBOLS", "SPY,QQQ").split(",")
        if s.strip()
    ]
    if not symbols:
        print("[autotrader] TRADING_SYMBOLS empty — exiting")
        return 1

    interval_sec = _env_int("LOOP_INTERVAL_SECONDS", 60, minimum=30)
    trade_enabled = _env_bool("TRADE_ENABLED", True)
    trade_amount = float(os.getenv("TRADE_DOLLAR_AMOUNT", "1000"))
    allow_shorts = _env_bool("ALLOW_SHORTS", False)
    research_depth = os.getenv("RESEARCH_DEPTH", "Shallow")
    llm_provider = os.getenv("LLM_PROVIDER", "google")
    quick_llm = os.getenv("QUICK_THINK_LLM") or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    deep_llm = os.getenv("DEEP_THINK_LLM") or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    trade_only_open = _env_bool("TRADE_ONLY_MARKET_HOURS", True)
    analysts = _parse_analysts()

    app_state.trade_enabled = trade_enabled
    app_state.trade_amount = trade_amount

    print("[autotrader] starting headless loop")
    print(f"[autotrader] symbols={symbols} interval={interval_sec}s trade={trade_enabled} amount=${trade_amount}")
    print(f"[autotrader] analysts={analysts} depth={research_depth} provider={llm_provider}")
    print(f"[autotrader] models quick={quick_llm} deep={deep_llm}")
    if trade_only_open:
        print("[autotrader] will skip cycles when US equity market is closed")

    iteration = 0
    while True:
        iteration += 1
        if trade_only_open and not is_market_open():
            print(f"[autotrader] market closed — sleeping {interval_sec}s")
            time.sleep(interval_sec)
            continue

        print(f"[autotrader] === cycle {iteration} ===")
        for symbol in symbols:
            try:
                app_state.init_symbol_state(symbol)
                app_state.current_symbol = symbol
                app_state.analyzing_symbol = symbol
                msg = start_analysis(
                    symbol,
                    analysts["market"],
                    analysts["social"],
                    analysts["news"],
                    analysts["fundamentals"],
                    analysts["macro"],
                    research_depth,
                    allow_shorts,
                    quick_llm,
                    deep_llm,
                    quick_llm_params={},
                    deep_llm_params={},
                    llm_provider=llm_provider,
                    backend_url=None,
                    output_language="English",
                    checkpoint_enabled=False,
                    provider_settings={"google_thinking_level": "minimal"},
                )
                print(f"[autotrader] {symbol}: {msg}")
            except Exception as exc:
                print(f"[autotrader] {symbol} failed: {exc}")
                import traceback
                traceback.print_exc()

        print(f"[autotrader] cycle {iteration} done — sleeping {interval_sec}s")
        time.sleep(interval_sec)


if __name__ == "__main__":
    sys.exit(main())
