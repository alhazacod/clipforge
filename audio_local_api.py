import requests

with open('script.txt', 'r', encoding='utf-8') as f:
    text = f.read()

url = "http://localhost:8880/v1/audio/speech"
payload = {
    "input": text,
    "voice": "af_bella",
    "response_format": "wav",  
    "velocity": 0.8
}

response = requests.post(url, json=payload, stream=True)

if response.status_code == 200:
    with open("output.wav", "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    print("Saved to output.wav")
else:
    print("Error:", response.status_code, response.text)
