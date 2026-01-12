#!/usr/bin/env python3
"""
Video Player - Plays video files with audio from organized channel subfolders
Supports MKV, AVI, and MP4 file formats
"""

import os
import sys
import time
import pygame
from ffpyplayer.player import MediaPlayer
from pathlib import Path
from DBHandler import DbHandler
from datetime import datetime
from video_duration_sum import sum_folder_durations_seconds, report_folder_durations
from channel_live import time_since_golive, time_to_seek_in_channel

class VideoPlayer:
    """Video player that manages channel-based video playback"""
    
    # Class constants
    DEFAULT_WIDTH = 800
    DEFAULT_HEIGHT = 600
    MAX_FPS = 120
    DEFAULT_FPS = 30
    
    def __init__(self, root_folder='freevideos'):
        """
        Initialize the video player
        
        Args:
            root_folder: Root folder containing channel subfolders
        """
        # Get the current date and time
        current_datetime = datetime.now()
        
        pygame.init()
        pygame.font.init()
        
        # Set up display
        self.screen = pygame.display.set_mode((self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Video Player")
        
        # Configuration
        self.root_folder = root_folder
        self.channels = ['channel1', 'channel2', 'channel3']
        self.current_channel_index = 0
        self.current_video_index = 0
        self.video_extensions = ['.mkv', '.avi', '.mp4']
        
        # Clock for frame rate
        self.clock = pygame.time.Clock()
        
        # Video state
        self.media_player = None
        self.is_playing = False
        self.videos_in_channel = []
        self.current_video_fps = self.DEFAULT_FPS
        
        self.db = DbHandler(".\\db\\showsequencer.db", enable_wal=True)
        self.db.init_db()
        print("Database initialized.")
        print("All:", self.db.list_channels())

        # Scan durations for your root folder (e.g., 'freevideos') before launching the player
        self.summary = self.db.scan_and_store_durations(root_folder, channel_names=['channel1', 'channel2', 'channel3'],
                                            recursive=False, use_stream_duration=False)

        print(f"Files scanned: {self.summary['files_scanned']}")
        print(f"Total duration: {self.summary['total_seconds']:.3f} s "
            f"({self.summary['total_seconds']/60:.2f} min, {self.summary['total_seconds']/3600:.2f} h)")
        for ch, secs in self.summary['by_channel'].items():
            print(f"  {ch}: {secs:.3f} s ({secs/60:.2f} min)")

        # Initialize first channel
        self.load_channel(self.current_channel_index)
        
    def get_channel_path(self, channel_index):
        """Get the path for a specific channel"""
        channel_name = self.channels[channel_index]
        return os.path.join(self.root_folder, channel_name)
    
    def get_videos_from_channel(self, channel_index):
        """
        Get sorted list of video files from a channel
        
        Args:
            channel_index: Index of the channel
            
        Returns:
            List of video file paths sorted by name
        """
        channel_path = self.get_channel_path(channel_index)
        
        if not os.path.exists(channel_path):
            print(f"Warning: Channel path '{channel_path}' does not exist")
            return []

        videos = []
        for file in os.listdir(channel_path):
            file_path = os.path.join(channel_path, file)
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(file.lower())
                if ext in self.video_extensions:
                    videos.append(file_path)
        
        # Sort by filename
        videos.sort()
        return videos
    
    def load_channel(self, channel_index):
        """Load videos from a specific channel"""
        self.current_channel_index = channel_index
        channel_results = self.db.list_videos_by_channelId(channel_index+1)
        
        self.videos_in_channel = [row["Path"] for row in channel_results] #self.get_videos_from_channel(channel_index)
        video_durations = [row["DurationSeconds"] for row in channel_results]

        channel_duration = self.summary['by_channel'][self.channels[channel_index]]
        time_to_play_in_channel = time_to_seek_in_channel(channel_duration)  # Example channel duration of 1 hour
        print(f"\nChannel: {self.channels[channel_index]}  |  Channel duration: {channel_duration:.3f} seconds  |  Time to play: {time_to_play_in_channel:.3f} seconds")

        self.current_video_index = 0
        timeIndex = 0
        time_to_play_in_video = time_to_play_in_channel # initialize to total time to play in channel in case first video is longer than time to play
        for video_duration in video_durations:
            timeIndex += video_duration
            if time_to_play_in_channel < timeIndex:
                break
            self.current_video_index += 1
            time_to_play_in_video -= video_duration
                            
        if self.videos_in_channel:
            self.play_video(self.current_video_index, time_to_play_in_video)
        else:
            print(f"No videos found in {self.channels[channel_index]}")
            self.show_no_video_message()
    
    def play_video(self, video_index, start_time=0):
        """
        Play a specific video by index
        
        Args:
            video_index: Index of the video in current channel
        """
        if not self.videos_in_channel:
            return
        
        # Clean up previous video
        if self.media_player:
            self.media_player.close_player()
            self.media_player = None
        
        self.current_video_index = video_index
        video_path = self.videos_in_channel[video_index]
        
        #print(f"Playing: {os.path.basename(video_path)} starting at {start_time} seconds")
        
        try:
            # Create MediaPlayer with audio enabled
            self.media_player = MediaPlayer(
                video_path, 
                ff_opts={
                    'paused': False, 
                    'autoexit': False,
                    'ss': start_time}  # Start at specified time
            )

            # Get video metadata
            metadata = self.media_player.get_metadata()
            frame_rate = metadata.get('frame_rate', (self.DEFAULT_FPS, 1))
            
            # Calculate FPS from frame rate tuple (numerator, denominator)
            if frame_rate and isinstance(frame_rate, tuple) and len(frame_rate) == 2 and frame_rate[1] != 0:
                self.current_video_fps = frame_rate[0] / frame_rate[1]
            else:
                self.current_video_fps = self.DEFAULT_FPS
            
            # Limit to max FPS
            if self.current_video_fps == 0 or self.current_video_fps > self.MAX_FPS:
                self.current_video_fps = self.DEFAULT_FPS
            
            self.is_playing = True
        except Exception as e:
            print(f"Error playing video: {e}")
            # Try next video
            self.play_next_video()
    
    def play_next_video(self):
        """Play the next video in sequence (loop back to first)"""
        if not self.videos_in_channel:
            return
        
        next_index = (self.current_video_index + 1) % len(self.videos_in_channel)
        self.play_video(next_index)
    
    def switch_channel(self, direction):
        """
        Switch to a different channel
        
        Args:
            direction: 1 for next channel (down), -1 for previous channel (up)
        """
        new_index = (self.current_channel_index + direction) % len(self.channels)
        print(f"Switching to {self.channels[new_index]}")
        self.load_channel(new_index)
    
    def show_no_video_message(self):
        """Display a message when no videos are available"""
        try:
            font = pygame.font.Font(None, 36)
            self.screen.fill((0, 0, 0))
            
            channel_name = self.channels[self.current_channel_index]
            text = font.render(f"No videos in {channel_name}", True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.screen.get_width() // 2, 
                                              self.screen.get_height() // 2))
            self.screen.blit(text, text_rect)
            
            instruction = pygame.font.Font(None, 24)
            inst_text = instruction.render("Use UP/DOWN arrows to switch channels", 
                                          True, (200, 200, 200))
            inst_rect = inst_text.get_rect(center=(self.screen.get_width() // 2, 
                                                   self.screen.get_height() // 2 + 50))
            self.screen.blit(inst_text, inst_rect)
            
            pygame.display.flip()
        except Exception as e:
            print(f"Error displaying message: {e}")
    
    def update_video_frame(self):
        """Read and display the current video frame"""
        if not self.is_playing or not self.media_player:
            return True
        
        # Get frame from media player
        frame, val = self.media_player.get_frame()
        
        if val == 'eof':
            # Video finished, play next
            self.play_next_video()
            return True
        
        if frame is None:
            # No frame available yet, continue
            return True
        
        # Extract image and timestamp
        img, pts = frame
        
        # Get frame dimensions
        frame_width, frame_height = img.get_size()
        frame_data = img.to_bytearray()[0]
        
        # Convert frame data to pygame surface
        # ffpyplayer returns RGB24 format by default
        surface = pygame.image.frombuffer(frame_data, (frame_width, frame_height), 'RGB')
        
        # Resize frame to fit screen while maintaining aspect ratio
        screen_width, screen_height = self.screen.get_size()
        
        # Calculate scaling
        scale = min(screen_width / frame_width, screen_height / frame_height)
        new_width = int(frame_width * scale)
        new_height = int(frame_height * scale)
        
        if scale != 1.0:
            surface = pygame.transform.scale(surface, (new_width, new_height))
        
        # Center the video on screen
        x = (screen_width - new_width) // 2
        y = (screen_height - new_height) // 2
        
        self.screen.fill((0, 0, 0))
        self.screen.blit(surface, (x, y))
        pygame.display.flip()
        
        # Sleep only if recommended by ffpyplayer for sync
        # This is necessary to maintain proper audio/video synchronization
        # val represents the delay needed before fetching the next frame
        if val > 0:
            # Cap sleep time to avoid UI freezing
            time.sleep(min(val, 0.1))
        
        return True
    
    def handle_events(self):
        """Handle keyboard and window events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    return False
                
                elif event.key == pygame.K_DOWN:
                    # Switch to next channel
                    self.switch_channel(1)
                
                elif event.key == pygame.K_UP:
                    # Switch to previous channel
                    self.switch_channel(-1)
        
        return True
    
    def run(self):
        """Main loop for the video player"""
        running = True
        
        print("Video Player Started")
        print("Controls:")
        print("  UP Arrow    - Previous channel")
        print("  DOWN Arrow  - Next channel")
        print("  ESC or Q    - Quit")
        print()
        
        while running:
            running = self.handle_events()
            if running:
                self.update_video_frame()
                # Use minimal tick to keep the UI responsive
                # The actual frame timing is handled by time.sleep in update_video_frame
                self.clock.tick(60)
        
        # Cleanup
        if self.media_player:
            self.media_player.close_player()
        pygame.quit()
        print("Video Player Closed")


def main():
    """Main entry point"""
    # Check if root folder is provided as argument
    root_folder = 'freevideos'
    if len(sys.argv) > 1:
        root_folder = sys.argv[1]
    
    # Create root folder structure if it doesn't exist
    if not os.path.exists(root_folder):
        print(f"Creating folder structure: {root_folder}/channel[1-3]")
        os.makedirs(root_folder)
        for i in range(1, 4):
            channel_path = os.path.join(root_folder, f'channel{i}')
            os.makedirs(channel_path, exist_ok=True)
        print("Folder structure created. Please add video files (.mkv, .avi, .mp4)")
        print("to the channel folders and run the player again.")
        return

          
    # Start the player
    try:
        player = VideoPlayer(root_folder)
        player.run()
    except KeyboardInterrupt:
        print("\nPlayer interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
