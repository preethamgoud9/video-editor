# Voice-Controlled Video Editing Prototype

## Overview
This project is a **simulated voice-controlled video editing system** using a **mock LLM (Language Model Model)**. It enables users to give voice or text-based commands to perform basic video editing operations such as trimming, adding text, and transitions. The system processes commands and returns **JSON-based instructions**, simulating how an actual AI-powered video editor would function.

## Features
- **Voice & Text Command Support**: Users can give commands via voice input (if enabled) or text input.
- **Mock LLM Processing**: Simulated AI model that interprets video editing commands.
- **Keyword-Based Parsing**: Extracts editing instructions based on user input.
- **JSON-Based Editing Instructions**: Outputs structured data that a real video editor could use.
- **Simulated Video Editing**: Prints out the steps and results of the edits in a realistic manner.

## Dependencies
The project requires **Python 3.7+**. Optional dependencies include:
- `speechrecognition` (for voice command input)
- `pyaudio` (required for voice recognition to work)
- `time` and `json` (for processing and simulating delays)

To install the optional dependencies, use:
```sh
pip install speechrecognition pyaudio
```

## How It Works
### 1. Mock LLM (Language Model Model)
Instead of using an external LLM like OpenAI's GPT, a **custom lightweight LLM simulation** (`MockLLM`) is used. It interprets commands based on keywords and generates **structured JSON instructions**.

### 2. Command Processing Flow
1. The user provides a **voice or text command**.
2. The **prompt template** fills in the command details.
3. The **mock LLM processes the command** and returns an **actionable JSON response**.
4. The **video editing simulator** interprets and prints the results.

## Example Commands
- **Trimming a Video**
  - "Trim the file vacation.mp4 from 1:30 to 2:45."
  - Output JSON:
    ```json
    {
      "action": "trim",
      "file_name": "vacation.mp4",
      "start_time": "00:01:30",
      "end_time": "00:02:45",
      "output_file": "trimmed_vacation.mp4"
    }
    ```

- **Adding Text to a Video**
  - "Add text saying 'Welcome' at the center at timestamp 15 seconds."
  - Output JSON:
    ```json
    {
      "action": "add_text",
      "file_name": "default_video.mp4",
      "text": "Welcome",
      "position": "center",
      "time": "00:00:15",
      "output_file": "text_default_video.mp4"
    }
    ```

- **Adding a Transition**
  - "Add a fade transition at the beginning of the video."
  - Output JSON:
    ```json
    {
      "action": "add_transition",
      "file_name": "default_video.mp4",
      "transition_type": "fade",
      "time": "00:00:00",
      "output_file": "transition_default_video.mp4"
    }
    ```

## Running the Program
1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/video-editing-prototype.git
   cd video-editing-prototype
   ```
2. Run the script:
   ```sh
   python script.py
   ```
3. Choose whether to enable voice recognition.
4. Provide video editing commands via text or voice.

## Customization
- Modify **`MockLLM`** to recognize additional editing actions.
- Adjust the **`_extract_filename`** method for improved filename extraction.
- Integrate **real video editing APIs** for actual processing.

## Limitations
- **Does not perform real video editing** (simulation only).
- **Simple keyword-based parsing** (no advanced NLP processing).
- **Limited command set** (expandable by modifying the mock LLM).

## Future Improvements
- Integrate **FFmpeg** for real video editing capabilities.
- Improve **command understanding** using NLP techniques.
- Implement **GUI-based interaction**.

## License
This project is open-source and available under the MIT License.

---
**Contributors**
- Your Name ([GitHub Profile](https://github.com/your-profile))

Feel free to fork, modify, and contribute!

