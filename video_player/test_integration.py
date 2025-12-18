#!/usr/bin/env python3
"""
Integration Test - Tests video player with actual video files
"""

import os
import sys

# Set SDL to use dummy video driver for headless testing
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_video_player_initialization():
    """Test that video player can be initialized"""
    try:
        from video_player import VideoPlayer
        
        # Create player with test folder
        player = VideoPlayer('freevideos')
        
        # Check initial state
        assert player.root_folder == 'freevideos'
        assert player.channels == ['channel1', 'channel2', 'channel3']
        assert player.current_channel_index == 0
        assert len(player.video_extensions) == 3
        
        print("✓ Video player initialization test passed")
        return True
    except Exception as e:
        print(f"✗ Video player initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_video_loading():
    """Test that videos are loaded correctly"""
    try:
        from video_player import VideoPlayer
        
        player = VideoPlayer('freevideos')
        
        # Check that videos were loaded
        assert len(player.videos_in_channel) > 0, "No videos loaded"
        assert player.current_channel_index == 0, "Not on first channel"
        
        # Check video paths
        for video_path in player.videos_in_channel:
            assert os.path.exists(video_path), f"Video file doesn't exist: {video_path}"
            assert video_path.endswith(('.mp4', '.mkv', '.avi')), f"Invalid extension: {video_path}"
        
        print(f"✓ Video loading test passed ({len(player.videos_in_channel)} videos found)")
        return True
    except Exception as e:
        print(f"✗ Video loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_channel_switching():
    """Test channel switching logic"""
    try:
        from video_player import VideoPlayer
        
        player = VideoPlayer('freevideos')
        
        initial_channel = player.current_channel_index
        assert initial_channel == 0, "Should start on channel 0"
        
        # Test forward switching
        player.load_channel(1)
        assert player.current_channel_index == 1, "Should be on channel 1"
        
        player.load_channel(2)
        assert player.current_channel_index == 2, "Should be on channel 2"
        
        # Test wrap around
        new_index = (player.current_channel_index + 1) % len(player.channels)
        assert new_index == 0, "Should wrap to channel 0"
        
        print("✓ Channel switching test passed")
        return True
    except Exception as e:
        print(f"✗ Channel switching failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_video_extensions_filtering():
    """Test that only valid video extensions are loaded"""
    try:
        from video_player import VideoPlayer
        
        player = VideoPlayer('freevideos')
        
        # All loaded videos should have valid extensions
        for video_path in player.videos_in_channel:
            ext = os.path.splitext(video_path)[1].lower()
            assert ext in player.video_extensions, f"Invalid extension {ext} for {video_path}"
        
        print("✓ Video extension filtering test passed")
        return True
    except Exception as e:
        print(f"✗ Video extension filtering failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_channels_have_videos():
    """Test that all channels have videos"""
    try:
        from video_player import VideoPlayer
        
        player = VideoPlayer('freevideos')
        
        for i in range(len(player.channels)):
            videos = player.get_videos_from_channel(i)
            assert len(videos) > 0, f"Channel {i} ({player.channels[i]}) has no videos"
            print(f"  Channel {player.channels[i]}: {len(videos)} videos")
        
        print("✓ All channels have videos test passed")
        return True
    except Exception as e:
        print(f"✗ All channels have videos test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("Running Video Player Integration Tests...")
    print()
    
    # Check if demo videos exist
    if not os.path.exists('freevideos/channel1/video_1.mp4'):
        print("Demo videos not found. Creating them first...")
        import create_demo_videos
        create_demo_videos.main()
        print()
    
    results = []
    
    results.append(test_video_player_initialization())
    results.append(test_video_loading())
    results.append(test_channel_switching())
    results.append(test_video_extensions_filtering())
    results.append(test_all_channels_have_videos())
    
    print()
    
    if all(results):
        print("All integration tests passed! ✓")
        sys.exit(0)
    else:
        print("Some tests failed! ✗")
        sys.exit(1)
