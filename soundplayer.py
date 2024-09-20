import pyaudio
import wave
from pydub import AudioSegment

# Audio format settings
FORMAT = pyaudio.paInt16  # 16-bit audio
CHANNELS = 2  # Stereo
RATE = 44100  # Sample rate
CHUNK = 1024  # Number of frames per buffer

def stream_audio(file_path):
    p = pyaudio.PyAudio()

    if file_path.endswith('.wav'):
        # Open the WAV file
        wf = wave.open(file_path, 'rb')
    elif file_path.endswith('.mp3'):
        # Load the MP3 file and export it to a temporary WAV format
        audio = AudioSegment.from_mp3(file_path)
        audio = audio.set_frame_rate(RATE).set_channels(CHANNELS)
        wav_file_path = file_path.replace('.mp3', '.wav')
        audio.export(wav_file_path, format='wav')
        wf = wave.open(wav_file_path, 'rb')
    else:
        raise ValueError("Unsupported file format. Please use .wav or .mp3.")

    # Open stream for output (to virtual microphone)
    output_stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            output=True,
                            frames_per_buffer=CHUNK)

    print("Starting to stream audio into virtual mic...")

    try:
        # Read data in chunks
        data = wf.readframes(CHUNK)
        while data:
            output_stream.write(data)
            data = wf.readframes(CHUNK)
    except KeyboardInterrupt:
        print("Stopped by user")

    # Stop and close streams
    output_stream.stop_stream()
    output_stream.close()
    wf.close()
    p.terminate()

def main():
    # Replace with your audio file path
    #audio_file_path = r"C:\Users\David\Music\Projekte\slts4.wav"
    audio_file_path = r"C:\Users\David\Music\ki gack\adem.mp3"
    stream_audio(audio_file_path)
