"""
Background worker for downloading videos using yt-dlp.
"""
import os
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
    output_path = None

    try:
        if format not in ("mp3", "mp4"):
            raise ValueError("Formato no válido. Usa mp3 o mp4.")

        log_info(f"Iniciando descarga {job_id}: {url} ({format})")
        update_job_status(job_id, status="processing", progress=10)

        DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

        if not shutil.which("yt-dlp"):
            raise RuntimeError(
                "yt-dlp no está instalado o no se encuentra en PATH. "
                "Revisa requirements.txt y el despliegue de Railway."
            )

        # Elimina archivos antiguos del mismo trabajo.
        for old_file in DOWNLOADS_DIR.glob(f"{job_id}.*"):
            if old_file.is_file():
                try:
                    old_file.unlink()
                except OSError:
                    pass

        output_template = str(DOWNLOADS_DIR / f"{job_id}.%(ext)s")

        cmd = [
            "yt-dlp",
            "--ignore-config",
            "--no-playlist",
            "--no-warnings",
            "--retries", "3",
            "--extractor-retries", "3",
            "--fragment-retries", "3",
            "--socket-timeout", "30",
            "--extractor-args",
            "youtube:player_client=default,web_embedded",
            "--output", output_template,
        ]

        if format == "mp3":
            cmd.extend([
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "192K",
            ])
        else:
            cmd.extend([
                "--format",
                "best[height<=720][ext=mp4]/best[height<=720]/best",
                "--merge-output-format", "mp4",
            ])

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
            error_msg = (
                result.stderr or result.stdout or "La descarga falló."
            ).strip()

            log_error(f"Trabajo {job_id} fallido: {error_msg}")

            update_job_status(
                job_id,
                status="error",
                error=error_msg[-1500:],
                progress=0,
            )
            return

        update_job_status(job_id, status="processing", progress=90)

        expected_extension = ".mp3" if format == "mp3" else ".mp4"
        output_path = DOWNLOADS_DIR / f"{job_id}{expected_extension}"

        # Busca el archivo real si yt-dlp generó una extensión diferente.
        if not output_path.is_file():
            candidates = [
                file for file in DOWNLOADS_DIR.glob(f"{job_id}.*")
                if file.is_file()
                and file.suffix.lower() in (".mp3", ".mp4")
                and file.stat().st_size > 0
            ]

            output_path = candidates[0] if candidates else None

        if output_path is None or not output_path.is_file():
            raise RuntimeError(
                "La descarga terminó, pero no se encontró el archivo MP3/MP4."
            )

        if output_path.stat().st_size == 0:
            raise RuntimeError("El archivo descargado está vacío.")

        update_job_status(
            job_id,
            status="finished",
            progress=100,
            filename=output_path.name,
        )

        log_info(
            f"Trabajo {job_id} completado: {output_path.name} "
            f"({output_path.stat().st_size} bytes)"
        )

    except subprocess.TimeoutExpired:
        error_msg = "La descarga superó el límite de 300 segundos."
        log_error(f"Trabajo {job_id}: {error_msg}")

        update_job_status(
            job_id,
            status="error",
            error=error_msg,
            progress=0,
        )

    except Exception as error:
        error_msg = str(error) or "Error desconocido durante la descarga."
        log_error(f"Error en trabajo {job_id}: {error_msg}")

        try:
            update_job_status(
                job_id,
                status="error",
                error=error_msg[-1500:],
                progress=0,
            )
        except Exception as status_error:
            log_error(
                f"No se pudo actualizar el estado de {job_id}: "
                f"{status_error}"
        )
