"""
Módulo de exportação de dados da carteira.

Este módulo é responsável por gerar arquivos JSON consolidados
com todos os dados da carteira, resumo e histórico de proventos.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from models import Carteira, Provento
from calculator import AtivoConsolidado, ResumoCarteira


def gerar_exportacao_json(
    ativos_consolidados: List[AtivoConsolidado],
    resumo: ResumoCarteira,
    arquivo_saida: str = "carteira_consolidada.json",
    versao: str = "1.0"
) -> bool:
    """
    Gera um arquivo JSON completo com todos os dados da carteira.

    A estrutura do JSON segue o formato:
    {
        "meta_dados": { "data_geracao": "...", "versao": "1.0" },
        "resumo_carteira": { ... },
        "ativos": [ ... ],
        "historico_proventos": [ ... ]
    }

    Args:
        ativos_consolidados: Lista de ativos com dados consolidados.
        resumo: Objeto com resumo da carteira.
        arquivo_saida: Nome do arquivo de saída.
        versao: Versão do formato de exportação.

    Returns:
        True se exportado com sucesso, False caso contrário.
    """
    try:
        # Coletar todos os proventos únicos
        todos_proventos = []
        proventos_vistos = set()
        
        for ativo in ativos_consolidados:
            for provento in ativo.proventos:
                # Criar chave única para evitar duplicatas
                chave = (provento.ticker, provento.data.isoformat(), provento.valor_por_cota)
                if chave not in proventos_vistos:
                    proventos_vistos.add(chave)
                    todos_proventos.append(provento.to_dict())
        
        # Ordenar proventos por data (mais recente primeiro)
        todos_proventos.sort(key=lambda p: p["data"], reverse=True)
        
        # Estruturar dados para exportação
        dados_exportacao = {
            "meta_dados": {
                "data_geracao": datetime.now().isoformat(),
                "versao": versao,
                "descricao": "Exportação de carteira de investimentos - Ações e FIIs"
            },
            "resumo_carteira": resumo.to_dict(),
            "ativos": [ativo.to_dict() for ativo in ativos_consolidados],
            "historico_proventos": todos_proventos
        }
        
        # Garantir que o diretório existe
        path_saida = Path(arquivo_saida)
        path_saida.parent.mkdir(parents=True, exist_ok=True)
        
        # Escrever arquivo JSON formatado
        with open(path_saida, 'w', encoding='utf-8') as f:
            json.dump(
                dados_exportacao,
                f,
                indent=2,
                ensure_ascii=False,
                default=str
            )
        
        print(f"[INFO] Exportação realizada com sucesso: {arquivo_saida}")
        print(f"     - Ativos exportados: {len(ativos_consolidados)}")
        print(f"     - Proventos exportados: {len(todos_proventos)}")
        return True
        
    except Exception as e:
        print(f"[ERRO] Falha ao exportar dados: {e}")
        return False


def gerar_relatorio_simples(
    ativos_consolidados: List[AtivoConsolidado],
    resumo: ResumoCarteira,
    arquivo_saida: str = "relatorio_carteira.json"
) -> bool:
    """
    Gera um relatório JSON simplificado apenas com dados essenciais.

    Útil para visualização rápida ou integração com outras ferramentas.

    Args:
        ativos_consolidados: Lista de ativos com dados consolidados.
        resumo: Objeto com resumo da carteira.
        arquivo_saida: Nome do arquivo de saída.

    Returns:
        True se exportado com sucesso, False caso contrário.
    """
    try:
        dados_relatorio = {
            "data_geracao": datetime.now().isoformat(),
            "resumo": {
                "valor_total_investido": resumo.valor_total_investido,
                "valor_total_mercado": resumo.valor_total_mercado,
                "lucro_prejuizo": resumo.lucro_prejuizo_total,
                "lucro_prejuizo_percentual": resumo.lucro_prejuizo_percentual,
                "proventos_12m": resumo.total_proventos_12m,
                "quantidade_ativos": resumo.quantidade_ativos
            },
            "ativos": [
                {
                    "ticker": a.ticker,
                    "tipo": a.tipo.value,
                    "quantidade": a.quantidade,
                    "preco_medio": a.preco_medio,
                    "preco_atual": a.preco_atual,
                    "valor_mercado": a.valor_mercado,
                    "lucro_prejuizo_percentual": a.lucro_prejuizo_percentual,
                    "dividend_yield": a.dividend_yield,
                    "yield_on_cost": a.yield_on_cost
                }
                for a in ativos_consolidados
            ]
        }
        
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(dados_relatorio, f, indent=2, ensure_ascii=False)
        
        print(f"[INFO] Relatório simples gerado: {arquivo_saida}")
        return True
        
    except Exception as e:
        print(f"[ERRO] Falha ao gerar relatório simples: {e}")
        return False


def carregar_exportacao_anterior(arquivo_path: str) -> Optional[Dict[str, Any]]:
    """
    Carrega uma exportação JSON anterior.

    Args:
        arquivo_path: Caminho para o arquivo JSON.

    Returns:
        Dicionário com os dados ou None se houver erro.
    """
    try:
        path = Path(arquivo_path)
        if not path.exists():
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERRO] Falha ao carregar exportação anterior: {e}")
        return None


def validar_exportacao(dados: Dict[str, Any]) -> bool:
    """
    Valida se uma exportação JSON tem a estrutura esperada.

    Args:
        dados: Dicionário com os dados da exportação.

    Returns:
        True se válido, False caso contrário.
    """
    campos_obrigatorios = ["meta_dados", "resumo_carteira", "ativos"]
    
    for campo in campos_obrigatorios:
        if campo not in dados:
            print(f"[ERRO] Campo obrigatório ausente: {campo}")
            return False
    
    # Validar meta_dados
    if "data_geracao" not in dados["meta_dados"]:
        print("[ERRO] Data de geração ausente nos meta_dados")
        return False
    
    # Validar ativos
    if not isinstance(dados["ativos"], list):
        print("[ERRO] Ativos deve ser uma lista")
        return False
    
    return True


# Fim do módulo exporter
