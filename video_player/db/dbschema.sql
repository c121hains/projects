
-- Enable FK constraints per connection (do in code after connect):
-- PRAGMA foreign_keys = ON;

-- Channels table (if you don't have it already)
CREATE TABLE IF NOT EXISTS channels (
    Id INTEGER PRIMARY KEY,
    Name TEXT NOT NULL UNIQUE,
    Description TEXT DEFAULT ''
);

-- Videos table: one row per physical file
CREATE TABLE IF NOT EXISTS videos (
    Id INTEGER PRIMARY KEY,
    ChannelId INTEGER NOT NULL,
    Path TEXT NOT NULL UNIQUE,              -- absolute or canonical path
    FileName TEXT NOT NULL,
    DurationSeconds REAL NOT NULL,          -- from ffprobe, in seconds
    SizeBytes INTEGER,                      -- file size at scan time
    ModifiedAt TEXT,                        -- ISO8601 timestamp (filesystem mtime)
    ScannedAt TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ChannelId) REFERENCES channels(Id) ON DELETE CASCADE
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_videos_channel ON videos(ChannelId);
CREATE UNIQUE INDEX IF NOT EXISTS idx_videos_path ON videos(Path);
