import numpy as np

class AudioTranscoder:
    """Handles conversion between Twilio (Mulaw 8k) and Gemini (PCM 16k)"""

    def _ulaw2lin(self, ulaw_data):
        """Convert 8-bit u-law to 16-bit PCM"""
        if len(ulaw_data) == 0:
            return np.array([], dtype=np.int16)
            
        ulaw_data = np.frombuffer(ulaw_data, dtype=np.uint8)
        
        # U-law decoding algorithm
        sign = (ulaw_data & 0x80)
        exponent = (ulaw_data & 0x70) >> 4
        mantissa = ulaw_data & 0x0F
        
        # Compute magnitude
        magnitude = ((mantissa << 3) + 0x84) << (exponent)
        magnitude = magnitude - 0x84
        
        # Apply sign
        sample = np.where(sign != 0, magnitude, -magnitude)
        
        return sample.astype(np.int16)

    def _lin2ulaw(self, pcm_data):
        """Convert 16-bit PCM to 8-bit u-law"""
        if len(pcm_data) == 0:
            return b""
            
        pcm_data = np.frombuffer(pcm_data, dtype=np.int16)
        
        # Get sign and magnitude
        sign = (pcm_data < 0).astype(np.uint8)
        magnitude = np.abs(pcm_data).astype(np.int32)
        
        # Add bias
        magnitude = np.clip(magnitude + 0x84, 0, 0x7FFF)
        
        # Find exponent and mantissa
        exponent = np.zeros_like(magnitude, dtype=np.uint8)
        for i in range(7, -1, -1):
            mask = magnitude >= (0x84 << (i + 1))
            exponent[mask] = np.maximum(exponent[mask], i)
        
        mantissa = ((magnitude >> (exponent + 3)) & 0x0F).astype(np.uint8)
        
        # Construct u-law byte
        ulaw = (sign << 7) | (exponent << 4) | mantissa
        
        return (~ulaw).tobytes()

    def _resample_8k_to_16k(self, pcm_8k):
        """Resample from 8kHz to 16kHz using linear interpolation"""
        if len(pcm_8k) == 0:
            return np.array([], dtype=np.int16)
        
        n = len(pcm_8k)
        # Simple 2x upsampling with linear interpolation
        pcm_16k = np.zeros(n * 2, dtype=np.int16)
        pcm_16k[::2] = pcm_8k  # Original samples
        
        # Interpolate only if we have more than 1 sample
        if n > 1:
            pcm_16k[1:-1:2] = (pcm_8k[:-1] + pcm_8k[1:]) // 2
            pcm_16k[-1] = pcm_8k[-1]
        
        return pcm_16k

    def _resample_24k_to_8k(self, pcm_24k):
        """Downsample from 24kHz to 8kHz (every 3rd sample)"""
        if len(pcm_24k) == 0:
            return np.array([], dtype=np.int16)
        return pcm_24k[::3]

    def process_twilio_to_gemini_16k(self, mulaw_data: bytes) -> bytes:
        """Twilio (8k Mulaw) -> Gemini (16k PCM)"""
        if not mulaw_data or len(mulaw_data) == 0:
            return b""
        try:
            # Step 1: Decode µ-law to 8kHz PCM
            pcm_8k = self._ulaw2lin(mulaw_data)
            if len(pcm_8k) == 0:
                return b""
            
            # Step 2: Resample from 8kHz to 16kHz
            pcm_16k = self._resample_8k_to_16k(pcm_8k)
            if len(pcm_16k) == 0:
                return b""
            
            return pcm_16k.tobytes()
        except Exception as e:
            print(f"Error in process_twilio_to_gemini_16k: {e}")
            return b""

    def process_gemini_to_twilio(self, pcm_data: bytes) -> bytes:
        """Gemini (24k PCM) -> Twilio (8k Mulaw)"""
        if not pcm_data or len(pcm_data) == 0:
            return b""
        try:
            pcm_24k = np.frombuffer(pcm_data, dtype=np.int16)
            if len(pcm_24k) == 0:
                return b""
            
            # Downsample from 24kHz to 8kHz
            pcm_8k = self._resample_24k_to_8k(pcm_24k)
            if len(pcm_8k) == 0:
                return b""
            
            return self._lin2ulaw(pcm_8k.tobytes())
        except Exception as e:
            print(f"Error in process_gemini_to_twilio: {e}")
            return b""