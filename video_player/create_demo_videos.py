#!/usr/bin/env python3
"""
Demo Script - Creates sample test videos for testing the video player
"""

import os
import cv2
import numpy as np


def create_test_video(filepath, duration_seconds=5, fps=30, text="Test Video"):
    """
    Create a simple test video with text
    
    Args:
        filepath: Path to save the video
        duration_seconds: Duration of the video in seconds
        fps: Frames per second
        text: Text to display on the video
    """
    width, height = 640, 480
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
    print(f"Created: {filepath}")


def main():
    """Create demo videos for all channels"""
    root_folder = 'freevideos'
    
    # Ensure folder structure exists
    if not os.path.exists(root_folder):
        os.makedirs(root_folder)
        for i in range(1, 4):
            os.makedirs(os.path.join(root_folder, f'channel{i}'), exist_ok=True)
    
    print("Creating demo videos...")
    print()
    
    # Create videos for each channel
    for channel_num in range(1, 4):
        channel_path = os.path.join(root_folder, f'channel{channel_num}')
        
        # Create 3 videos per channel
        for video_num in range(1, 4):
            filename = f"video_{video_num}.mp4"
            filepath = os.path.join(channel_path, filename)
            text = f"Channel {channel_num} - Video {video_num}"
            create_test_video(filepath, duration_seconds=3, text=text)
    
    print()
    print("Demo videos created successfully!")
    print(f"Total: 9 videos (3 per channel)")
    print()
    print("Now you can run: python3 video_player.py")


if __name__ == '__main__':
    main()
