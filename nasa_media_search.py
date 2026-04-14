#!/usr/bin/env python3
"""
NASA Media Search - Aplicação de Busca de Imagens e Vídeos da NASA

MVP que permite buscar e visualizar imagens e vídeos do acervo público da NASA
através da API oficial, utilizando palavras-chave ou frases.

API: https://images-api.nasa.gov/search
"""

import requests
import webbrowser
import json
from typing import List, Dict, Optional


class NASAMediaSearch:
    """Classe principal para busca de mídia da NASA."""
    
    BASE_URL = "https://images-api.nasa.gov/search"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NASA-Media-Search-MVP/1.0'
        })
    
    def search(
        self, 
        query: str, 
        media_type: Optional[str] = None,
        page: int = 1
    ) -> List[Dict]:
        """
        Realiza busca na API da NASA.
        
        Args:
            query: Termo de busca (palavra-chave ou frase)
            media_type: Tipo de mídia ('image', 'video', ou None para ambos)
            page: Número da página para paginação
            
        Returns:
            Lista de dicionários com dados das mídias encontradas
        """
        params = {
            'q': query,
            'page': page
        }
        
        if media_type:
            params['media_type'] = media_type
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            items = data.get('collection', {}).get('items', [])
            return self._parse_results(items)
            
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição à API: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Erro ao processar resposta JSON: {e}")
            return []
    
    def _parse_results(self, items: List[Dict]) -> List[Dict]:
        """
        Extrai dados relevantes dos itens retornados pela API.
        
        Args:
            items: Lista de itens brutos da API
            
        Returns:
            Lista de dicionários com dados processados
        """
        results = []
        
        for item in items:
            data = item.get('data', [{}])[0]
            links = item.get('links', [])
            
            # Extrair URLs de mídia
            thumbnail_url = None
            media_url = None
            video_url = None
            
            for link in links:
                href = link.get('href', '')
                rel = link.get('rel', '')
                
                if rel == 'thumbnail':
                    thumbnail_url = href
                elif rel == 'preview':
                    media_url = href
                elif link.get('type', '').startswith('video'):
                    video_url = href
                
                # Se não tiver thumbnail, usa o primeiro link como fallback
                if not thumbnail_url and href:
                    thumbnail_url = href
            
            # Determinar tipo de mídia
            media_type = data.get('media_type', 'unknown')
            
            result = {
                'id': data.get('nasa_id', ''),
                'title': data.get('title', 'Sem título'),
                'description': data.get('description', 'Sem descrição'),
                'date_created': data.get('date_created', ''),
                'center': data.get('center', 'Desconhecido'),
                'media_type': media_type,
                'thumbnail_url': thumbnail_url,
                'media_url': media_url or thumbnail_url,
                'video_url': video_url,
                'link_508': data.get('link_508', '')
            }
            
            results.append(result)
        
        return results
    
    def open_in_browser(self, url: str) -> bool:
        """
        Abre URL no navegador padrão.
        
        Args:
            url: URL para abrir
            
        Returns:
            True se conseguiu abrir, False caso contrário
        """
        try:
            webbrowser.open(url)
            return True
        except Exception as e:
            print(f"Erro ao abrir navegador: {e}")
            return False
    
    def save_results(self, results: List[Dict], filename: str, format: str = 'json') -> bool:
        """
        Salva resultados em arquivo.
        
        Args:
            results: Lista de resultados para salvar
            filename: Nome do arquivo
            format: Formato do arquivo ('json' ou 'csv')
            
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            if format == 'json':
                if not filename.endswith('.json'):
                    filename += '.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
            elif format == 'csv':
                import csv
                if not filename.endswith('.csv'):
                    filename += '.csv'
                
                if results:
                    fieldnames = results[0].keys()
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(results)
            
            print(f"Resultados salvos em: {filename}")
            return True
        except Exception as e:
            print(f"Erro ao salvar arquivo: {e}")
            return False


def display_results(results: List[Dict], max_display: int = 20):
    """
    Exibe resultados formatados no terminal.
    
    Args:
        results: Lista de resultados para exibir
        max_display: Máximo de resultados para mostrar
    """
    if not results:
        print("\nNenhum resultado encontrado.")
        return
    
    count = min(len(results), max_display)
    print(f"\n{'='*70}")
    print(f"Resultados encontrados: {len(results)} (mostrando {count})")
    print(f"{'='*70}\n")
    
    for i, result in enumerate(results[:count], 1):
        media_type = result['media_type'].upper()
        title = result['title'][:60] + '...' if len(result['title']) > 60 else result['title']
        description = result['description'][:100] + '...' if len(result['description']) > 100 else result['description']
        
        print(f"[{i}] {title}")
        print(f"    Tipo: {media_type} | Centro: {result['center']}")
        print(f"    Data: {result['date_created'][:10] if result['date_created'] else 'N/A'}")
        print(f"    Descrição: {description}")
        print(f"    Thumbnail: {result['thumbnail_url']}")
        if result['video_url']:
            print(f"    Vídeo: {result['video_url']}")
        print()


def get_user_choice(max_option: int) -> Optional[int]:
    """
    Obtém escolha do usuário.
    
    Args:
        max_option: Número máximo de opção válida
        
    Returns:
        Número escolhido ou None para sair
    """
    while True:
        choice = input("\nDigite o número do item para abrir no navegador (0 para sair): ").strip()
        
        if choice == '0':
            return None
        
        try:
            num = int(choice)
            if 1 <= num <= max_option:
                return num
            else:
                print(f"Por favor, digite um número entre 1 e {max_option}")
        except ValueError:
            print("Por favor, digite um número válido")


def main():
    """Função principal da aplicação."""
    print("="*70)
    print("NASA MEDIA SEARCH - Busca de Imagens e Vídeos da NASA")
    print("="*70)
    print("\nBusque no acervo público da NASA por imagens e vídeos.\n")
    
    search_engine = NASAMediaSearch()
    
    while True:
        # Obter termo de busca
        query = input("Digite o termo de busca (ou 'sair' para encerrar): ").strip()
        
        if query.lower() in ['sair', 'exit', 'quit']:
            print("\nObrigado por usar o NASA Media Search!")
            break
        
        if not query:
            print("Por favor, digite um termo de busca.")
            continue
        
        # Obter filtros opcionais
        print("\nFiltros opcionais (deixe em branco para pular):")
        media_type = input("  Tipo de mídia (image/video): ").strip().lower() or None
        
        if media_type and media_type not in ['image', 'video']:
            print("Tipo de mídia inválido. Usando todos os tipos.")
            media_type = None
        
        # Realizar busca
        print(f"\nBuscando por '{query}'...")
        results = search_engine.search(query, media_type=media_type)
        
        # Exibir resultados
        display_results(results)
        
        if results:
            # Opção para abrir no navegador
            choice = get_user_choice(len(results))
            
            if choice is not None:
                selected = results[choice - 1]
                url_to_open = selected['video_url'] or selected['media_url'] or selected['thumbnail_url']
                
                if url_to_open:
                    print(f"\nAbrindo: {url_to_open}")
                    search_engine.open_in_browser(url_to_open)
                else:
                    print("URL não disponível para este item.")
            
            # Opção para salvar resultados
            save_choice = input("\nDeseja salvar os resultados? (s/n): ").strip().lower()
            if save_choice == 's':
                format_choice = input("Formato (json/csv): ").strip().lower() or 'json'
                filename = input("Nome do arquivo: ").strip() or f"nasa_search_{query.replace(' ', '_')}"
                search_engine.save_results(results, filename, format=format_choice)
        
        print("\n" + "-"*70)


if __name__ == "__main__":
    main()
