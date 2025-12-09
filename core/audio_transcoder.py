import numpy as np

class AudioTranscoder:
    """
    Handles conversion between Twilio (Mulaw 8k) and Gemini.
    """

    def _ulaw2lin(self, ulaw_data):
        """Convert 8-bit u-law to 16-bit PCM"""
        ulaw_data = np.frombuffer(ulaw_data, dtype=np.uint8)
        ulaw_data = ~ulaw_data
        sign = (ulaw_data & 0x80)
        exponent = (ulaw_data >> 4) & 0x07
        mantissa = ulaw_data & 0x0F
        sample = ((mantissa << 3) + 0x84) << exponent
        sample = sample - 0x84
        sample = np.where(sign == 0, -sample, sample)
        return sample.astype(np.int16)

    def _lin2ulaw(self, pcm_data):
        """Convert 16-bit PCM to 8-bit u-law"""
        pcm_data = np.frombuffer(pcm_data, dtype=np.int16)
        pcm_data = pcm_data.astype(np.int32) # Prevent overflow
        
        sign = (pcm_data < 0)
        pcm_data = np.abs(pcm_data)
        pcm_data = np.clip(pcm_data + 0x84, 0, 32767)
        
        exponent = np.floor(np.log2(pcm_data) - 7).astype(np.int16)
        exponent = np.clip(exponent, 0, 7)
        
        mantissa = (pcm_data >> (exponent + 3)) & 0x0F
        ulaw = (sign.astype(np.uint8) << 7) | (exponent.astype(np.uint8) << 4) | mantissa.astype(np.uint8)
        return (~ulaw).tobytes()

    def process_twilio_to_gemini_8k(self, mulaw_data: bytes) -> bytes:
        """
        Direct 8k -> 8k conversion. 
        No upsampling. Best for latency and clarity on Gemini 2.0.
        """
        if not mulaw_data: return b""
        return self._ulaw2lin(mulaw_data).tobytes()

    def process_gemini_to_twilio(self, pcm_data: bytes) -> bytes:
        """Gemini (24k PCM) -> Twilio (8k Mulaw)"""
        if not pcm_data: return b""
        pcm_24k = np.frombuffer(pcm_data, dtype=np.int16)
        # Decimate 24k -> 8k (Take every 3rd sample)
        pcm_8k = pcm_24k[::3]
        return self._lin2ulaw(pcm_8k.tobytes())