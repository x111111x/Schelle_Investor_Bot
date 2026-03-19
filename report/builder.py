"""Report Builder — aggregates all module data into Telegram MarkdownV2."""

from utils.helpers import escape_md2, now_china
from utils.logger import get_logger

logger = get_logger("report_builder")

# Telegram message limit
MAX_MSG_LEN = 4000  # leave some buffer under 4096

# Stock ticker to company name mapping
TICKER_TO_COMPANY = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet (Google)",
    "NVDA": "NVIDIA",
    "META": "Meta (Facebook)",
    "AMZN": "Amazon",
    "TSM": "Taiwan Semiconductor",
    "JPM": "JPMorgan Chase",
    "V": "Visa",
    "UNH": "UnitedHealth",
    "CAT": "Caterpillar",
    "XOM": "ExxonMobil",
    "LIN": "Linde",
    "ASML": "ASML",
    "SAP": "SAP",
    "NVO": "Novo Nordisk",
    "COST": "Costco",
    "PG": "Procter & Gamble",
    "KO": "Coca-Cola",
    "BABA": "Alibaba",
}


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
            f"*📊 DAILY INVESTMENT BRIEF*\n"
            f"_{d}_"
        )

    def _build_executive_summary(self, macro: dict, sentiment: dict) -> str:
        mood = sentiment.get("overall_market_mood", "Neutral")
        mood_emoji = self._mood_to_emoji(mood)
        summary = escape_md2(macro.get("macro_summary", "Data unavailable"))
        return (
            f"\n*🎯 QUICK SUMMARY*\n"
            f"Market Feeling: *{mood_emoji} {escape_md2(mood)}*\n"
            f"{summary}"
        )

    @staticmethod
    def _mood_to_emoji(mood: str) -> str:
        """Convert mood to emoji."""
        mood_lower = mood.lower()
        if "bullish" in mood_lower or "positive" in mood_lower:
            return "😊"
        elif "bearish" in mood_lower or "negative" in mood_lower:
            return "😟"
        else:
            return "😐"

    def _build_macro_section(self, macro: dict) -> str:
        risk = escape_md2(macro.get("risk_level", "N/A"))
        fed = escape_md2(macro.get("fed_sentiment", "N/A"))
        fed_detail = escape_md2(macro.get("fed_detail", ""))

        lines = [
            f"\n*🌍 BIG PICTURE OUTLOOK*",
            f"Overall Market Risk: *{risk}*",
            f"What the Fed Is Doing: *{fed}*",
            f"_{fed_detail}_",
        ]

        events = macro.get("key_events", [])
        if events:
            lines.append("\nImportant News:")
            for evt in events[:5]:
                lines.append(f"  • {escape_md2(evt[:100])}")

        fred = macro.get("fred_data", {})
        if fred:
            parts = []
            if "10Y_YIELD" in fred:
                yield_val = fred['10Y_YIELD']
                parts.append(f"10\\-Year Bond Yield: {escape_md2(str(yield_val))}%")
            if "VIX" in fred:
                vix_val = fred['VIX']
                vix_status = "High Fear" if float(vix_val) > 25 else "Normal"
                parts.append(f"Fear Index: {escape_md2(str(vix_val))} \\({vix_status}\\)")
            if parts:
                lines.append("\nKey Numbers:")
                for part in parts:
                    lines.append(f"  • {part}")

        return "\n".join(lines)

    def _build_recommendations(self, picks: list[dict], sentiment: dict) -> list[str]:
        sections = ["\n*📈 WHAT TO BUY OR SELL TODAY*"]

        # Show top picks (Buy/Sell only, limit to 8)
        actionable = [p for p in picks if p["action"] in ("Buy", "Sell")]
        if not actionable:
            sections.append("_No changes recommended today. Hold steady\\._")
            return sections

        for pick in actionable[:8]:
            ticker = pick["ticker"]
            company = TICKER_TO_COMPANY.get(ticker, ticker)
            action = pick["action"]
            action_emoji = "🟢 BUY" if action == "Buy" else "🔴 SELL"

            # Get sentiment for this ticker
            tick_sent = sentiment.get("ticker_sentiments", {}).get(ticker, {})
            trend = escape_md2(tick_sent.get("trend", "Neutral"))

            current = f"${pick.get('current_price', 0):.2f}"
            entry_low = f"${pick.get('entry_price_low', 0):.2f}"
            entry_high = f"${pick.get('entry_price_high', 0):.2f}"
            stop = f"${pick.get('stop_loss', 0):.2f}"
            conf = pick.get("confidence", 0)
            rationale = escape_md2(pick.get("rationale", "")[:150])

            block = (
                f"\n*{escape_md2(company)}* \\({escape_md2(ticker)}\\) — *{action_emoji}*\n"
                f"  Current Price: *{escape_md2(current)}*\n"
                f"  Good Price to Buy: {escape_md2(entry_low)} \\- {escape_md2(entry_high)}\n"
                f"  Exit Point \\(If Loss\\): {escape_md2(stop)}\n"
                f"  Confidence: *{conf}\\/{10}* \\(higher is better\\)\n"
                f"  Market Outlook: {trend}\n"
                f"  Why: _{rationale}_"
            )
            sections.append(block)

        return sections

    def _build_portfolio_section(self, snapshot: dict, performance: dict) -> str:
        total = f"${snapshot.get('total_value', 0):,.2f}"
        cash = f"${snapshot.get('cash', 0):,.2f}"
        ret = f"{snapshot.get('return_pct', 0):.2f}%"
        spy_ret = f"{performance.get('spy_return', 0):.2f}%"
        alpha = f"{performance.get('alpha', 0):.2f}%"
        capital = "$50,000"

        ret_color = "📈" if float(ret.rstrip('%')) >= 0 else "📉"
        alpha_color = "✅" if float(alpha.rstrip('%')) >= 0 else "⚠️"

        lines = [
            f"\n*💼 YOUR PAPER PORTFOLIO*",
            f"Started With: {escape_md2(capital)}",
            f"Worth Today: *{escape_md2(total)}*",
            f"Cash on Hand: {escape_md2(cash)}",
            f"Your Gain/Loss: *{ret_color} {escape_md2(ret)}*",
            f"Market Benchmark \\(S&P 500\\): {escape_md2(spy_ret)}",
            f"You vs Market: *{alpha_color} {escape_md2(alpha)}*",
        ]

        positions = snapshot.get("positions", [])
        if positions:
            lines.append("\nStocks You Own:")
            for pos in positions:
                ticker = pos["ticker"]
                company = TICKER_TO_COMPANY.get(ticker, ticker)
                sh = int(pos["shares"])
                avg = f"${pos['avg_cost']:.2f}"
                cur = f"${pos['current_price']:.2f}"
                pct = f"{pos['pct_change']:.1f}%"
                pct_emoji = "📈" if pos['pct_change'] >= 0 else "📉"
                lines.append(
                    f"  • {escape_md2(company)} \\({escape_md2(ticker)}\\): "
                    f"{sh} shares | "
                    f"Cost: {escape_md2(avg)} → Now: {escape_md2(cur)} "
                    f"{pct_emoji} {escape_md2(pct)}"
                )
        else:
            lines.append("\n_No stocks owned yet\\._")

        return "\n".join(lines)

    def _build_footer(self) -> str:
        return (
            f"\n_⚠️ This is a practice portfolio \\(no real money invested\\)_\n"
            f"_Project Alpha • Automated Daily Report_"
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
