import json
import os
import time
import re
import subprocess
import threading
from datetime import datetime
import moviepy
try:
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, vfx
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

# Base LLM class for processing commands
class CommandProcessor:
    def __init__(self):
        pass
    
    def process_command(self, command_text, current_file):
        """Process a command and return structured editing instructions"""
        # Extract common patterns from commands using regex
        
        # Check for trim/cut commands
        trim_match = re.search(r'(?:trim|cut).*?from\s+(\d+:?\d*:?\d*)\s+to\s+(\d+:?\d*:?\d*)', command_text, re.IGNORECASE)
        if trim_match:
            start_time = self._parse_timestamp(trim_match.group(1))
            end_time = self._parse_timestamp(trim_match.group(2))
            return {
                "action": "trim",
                "file_name": self._extract_filename(command_text, current_file),
                "start_time": start_time,
                "end_time": end_time,
                "output_file": f"trimmed_{os.path.basename(current_file)}"
            }
        
        # Check for text overlay commands
        text_match = re.search(r'(?:add|insert|place)\s+text\s+(?:saying\s+)?["\']?([^"\']+)["\']?\s+(?:at|in)\s+(?:the\s+)?(\w+)', command_text, re.IGNORECASE)
        if text_match:
            text_content = text_match.group(1)
            position = text_match.group(2).lower()
            
            # Extract timestamp if provided
            timestamp = "00:00:00"
            time_match = re.search(r'(?:at|from)\s+(?:time|timestamp)?\s*(\d+:?\d*:?\d*)', command_text, re.IGNORECASE)
            if time_match:
                timestamp = self._parse_timestamp(time_match.group(1))
            
            return {
                "action": "add_text",
                "file_name": self._extract_filename(command_text, current_file),
                "text": text_content,
                "position": position,
                "time": timestamp,
                "output_file": f"text_{os.path.basename(current_file)}"
            }
        
        # Check for transition commands
        transition_match = re.search(r'(?:add|insert|apply)\s+(?:a\s+)?(\w+)\s+transition', command_text, re.IGNORECASE)
        if transition_match:
            transition_type = transition_match.group(1).lower()
            
            # Extract timestamp if provided
            timestamp = "00:00:00"
            time_match = re.search(r'(?:at|from)\s+(?:time|timestamp)?\s*(\d+:?\d*:?\d*)', command_text, re.IGNORECASE)
            if time_match:
                timestamp = self._parse_timestamp(time_match.group(1))
            
            return {
                "action": "add_transition",
                "file_name": self._extract_filename(command_text, current_file),
                "transition_type": transition_type,
                "time": timestamp,
                "output_file": f"{transition_type}_{os.path.basename(current_file)}"
            }
            
        # Check for speed adjustment
        speed_match = re.search(r'(?:change|set|adjust)\s+(?:the\s+)?speed\s+(?:to|by)\s+([\d\.]+)(?:x)?', command_text, re.IGNORECASE)
        if speed_match:
            speed_factor = float(speed_match.group(1))
            return {
                "action": "adjust_speed",
                "file_name": self._extract_filename(command_text, current_file),
                "speed_factor": speed_factor,
                "output_file": f"speed{speed_factor}x_{os.path.basename(current_file)}"
            }
            
        # Check for crop commands
        crop_match = re.search(r'crop', command_text, re.IGNORECASE)
        if crop_match:
            return {
                "action": "crop",
                "file_name": self._extract_filename(command_text, current_file),
                "output_file": f"cropped_{os.path.basename(current_file)}"
            }
            
        # If no patterns match
        return {
            "action": "unknown",
            "file_name": self._extract_filename(command_text, current_file),
            "original_command": command_text,
            "error": "Could not determine specific edit command"
        }
    
    def _extract_filename(self, text, default_file):
        """Extract filename from command or use default"""
        filename_match = re.search(r'(?:file|video)\s+["\']?([^"\']+?\.(?:mp4|mov|avi|mkv))["\']?', text, re.IGNORECASE)
        if filename_match:
            return filename_match.group(1)
        return default_file
    
    def _parse_timestamp(self, timestamp_str):
        """Convert various timestamp formats to HH:MM:SS"""
        # If it's already in HH:MM:SS format
        if re.match(r'\d+:\d+:\d+', timestamp_str):
            return timestamp_str
            
        # If it's in MM:SS format
        if re.match(r'\d+:\d+$', timestamp_str):
            return f"00:{timestamp_str}"
            
        # If it's just seconds
        if re.match(r'\d+$', timestamp_str):
            seconds = int(timestamp_str)
            minutes, seconds = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
        # Default
        return "00:00:00"

# Voice recognition module with fallback
class VoiceRecognizer:
    def __init__(self):
        self.speech_recognition_available = False
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.speech_recognition_available = True
        except ImportError:
            print("Speech recognition not available. Using text input only.")
    
    def listen(self):
        """Listen for voice command or fall back to text input"""
        if not self.speech_recognition_available:
            return input("Enter your command (as if speaking): ")
            
        try:
            import speech_recognition as sr
            with sr.Microphone() as source:
                print("Listening for your command...")
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            command = self.recognizer.recognize_google(audio)
            print(f"Recognized command: {command}")
            return command
        except Exception as e:
            print(f"Speech recognition error: {e}")
            return input("Enter your command: ")

# Video editor implementation
class VideoEditor:
    def __init__(self):
        self.editor_type = "simulation"
        if MOVIEPY_AVAILABLE:
            self.editor_type = "moviepy"
            
    def process_edit(self, edit_instructions):
        """Process the edit instructions"""
        if isinstance(edit_instructions, str):
            try:
                edit_instructions = json.loads(edit_instructions)
            except:
                return "Error: Invalid edit instructions format", None
                
        action = edit_instructions.get("action", "unknown")
        file_name = edit_instructions.get("file_name", "unknown")
        output_file = edit_instructions.get("output_file", f"output_{file_name}")
        
        # Add timestamp to output filename to avoid overwriting
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(output_file)
        output_file = f"{name}_{timestamp}{ext}"
        
        # Check if we can do real editing
        if self.editor_type == "moviepy" and os.path.exists(file_name):
            return self._process_with_moviepy(action, file_name, output_file, edit_instructions)
        else:
            return self._simulate_editing(action, file_name, output_file, edit_instructions)
            
    def _process_with_moviepy(self, action, file_name, output_file, edit_instructions):
        """Process video edits with MoviePy"""
        try:
            clip = VideoFileClip(file_name)
            result_clip = None
            
            if action == "trim":
                start_time = self._timestamp_to_seconds(edit_instructions.get("start_time", "00:00:00"))
                end_time = self._timestamp_to_seconds(edit_instructions.get("end_time", str(clip.duration)))
                result_clip = clip.subclip(start_time, end_time)
                
            elif action == "add_text":
                text = edit_instructions.get("text", "Sample Text")
                position = edit_instructions.get("position", "center")
                time_str = edit_instructions.get("time", "00:00:00")
                time_sec = self._timestamp_to_seconds(time_str)
                
                # Create text clip
                txt_clip = TextClip(text, fontsize=70, color='white')
                
                # Position the text
                if position == "center":
                    txt_clip = txt_clip.set_position('center')
                elif position == "top":
                    txt_clip = txt_clip.set_position(('center', 50))
                elif position == "bottom":
                    txt_clip = txt_clip.set_position(('center', 'bottom'))
                
                # Set duration to 5 seconds or until end of video
                txt_duration = min(5, clip.duration - time_sec)
                txt_clip = txt_clip.set_start(time_sec).set_duration(txt_duration)
                
                # Composite with original video
                result_clip = CompositeVideoClip([clip, txt_clip])
                
            elif action == "add_transition":
                transition_type = edit_instructions.get("transition_type", "fade")
                
                if transition_type == "fade":
                    # Add fade in effect
                    result_clip = clip.fadein(2)
                else:
                    # Default for unsupported transitions
                    result_clip = clip
                    
            elif action == "adjust_speed":
                speed_factor = float(edit_instructions.get("speed_factor", 1.0))
                result_clip = clip.speedx(speed_factor)
                
            else:
                # Unsupported action
                return f"Action '{action}' not supported with MoviePy", None
                
            # Make sure we have a result clip
            if result_clip is None:
                result_clip = clip
                
            # Write output file
            print(f"Processing video with MoviePy... (this may take some time)")
            
            # Use a progress printer for long operations
            def progress_callback(t):
                print(f"Processing: {int(t * 100)}% complete", end="\r")
                
            # Start processing in a separate thread with progress
            result_clip.write_videofile(
                output_file, 
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                fps=clip.fps,
                threads=4,
                preset='ultrafast',  # Use fast preset for quick results
                logger=None
            )
            
            # Close the clips to release resources
            clip.close()
            if result_clip != clip:
                result_clip.close()
                
            return f"Successfully applied {action} to {file_name} and saved as {output_file}", output_file
            
        except Exception as e:
            return f"Error processing video with MoviePy: {str(e)}", None
            
    def _simulate_editing(self, action, file_name, output_file, edit_instructions):
        """Simulate video editing for prototype purposes"""
        print("\n--- SIMULATING VIDEO EDITING ---")
        print(f"Action: {action}")
        print(f"Input file: {file_name}")
        print(f"Output file: {output_file}")
        
        for key, value in edit_instructions.items():
            if key not in ["action", "file_name", "output_file"]:
                print(f"{key}: {value}")
        
        # Simulate processing time
        print("\nProcessing video edit...")
        for i in range(5):
            time.sleep(0.5)
            print(".", end="", flush=True)
        print("\n")
        
        return f"Successfully applied {action} to {file_name} and saved as {output_file}", output_file
        
    def _timestamp_to_seconds(self, timestamp):
        """Convert HH:MM:SS timestamp to seconds"""
        parts = timestamp.split(':')
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        else:
            return float(parts[0])

# Main application class
class VoiceVideoEditor:
    def __init__(self):
        self.command_processor = CommandProcessor()
        self.voice_recognizer = VoiceRecognizer()
        self.video_editor = VideoEditor()
        self.current_file = None
        self.edit_history = []
        
    def process_command(self):
        """Process a single voice command"""
        if not self.current_file:
            print("No video file selected.")
            return False
            
        # Get voice command
        command = self.voice_recognizer.listen()
        
        if not command:
            return False
            
        # Process the command
        edit_instructions = self.command_processor.process_command(command, self.current_file)
        
        if edit_instructions["action"] == "unknown":
            print(f"Could not understand the command: {command}")
            print("Try again with a more specific command like:")
            print("- 'Trim the video from 1:30 to 2:45'")
            print("- 'Add text saying Hello at the center at timestamp 15 seconds'")
            return False
        
        # Execute the edit
        result, output_file = self.video_editor.process_edit(edit_instructions)
        print(f"\nResult: {result}")
        
        # Update current file and history if successful
        if output_file:
            self.edit_history.append({
                "input_file": self.current_file,
                "output_file": output_file,
                "action": edit_instructions["action"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            self.current_file = output_file
            
        return True
        
    def run(self):
        """Run the main application loop"""
        self._print_welcome()
        
        # Ask for initial file
        self._select_file()
        
        if not self.current_file:
            print("No file selected. Exiting.")
            return
            
        # Main command loop
        while True:
            print("\n" + "-"*50)
            print(f"Currently editing: {self.current_file}")
            
            # Show menu
            print("\nOptions:")
            print("1. Issue voice/text command")
            print("2. Select different file")
            print("3. Show editing history")
            print("4. Exit")
            
            choice = input("Choose an option (1-4): ")
            
            if choice == "1":
                self.process_command()
            elif choice == "2":
                self._select_file()
            elif choice == "3":
                self._show_history()
            elif choice == "4":
                break
            else:
                print("Invalid choice. Please try again.")
                
        print("\nThank you for using the Voice Video Editor!")
        
    def _print_welcome(self):
        """Print welcome message"""
        print("="*50)
        print("VOICE-CONTROLLED VIDEO EDITOR")
        print("="*50)
        
        if MOVIEPY_AVAILABLE:
            print("MoviePy detected! Real video editing is available.")
        else:
            print("MoviePy not detected. Running in simulation mode.")
            print("To enable real video editing, install MoviePy:")
            print("pip install moviepy")
            
        print("="*50)
        
    def _select_file(self):
        """Select a video file to edit"""
        print("\nSelect a file to edit:")
        
        # Look for video files in current directory
        video_files = [f for f in os.listdir('.') if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]
        
        if video_files:
            print("\nAvailable video files:")
            for i, file in enumerate(video_files, 1):
                print(f"{i}. {file}")
            print(f"{len(video_files)+1}. Enter custom path")
            print(f"{len(video_files)+2}. Create simulation file")
            
            try:
                choice = int(input("\nEnter number: "))
                if 1 <= choice <= len(video_files):
                    self.current_file = video_files[choice-1]
                elif choice == len(video_files)+1:
                    custom_path = input("Enter full path to video file: ")
                    if os.path.exists(custom_path):
                        self.current_file = custom_path
                    else:
                        print(f"File not found: {custom_path}")
                        self.current_file = input("Enter a filename for simulation: ")
                elif choice == len(video_files)+2:
                    self.current_file = input("Enter a filename for simulation: ")
                else:
                    print("Invalid choice")
                    self.current_file = input("Enter a filename for simulation: ")
            except ValueError:
                print("Invalid input")
                self.current_file = input("Enter a filename for simulation: ")
        else:
            print("No video files found in current directory.")
            create_simulation = input("Create a simulation file? (y/n): ")
            if create_simulation.lower() == 'y':
                self.current_file = input("Enter a filename for simulation: ")
            else:
                custom_path = input("Enter full path to video file: ")
                if os.path.exists(custom_path):
                    self.current_file = custom_path
                else:
                    print(f"File not found: {custom_path}")
                    self.current_file = input("Enter a filename for simulation: ")
    
    def _show_history(self):
        """Show editing history"""
        if not self.edit_history:
            print("\nNo editing history available.")
            return
            
        print("\n--- EDITING HISTORY ---")
        for i, entry in enumerate(self.edit_history, 1):
            print(f"{i}. {entry['timestamp']} - {entry['action']}")
            print(f"   {entry['input_file']} → {entry['output_file']}")

# Run the application if script is executed directly
if __name__ == "__main__":
    app = VoiceVideoEditor()
    app.run()