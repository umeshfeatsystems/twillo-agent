import audioop
import base64
import io
import logging
import wave
from typing import Any, Dict, Iterable, Optional, Tuple

import requests

from config import Config

logger = logging.getLogger("SarvamService")


class SarvamService:
    def __init__(self):
        self.api_key = Config.SARVAM_API_KEY
        self.base_url = Config.SARVAM_BASE_URL.rstrip("/")
        self.tts_endpoint = self._normalize_endpoint(Config.SARVAM_TTS_ENDPOINT)
        self.stt_endpoint = self._normalize_endpoint(Config.SARVAM_STT_ENDPOINT)
        self.stt_model = Config.SARVAM_STT_MODEL
        self.tts_model = Config.SARVAM_TTS_MODEL
        self.tts_speaker = Config.SARVAM_TTS_SPEAKER
        self.tts_output_codec = Config.SARVAM_TTS_OUTPUT_CODEC
        self.tts_sample_rate = Config.SARVAM_TTS_SAMPLE_RATE
        self.timeout_seconds = Config.SARVAM_TIMEOUT_SECONDS
        self._tts_cache: Dict[str, bytes] = {}

        if self.api_key:
            logger.info("Sarvam client configured")
        else:
            logger.warning("Sarvam API key missing. STT/TTS calls will fail.")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _normalize_endpoint(self, endpoint: str) -> str:
        if not endpoint:
            return ""
        return endpoint if endpoint.startswith("/") else f"/{endpoint}"

    def _headers(self, include_json_content_type: bool = False) -> Dict[str, str]:
        headers = {"api-subscription-key": self.api_key or ""}
        if include_json_content_type:
            headers["Content-Type"] = "application/json"
        return headers

    def _candidate_endpoints(self, primary: str, fallbacks: Iterable[str]) -> Iterable[str]:
        seen = set()
        candidates = [primary, *fallbacks]
        for raw in candidates:
            endpoint = self._normalize_endpoint(raw)
            if endpoint and endpoint not in seen:
                seen.add(endpoint)
                yield endpoint

    def synthesize_to_mulaw(
        self, text: str, language_code: str = "en-IN", voice_override: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Converts text to 8kHz MULAW bytes for Twilio media stream playback.
        """
        if not text or not self.enabled:
            return None

        speaker = voice_override or self.tts_speaker
        clean_text = text.strip()
        cache_key = f"{language_code}|{self.tts_model}|{speaker}|{clean_text}"
        if cache_key in self._tts_cache:
            return self._tts_cache[cache_key]

        # First payload follows current Sarvam docs. Second keeps compatibility
        # with older payload contracts seen in previous integrations.
        payloads = [
            {
                "text": clean_text,
                "target_language_code": language_code,
                "speaker": speaker,
                "model": self.tts_model,
                "output_audio_codec": self.tts_output_codec,
                "speech_sample_rate": self.tts_sample_rate,
            },
            {
                "inputs": [clean_text],
                "target_language_code": language_code,
                "speaker": speaker,
                "model": self.tts_model,
                "output_audio_codec": self.tts_output_codec,
                "speech_sample_rate": self.tts_sample_rate,
            },
        ]
        endpoints = list(
            self._candidate_endpoints(
                self.tts_endpoint,
                ["/text-to-speech", "/v1/text-to-speech"],
            )
        )

        last_error = None
        for endpoint in endpoints:
            for payload in payloads:
                try:
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        headers=self._headers(include_json_content_type=True),
                        json=payload,
                        timeout=self.timeout_seconds,
                    )
                    response.raise_for_status()
                    audio_bytes = self._extract_audio_bytes(response)
                    if not audio_bytes:
                        continue

                    mulaw_audio = self._to_mulaw_8k(audio_bytes)
                    if not mulaw_audio:
                        continue

                    self._tts_cache[cache_key] = mulaw_audio
                    return mulaw_audio
                except Exception as exc:
                    last_error = exc

        if last_error:
            logger.error("Sarvam TTS error: %s", last_error)
        return None

    def synthesize_speech(
        self, text: str, language: str = "en-IN", voice_override: Optional[str] = None
    ) -> Optional[str]:
        """
        Legacy method for routes expecting base64-encoded audio.
        """
        audio_bytes = self.synthesize_to_mulaw(
            text=text,
            language_code=language,
            voice_override=voice_override,
        )
        if not audio_bytes:
            return None
        return base64.b64encode(audio_bytes).decode("utf-8")

    def transcribe_mulaw(self, mulaw_audio: bytes, language_code: str = "en-IN") -> Optional[str]:
        """
        Converts Twilio MULAW chunks to WAV and sends them to Sarvam STT.
        """
        transcript, _ = self.transcribe_mulaw_with_language(mulaw_audio, [language_code])
        return transcript

    def transcribe_mulaw_with_language(
        self, mulaw_audio: bytes, language_codes: Iterable[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Tries one or more language codes and returns the first successful transcript
        with the language code that produced it.
        """
        if not mulaw_audio or not self.enabled:
            return None, None

        wav_bytes = self._mulaw_to_wav_16khz(mulaw_audio)
        unique_codes = []
        seen = set()
        for code in language_codes:
            clean = (code or "").strip()
            if clean and clean not in seen:
                seen.add(clean)
                unique_codes.append(clean)
        if not unique_codes:
            unique_codes = ["en-IN"]

        for language_code in unique_codes:
            transcript = self._transcribe_wav(wav_bytes, language_code)
            if transcript:
                return transcript, language_code

        return None, None

    def _transcribe_wav(self, wav_bytes: bytes, language_code: str) -> Optional[str]:
        files = {"file": ("audio.wav", wav_bytes, "audio/wav")}
        data = {
            "model": self.stt_model,
            "language_code": language_code,
            "language": language_code,
        }
        endpoints = list(
            self._candidate_endpoints(
                self.stt_endpoint,
                ["/speech-to-text", "/v1/speech-to-text"],
            )
        )

        for endpoint in endpoints:
            try:
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    headers=self._headers(),
                    data=data,
                    files=files,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                try:
                    payload = response.json()
                except ValueError:
                    payload = response.text
                transcript = self._extract_transcript(payload)
                if transcript:
                    return transcript.strip()
            except Exception as exc:
                logger.debug("Sarvam STT failed for language=%s endpoint=%s: %s", language_code, endpoint, exc)
        return None

    def _extract_audio_bytes(self, response: requests.Response) -> Optional[bytes]:
        content_type = response.headers.get("content-type", "").lower()

        # Some responses return direct audio bytes.
        if "application/json" not in content_type:
            return response.content

        payload = response.json()
        encoded_audio = None

        if isinstance(payload, dict):
            if isinstance(payload.get("audios"), list) and payload["audios"]:
                encoded_audio = payload["audios"][0]
            elif isinstance(payload.get("audio"), str):
                encoded_audio = payload["audio"]
            elif isinstance(payload.get("audio_base64"), str):
                encoded_audio = payload["audio_base64"]
            elif isinstance(payload.get("data"), dict):
                data = payload["data"]
                if isinstance(data.get("audios"), list) and data["audios"]:
                    encoded_audio = data["audios"][0]
                elif isinstance(data.get("audio"), str):
                    encoded_audio = data["audio"]

        if not encoded_audio:
            logger.error("Sarvam TTS response did not contain audio bytes")
            return None

        try:
            return base64.b64decode(encoded_audio)
        except Exception as exc:
            logger.error("Failed to decode Sarvam TTS audio: %s", exc)
            return None

    def _to_mulaw_8k(self, audio_bytes: bytes) -> Optional[bytes]:
        """
        Converts WAV/PCM to mono 8kHz MULAW bytes expected by Twilio media streams.
        """
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wav_in:
                channels = wav_in.getnchannels()
                sample_width = wav_in.getsampwidth()
                frame_rate = wav_in.getframerate()
                pcm_bytes = wav_in.readframes(wav_in.getnframes())
        except wave.Error:
            # If already raw MULAW, pass through.
            return audio_bytes

        if sample_width not in (1, 2, 4):
            logger.error("Unsupported sample width: %s", sample_width)
            return None

        if channels > 1:
            pcm_bytes = audioop.tomono(pcm_bytes, sample_width, 0.5, 0.5)

        if sample_width != 2:
            pcm_bytes = audioop.lin2lin(pcm_bytes, sample_width, 2)

        if frame_rate != 8000:
            pcm_bytes, _ = audioop.ratecv(pcm_bytes, 2, 1, frame_rate, 8000, None)

        return audioop.lin2ulaw(pcm_bytes, 2)

    def _mulaw_to_wav_16khz(self, mulaw_audio: bytes) -> bytes:
        pcm_8k = audioop.ulaw2lin(mulaw_audio, 2)
        pcm_16k, _ = audioop.ratecv(pcm_8k, 2, 1, 8000, 16000, None)
        output = io.BytesIO()
        with wave.open(output, "wb") as wav_out:
            wav_out.setnchannels(1)
            wav_out.setsampwidth(2)
            wav_out.setframerate(16000)
            wav_out.writeframes(pcm_16k)
        return output.getvalue()

    def _extract_transcript(self, payload: Any) -> Optional[str]:
        if isinstance(payload, str):
            return payload

        if isinstance(payload, dict):
            for key in ("transcript", "text", "final_transcript", "utterance"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value

            data = payload.get("data")
            if data:
                nested = self._extract_transcript(data)
                if nested:
                    return nested

            results = payload.get("results")
            if isinstance(results, list):
                for item in results:
                    nested = self._extract_transcript(item)
                    if nested:
                        return nested

            transcripts = payload.get("transcripts")
            if isinstance(transcripts, list):
                for item in transcripts:
                    nested = self._extract_transcript(item)
                    if nested:
                        return nested

            alternatives = payload.get("alternatives")
            if isinstance(alternatives, list):
                for item in alternatives:
                    nested = self._extract_transcript(item)
                    if nested:
                        return nested

        if isinstance(payload, list):
            for item in payload:
                nested = self._extract_transcript(item)
                if nested:
                    return nested

        return None


sarvam_service = SarvamService()
