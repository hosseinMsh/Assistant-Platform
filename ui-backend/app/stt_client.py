import logging
import subprocess
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


def _convert_to_wav(file_bytes: bytes) -> bytes:
    try:
        proc = subprocess.run(
            [
                "ffmpeg",
                "-i", "pipe:0",
                "-f", "wav",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                "pipe:1",
            ],
            input=file_bytes,
            capture_output=True,
            timeout=30,
        )
        if proc.returncode != 0:
            logger.error("ffmpeg conversion failed: %s", proc.stderr.decode("utf-8", errors="ignore"))
            raise RuntimeError("ffmpeg audio conversion failed")
        return proc.stdout
    except Exception:
        logger.exception("ffmpeg conversion exception")
        raise


async def transcribe_audio(file_bytes: bytes, filename: str = "audio.webm", content_type: str = "audio/webm") -> str:
    url = f"{settings.stt_base_url}/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {settings.stt_api_key}",
    }
    wav_bytes = _convert_to_wav(file_bytes)
    files = {"file": ("audio.wav", wav_bytes, "audio/wav")}
    data = {
        "model": settings.stt_model,
        "language": "fa",
        "response_format": "json",
    }
    async with httpx.AsyncClient(timeout=settings.stt_timeout) as client:
        response = await client.post(url, headers=headers, files=files, data=data)
        print("aaaaa ",response.text)
        response.raise_for_status()
        result = response.json()
        text = result.get("text", "")
        logger.info("stt_result text_length=%d", len(text))
        return text
