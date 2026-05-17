import datetime


def build_full_briefing(market_block, edition='Morning'):
    now = datetime.datetime.now().strftime('%H:%M on %-d %b %Y')
    date_str = datetime.datetime.now().strftime('%A %-d %B %Y')
    return '\n'.join([
        f'📈 <b>Marketfeed — {edition} Briefing</b>',
        f'📅 {date_str}',
        '',
        market_block,
        '',
        f'🕐 <i>Marketfeed — {now}</i>',
    ])
