import os
import subprocess
import threading
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

from config import Config, LOG_FILE
from market_data import fetch_market_data, format_market_block
from summarizer import build_full_briefing
from telegram_client import send_message, test_connection, TelegramError

STYLE_PATH = os.path.join(os.path.dirname(__file__), 'style.css')

def _load_css():
    provider = Gtk.CssProvider()
    try:
        provider.load_from_path(STYLE_PATH)
    except Exception:
        pass
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


def fl(text):
    lbl = Gtk.Label(label=text, xalign=1)
    lbl.get_style_context().add_class('field-label')
    return lbl


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title='Marketfeed')
        self.set_default_size(520, 420)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name('marketfeed')
        _load_css()
        self.config = Config()
        self._busy = False
        self._build_ui()
        self._refresh_status()

    def _build_ui(self):
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.set_title('Marketfeed')
        header.set_subtitle('Markets & financial news → Telegram')
        self.set_titlebar(header)

        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content.set_border_width(20)
        main.pack_start(content, False, False, 0)

        # Status card
        status_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        status_card.get_style_context().add_class('status-card')
        lbl = Gtk.Label(label='Status', xalign=0)
        lbl.get_style_context().add_class('section-title')
        status_card.pack_start(lbl, False, False, 0)
        self._status_label = Gtk.Label(label='Not yet run', xalign=0)
        self._status_label.set_line_wrap(True)
        self._status_label.set_max_width_chars(60)
        self._status_label.get_style_context().add_class('status-pending')
        status_card.pack_start(self._status_label, False, False, 0)
        self._last_run_label = Gtk.Label(label='', xalign=0)
        self._last_run_label.set_ellipsize(3)
        self._last_run_label.set_max_width_chars(60)
        self._last_run_label.get_style_context().add_class('meta-label')
        status_card.pack_start(self._last_run_label, False, False, 0)
        content.pack_start(status_card, False, False, 0)

        # Run now
        run_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self._run_btn = Gtk.Button(label='Send Briefing Now')
        self._run_btn.get_style_context().add_class('action-btn')
        self._run_btn.connect('clicked', self._on_run_now)
        run_row.pack_start(self._run_btn, False, False, 0)
        self._spinner = Gtk.Spinner()
        run_row.pack_start(self._spinner, False, False, 0)
        content.pack_start(run_row, False, False, 0)

        content.pack_start(Gtk.Separator(), False, False, 0)

        # Telegram
        t = Gtk.Label(label='Telegram', xalign=0)
        t.get_style_context().add_class('section-title')
        content.pack_start(t, False, False, 0)
        tg = Gtk.Grid()
        tg.set_column_spacing(12)
        tg.set_row_spacing(8)
        tg.attach(fl('Token:'), 0, 0, 1, 1)
        self._tg_token = Gtk.Entry()
        self._tg_token.set_hexpand(True)
        self._tg_token.set_visibility(False)
        self._tg_token.set_text(self.config.telegram_token)
        self._tg_token.set_placeholder_text('123456789:ABCdef...')
        tg.attach(self._tg_token, 1, 0, 1, 1)
        tg.attach(fl('Chat ID:'), 0, 1, 1, 1)
        self._tg_chat = Gtk.Entry()
        self._tg_chat.set_text(self.config.telegram_chat_id)
        tg.attach(self._tg_chat, 1, 1, 1, 1)
        content.pack_start(tg, False, False, 0)

        content.pack_start(Gtk.Separator(), False, False, 0)

        # Schedule
        s = Gtk.Label(label='Schedule', xalign=0)
        s.get_style_context().add_class('section-title')
        content.pack_start(s, False, False, 0)
        sg = Gtk.Grid()
        sg.set_column_spacing(12)
        sg.set_row_spacing(8)

        sg.attach(fl('Morning briefing:'), 0, 0, 1, 1)
        mb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._morning_spin = Gtk.SpinButton.new_with_range(0, 23, 1)
        self._morning_spin.set_value(self.config.morning_hour)
        self._morning_spin.set_size_request(60, -1)
        mb.pack_start(self._morning_spin, False, False, 0)
        l1 = Gtk.Label(label=':00  (24h)')
        l1.get_style_context().add_class('field-label')
        mb.pack_start(l1, False, False, 0)
        sg.attach(mb, 1, 0, 1, 1)

        sg.attach(fl('Evening briefing:'), 0, 1, 1, 1)
        eb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._evening_spin = Gtk.SpinButton.new_with_range(-1, 23, 1)
        self._evening_spin.set_value(self.config.evening_hour)
        self._evening_spin.set_size_request(60, -1)
        eb.pack_start(self._evening_spin, False, False, 0)
        l2 = Gtk.Label(label=':00  (-1 = disabled)')
        l2.get_style_context().add_class('field-label')
        eb.pack_start(l2, False, False, 0)
        sg.attach(eb, 1, 1, 1, 1)
        content.pack_start(sg, False, False, 0)

        # Buttons
        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        save_btn = Gtk.Button(label='Save Settings')
        save_btn.get_style_context().add_class('action-btn')
        save_btn.connect('clicked', self._on_save)
        btn_row.pack_start(save_btn, False, False, 0)
        test_btn = Gtk.Button(label='Test Telegram')
        test_btn.connect('clicked', self._on_test)
        btn_row.pack_start(test_btn, False, False, 0)
        log_btn = Gtk.Button(label='View Log')
        log_btn.connect('clicked', self._on_log)
        btn_row.pack_end(log_btn, False, False, 0)
        content.pack_start(btn_row, False, False, 0)

        # Status bar
        self._status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._status_bar.get_style_context().add_class('status-bar')
        self._bar_label = Gtk.Label(label='', xalign=0)
        self._status_bar.pack_start(self._bar_label, True, True, 0)
        main.pack_start(self._status_bar, False, False, 0)

    def _refresh_status(self):
        last_run = self.config.get('last_run', '')
        last_status = self.config.get('last_status', '')
        ctx = self._status_label.get_style_context()
        if last_status.startswith('OK'):
            self._status_label.set_text(last_status)
            ctx.add_class('status-ok')
            ctx.remove_class('status-error')
            ctx.remove_class('status-pending')
        elif last_status.startswith('Error'):
            self._status_label.set_text(last_status[:120])
            ctx.add_class('status-error')
            ctx.remove_class('status-ok')
            ctx.remove_class('status-pending')
        else:
            self._status_label.set_text('Not yet run')
        self._last_run_label.set_text(f'Last run: {last_run}' if last_run else 'Last run: never')

    def _on_save(self, btn):
        self.config.set('telegram_token', self._tg_token.get_text().strip())
        self.config.set('telegram_chat_id', self._tg_chat.get_text().strip())
        self.config.set('morning_hour', int(self._morning_spin.get_value()))
        self.config.set('evening_hour', int(self._evening_spin.get_value()))
        self.config.save()
        self._set_bar('Settings saved.')

    def _on_test(self, btn):
        token = self._tg_token.get_text().strip()
        chat_id = self._tg_chat.get_text().strip()
        if not token or not chat_id:
            self._show_error('Missing details', 'Enter your Telegram token and chat ID first.')
            return
        try:
            test_connection(token, chat_id)
            self._set_bar('Test message sent to Telegram.')
        except TelegramError as e:
            self._show_error('Telegram test failed', str(e))

    def _on_run_now(self, btn):
        if self._busy:
            return
        self._busy = True
        self._run_btn.set_sensitive(False)
        self._spinner.start()

        def run():
            try:
                market_data = fetch_market_data()
                market_block = format_market_block(market_data)
                message = build_full_briefing(market_block, edition='Market Update')
                send_message(self.config.telegram_token, self.config.telegram_chat_id, message)
                GLib.idle_add(self._on_run_done, True, 'Market briefing sent.')
            except Exception as e:
                GLib.idle_add(self._on_run_done, False, str(e)[:120])

        threading.Thread(target=run, daemon=True).start()

    def _on_run_done(self, success, msg):
        self._busy = False
        self._spinner.stop()
        self._run_btn.set_sensitive(True)
        self._set_bar(msg)

    def _on_log(self, btn):
        if os.path.exists(LOG_FILE):
            subprocess.Popen(['xdg-open', LOG_FILE])
        else:
            self._set_bar('No log file yet.')

    def _set_bar(self, msg):
        self._bar_label.set_text(msg)

    def _show_error(self, title, msg):
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK, text=title,
        )
        dialog.format_secondary_text(msg)
        dialog.run()
        dialog.destroy()
