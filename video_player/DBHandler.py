
import sqlite3
from pathlib import Path
import subprocess
import shlex
import shutil
import time
from typing import Optional, Iterable

class DbHandler:
    def __init__(self, db_path: str | Path = "showsequencer.db", enable_wal: bool = False):
        self.db_path = Path(db_path)
        self.enable_wal = enable_wal

        # Ensure parent folder exists (e.g., .\db\)
        if self.db_path.parent and not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        if self.enable_wal:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    # ------------------- Schema -------------------
    def init_db(self) -> None:
        with self._connect() as conn:
            # Channels (keep existing if you already have it)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    Id INTEGER PRIMARY KEY,
                    Name TEXT NOT NULL UNIQUE,
                    Description TEXT DEFAULT ''
                );
            """)
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_channels_name ON channels(Name);")

            # Videos
            conn.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    Id INTEGER PRIMARY KEY,
                    ChannelId INTEGER NOT NULL,
                    Path TEXT NOT NULL UNIQUE,
                    FileName TEXT NOT NULL,
                    DurationSeconds REAL NOT NULL,
                    SizeBytes INTEGER,
                    ModifiedAt TEXT,
                    ScannedAt TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ChannelId) REFERENCES channels(Id) ON DELETE CASCADE
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_videos_channel ON videos(ChannelId);")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_videos_path ON videos(Path);")
            conn.commit()

    # ------------------- Channels -------------------
    def list_channels(self) -> list[dict]:
        with self._connect() as conn:
            return [dict(r) for r in conn.execute("SELECT Name FROM channels ORDER BY Name;").fetchall()]

    def get_or_create_channel(self, name: str, description: str = "") -> int:
        with self._connect() as conn:
            # Try get
            row = conn.execute("SELECT Id FROM channels WHERE Name = ?;", (name,)).fetchone()
            if row:
                return row["Id"]
            # Create
            cur = conn.execute(
                "INSERT INTO channels (Name, Description) VALUES (?, ?);",
                (name, description)
            )
            conn.commit()
            return cur.lastrowid

    # ------------------- ffprobe -------------------
    def ffprobe_duration_seconds(self, path: Path, use_stream_duration: bool = False) -> Optional[float]:
        """
        Returns duration in seconds using ffprobe or None if ffprobe is missing or fails.
        - Container duration: format=duration
        - First video stream duration: stream=duration with -select_streams v:0
        """
        if not shutil.which("ffprobe"):
            return None
        # Build command
        if use_stream_duration:
            cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=duration ' \
                  f'-of default=noprint_wrappers=1:nokey=1 "{path}"'
        else:
            cmd = f'ffprobe -v error -show_entries format=duration ' \
                  f'-of default=noprint_wrappers=1:nokey=1 "{path}"'
        try:
            out = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
            txt = out.decode().strip()
            return float(txt) if txt else None
        except Exception:
            return None

    # ------------------- Videos -------------------
    def upsert_video(self,
                     channel_id: int,
                     path: Path,
                     duration_seconds: float,
                     size_bytes: Optional[int],
                     modified_at_iso: Optional[str]) -> int:
        """
        Insert or update a single video row identified by Path (UNIQUE).
        Returns the row id (Id).
        """
        with self._connect() as conn:
            sql = """
            INSERT INTO videos (ChannelId, Path, FileName, DurationSeconds, SizeBytes, ModifiedAt, ScannedAt)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(Path) DO UPDATE SET
                ChannelId = excluded.ChannelId,
                FileName = excluded.FileName,
                DurationSeconds = excluded.DurationSeconds,
                SizeBytes = excluded.SizeBytes,
                ModifiedAt = excluded.ModifiedAt,
                ScannedAt = CURRENT_TIMESTAMP;
            """
            file_name = path.name
            cur = conn.execute(sql, (
                channel_id, str(path), file_name, float(duration_seconds),
                size_bytes, modified_at_iso
            ))
            conn.commit()
            # Get Id (works both for insert and update)
            row = conn.execute("SELECT Id FROM videos WHERE Path = ?;", (str(path),)).fetchone()
            return int(row["Id"]) if row else -1

    def scan_and_store_durations(self,
                                 root_folder: str | Path,
                                 channel_names: Iterable[str] | None = None,
                                 recursive: bool = False,
                                 use_stream_duration: bool = False) -> dict:
        """
        Scans 'root_folder' for videos, grouped by channel subfolders (e.g., channel1/2/3),
        probes duration via ffprobe, and upserts into the 'videos' table.
        Returns a summary dict: { 'total_seconds': float, 'by_channel': {name: seconds}, 'files_scanned': int }.
        """
        root = Path(root_folder)
        total = 0.0
        files_scanned = 0
        by_channel: dict[str, float] = {}

        # Default channel names: discover subfolders that look like channels if not provided
        if channel_names is None:
            channel_names = sorted([p.name for p in root.iterdir() if p.is_dir()])

        for ch_name in channel_names:
            ch_path = root / ch_name
            if not ch_path.exists() or not ch_path.is_dir():
                continue

            # Ensure channel row
            ch_id = self.get_or_create_channel(ch_name, description=f"Auto-discovered in {root}")

            # Collect files
            video_exts = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}
            files = (ch_path.rglob("*") if recursive else ch_path.glob("*"))
            channel_total = 0.0

            for f in files:
                if not f.is_file() or f.suffix.lower() not in video_exts:
                    continue

                # ffprobe duration
                dur = self.ffprobe_duration_seconds(f, use_stream_duration=use_stream_duration)
                if dur is None:
                    # Skip files we couldn't probe
                    continue

                # File attributes
                try:
                    stat = f.stat()
                    size_bytes = stat.st_size
                    # Convert mtime to ISO8601 (UTC or local; here we use time.strftime on localtime)
                    modified_at_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(stat.st_mtime))
                except Exception:
                    size_bytes = None
                    modified_at_iso = None

                # Upsert row
                self.upsert_video(ch_id, f, dur, size_bytes, modified_at_iso)

                channel_total += dur
                total += dur
                files_scanned += 1

            by_channel[ch_name] = channel_total

        return {
            "total_seconds": total,
            "by_channel": by_channel,
            "files_scanned": files_scanned
        }

    # ------------------- Queries -------------------
    def total_video_seconds(self) -> float:
        with self._connect() as conn:
            row = conn.execute("SELECT COALESCE(SUM(DurationSeconds), 0.0) AS total FROM videos;").fetchone()
            return float(row["total"])

    def channel_video_seconds(self, channel_name: str) -> float:
        with self._connect() as conn:
            row = conn.execute("""
                SELECT COALESCE(SUM(v.DurationSeconds), 0.0) AS total
                FROM videos v
                JOIN channels c ON c.Id = v.ChannelId
                WHERE c.Name = ?;
            """, (channel_name,)).fetchone()
            return float(row["total"])

    def list_videos(self) -> list[dict]:
        with self._connect() as conn:
            sql = """
            SELECT v.Id, c.Name AS Channel, v.FileName, v.Path, v.DurationSeconds,
                   v.SizeBytes, v.ModifiedAt, v.ScannedAt
            FROM videos v
            JOIN channels c ON c.Id = v.ChannelId
            ORDER BY c.Name, v.FileName;
            """
            return [dict(r) for r in conn.execute(sql).fetchall()]
