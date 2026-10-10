
"""
Background worker for downloading videos using yt-dlp.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

from app.queue import update_job_status
from app.utils import log_info, log_error

DOWNLOADS_DIR = Path(
    os.environ.get(
        "DOWNLOAD_DIR",
        str(Path(__file__).parent / "downloads")
    )
)


def download_video(job_id: str, url: str, format: str):
    """Download video as MP4 or extract audio as MP3."""
    try:
        if format not in ("mp3", "mp4"):
            raise ValueError("Formato no válido. Usa mp3 o mp4.")

        log_info(f"Iniciando descarga {job_id}: {format}")
        update_job_status(job_id, status="processing", progress=10)

        DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

        if not shutil.which("yt-dlp"):
            raise RuntimeError("yt-dlp no está instalado.")
        
        output_template = str(DOWNLOADS_DIR / f"{job_id}.%(ext)s")

        cmd = [
            "yt-dlp",
            "--ignore-config",
            "--no-playlist",
            "--no-warnings",
            "--retries", "2",
            "--extractor-retries", "2",
            "--socket-timeout", "30",
            "--extractor-args", "youtube:player_client=tv,web_safari",
            "--output", output_template,
        ]

        if format == "mp3":
            cmd += [
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "192K",
            ]
        else:
            cmd += [
                "--format",
                "best[height<=720][ext=mp4]/best[height<=720]/best",
                "--merge-output-format", "mp4",
            ]

        cmd.append(url)

        update_job_status(job_id, status="processing", progress=30)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )

        if result.returncode != 0:
            error_msg = (result.stderr or result.stdout or "Descarga fallida").strip()
            log_error(f"Trabajo {job_id} fallido: {error_msg}")

            update_job_status(
                job_id,
                status="error",
                error=error_msg[-1500:],
                progress=0,
            )
            return

        update_job_status(job_id, status="processing", progress=90)

        output_path = DOWNLOADS_DIR / (
            f"{job_id}.mp3" if format == "mp3" else f"{job_id}.mp4"
        )

        # yt-dlp puede añadir otra extensión; busca el archivo generado.
        if not output_path.is_file():
            candidates = [
                p for p in DOWNLOADS_DIR.glob(f"{job_id}.*")
                if p.is_file() and p.suffix.lower() in (".mp3", ".mp4")
            ]
            output_path = candidates[0] if candidates else None

        if not output_path or not output_path.is_file():
            raise RuntimeError(
                "La descarga terminó, pero no se encontró el archivo MP3/MP4."
            )

        update_job_status(
            job_id,
            status="finished",
            progress=100,
            filename=output_path.name,
        )

        log_info(f"Trabajo {job_id} completado: {output_path.name}")

    except subprocess.TimeoutExpired:
        log_error(f"Trabajo {job_id}: tiempo agotado")
        update_job_status(
            job_id,
            status="error",
            error="La descarga superó el límite de 5 minutos.",
            progress=0,
        )

    except Exception as e:
        log_error(f"Trabajo {job_id}: {e}")
        update_job_status(
            job_id,
            status="error",
            error=str(e),
            progress=0,
        )
