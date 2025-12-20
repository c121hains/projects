#!/usr/bin/env python3
"""
Demo Script - Creates sample test videos with audio for testing the video player
"""

import os
import subprocess
import sys


def create_test_video_with_audio(filepath, duration_seconds=5, text="Test Video"):
    """
    Create a simple test video with text and audio using ffmpeg
    
    Args:
        filepath: Path to save the video
        duration_seconds: Duration of the video in seconds
        text: Text to display on the video
    """
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: ffmpeg is not installed or not in PATH")
        print("Please install ffmpeg to create demo videos with audio")
        sys.exit(1)
    
    # Create a temporary video without audio first
    temp_video = filepath + '.temp.mp4'
    
    # Generate video with color background and text overlay using ffmpeg
    # This creates a video with a gradient background and text
    try:
        # Create video with lavfi (libavfilter) - generates a test pattern with sine wave audio
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'color=c=blue:s=640x480:d={duration_seconds},format=rgb24',
            '-f', 'lavfi',
            '-i', f'sine=frequency=1000:duration={duration_seconds}',
            '-vf', f"drawtext=text='{text}':fontsize=40:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-shortest',
            filepath
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Warning: Could not create video with audio for {filepath}")
            print(f"Error: {result.stderr}")
            # Fallback: create without audio
            create_test_video_no_audio(filepath, duration_seconds, text)
        else:
            print(f"Created: {filepath} (with audio)")
            
    except Exception as e:
        print(f"Error creating video: {e}")
        # Fallback: create without audio
        create_test_video_no_audio(filepath, duration_seconds, text)


def create_test_video_no_audio(filepath, duration_seconds=5, text="Test Video"):
    """
    Fallback: Create a simple test video without audio using opencv
    
    Args:
        filepath: Path to save the video
        duration_seconds: Duration of the video in seconds
        text: Text to display on the video
    """
    try:
        import cv2
        import numpy as np
        
        print(f"Creating video without audio: {filepath}")
        
        width, height = 640, 480
        fps = 30
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        out = cv2.VideoWriter(filepath, fourcc, fps, (width, height))
        
        total_frames = duration_seconds * fps
        
        for frame_num in range(total_frames):
            # Create a frame with gradient background
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Create gradient effect
            for y in range(height):
                color_value = int(255 * (y / height))
                frame[y, :] = [color_value // 3, color_value // 2, color_value]
            
            # Add text
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(frame, text, (50, height // 2), font, 1.5, (255, 255, 255), 3)
            
            # Add frame counter
            time_text = f"Frame: {frame_num}/{total_frames}"
            cv2.putText(frame, time_text, (50, height - 50), font, 0.7, (200, 200, 200), 2)
            
            out.write(frame)
        
        out.release()
        print(f"Created: {filepath} (no audio)")
        
    except ImportError:
        print("Error: opencv-python not available for fallback video creation")
        print("Please install ffmpeg or opencv-python")
        sys.exit(1)


def main():
    """Create demo videos for all channels"""
    root_folder = 'freevideos'
    
    # Ensure folder structure exists
    if not os.path.exists(root_folder):
        os.makedirs(root_folder)
        for i in range(1, 4):
            os.makedirs(os.path.join(root_folder, f'channel{i}'), exist_ok=True)
    
    print("Creating demo videos with audio...")
    print()
    
    # Create videos for each channel
    for channel_num in range(1, 4):
        channel_path = os.path.join(root_folder, f'channel{channel_num}')
        
        # Create 3 videos per channel
        for video_num in range(1, 4):
            filename = f"video_{video_num}.mp4"
            filepath = os.path.join(channel_path, filename)
            text = f"Channel {channel_num} - Video {video_num}"
            create_test_video_with_audio(filepath, duration_seconds=3, text=text)
    
    print()
    print("Demo videos created successfully!")
    print(f"Total: 9 videos (3 per channel)")
    print()
    print("Now you can run: python3 video_player.py")


if __name__ == '__main__':
    main()
