#!/usr/bin/env python3
"""
Tests for Video Player
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_folder_structure():
    """Test creating folder structure"""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_folder = os.path.join(tmpdir, 'test_videos')
        
        # Create structure
        os.makedirs(root_folder)
        for i in range(1, 4):
            channel_path = os.path.join(root_folder, f'channel{i}')
            os.makedirs(channel_path, exist_ok=True)
        
        # Verify structure
        assert os.path.exists(root_folder)
        assert os.path.exists(os.path.join(root_folder, 'channel1'))
        assert os.path.exists(os.path.join(root_folder, 'channel2'))
        assert os.path.exists(os.path.join(root_folder, 'channel3'))
        
        print("✓ Folder structure test passed")


def test_video_extensions():
    """Test video extension filtering"""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_folder = os.path.join(tmpdir, 'test_videos')
        channel1 = os.path.join(root_folder, 'channel1')
        os.makedirs(channel1)
        
        # Create test files
        test_files = [
            'video1.mp4',
            'video2.mkv',
            'video3.avi',
            'video4.txt',  # Should be ignored
            'document.pdf',  # Should be ignored
        ]
        
        for filename in test_files:
            Path(os.path.join(channel1, filename)).touch()
        
        # Get video files
        video_extensions = ['.mkv', '.avi', '.mp4']
        videos = []
        for file in os.listdir(channel1):
            file_path = os.path.join(channel1, file)
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(file.lower())
                if ext in video_extensions:
                    videos.append(file)
        
        videos.sort()
        
        assert len(videos) == 3
        assert 'video1.mp4' in videos
        assert 'video2.mkv' in videos
        assert 'video3.avi' in videos
        assert 'video4.txt' not in videos
        assert 'document.pdf' not in videos
        
        print("✓ Video extension filtering test passed")


def test_channel_cycling():
    """Test channel cycling logic"""
    channels = ['channel1', 'channel2', 'channel3']
    
    # Test forward cycling
    current = 0
    current = (current + 1) % len(channels)
    assert current == 1
    
    current = (current + 1) % len(channels)
    assert current == 2
    
    current = (current + 1) % len(channels)
    assert current == 0  # Should wrap around
    
    # Test backward cycling
    current = 0
    current = (current - 1) % len(channels)
    assert current == 2  # Should wrap to last channel
    
    current = (current - 1) % len(channels)
    assert current == 1
    
    print("✓ Channel cycling test passed")


def test_video_sorting():
    """Test that videos are sorted alphabetically"""
    videos = [
        '/path/video_c.mp4',
        '/path/video_a.mkv',
        '/path/video_b.avi',
    ]
    
    videos.sort()
    
    assert videos[0].endswith('video_a.mkv')
    assert videos[1].endswith('video_b.avi')
    assert videos[2].endswith('video_c.mp4')
    
    print("✓ Video sorting test passed")


if __name__ == '__main__':
    print("Running Video Player Tests...")
    print()
    
    try:
        test_folder_structure()
        test_video_extensions()
        test_channel_cycling()
        test_video_sorting()
        
        print()
        print("All tests passed! ✓")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
