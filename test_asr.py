# import os
# import whisper

# os.environ["PATH"] += os.pathsep + r"C:\Users\Ruchika Singh\OneDrive\Desktop\ffmpeg\ffmpeg-2026-02-09-git-9bfa1635ae-full_build\bin"

# print("Loading model...")
# model = whisper.load_model("base")

# print("Model loaded successfully!")

# audio_file = "sample.mp3"

# print("Starting transcription...")
# result = model.transcribe(audio_file)

# print("\nTranscription Result:")
# print(result["text"])

import whisper
model = whisper.load_model("base")

def transcribe_audio(audio_file):
    result = model.transcribe(audio_file)
    return result['text']

if __name__ == "__main__":
    audio_file = "sample.mp3"  
    text = transcribe_audio(audio_file)
    print("\n📝 Transcribed Text:\n", text)
    txt_filename = f"{audio_file}.txt"

    with open(txt_filename, "w", encoding="utf-8") as file:
        file.write(text)

    print(f"📁 Transcription saved to: {txt_filename}")