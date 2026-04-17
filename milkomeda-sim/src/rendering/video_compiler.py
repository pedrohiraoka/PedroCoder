"""
video_compiler.py - Compilação de frames em vídeo para Milkomeda.

Este módulo compila frames PNG renderizados em vídeos MP4 usando
ffmpeg ou matplotlib.animation como fallback.
"""

from typing import List, Optional, Tuple
import subprocess
import shutil
from pathlib import Path
import numpy as np
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VideoCompiler:
    """
    Compilador de frames PNG em vídeo MP4.

    Usa ffmpeg quando disponível, com fallback para matplotlib.

    Attributes:
        fps: Frames por segundo do vídeo.
        resolution: Resolução do vídeo (largura, altura).
        codec: Codec de vídeo.
        bitrate: Bitrate do vídeo.
    """

    def __init__(
        self,
        fps: int = 30,
        resolution: Tuple[int, int] = (1280, 720),
        codec: str = "h264",
        bitrate: str = "2M",
    ):
        """
        Inicializa o compilador de vídeo.

        Args:
            fps: Frames por segundo.
            resolution: Resolução (width, height).
            codec: Codec de vídeo.
            bitrate: Bitrate (ex: '2M').
        """
        self.fps = fps
        self.resolution = resolution
        self.codec = codec
        self.bitrate = bitrate

        # Verificar disponibilidade do ffmpeg
        self.ffmpeg_available = shutil.which("ffmpeg") is not None

        logger.info(
            f"VideoCompiler inicializado: fps={fps}, res={resolution}, "
            f"ffmpeg={'disponível' if self.ffmpeg_available else 'não encontrado'}"
        )

    def compile_frames(
        self,
        frame_paths: List[Path],
        output_path: Path,
        cleanup: bool = False,
    ) -> Path:
        """
        Compila frames em vídeo.

        Args:
            frame_paths: Lista de caminhos dos frames PNG.
            output_path: Caminho do vídeo de saída.
            cleanup: Se True, remove frames após compilar.

        Returns:
            Path: Caminho do vídeo criado.

        Raises:
            FileNotFoundError: Se ffmpeg não estiver disponível e matplotlib falhar.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if len(frame_paths) == 0:
            raise ValueError("Nenhum frame fornecido para compilação")

        logger.info(f"Compilando {len(frame_paths)} frames em vídeo...")

        if self.ffmpeg_available:
            return self._compile_with_ffmpeg(frame_paths, output_path, cleanup)
        else:
            logger.warning("ffmpeg não encontrado, tentando matplotlib...")
            return self._compile_with_matplotlib(frame_paths, output_path, cleanup)

    def _compile_with_ffmpeg(
        self,
        frame_paths: List[Path],
        output_path: Path,
        cleanup: bool = False,
    ) -> Path:
        """
        Compila frames usando ffmpeg diretamente.

        Args:
            frame_paths: Lista de frames.
            output_path: Saída do vídeo.
            cleanup: Remover frames após compilação.

        Returns:
            Path: Vídeo compilado.
        """
        # Criar arquivo de lista de frames (para muitos arquivos)
        list_file = output_path.parent / "frames_list.txt"

        with open(list_file, 'w') as f:
            for frame_path in frame_paths:
                f.write(f"file '{frame_path.absolute()}'\n")

        # Comando ffmpeg
        cmd = [
            "ffmpeg",
            "-y",  # Sobrescrever saída
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-vf", f"fps={self.fps},scale={self.resolution[0]}:{self.resolution[1]}",
            "-c:v", "libx264",
            "-preset", "medium",
            "-b:v", self.bitrate,
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_path),
        ]

        logger.debug(f"Executando: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300,  # 5 minutos timeout
            )

            if result.returncode == 0:
                logger.info(f"Vídeo compilado com sucesso: {output_path}")

                # Limpar frames se solicitado
                if cleanup:
                    self._cleanup_frames(frame_paths, list_file)

                return output_path
            else:
                raise RuntimeError(f"ffmpeg falhou: {result.stderr}")

        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg error: {e.stderr}")
            raise
        except subprocess.TimeoutExpired:
            logger.error("Timeout na compilação do vídeo")
            raise

    def _compile_with_matplotlib(
        self,
        frame_paths: List[Path],
        output_path: Path,
        cleanup: bool = False,
    ) -> Path:
        """
        Compila frames usando matplotlib.animation (fallback).

        Args:
            frame_paths: Lista de frames.
            output_path: Saída do vídeo.
            cleanup: Remover frames após compilação.

        Returns:
            Path: Vídeo compilado.
        """
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation, PillowWriter
        from matplotlib.image import imread

        logger.info("Usando matplotlib para compilação...")

        # Carregar primeiro frame para dimensões
        first_frame = imread(str(frame_paths[0]))
        fig, ax = plt.subplots(figsize=(12, 7))
        img_display = ax.imshow(first_frame)
        ax.axis('off')

        def update(frame_idx):
            if frame_idx < len(frame_paths):
                frame_data = imread(str(frame_paths[frame_idx]))
                img_display.set_data(frame_data)
            return [img_display]

        anim = FuncAnimation(fig, update, frames=len(frame_paths), interval=1000/self.fps)

        # Salvar como MP4 se possível, senão GIF
        try:
            anim.save(
                str(output_path),
                writer='pillow',
                fps=self.fps,
                dpi=100,
            )
            logger.info(f"Vídeo salvo via matplotlib: {output_path}")
        except Exception as e:
            # Fallback para GIF
            gif_path = output_path.with_suffix('.gif')
            anim.save(str(gif_path), writer='pillow', fps=self.fps//2)
            logger.info(f"GIF salvo: {gif_path}")
            output_path = gif_path

        plt.close(fig)

        if cleanup:
            self._cleanup_frames(frame_paths)

        return output_path

    def _cleanup_frames(
        self,
        frame_paths: List[Path],
        list_file: Optional[Path] = None,
    ) -> None:
        """
        Remove arquivos de frames temporários.

        Args:
            frame_paths: Lista de frames para remover.
            list_file: Arquivo de lista ffmpeg para remover.
        """
        removed = 0
        for path in frame_paths:
            try:
                if path.exists():
                    path.unlink()
                    removed += 1
            except Exception as e:
                logger.warning(f"Não foi possível remover {path}: {e}")

        if list_file and list_file.exists():
            try:
                list_file.unlink()
            except Exception:
                pass

        logger.info(f"{removed} frames removidos")

    def add_watermark(
        self,
        input_video: Path,
        output_video: Path,
        text: str = "Milkomeda Sim",
    ) -> Path:
        """
        Adiciona marca d'água/texto ao vídeo.

        Args:
            input_video: Vídeo de entrada.
            output_video: Vídeo de saída.
            text: Texto da marca d'água.

        Returns:
            Path: Vídeo com watermark.
        """
        if not self.ffmpeg_available:
            logger.warning("ffmpeg necessário para watermark")
            return input_video

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(input_video),
            "-vf", f"drawtext=text='{text}':fontsize=24:fontcolor=white:x=10:y=10",
            "-c:a", "copy",
            str(output_video),
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Watermark adicionada: {output_video}")
            return output_video
        except subprocess.CalledProcessError as e:
            logger.error(f"Falha ao adicionar watermark: {e}")
            return input_video

    def get_video_info(self, video_path: Path) -> dict:
        """
        Obtém informações sobre um vídeo usando ffprobe.

        Args:
            video_path: Caminho do vídeo.

        Returns:
            dict: Informações do vídeo (duração, resolução, etc.).
        """
        if not self.ffmpeg_available:
            return {"error": "ffmpeg não disponível"}

        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            import json
            info = json.loads(result.stdout)
            logger.debug(f"Informações do vídeo: {info}")
            return info
        except Exception as e:
            logger.error(f"Erro ao obter info do vídeo: {e}")
            return {"error": str(e)}


def compile_frames_to_video(
    frame_paths: List[Path],
    output_path: Path,
    fps: int = 30,
    resolution: Tuple[int, int] = (1280, 720),
    codec: str = "h264",
    bitrate: str = "2M",
    cleanup: bool = False,
) -> Path:
    """
    Função utilitária para compilar frames em vídeo.

    Args:
        frame_paths: Lista de frames PNG.
        output_path: Vídeo de saída.
        fps: Frames por segundo.
        resolution: Resolução.
        codec: Codec.
        bitrate: Bitrate.
        cleanup: Remover frames após compilação.

    Returns:
        Path: Vídeo compilado.
    """
    compiler = VideoCompiler(
        fps=fps,
        resolution=resolution,
        codec=codec,
        bitrate=bitrate,
    )

    return compiler.compile_frames(frame_paths, output_path, cleanup)
