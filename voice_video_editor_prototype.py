# Import from langchain_core instead of langchain for newer versions
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import os
import time

# No need for dotenv if we're not using real APIs
# from dotenv import load_dotenv

# Custom LLM class that doesn't depend on langchain-community
class MockLLM:
    def __init__(self, temperature=0.7):
        self.temperature = temperature
    
    def invoke(self, text):
        print("Processing with simulated LLM...")
        time.sleep(1)  # Simulate processing delay
        
        # Simple keyword-based parsing for prototype
        if "trim" in text.lower() or "cut" in text.lower():
            return json.dumps({
                "action": "trim",
                "file_name": self._extract_filename(text),
                "start_time": "00:01:30",
                "end_time": "00:02:45",
                "output_file": "trimmed_" + self._extract_filename(text)
            })
        elif "text" in text.lower():
            return json.dumps({
                "action": "add_text",
                "file_name": self._extract_filename(text),
                "text": "Sample Text",
                "position": "center",
                "time": "00:00:15",
                "output_file": "text_" + self._extract_filename(text)
            })
        elif "transition" in text.lower():
            return json.dumps({
                "action": "add_transition",
                "file_name": self._extract_filename(text),
                "transition_type": "fade",
                "time": "00:00:00",
                "output_file": "transition_" + self._extract_filename(text)
            })
        else:
            return json.dumps({
                "action": "unknown",
                "file_name": self._extract_filename(text),
                "error": "Could not determine specific edit command"
            })
    
    def _extract_filename(self, text):
        # Very basic extraction - in a real system, this would be more sophisticated
        if "file" in text.lower() and ".mp4" in text.lower():
            start = text.lower().find("file") + 5
            end = text.lower().find(".mp4") + 4
            return text[start:end]
        return "default_video.mp4"

# Initialize Speech Recognition (with fallback to text input for prototype)
def get_voice_command(use_voice=False):
    if use_voice:
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                print("Listening for your command...")
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)
            
            command = recognizer.recognize_google(audio)
            print(f"Recognized command: {command}")
            return command
        except Exception as e:
            print(f"Speech recognition error: {e}")
            print("Falling back to text input...")
            return input("Enter your command: ")
    else:
        return input("Enter your command (as if speaking): ")

# Initialize mock LLM
mock_llm = MockLLM()

# Create a simple chain without depending on LangChain's chain classes
def process_with_template(llm, template, **kwargs):
    # Replace template variables
    formatted_prompt = template
    for key, value in kwargs.items():
        formatted_prompt = formatted_prompt.replace(f"{{{key}}}", str(value))
    
    # Process with LLM
    return llm.invoke(formatted_prompt)

# Template for command processing
command_template = """
Parse the following voice command for video editing:

Current video file: {current_file}
Voice Command: {voice_command}
"""

# Simulated video editor function
def simulate_video_editing(edit_instructions):
    if isinstance(edit_instructions, str):
        try:
            edit_instructions = json.loads(edit_instructions)
        except:
            return "Error: Invalid JSON format"
    
    action = edit_instructions.get("action", "unknown")
    file_name = edit_instructions.get("file_name", "unknown")
    output_file = edit_instructions.get("output_file", f"output_{file_name}")
    
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
    
    return f"Successfully applied {action} to {file_name} and saved as {output_file}"

# Main function
def process_voice_command_for_video_editing(current_file=None, use_voice=False):
    # Set default file if none provided
    if current_file is None or current_file == "":
        current_file = "default_video.mp4"
    
    # Get command (voice or text input)
    voice_command = get_voice_command(use_voice)
    
    if not voice_command:
        return "No command detected. Please try again.", current_file
    
    # Process the command through template
    result = process_with_template(
        mock_llm, 
        command_template,
        current_file=current_file,
        voice_command=voice_command
    )
    
    try:
        # Parse the result
        edit_instructions = json.loads(result) if isinstance(result, str) else result
        
        # Update current file if needed
        if "file_name" in edit_instructions and edit_instructions["file_name"] != "unknown":
            current_file = edit_instructions["file_name"]
        
        # Simulate sending to video editing API
        editing_result = simulate_video_editing(edit_instructions)
        
        # Track output file as new current file
        if "output_file" in edit_instructions:
            current_file = edit_instructions["output_file"]
        
        return editing_result, current_file
    
    except Exception as e:
        return f"Error processing command: {str(e)}", current_file

# Demo UI
def run_demo():
    print("="*50)
    print("VOICE-CONTROLLED VIDEO EDITING PROTOTYPE")
    print("="*50)
    print("This is a simulated prototype without actual API calls")
    print("Commands are processed through a mock LLM system")
    print("="*50)
    
    current_file = None
    use_voice = False
    
    # Ask if user wants to use real voice recognition
    voice_choice = input("Would you like to try using real voice recognition? (y/n): ").lower()
    if voice_choice == 'y':
        try:
            import speech_recognition as sr
            test_recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                print("Testing microphone...")
                test_recognizer.adjust_for_ambient_noise(source)
            use_voice = True
            print("Voice recognition enabled!")
        except Exception as e:
            print(f"Couldn't initialize voice recognition: {e}")
            print("Continuing with text input simulation.")
    
    # Ask for initial file
    file_input = input("\nEnter the name of the video file to edit (or press Enter for default): ")
    if file_input.strip():
        current_file = file_input
    
    print("\nExample commands you can try:")
    print("- 'Trim the file vacation.mp4 from 1:30 to 2:45'")
    print("- 'Add text saying Welcome at the center at timestamp 15 seconds'")
    print("- 'Add a fade transition at the beginning of the video'")
    
    while True:
        print("\n" + "-"*50)
        print(f"Currently editing: {current_file}")
        
        result, current_file = process_voice_command_for_video_editing(current_file, use_voice)
        print(f"\nResult: {result}")
        
        continue_editing = input("\nContinue editing? (yes/no): ")
        if continue_editing.lower() not in ["yes", "y"]:
            break
    
    print("\nThank you for trying the video editing prototype!")

# Run the demo
if __name__ == "__main__":
    run_demo()