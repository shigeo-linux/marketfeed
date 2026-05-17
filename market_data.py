WATCHLIST = [
    ('^GSPC',   'S&P 500',         '📈', ''),
    ('^DJI',    'Dow Jones',        '📈', ''),
    ('^IXIC',   'Nasdaq',           '📈', ''),
    ('GC=F',    'Gold',             '🥇', '/oz'),
    ('SI=F',    'Silver',           '🥈', '/oz'),
    ('BTC-USD', 'Bitcoin',          '₿',  ''),
    ('^TNX',    '10Y Treasury',     '🏦', '%'),
]


def fetch_market_data():
    """Fetch latest prices for the watchlist. Returns list of dicts."""
    import yfinance as yf

    results = []
    for symbol, name, icon, unit in WATCHLIST:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            price = info.last_price
            prev = info.previous_close
            chg = (price - prev) / prev * 100 if prev and prev != 0 else 0
            currency = info.currency or 'USD'

            results.append({
                'symbol': symbol,
                'name': name,
                'icon': icon,
                'price': price,
                'change_pct': chg,
                'currency': currency,
                'unit': unit,
            })
        except Exception as e:
            results.append({
                'symbol': symbol,
                'name': name,
                'icon': icon,
                'price': None,
                'change_pct': 0,
                'currency': 'USD',
                'unit': unit,
                'error': str(e),
            })

    return results


def format_market_block(market_data):
    """Format market data as a Telegram HTML block."""
    lines = ['📊 <b>Markets</b>']
    for item in market_data:
        if item.get('error') or item['price'] is None:
            lines.append(f"{item['icon']} {item['name']}: N/A")
            continue

        price = item['price']
        chg = item['change_pct']
        unit = item['unit']
        arrow = '▲' if chg >= 0 else '▼'
        chg_str = f"{arrow} {abs(chg):.2f}%"

        # Format price
        if item['symbol'] == '^TNX':
            price_str = f"{price:.2f}%"
        elif price >= 1000:
            price_str = f"${price:,.2f}{unit}"
        elif price >= 1:
            price_str = f"${price:.2f}{unit}"
        else:
            price_str = f"${price:.4f}{unit}"

        lines.append(f"{item['icon']} <b>{item['name']}</b>: {price_str}  {chg_str}")

    return '\n'.join(lines)
