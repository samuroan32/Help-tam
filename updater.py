"""Standalone updater GUI.

Performs:
- fetch latest release info
- download release zip with progress bar
- extract to temp folder
- copy files into game folder with preserve-list support
- update local version.json
- start game executable
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from zipfile import BadZipFile, ZipFile

import requests

import config
from version_checker import VersionError, fetch_latest_release_info


logging.basicConfig(
    filename=config.UPDATER_LOG,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)


class UpdaterUI:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Updater")
        self.root.geometry("620x280")
        self.root.resizable(False, False)

        self.status_var = tk.StringVar(value="Проверка версии...")
        self.error_var = tk.StringVar(value="")
        self.progress_var = tk.DoubleVar(value=0.0)

        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Обновление игры", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(frame, textvariable=self.status_var).pack(anchor="w", pady=(10, 6))

        self.progress = ttk.Progressbar(
            frame,
            orient="horizontal",
            mode="determinate",
            length=560,
            variable=self.progress_var,
            maximum=100,
        )
        self.progress.pack(anchor="w", pady=(0, 10))

        ttk.Label(frame, textvariable=self.error_var, foreground="red", wraplength=560).pack(
            anchor="w", pady=(0, 12)
        )

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(anchor="e")

        self.retry_btn = ttk.Button(btn_frame, text="Повторить", command=self.start_update)
        self.retry_btn.pack(side="left", padx=6)
        self.retry_btn.configure(state="disabled")

        self.close_btn = ttk.Button(btn_frame, text="Выход", command=self.root.destroy)
        self.close_btn.pack(side="left", padx=6)

    def set_status(self, text: str) -> None:
        logging.info(text)
        self.status_var.set(text)
        self.root.update_idletasks()

    def set_error(self, text: str) -> None:
        logging.error(text)
        self.error_var.set(text)
        self.retry_btn.configure(state="normal")
        self.root.update_idletasks()

    def set_progress(self, value: float) -> None:
        self.progress_var.set(max(0.0, min(100.0, value)))
        self.root.update_idletasks()

    def start_update(self) -> None:
        self.error_var.set("")
        self.retry_btn.configure(state="disabled")
        thread = threading.Thread(target=self._run_update, daemon=True)
        thread.start()

    def _run_update(self) -> None:
        try:
            game_dir = Path(__file__).resolve().parent
            self.set_status("Проверка актуальной версии на GitHub...")
            release = fetch_latest_release_info()
            if not release.download_url:
                raise VersionError(
                    "Не найдена ссылка на zip-архив в релизе. "
                    "Проверьте RELEASE_ASSET_NAME в config.py."
                )

            with tempfile.TemporaryDirectory(prefix="game_updater_") as tmp_dir_str:
                tmp_dir = Path(tmp_dir_str)
                archive_path = tmp_dir / "update.zip"
                extract_dir = tmp_dir / "extracted"

                self.set_status("Загрузка обновления...")
                self._download_with_progress(release.download_url, archive_path)

                self.set_status("Распаковка архива...")
                self._extract_archive(archive_path, extract_dir)

                self.set_status("Установка обновления...")
                self._install_files(extract_dir, game_dir)

            self.set_status("Сохранение версии...")
            self._write_local_version(release.version)

            self.set_progress(100)
            self.set_status("Готово. Запуск игры...")
            self._start_game(game_dir)
            self.root.after(800, self.root.destroy)

        except Exception as exc:
            logging.exception("Update failed")
            self.set_error(f"Ошибка обновления: {exc}")
            self.set_status("Обновление не завершено")

    def _download_with_progress(self, url: str, target_path: Path) -> None:
        try:
            with requests.get(
                url,
                stream=True,
                timeout=config.REQUEST_TIMEOUT_SECONDS,
                headers={"Accept": "application/octet-stream"},
            ) as response:
                if response.status_code != 200:
                    raise RuntimeError(
                        f"Не удалось скачать файл. HTTP {response.status_code}: {response.text[:200]}"
                    )

                total = int(response.headers.get("Content-Length", "0"))
                downloaded = 0
                with target_path.open("wb") as fp:
                    for chunk in response.iter_content(chunk_size=config.DOWNLOAD_CHUNK_SIZE):
                        if not chunk:
                            continue
                        fp.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            percent = downloaded * 100 / total
                            self.set_progress(percent * 0.7)  # 0..70 for download
        except requests.RequestException as exc:
            raise RuntimeError(f"Проблема сети при скачивании: {exc}") from exc

    def _extract_archive(self, archive_path: Path, extract_dir: Path) -> None:
        try:
            with ZipFile(archive_path, "r") as zf:
                zf.extractall(extract_dir)
            self.set_progress(80)
        except BadZipFile as exc:
            raise RuntimeError("Архив повреждён или не является zip") from exc

    def _install_files(self, source_root: Path, target_root: Path) -> None:
        # If archive has single top-level folder, use it as source
        children = [p for p in source_root.iterdir()]
        if len(children) == 1 and children[0].is_dir():
            source_root = children[0]

        for src in source_root.rglob("*"):
            rel = src.relative_to(source_root)
            if not rel.parts:
                continue

            if rel.parts[0].lower() in {name.lower() for name in config.PRESERVE_DIRS}:
                # Keep user's own data untouched
                continue

            dst = target_root / rel
            if src.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
                continue

            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src, dst)
            except PermissionError as exc:
                raise RuntimeError(f"Нет прав на запись: {dst}") from exc
            except OSError as exc:
                raise RuntimeError(f"Не удалось заменить файл: {dst}. {exc}") from exc

        self.set_progress(95)

    def _write_local_version(self, version: str) -> None:
        payload = {"version": version}
        config.LOCAL_VERSION_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _start_game(self, game_dir: Path) -> None:
        if getattr(sys, "frozen", False):
            game_exe = game_dir / config.GAME_EXE_NAME
            if game_exe.exists():
                subprocess.Popen([str(game_exe)], cwd=str(game_dir), close_fds=True)
            else:
                raise RuntimeError(f"Не найден исполняемый файл игры: {game_exe.name}")
        else:
            # Dev mode: launch app.py again
            subprocess.Popen([sys.executable, str(game_dir / "app.py")], cwd=str(game_dir), close_fds=True)

    def run(self) -> None:
        self.start_update()
        self.root.mainloop()


def main() -> None:
    ui = UpdaterUI()
    ui.run()


if __name__ == "__main__":
    main()
