"""
Gerenciador da carteira de investimentos.

Este módulo é responsável por persistir e gerenciar os dados da carteira
localmente usando um arquivo JSON.
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from models import Carteira, Ativo, TipoAtivo


ARQUIVO_CARTEIRA = "carteira.json"


class PortfolioManager:
    """
    Gerencia a carteira de investimentos com persistência em JSON.

    Esta classe fornece métodos para adicionar, remover e atualizar
    ativos na carteira, além de carregar e salvar os dados em disco.
    """

    def __init__(self, arquivo_path: str = ARQUIVO_CARTEIRA) -> None:
        """
        Inicializa o gerenciador de carteira.

        Args:
            arquivo_path: Caminho para o arquivo JSON de persistência.
        """
        self.arquivo_path = Path(arquivo_path)
        self.carteira = Carteira()
        self._carregar_carteira()

    def _carregar_carteira(self) -> None:
        """
        Carrega a carteira do arquivo JSON se ele existir.

        Se o arquivo não existir ou estiver corrompido, inicia uma
        carteira vazia.
        """
        if not self.arquivo_path.exists():
            print("[INFO] Nenhuma carteira encontrada. Iniciando carteira vazia.")
            return

        try:
            with open(self.arquivo_path, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                self.carteira = Carteira.from_dict(dados)
                print(f"[INFO] Carteira carregada com sucesso de {self.arquivo_path}")
        except json.JSONDecodeError as e:
            print(f"[ERRO] Erro ao parsear arquivo da carteira: {e}")
            print("[INFO] Iniciando carteira vazia.")
            self.carteira = Carteira()
        except Exception as e:
            print(f"[ERRO] Erro ao carregar carteira: {e}")
            print("[INFO] Iniciando carteira vazia.")
            self.carteira = Carteira()

    def salvar_carteira(self) -> bool:
        """
        Salva a carteira no arquivo JSON.

        Returns:
            True se salvo com sucesso, False caso contrário.
        """
        try:
            # Garantir que o diretório existe
            self.arquivo_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.arquivo_path, 'w', encoding='utf-8') as f:
                json.dump(
                    self.carteira.to_dict(),
                    f,
                    indent=2,
                    ensure_ascii=False,
                    default=str
                )
            print(f"[INFO] Carteira salva com sucesso em {self.arquivo_path}")
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao salvar carteira: {e}")
            return False

    def adicionar_ativo(
        self,
        ticker: str,
        tipo: str,
        quantidade: float,
        preco_medio: float
    ) -> bool:
        """
        Adiciona ou atualiza um ativo na carteira.

        Args:
            ticker: Código do ativo (ex: PETR4, HGLG11).
            tipo: Tipo do ativo ('ACAO' ou 'FII').
            quantidade: Quantidade de cotas/ações.
            preco_medio: Preço médio de compra.

        Returns:
            True se adicionado/atualizado com sucesso, False caso contrário.
        """
        try:
            # Validar entradas
            if quantidade <= 0:
                print("[ERRO] A quantidade deve ser positiva.")
                return False
            
            if preco_medio <= 0:
                print("[ERRO] O preço médio deve ser positivo.")
                return False

            tipo_ativo = TipoAtivo.ACAO if tipo.upper() == "ACAO" else TipoAtivo.FII
            
            # Verificar se já existe o ativo
            ativo_existente = self.carteira.obter_ativo(ticker)
            
            if ativo_existente:
                # Atualizar quantidade e preço médio (média ponderada)
                qtd_atual = ativo_existente.quantidade
                pm_atual = ativo_existente.preco_medio
                
                nova_qtd = qtd_atual + quantidade
                novo_pm = ((pm_atual * qtd_atual) + (preco_medio * quantidade)) / nova_qtd
                
                ativo_existente.quantidade = nova_qtd
                ativo_existente.preco_medio = round(novo_pm, 2)
                print(f"[INFO] Ativo {ticker} atualizado. Nova quantidade: {nova_qtd}, Novo PM: R$ {novo_pm:.2f}")
            else:
                # Criar novo ativo
                ativo = Ativo(
                    ticker=ticker,
                    tipo=tipo_ativo,
                    quantidade=quantidade,
                    preco_medio=round(preco_medio, 2)
                )
                self.carteira.adicionar_ativo(ativo)
                print(f"[INFO] Ativo {ticker} adicionado à carteira.")
            
            # Salvar automaticamente
            self.salvar_carteira()
            return True
            
        except Exception as e:
            print(f"[ERRO] Falha ao adicionar ativo: {e}")
            return False

    def remover_ativo(self, ticker: str) -> bool:
        """
        Remove um ativo da carteira.

        Args:
            ticker: Código do ativo a ser removido.

        Returns:
            True se removido com sucesso, False se o ativo não existir.
        """
        if self.carteira.remover_ativo(ticker):
            print(f"[INFO] Ativo {ticker.upper()} removido da carteira.")
            self.salvar_carteira()
            return True
        else:
            print(f"[ERRO] Ativo {ticker.upper()} não encontrado na carteira.")
            return False

    def atualizar_preco_medio(
        self,
        ticker: str,
        novo_preco_medio: float,
        nova_quantidade: Optional[float] = None
    ) -> bool:
        """
        Atualiza o preço médio e/ou quantidade de um ativo.

        Args:
            ticker: Código do ativo.
            novo_preco_medio: Novo preço médio.
            nova_quantidade: Nova quantidade (opcional).

        Returns:
            True se atualizado com sucesso, False caso contrário.
        """
        try:
            ativo = self.carteira.obter_ativo(ticker)
            
            if not ativo:
                print(f"[ERRO] Ativo {ticker.upper()} não encontrado.")
                return False
            
            if novo_preco_medio <= 0:
                print("[ERRO] O preço médio deve ser positivo.")
                return False
            
            if nova_quantidade is not None and nova_quantidade <= 0:
                print("[ERRO] A quantidade deve ser positiva.")
                return False
            
            ativo.preco_medio = round(novo_preco_medio, 2)
            
            if nova_quantidade is not None:
                ativo.quantidade = nova_quantidade
            
            print(f"[INFO] Ativo {ticker.upper()} atualizado.")
            self.salvar_carteira()
            return True
            
        except Exception as e:
            print(f"[ERRO] Falha ao atualizar ativo: {e}")
            return False

    def listar_ativos(self):
        """
        Retorna a lista de ativos da carteira.

        Returns:
            Lista de objetos Ativo.
        """
        return self.carteira.listar_ativos()

    def obter_carteira(self) -> Carteira:
        """
        Retorna o objeto Carteira completo.

        Returns:
            Objeto Carteira.
        """
        return self.carteira

    def total_ativos(self) -> int:
        """
        Retorna o número total de ativos na carteira.

        Returns:
            Quantidade de ativos.
        """
        return len(self.carteira.ativos)

    def limpar_carteira(self, confirmar: bool = False) -> bool:
        """
        Limpa toda a carteira (remove todos os ativos).

        Args:
            confirmar: Deve ser True para confirmar a operação.

        Returns:
            True se limpo com sucesso, False caso contrário.
        """
        if not confirmar:
            print("[ERRO] É necessário confirmar a limpeza da carteira.")
            return False
        
        self.carteira = Carteira()
        
        # Remover arquivo se existir
        if self.arquivo_path.exists():
            self.arquivo_path.unlink()
        
        print("[INFO] Carteira limpa com sucesso.")
        return True
