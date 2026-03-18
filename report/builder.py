"""Report Builder — aggregates all module data into Telegram MarkdownV2."""

from utils.helpers import escape_md2, now_china
from utils.logger import get_logger

logger = get_logger("report_builder")

# Telegram message limit
MAX_MSG_LEN = 4000  # leave some buffer under 4096


class ReportBuilder:
    def build(
        self,
        macro: dict,
        picks: list[dict],
        sentiment: dict,
        snapshot: dict,
        performance: dict,
    ) -> list[str]:
        """Build the full Executive Alpha Briefing and return as list of message strings."""
        sections = []

        # Header
        date_str = now_china().strftime("%Y-%m-%d %H:%M CST")
        sections.append(self._build_header(date_str))

        # Executive Summary
        sections.append(self._build_executive_summary(macro, sentiment))

        # Macro Outlook
        sections.append(self._build_macro_section(macro))

        # Stock Recommendations (each as its own section to allow splitting)
        rec_sections = self._build_recommendations(picks, sentiment)
        sections.extend(rec_sections)

        # Paper Portfolio
        sections.append(self._build_portfolio_section(snapshot, performance))

        # Footer
        sections.append(self._build_footer())

        # Join and split into Telegram-safe messages
        return self._split_messages(sections)

    def _build_header(self, date_str: str) -> str:
        d = escape_md2(date_str)
        return (
            f"*{'=' * 28}*\n"
            f"*ALPHA ADVISORY DAILY BRIEF*\n"
            f"_{d}_\n"
            f"*{'=' * 28}*"
        )

    def _build_executive_summary(self, macro: dict, sentiment: dict) -> str:
        mood = escape_md2(sentiment.get("overall_market_mood", "N/A"))
        summary = escape_md2(macro.get("macro_summary", "Data unavailable"))
        return (
            f"\n*EXECUTIVE SUMMARY*\n"
            f"Market Mood: *{mood}*\n"
            f"{summary}"
        )

    def _build_macro_section(self, macro: dict) -> str:
        risk = escape_md2(macro.get("risk_level", "N/A"))
        fed = escape_md2(macro.get("fed_sentiment", "N/A"))
        fed_detail = escape_md2(macro.get("fed_detail", ""))

        lines = [
            f"\n*MACRO OUTLOOK*",
            f"Risk Level: *{risk}*",
            f"Fed Stance: *{fed}*",
            f"_{fed_detail}_",
        ]

        events = macro.get("key_events", [])
        if events:
            lines.append("\nKey Events:")
            for evt in events[:5]:
                lines.append(f"  • {escape_md2(evt[:100])}")

        fred = macro.get("fred_data", {})
        if fred:
            parts = []
            if "10Y_YIELD" in fred:
                parts.append(f"10Y: {escape_md2(str(fred['10Y_YIELD']))}%")
            if "VIX" in fred:
                parts.append(f"VIX: {escape_md2(str(fred['VIX']))}")
            if parts:
                lines.append("Indicators: " + " | ".join(parts))

        return "\n".join(lines)

    def _build_recommendations(self, picks: list[dict], sentiment: dict) -> list[str]:
        sections = ["\n*STOCK RECOMMENDATIONS*"]

        # Show top picks (Buy/Sell only, limit to 8)
        actionable = [p for p in picks if p["action"] in ("Buy", "Sell")]
        if not actionable:
            sections.append("_No actionable recommendations today\\._")
            return sections

        for pick in actionable[:8]:
            ticker = escape_md2(pick["ticker"])
            exchange = escape_md2(pick.get("exchange", ""))
            action = pick["action"]
            action_emoji = "BUY" if action == "Buy" else "SELL"

            # Get sentiment for this ticker
            tick_sent = sentiment.get("ticker_sentiments", {}).get(pick["ticker"], {})
            trend = escape_md2(tick_sent.get("trend", "N/A"))

            entry_low = escape_md2(f"${pick.get('entry_price_low', 0):.2f}")
            entry_high = escape_md2(f"${pick.get('entry_price_high', 0):.2f}")
            stop = escape_md2(f"${pick.get('stop_loss', 0):.2f}")
            conf = pick.get("confidence", 0)
            rationale = escape_md2(pick.get("rationale", "N/A")[:200])
            current = escape_md2(f"${pick.get('current_price', 0):.2f}")

            block = (
                f"\n*{ticker}* \\({exchange}\\) — *{escape_md2(action_emoji)}*\n"
                f"  Price: {current}\n"
                f"  Entry: {entry_low} \\- {entry_high}\n"
                f"  Stop\\-Loss: {stop}\n"
                f"  Confidence: *{conf}/10*\n"
                f"  Sentiment: {trend}\n"
                f"  _{rationale}_"
            )
            sections.append(block)

        return sections

    def _build_portfolio_section(self, snapshot: dict, performance: dict) -> str:
        total = escape_md2(f"${snapshot.get('total_value', 0):,.2f}")
        cash = escape_md2(f"${snapshot.get('cash', 0):,.2f}")
        ret = escape_md2(f"{snapshot.get('return_pct', 0):.2f}%")
        spy_ret = escape_md2(f"{performance.get('spy_return', 0):.2f}%")
        alpha = escape_md2(f"{performance.get('alpha', 0):.2f}%")
        capital = escape_md2("$50,000")

        lines = [
            f"\n*PAPER PORTFOLIO*",
            f"Starting Capital: {capital}",
            f"Current Value: *{total}*",
            f"Cash: {cash}",
            f"Return: *{ret}*",
            f"S&P 500 Return: {spy_ret}",
            f"Alpha: *{alpha}*",
        ]

        positions = snapshot.get("positions", [])
        if positions:
            lines.append("\nOpen Positions:")
            for pos in positions:
                t = escape_md2(pos["ticker"])
                sh = int(pos["shares"])
                avg = escape_md2(f"${pos['avg_cost']:.2f}")
                cur = escape_md2(f"${pos['current_price']:.2f}")
                pct = escape_md2(f"{pos['pct_change']:.1f}%")
                lines.append(f"  • {t}: {sh} shares @ {avg} → {cur} \\({pct}\\)")
        else:
            lines.append("\n_No open positions\\._")

        return "\n".join(lines)

    def _build_footer(self) -> str:
        return (
            f"\n*{'=' * 28}*\n"
            f"_Advisory Only \\- No Real Trades_\n"
            f"_Project Alpha by Schelle\\_investor\\_bot_"
        )

    def _split_messages(self, sections: list[str]) -> list[str]:
        """Split sections into messages that fit Telegram's limit."""
        messages = []
        current = ""

        for section in sections:
            if len(current) + len(section) + 1 > MAX_MSG_LEN:
                if current:
                    messages.append(current)
                current = section
            else:
                current = current + "\n" + section if current else section

        if current:
            messages.append(current)

        return messages if messages else ["_No data available for today's report\\._"]
