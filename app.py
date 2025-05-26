import customtkinter as ctk
from tkinter import messagebox
import requests
import re
from datetime import timedelta
import threading
import time

# Optional imports for enhanced features
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import numpy as np
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from ttkbootstrap import Style
    TTKBOOTSTRAP_AVAILABLE = True
except ImportError:
    TTKBOOTSTRAP_AVAILABLE = False

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class AnimatedProgressBar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.canvas = ctk.CTkCanvas(self, height=8)
        self.canvas.pack(fill="x", padx=20, pady=10)
        
        self.progress = 0
        self.animation_id = None
        self.is_running = False
        
    def start(self):
        self.is_running = True
        self.animate()
        
    def stop(self):
        self.is_running = False
        if self.animation_id:
            self.after_cancel(self.animation_id)
        self.canvas.delete("all")
        
    def animate(self):
        if not self.is_running:
            return
            
        self.canvas.delete("all")
        width = self.canvas.winfo_width()
        if width > 1:
            # Create moving progress bar effect
            bar_width = int(width * 0.3)
            start_x = self.progress % width
            
            # Draw main progress bar
            self.canvas.create_rectangle(
                start_x, 2, start_x + bar_width, 6,
                fill="#3b82f6", outline=""
            )
            
            # Add glow effect
            if start_x + bar_width < width:
                self.canvas.create_rectangle(
                    start_x + bar_width, 2, start_x + bar_width + 20, 6,
                    fill="#60a5fa", outline=""
                )
        
        self.progress = (self.progress + 8) % (self.canvas.winfo_width() if self.canvas.winfo_width() > 1 else 300)
        self.animation_id = self.after(80, self.animate)

class StatsCard(ctk.CTkFrame):
    def __init__(self, master, title, value, icon="📊", color="#1f538d", **kwargs):
        super().__init__(master, corner_radius=15, **kwargs)
        
        # Icon and title frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        icon_label = ctk.CTkLabel(header_frame, text=icon, font=ctk.CTkFont(size=24))
        icon_label.pack(side="left")
        
        title_label = ctk.CTkLabel(header_frame, text=title, 
                                  font=ctk.CTkFont(size=14, weight="bold"),
                                  text_color=color)
        title_label.pack(side="left", padx=(10, 0))
        
        # Value
        self.value_label = ctk.CTkLabel(self, text=value, 
                                       font=ctk.CTkFont(size=20, weight="bold"))
        self.value_label.pack(pady=(0, 15))
        
    def update_value(self, new_value):
        self.value_label.configure(text=new_value)

class SpeedCard(ctk.CTkFrame):
    def __init__(self, master, speed, time_text, saved_text="", **kwargs):
        super().__init__(master, corner_radius=12, **kwargs)
        
        # Speed badge
        speed_frame = ctk.CTkFrame(self, corner_radius=20, height=35)
        speed_frame.pack(fill="x", padx=15, pady=(15, 10))
        speed_frame.pack_propagate(False)
        
        speed_label = ctk.CTkLabel(speed_frame, text=f"{speed}x", 
                                  font=ctk.CTkFont(size=16, weight="bold"))
        speed_label.pack(expand=True)
        
        # Time
        time_label = ctk.CTkLabel(self, text=time_text, 
                                 font=ctk.CTkFont(size=18, weight="bold"))
        time_label.pack(pady=(0, 5))
        
        # Saved time
        if saved_text:
            saved_label = ctk.CTkLabel(self, text=saved_text, 
                                     font=ctk.CTkFont(size=12),
                                     text_color="#4ade80")
            saved_label.pack(pady=(0, 15))
        else:
            ctk.CTkLabel(self, text="").pack(pady=(0, 15))

class YouTubePlaylistCalculator:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.geometry("1200x800")
        self.app.title("YouTube Playlist Time Calculator")
        
        # Center the window
        self.center_window()
        
        # Variables
        self.api_key = ""
        self.results_data = None
        
        # Create UI
        self.setup_ui()
        
        # Animation variables
        self.fade_in_progress = 0
        self.typing_animation_active = False
        
    def center_window(self):
        self.app.update_idletasks()
        width = 1200
        height = 800
        x = (self.app.winfo_screenwidth() // 2) - (width // 2)
        y = (self.app.winfo_screenheight() // 2) - (height // 2)
        self.app.geometry(f'{width}x{height}+{x}+{y}')
        
    def setup_ui(self):
        # Main container with padding
        main_container = ctk.CTkFrame(self.app, corner_radius=0, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header section
        self.create_header(main_container)
        
        # Content area with scrollable frame
        content_frame = ctk.CTkScrollableFrame(main_container, corner_radius=15)
        content_frame.pack(fill="both", expand=True, pady=(20, 0))
        
        # Input section
        self.create_input_section(content_frame)
        
        # Results section (initially hidden)
        self.results_section = ctk.CTkFrame(content_frame, corner_radius=15)
        self.create_results_section()
        
    def create_header(self, parent):
        header_frame = ctk.CTkFrame(parent, corner_radius=15, height=120)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Gradient-like effect with multiple frames
        gradient_frame = ctk.CTkFrame(header_frame, corner_radius=15, 
                                     fg_color=["#3b82f6", "#1e40af"])
        gradient_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Title with icon
        title_frame = ctk.CTkFrame(gradient_frame, fg_color="transparent")
        title_frame.pack(expand=True)
        
        icon_label = ctk.CTkLabel(title_frame, text="🎬", font=ctk.CTkFont(size=40))
        icon_label.pack(pady=(20, 5))
        
        title_label = ctk.CTkLabel(title_frame, text="YouTube Playlist Time Calculator",
                                  font=ctk.CTkFont(size=28, weight="bold"),
                                  text_color="white")
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(title_frame, 
                                     text="Calculate viewing time at different playback speeds",
                                     font=ctk.CTkFont(size=14),
                                     text_color="#e2e8f0")
        subtitle_label.pack(pady=(5, 20))
        
    def create_input_section(self, parent):
        input_frame = ctk.CTkFrame(parent, corner_radius=15)
        input_frame.pack(fill="x", pady=(20, 0))
        
        # API Key section with modern styling
        api_section = ctk.CTkFrame(input_frame, corner_radius=12)
        api_section.pack(fill="x", padx=20, pady=20)
        
        api_header = ctk.CTkLabel(api_section, text="🔑 API Configuration", 
                                 font=ctk.CTkFont(size=18, weight="bold"))
        api_header.pack(pady=(15, 10))
        
        self.api_key_var = ctk.StringVar()
        api_entry = ctk.CTkEntry(api_section, textvariable=self.api_key_var,
                               placeholder_text="Enter your YouTube Data API v3 key here...",
                               height=40, font=ctk.CTkFont(size=14),
                               show="*")
        api_entry.pack(fill="x", padx=20, pady=(0, 10))
        
        api_info = ctk.CTkLabel(api_section, 
                               text="💡 Get your free API key from Google Cloud Console → YouTube Data API v3",
                               font=ctk.CTkFont(size=12),
                               text_color="#64748b")
        api_info.pack(pady=(0, 15))
        
        # URL section
        url_section = ctk.CTkFrame(input_frame, corner_radius=12)
        url_section.pack(fill="x", padx=20, pady=(0, 20))
        
        url_header = ctk.CTkLabel(url_section, text="🔗 Playlist URL", 
                                 font=ctk.CTkFont(size=18, weight="bold"))
        url_header.pack(pady=(15, 10))
        
        self.url_var = ctk.StringVar()
        url_entry = ctk.CTkEntry(url_section, textvariable=self.url_var,
                               placeholder_text="Paste your YouTube playlist URL here...",
                               height=40, font=ctk.CTkFont(size=14))
        url_entry.pack(fill="x", padx=20, pady=(0, 15))
        
        # Range section with modern input styling
        range_section = ctk.CTkFrame(input_frame, corner_radius=12)
        range_section.pack(fill="x", padx=20, pady=(0, 20))
        
        range_header = ctk.CTkLabel(range_section, text="📊 Video Range (Optional)", 
                                   font=ctk.CTkFont(size=18, weight="bold"))
        range_header.pack(pady=(15, 10))
        
        range_inputs = ctk.CTkFrame(range_section, fg_color="transparent")
        range_inputs.pack(fill="x", padx=20)
        
        # Start input
        start_frame = ctk.CTkFrame(range_inputs)
        start_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(start_frame, text="Start from video #", 
                    font=ctk.CTkFont(size=14)).pack(pady=(10, 5))
        self.start_var = ctk.StringVar(value="1")
        start_entry = ctk.CTkEntry(start_frame, textvariable=self.start_var,
                                 height=35, justify="center")
        start_entry.pack(fill="x", padx=10, pady=(0, 10))
        
        # End input
        end_frame = ctk.CTkFrame(range_inputs)
        end_frame.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        ctk.CTkLabel(end_frame, text="End at video #", 
                    font=ctk.CTkFont(size=14)).pack(pady=(10, 5))
        self.end_var = ctk.StringVar()
        end_entry = ctk.CTkEntry(end_frame, textvariable=self.end_var,
                               placeholder_text="Last video",
                               height=35, justify="center")
        end_entry.pack(fill="x", padx=10, pady=(0, 10))
        
        range_info = ctk.CTkLabel(range_section, 
                                 text="💡 Leave end field empty to calculate until the last video",
                                 font=ctk.CTkFont(size=12),
                                 text_color="#64748b")
        range_info.pack(pady=(0, 15))
        
        # Calculate button with modern styling
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.calculate_btn = ctk.CTkButton(
            button_frame,
            text="🚀 Calculate Playlist Time",
            command=self.calculate_playlist_time,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=25,
            fg_color="#10b981",
            hover_color="#059669"
        )
        self.calculate_btn.pack(expand=True, fill="x")
        
        # Animated progress bar
        self.progress_bar = AnimatedProgressBar(input_frame)
        
    def create_results_section(self):
        # Main stats cards
        stats_frame = ctk.CTkFrame(self.results_section, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=20)
        
        # Create placeholder stats cards
        self.total_videos_card = StatsCard(stats_frame, "Total Videos", "0", "📹", "#3b82f6")
        self.total_videos_card.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.range_card = StatsCard(stats_frame, "Video Range", "N/A", "📊", "#8b5cf6")
        self.range_card.pack(side="left", fill="x", expand=True, padx=(10, 10))
        
        self.duration_card = StatsCard(stats_frame, "Total Duration", "0h 0m", "⏱️", "#f59e0b")
        self.duration_card.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Speed calculations section
        speeds_header = ctk.CTkLabel(self.results_section, 
                                    text="🎬 Playback Speed Analysis",
                                    font=ctk.CTkFont(size=20, weight="bold"))
        speeds_header.pack(pady=(20, 15))
        
        # Speed cards container
        self.speeds_frame = ctk.CTkFrame(self.results_section, fg_color="transparent")
        self.speeds_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Chart section
        chart_header = ctk.CTkLabel(self.results_section, 
                                   text="📈 Time Savings Visualization",
                                   font=ctk.CTkFont(size=20, weight="bold"))
        chart_header.pack(pady=(20, 15))
        
        self.chart_frame = ctk.CTkFrame(self.results_section, corner_radius=15, height=300)
        self.chart_frame.pack(fill="x", padx=20, pady=(0, 20))
        self.chart_frame.pack_propagate(False)
        
    def create_speed_cards(self, speeds_data):
        # Clear existing cards
        for widget in self.speeds_frame.winfo_children():
            widget.destroy()
            
        # Create grid layout for speed cards
        for i, (speed, time_str, saved_str) in enumerate(speeds_data):
            row = i // 3
            col = i % 3
            
            if col == 0:
                row_frame = ctk.CTkFrame(self.speeds_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=(0, 10))
            
            card = SpeedCard(row_frame, speed, time_str, saved_str)
            card.pack(side="left", fill="x", expand=True, 
                     padx=(0, 10) if col < 2 else (0, 0))
            
    def create_chart(self, speeds, times):
        # Clear existing chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
            
        if not MATPLOTLIB_AVAILABLE:
            # Create a simple text-based chart if matplotlib is not available
            chart_text = "📊 Time Comparison Chart\n\n"
            max_time = max(times)
            
            for speed, time_val in zip(speeds, times):
                bar_length = int((time_val / max_time) * 30)
                bar = "█" * bar_length + "░" * (30 - bar_length)
                chart_text += f"{speed}x: {bar} {time_val:.1f}h\n"
            
            chart_label = ctk.CTkLabel(self.chart_frame, 
                                      text=chart_text,
                                      font=ctk.CTkFont(size=12, family="Courier"),
                                      justify="left")
            chart_label.pack(expand=True, pady=20)
            return
            
        try:
            # Create matplotlib figure
            fig = Figure(figsize=(10, 4), facecolor='#212121')
            ax = fig.add_subplot(111, facecolor='#212121')
            
            # Create bars with nice colors
            colors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6']
            bars = ax.bar([f'{s}x' for s in speeds], times, color=colors, alpha=0.8)
            
            # Customize chart appearance
            ax.set_xlabel('Playback Speed', fontsize=12, color='white')
            ax.set_ylabel('Time (hours)', fontsize=12, color='white')
            ax.set_title('Viewing Time at Different Speeds', fontsize=14, fontweight='bold', color='white')
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white') 
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
            
            # Add value labels on bars
            for bar, time_val in zip(bars, times):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + max(times) * 0.02,
                       f'{time_val:.1f}h', ha='center', va='bottom', color='white', fontsize=10)
            
            # Embed chart
            canvas = FigureCanvasTkAgg(fig, self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            
        except Exception as e:
            # Fallback if matplotlib fails
            error_label = ctk.CTkLabel(self.chart_frame, 
                                      text=f"📊 Chart visualization temporarily unavailable\n{str(e)[:50]}...",
                                      font=ctk.CTkFont(size=14))
            error_label.pack(expand=True)
        
    def animate_results_appearance(self):
        """Animate the appearance of results section"""
        self.results_section.pack(fill="x", pady=(20, 0))
        
        # Fade in animation simulation
        def fade_in(alpha=0):
            if alpha <= 1:
                # This would be actual fade animation in a more advanced setup
                self.app.after(50, lambda: fade_in(alpha + 0.1))
                
        fade_in()
        
    def extract_playlist_id(self, url):
        """Extract playlist ID from YouTube URL"""
        patterns = [
            r'[?&]list=([a-zA-Z0-9_-]+)',
            r'playlist\?list=([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_playlist_videos(self, playlist_id):
        """Get all videos from a playlist"""
        videos = []
        next_page_token = None
        
        while True:
            url = f'https://www.googleapis.com/youtube/v3/playlistItems'
            params = {
                'part': 'snippet',
                'playlistId': playlist_id,
                'maxResults': 50,
                'key': self.api_key_var.get()
            }
            
            if next_page_token:
                params['pageToken'] = next_page_token
            
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
            
            data = response.json()
            
            for item in data['items']:
                video_id = item['snippet']['resourceId']['videoId']
                title = item['snippet']['title']
                videos.append({'id': video_id, 'title': title})
            
            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break
                
        return videos
    
    def get_video_durations(self, video_ids):
        """Get durations for multiple videos"""
        durations = {}
        
        # Process in batches of 50 (API limit)
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i+50]
            url = 'https://www.googleapis.com/youtube/v3/videos'
            params = {
                'part': 'contentDetails',
                'id': ','.join(batch),
                'key': self.api_key_var.get()
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code}")
            
            data = response.json()
            
            for item in data['items']:
                video_id = item['id']
                duration = item['contentDetails']['duration']
                durations[video_id] = self.parse_duration(duration)
        
        return durations
    
    def parse_duration(self, duration):
        """Parse ISO 8601 duration to seconds"""
        duration = duration[2:]
        
        hours = 0
        minutes = 0
        seconds = 0
        
        if 'H' in duration:
            hours = int(duration.split('H')[0])
            duration = duration.split('H')[1]
        
        if 'M' in duration:
            minutes = int(duration.split('M')[0])
            duration = duration.split('M')[1]
        
        if 'S' in duration:
            seconds = int(duration.split('S')[0])
        
        return hours * 3600 + minutes * 60 + seconds
    
    def format_time(self, seconds):
        """Format seconds to readable time"""
        td = timedelta(seconds=int(seconds))
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if td.days > 0:
            return f"{td.days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m {seconds}s"
    
    def calculate_playlist_time(self):
        """Main function to calculate playlist time"""
        # Validate inputs
        if not self.api_key_var.get().strip():
            messagebox.showerror("Error", "Please enter your YouTube API key")
            return
            
        if not self.url_var.get().strip():
            messagebox.showerror("Error", "Please enter a YouTube playlist URL")
            return
        
        # Start calculation in separate thread
        thread = threading.Thread(target=self._calculate_thread)
        thread.daemon = True
        thread.start()
    
    def _calculate_thread(self):
        """Thread function for calculation"""
        try:
            # Start progress animation
            self.app.after(0, lambda: self.progress_bar.pack(fill="x", padx=20, pady=(10, 20)))
            self.app.after(0, lambda: self.progress_bar.start())
            self.app.after(0, lambda: self.calculate_btn.configure(state='disabled', text="🔄 Calculating..."))
            
            # Extract playlist ID
            playlist_id = self.extract_playlist_id(self.url_var.get())
            if not playlist_id:
                raise Exception("Invalid playlist URL format")
            
            # Get playlist videos
            videos = self.get_playlist_videos(playlist_id)
            total_videos = len(videos)
            
            if total_videos == 0:
                raise Exception("No videos found or playlist is private")
            
            # Apply range filtering
            start_idx = max(1, int(self.start_var.get() or 1)) - 1
            end_idx = len(videos)
            
            if self.end_var.get().strip():
                end_idx = min(int(self.end_var.get()), len(videos))
            
            selected_videos = videos[start_idx:end_idx]
            
            # Get video durations
            video_ids = [video['id'] for video in selected_videos]
            durations = self.get_video_durations(video_ids)
            
            # Calculate total time
            total_seconds = sum(durations.get(video['id'], 0) for video in selected_videos)
            
            if total_seconds == 0:
                raise Exception("No valid video durations found")
            
            # Calculate speeds data
            speeds = [1.0, 1.25, 1.5, 1.75, 2.0]
            speeds_data = []
            chart_times = []
            
            for speed in speeds:
                time_at_speed = total_seconds / speed
                chart_times.append(time_at_speed / 3600)  # Convert to hours for chart
                
                if speed == 1.0:
                    speeds_data.append((speed, self.format_time(time_at_speed), ""))
                else:
                    time_saved = total_seconds - time_at_speed
                    speeds_data.append((speed, self.format_time(time_at_speed), 
                                     f"Saves {self.format_time(time_saved)}"))
            
            # Update UI with results
            self.app.after(0, lambda: self.update_results_ui(
                total_videos, start_idx + 1, end_idx, total_seconds, speeds_data, chart_times, speeds
            ))
            
        except Exception as e:
            self.app.after(0, lambda: messagebox.showerror("Error", str(e)))
        
        finally:
            # Stop progress and reset button
            self.app.after(0, lambda: self.progress_bar.stop())
            self.app.after(0, lambda: self.progress_bar.pack_forget())
            self.app.after(0, lambda: self.calculate_btn.configure(state='normal', text="🚀 Calculate Playlist Time"))
    
    def update_results_ui(self, total_videos, start_idx, end_idx, total_seconds, speeds_data, chart_times, speeds):
        """Update the results UI with calculated data"""
        # Update stats cards
        self.total_videos_card.update_value(str(total_videos))
        self.range_card.update_value(f"{start_idx} to {end_idx}")
        self.duration_card.update_value(self.format_time(total_seconds))
        
        # Create speed cards
        self.create_speed_cards(speeds_data)
        
        # Create chart
        self.create_chart(speeds, chart_times)
        
        # Show results section with animation
        self.animate_results_appearance()
    
    def run(self):
        self.app.mainloop()

def main():
    """
    Modern YouTube Playlist Time Calculator
    
    Required packages:
    pip install customtkinter requests
    
    Optional packages for enhanced features:
    pip install pillow matplotlib numpy ttkbootstrap
    
    Setup Instructions:
    1. Install required packages above
    2. Get YouTube Data API v3 key from Google Cloud Console
    3. Run the application
    """
    
    print("🎬 Modern YouTube Playlist Time Calculator")
    print("=" * 50)
    
    # Check for required packages
    missing_packages = []
    
    try:
        import customtkinter
    except ImportError:
        missing_packages.append("customtkinter")
    
    try:
        import requests
    except ImportError:
        missing_packages.append("requests")
    
    if missing_packages:
        print("❌ Missing required packages:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print(f"\n📦 Install with: pip install {' '.join(missing_packages)}")
        return
    
    # Check for optional packages
    optional_missing = []
    if not PIL_AVAILABLE:
        optional_missing.append("pillow")
    if not MATPLOTLIB_AVAILABLE:
        optional_missing.append("matplotlib numpy")
    if not TTKBOOTSTRAP_AVAILABLE:
        optional_missing.append("ttkbootstrap")
    
    if optional_missing:
        print("⚠️  Optional packages missing (app will work but with limited features):")
        for pkg in optional_missing:
            print(f"   - {pkg}")
        print(f"📦 Install for full features: pip install {' '.join(optional_missing)}")
        print()
    
    print("✅ Starting application...")
    print("🔑 Don't forget to get your YouTube Data API v3 key!")
    
    try:
        app = YouTubePlaylistCalculator()
        app.run()
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("\n💡 Try installing missing packages or check your Python environment")

if __name__ == "__main__":
    main()