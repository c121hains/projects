# Video Player Usage Examples

## Quick Start

### 1. Install Dependencies
```bash
cd video_player
pip install -r requirements.txt
```

### 2. Run with Demo Videos
```bash
# Create demo videos (creates 3 videos per channel)
python create_demo_videos.py

# Run the player
python video_player.py
```

## Usage Scenarios

### Scenario 1: Use with Existing Videos

If you already have video files:

```bash
# Create folder structure
mkdir -p freevideos/channel1 freevideos/channel2 freevideos/channel3

# Copy your videos to the channels
cp /path/to/videos/*.mp4 freevideos/channel1/
cp /path/to/more/*.mkv freevideos/channel2/
cp /path/to/other/*.avi freevideos/channel3/

# Run the player
python video_player.py
```

### Scenario 2: Custom Root Folder

```bash
# Use a different root folder
python video_player.py /path/to/my/videos
```

The folder should have the structure:
```
/path/to/my/videos/
├── channel1/
│   ├── video1.mp4
│   └── video2.mkv
├── channel2/
│   └── ...
└── channel3/
    └── ...
```

## Keyboard Controls

| Key | Action |
|-----|--------|
| **DOWN Arrow** | Switch to next channel (channel1 → channel2 → channel3 → channel1) |
| **UP Arrow** | Switch to previous channel (channel1 → channel3 → channel2 → channel1) |
| **ESC or Q** | Quit the application |

## Video Playback Behavior

1. **Start**: Player starts with channel1 and plays the first video (alphabetically)
2. **Sequential Play**: Videos play in alphabetical order by filename
3. **Auto Loop**: When the last video finishes, it loops back to the first video
4. **Channel Switch**: Switching channels immediately starts playing the first video from the new channel

## Supported Formats

- **MKV** (Matroska Video)
- **AVI** (Audio Video Interleave)
- **MP4** (MPEG-4 Part 14)

Files with other extensions are ignored.

## Testing

Run the unit tests:
```bash
python test_video_player.py
```

Run integration tests:
```bash
python test_integration.py
```

## Troubleshooting

### Problem: No module named 'pygame'
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Problem: Videos not playing
**Solution**: Check video codec compatibility
```bash
# Try re-encoding with ffmpeg
ffmpeg -i input.mkv -c:v libx264 -c:a aac output.mp4
```

### Problem: Folder structure error
**Solution**: Ensure folder structure exists
```bash
mkdir -p freevideos/channel{1,2,3}
```

## Example Workflow

```bash
# 1. Setup
cd video_player
pip install -r requirements.txt

# 2. Create demo content
python create_demo_videos.py

# 3. Run player
python video_player.py

# 4. Test it
#    - Press DOWN to switch to channel2
#    - Press UP to go back to channel1
#    - Wait for videos to loop
#    - Press Q to quit
```
