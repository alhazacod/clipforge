from gradio_client import Client
import shutil
import os

client = Client("Remsky/Kokoro-TTS-Zero")

with open('script.txt', 'r', encoding='utf-8') as f:
    text = f.read()

result = client.predict(
    text=text,
    voice_names="af_sky",
    speed=0.8,
    api_name="/generate_speech_from_ui"
)

# result[0] is the temporary path
temp_audio_path = result[0]

# Save it in the same folder as the script
script_dir = os.path.dirname(os.path.abspath(__file__))
final_path = os.path.join(script_dir, "output.wav")

shutil.copy(temp_audio_path, final_path)

print(f"Audio saved as: {final_path}")
