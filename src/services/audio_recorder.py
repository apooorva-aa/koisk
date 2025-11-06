import sounddevice as sd

async def record_user_voice(duration=5, sample_rate=16000):
    """
    Records the user's voice from the microphone.
    """
    print("\nPlease speak... Recording now.\n")

    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='float32'
    )
    sd.wait() 

    audio_np = recording.reshape(-1)

    return audio_np, sample_rate