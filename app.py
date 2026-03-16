"""Main game starter with update check.

Flow:
1) launcher starts
2) checks local and remote version
3) if outdated -> blocking update dialog
4) on "Update" starts updater and exits
5) on up-to-date starts game (or placeholder flow)
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox

import config
from version_checker import VersionError, fetch_latest_release_info, is_version_less, read_local_version


logging.basicConfig(
    filename=config.LAUNCHER_LOG,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)


def open_github_page(url: str) -> None:
    """Open URL in default browser (cross-platform)."""
    import webbrowser

    webbrowser.open(url, new=2)


def run_updater_and_exit() -> None:
    """Start updater process and close launcher/game starter."""
    updater_script = os.path.join(os.path.dirname(__file__), "updater.py")
    if getattr(sys, "frozen", False):
        # In packaged mode prefer standalone updater.exe
        updater_path = os.path.join(os.path.dirname(sys.executable), config.UPDATER_EXE_NAME)
        if os.path.exists(updater_path):
            subprocess.Popen([updater_path], close_fds=True)
        else:
            messagebox.showerror(
                "Ошибка",
                f"Не найден {config.UPDATER_EXE_NAME}. Добавьте updater рядом с игрой.",
            )
            return
    else:
        subprocess.Popen([sys.executable, updater_script], close_fds=True)

    logging.info("Updater started, launcher exiting")
    sys.exit(0)


def launch_game() -> None:
    """Launch the main game executable; in dev mode show placeholder."""
    if getattr(sys, "frozen", False):
        game_exe = os.path.join(os.path.dirname(sys.executable), config.GAME_EXE_NAME)
        if not os.path.exists(game_exe):
            messagebox.showerror("Ошибка", f"Файл игры не найден: {config.GAME_EXE_NAME}")
            return
        subprocess.Popen([game_exe], close_fds=True)
        sys.exit(0)

    # Dev placeholder behavior
    root = tk.Tk()
    root.title(config.APP_NAME)
    root.geometry("420x160")
    tk.Label(root, text="Версия актуальна. Здесь запускается игра.", font=("Segoe UI", 11)).pack(
        pady=30
    )
    tk.Button(root, text="Выход", width=16, command=root.destroy).pack()
    root.mainloop()


def show_update_required_dialog(remote_version: str, github_url: str) -> None:
    """Show blocking update-required UI with actions."""
    dlg = tk.Tk()
    dlg.title("Требуется обновление")
    dlg.geometry("520x220")
    dlg.resizable(False, False)

    msg = (
        "Ваша версия устарела. Требуется обновление.\n\n"
        f"Доступна версия: {remote_version}"
    )

    tk.Label(dlg, text=msg, font=("Segoe UI", 11), justify="left").pack(pady=20)

    button_frame = tk.Frame(dlg)
    button_frame.pack(pady=10)

    tk.Button(button_frame, text="Обновить", width=18, command=run_updater_and_exit).grid(
        row=0, column=0, padx=6
    )
    tk.Button(
        button_frame,
        text="Открыть GitHub",
        width=18,
        command=lambda: open_github_page(github_url),
    ).grid(row=0, column=1, padx=6)
    tk.Button(button_frame, text="Выход", width=18, command=lambda: sys.exit(0)).grid(
        row=0, column=2, padx=6
    )

    # Block normal game start until user decides
    dlg.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))
    dlg.mainloop()


def main() -> None:
    logging.info("Launcher started")
    try:
        local_version = read_local_version()
        remote = fetch_latest_release_info()
        logging.info("Local version=%s, remote=%s (%s)", local_version, remote.version, remote.source)

        if is_version_less(local_version, remote.version):
            show_update_required_dialog(remote.version, remote.release_page)
            return

        launch_game()

    except VersionError as exc:
        logging.exception("Version check failed: %s", exc)
        messagebox.showerror(
            "Ошибка проверки обновлений",
            f"Не удалось проверить версию:\n{exc}\n\n"
            "Проверьте интернет или настройки GitHub в config.py.",
        )
        sys.exit(1)
    except Exception as exc:  # defensive catch for launcher
        logging.exception("Unexpected launcher error: %s", exc)
        messagebox.showerror("Критическая ошибка", str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
