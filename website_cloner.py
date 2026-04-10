#!/usr/bin/env python3
"""
Website Cloner MVP

Um script Python que clona websites públicos de forma recursiva usando wget,
gera User-Agent aleatório para privacidade e compacta o resultado em ZIP.

Autor: PedroCoder
Licença: MIT
"""

import os
import random
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


# Lista de User-Agents de navegadores populares
USER_AGENTS: List[str] = [
    # Chrome - Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Chrome - macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Chrome - Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox - Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Firefox - macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Firefox - Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari - macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    # Edge - Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    # iOS - Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    # Android - Chrome
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.43 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.43 Mobile Safari/537.36",
]


def generate_random_user_agent() -> str:
    """
    Gera um User-Agent aleatório da lista predefinida.
    
    Returns:
        str: Uma string de User-Agent selecionada aleatoriamente.
    """
    return random.choice(USER_AGENTS)


def extract_domain(url: str) -> str:
    """
    Extrai o nome do domínio de uma URL para usar como nome do diretório.
    
    Args:
        url: A URL base do website.
        
    Returns:
        str: O nome do domínio extraído (ex: 'example.com').
    """
    # Remove protocolo e www se presente
    domain = url.replace("https://", "").replace("http://", "")
    domain = domain.lstrip("www.")
    # Pega apenas o domínio (antes da primeira barra)
    domain = domain.split("/")[0]
    # Remove porta se presente
    domain = domain.split(":")[0]
    return domain


def build_wget_command(user_agent: str, url: str) -> List[str]:
    """
    Constrói o comando wget com todos os argumentos necessários.
    
    Args:
        user_agent: A string do User-Agent a ser usada.
        url: A URL base do website a clonar.
        
    Returns:
        List[str]: Lista de argumentos para passar ao subprocesso.
    """
    command = [
        "wget",
        "--mirror",           # Download recursivo completo
        "--page-requisites",  # Baixa todos os recursos necessários para exibir a página
        "--convert-links",    # Converte links para navegação offline
        "--adjust-extension", # Adiciona extensão .html quando necessário
        "--no-parent",        # Não sobe para diretórios pais
        "--save-cookies",     # Salva cookies em arquivo
        "cookies.txt",
        "--keep-session-cookies",  # Mantém cookies de sessão
        f"--user-agent={user_agent}",  # User-Agent personalizado
        url,
    ]
    return command


def run_wget(command: List[str]) -> Tuple[bool, str]:
    """
    Executa o comando wget e captura o resultado.
    
    Args:
        command: Lista de argumentos do comando wget.
        
    Returns:
        Tuple[bool, str]: Tupla contendo (sucesso, mensagem de erro/sucesso).
    """
    try:
        print("\n" + "=" * 60)
        print("INICIANDO DOWNLOAD COM WGET")
        print("=" * 60)
        
        # Executa o wget e mostra output em tempo real
        process = subprocess.run(
            command,
            capture_output=False,  # Mostra output no terminal
            text=True,
        )
        
        if process.returncode == 0:
            return True, "Download concluído com sucesso!"
        else:
            # wget pode retornar códigos diferentes de 0 mesmo com sucesso parcial
            # (ex: páginas 404 não impedem o download do resto do site)
            if process.returncode in [0, 1, 2, 3, 4, 5, 6, 7, 8]:
                return True, f"Download concluído com avisos (código {process.returncode})"
            else:
                return False, f"Erro crítico no wget (código {process.returncode})"
                
    except FileNotFoundError:
        return False, "Erro: wget não encontrado. Instale o wget antes de executar este script."
    except Exception as e:
        return False, f"Erro inesperado na execução do wget: {str(e)}"


def find_downloaded_directory(domain: str) -> Optional[Path]:
    """
    Encontra o diretório criado pelo wget.
    
    Args:
        domain: O nome do domínio esperado.
        
    Returns:
        Optional[Path]: O caminho do diretório ou None se não encontrado.
    """
    # O wget cria um diretório com o nome do domínio
    possible_paths = [
        Path(domain),
        Path(domain.split(":")[0]),  # Caso tenha porta na URL
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_dir():
            return path
    
    # Se não encontrou exatamente, procura por diretórios que começam com o domínio
    current_dir = Path.cwd()
    for item in current_dir.iterdir():
        if item.is_dir() and item.name.startswith(domain.split(":")[0]):
            return item
    
    return None


def create_zip_archive(directory: Path, timestamp: str) -> Tuple[bool, str]:
    """
    Cria um arquivo ZIP contendo o diretório clonado.
    
    Args:
        directory: Caminho do diretório a ser compactado.
        timestamp: Timestamp para incluir no nome do arquivo.
        
    Returns:
        Tuple[bool, str]: Tupla contendo (sucesso, mensagem ou nome do arquivo).
    """
    # Gera nome do arquivo ZIP
    domain_safe = directory.name.replace(".", "_").replace(":", "_")
    zip_filename = f"backup_{domain_safe}_{timestamp}.zip"
    zip_path = Path(zip_filename)
    
    try:
        print("\n" + "=" * 60)
        print(f"COMPACTANDO DIRETÓRIO: {directory}")
        print("=" * 60)
        
        # Conta arquivos para feedback
        file_count = sum(1 for _ in directory.rglob("*") if _.is_file())
        print(f"Arquivos a serem compactados: {file_count}")
        
        # Cria o arquivo ZIP
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    # Calcula o caminho relativo para manter a estrutura no ZIP
                    arcname = file_path.relative_to(directory.parent)
                    zipf.write(file_path, arcname)
                    print(f"  Adicionado: {arcname}")
        
        return True, str(zip_filename)
        
    except PermissionError:
        return False, "Erro de permissão ao criar arquivo ZIP"
    except Exception as e:
        return False, f"Erro ao criar arquivo ZIP: {str(e)}"


def cleanup_cookies() -> None:
    """Remove o arquivo de cookies se existir."""
    cookies_file = Path("cookies.txt")
    if cookies_file.exists():
        try:
            cookies_file.unlink()
            print("\nArquivo de cookies limpo.")
        except Exception:
            pass


def main() -> int:
    """
    Função principal do script.
    
    Orquestra todo o processo de clonagem do website:
    1. Solicita URL ao usuário
    2. Gera User-Agent aleatório
    3. Executa wget para clonar o site
    4. Compacta o resultado em ZIP
    
    Returns:
        int: Código de retorno (0 para sucesso, 1 para erro).
    """
    print("\n" + "=" * 60)
    print("WEBSITE CLONER MVP - Python")
    print("=" * 60)
    print("\nEste script clona um website público e o compacta em um arquivo ZIP.")
    print("Nota: Respeite os termos de uso e robots.txt de cada website.\n")
    
    # Solicita URL do usuário
    url = input("Digite a URL base do website (ex: https://exemplo.com): ").strip()
    
    if not url:
        print("\nErro: URL não pode ser vazia.")
        return 1
    
    # Validação básica da URL
    if not (url.startswith("http://") or url.startswith("https://")):
        print("\nErro: URL deve começar com http:// ou https://")
        return 1
    
    # Gera User-Agent aleatório
    print("\n[1/4] Gerando User-Agent aleatório...")
    user_agent = generate_random_user_agent()
    print(f"✓ User-Agent selecionado:\n  {user_agent}\n")
    
    # Extrai domínio para nome do diretório
    domain = extract_domain(url)
    print(f"[2/4] Domínio identificado: {domain}")
    
    # Constroi comando wget
    command = build_wget_command(user_agent, url)
    print(f"✓ Comando wget preparado com {len(command)} argumentos")
    
    # Executa wget
    success, message = run_wget(command)
    print(f"\n{message}")
    
    if not success:
        print("\n❌ Falha crítica: não foi possível completar o download.")
        return 1
    
    # Encontra diretório baixado
    print("\n[3/4] Procurando diretório baixado...")
    downloaded_dir = find_downloaded_directory(domain)
    
    if downloaded_dir is None:
        print(f"\n❌ Erro: Diretório '{domain}' não encontrado após o download.")
        print("Verifique se o wget foi executado corretamente.")
        return 1
    
    print(f"✓ Diretório encontrado: {downloaded_dir.absolute()}")
    
    # Gera timestamp para nome do arquivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Cria arquivo ZIP
    print("\n[4/4] Criando arquivo ZIP...")
    success, result = create_zip_archive(downloaded_dir, timestamp)
    
    if success:
        print(f"\n{'=' * 60}")
        print("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
        print(f"{'=' * 60}")
        print(f"\n📦 Arquivo ZIP gerado: {result}")
        print(f"📁 Diretório clonado: {downloaded_dir}")
        print(f"\nO arquivo ZIP contém toda a estrutura do website clonado.")
        print(f"Você pode extrair o ZIP e navegar offline pelo site.\n")
        
        # Limpa arquivo de cookies
        cleanup_cookies()
        
        return 0
    else:
        print(f"\n❌ Erro na compactação: {result}")
        print(f"⚠️  O diretório clonado ainda está disponível em: {downloaded_dir}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
