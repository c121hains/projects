# Video Player

A Python-based video player that plays video files from organized channel subfolders with keyboard navigation.

## Features

- Plays video files with extensions: `.mkv`, `.avi`, `.mp4`
- Organizes videos in channel subfolders (`channel1`, `channel2`, `channel3`)
- Sequential playback with automatic looping
- Keyboard controls for channel switching
- Starts with `channel1` by default

## Directory Structure

```
freevideos/
├── channel1/
│   ├── video1.mp4
│   ├── video2.mkv
│   └── video3.avi
├── channel2/
│   └── ...
└── channel3/
    └── ...
```

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Create the folder structure with your video files:

```bash
mkdir -p freevideos/channel1 freevideos/channel2 freevideos/channel3
```

2. Add your video files (`.mkv`, `.avi`, `.mp4`) to the channel folders

3. Run the video player:

```bash
python video_player.py
```

Or specify a custom root folder:

```bash
python video_player.py /path/to/your/videos
```

## Keyboard Controls

- **DOWN Arrow**: Switch to next channel (channel1 → channel2 → channel3 → channel1)
- **UP Arrow**: Switch to previous channel (channel1 → channel3 → channel2 → channel1)
- **ESC or Q**: Quit the application

## Behavior

- Videos play sequentially by filename within each channel
- When all videos in a channel finish, playback loops back to the first video
- Switching channels starts playing the first video from the selected channel
- Videos are sorted alphabetically by filename

## Requirements

- Python 3.7+
- pygame 2.5.2
- opencv-python 4.8.1.78

## Troubleshooting

If the video player doesn't start:
- Ensure all dependencies are installed
- Check that video files are in the correct format (MKV, AVI, MP4)
- Verify the folder structure exists

If videos don't play:
- Check that the video codec is supported by OpenCV
- Try re-encoding problematic videos
