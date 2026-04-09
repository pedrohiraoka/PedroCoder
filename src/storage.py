"""
Storage - Armazenamento e exportação de dados

Módulo responsável por persistir dados extraídos em diferentes
formatos: JSON, CSV e SQLite.
"""

import json
import csv
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from enum import Enum

from src.models import Company, CrawledPage, Price, Service, Contact


logger = logging.getLogger("crawler.storage")


class StorageFormat(str, Enum):
    """Formatos de armazenamento suportados."""
    JSON = "json"
    CSV = "csv"
    SQLITE = "sqlite"


class Storage:
    """
    Gerenciador de armazenamento para dados do crawler.
    
    Suporta múltiplos formatos de exportação e persistência
    em banco de dados SQLite.
    """
    
    def __init__(self, output_path: Optional[str] = None):
        """
        Inicializa storage.
        
        Args:
            output_path: Caminho base para saída de arquivos
        """
        self.output_path = Path(output_path) if output_path else Path(".")
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Conexão SQLite (lazy initialization)
        self._db_connection: Optional[sqlite3.Connection] = None
        self._db_path: Optional[Path] = None
    
    def save(
        self,
        data: Union[List[CrawledPage], List[Company]],
        format: StorageFormat = StorageFormat.JSON,
        filename: Optional[str] = None
    ) -> str:
        """
        Salva dados no formato especificado.
        
        Args:
            data: Dados para salvar (lista de CrawledPage ou Company)
            format: Formato de armazenamento
            filename: Nome do arquivo (opcional)
        
        Returns:
            Caminho do arquivo salvo
        """
        # Extrai companies se for lista de CrawledPage
        if data and isinstance(data[0], CrawledPage):
            companies = []
            for page in data:
                companies.extend(page.companies)
                if page.company:
                    companies.append(page.company)
            data = companies
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == StorageFormat.JSON:
            filename = filename or f"companies_{timestamp}.json"
            return self._save_json(data, filename)
        
        elif format == StorageFormat.CSV:
            filename = filename or f"companies_{timestamp}.csv"
            return self._save_csv(data, filename)
        
        elif format == StorageFormat.SQLITE:
            filename = filename or f"companies_{timestamp}.db"
            return self._save_sqlite(data, filename)
        
        else:
            raise ValueError(f"Formato não suportado: {format}")
    
    def _save_json(self, data: List[Company], filename: str) -> str:
        """Salva dados em JSON."""
        filepath = self.output_path / filename
        
        # Converte modelos para dict
        records = [self._company_to_dict(company) for company in data]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Dados salvos em JSON: {filepath} ({len(data)} registros)")
        return str(filepath)
    
    def _save_csv(self, data: List[Company], filename: str) -> str:
        """Salva dados em CSV."""
        filepath = self.output_path / filename
        
        if not data:
            logger.warning("Nenhum dado para salvar em CSV")
            return str(filepath)
        
        # Prepara colunas principais
        fieldnames = [
            'id', 'nome', 'descricao', 'categoria', 'url_origem', 'data_coleta',
            'email', 'telefone', 'website', 'endereco',
            'servicos_count', 'precos_count'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for company in data:
                row = {
                    'id': company.id,
                    'nome': company.nome,
                    'descricao': company.descricao[:500] if company.descricao else '',
                    'categoria': company.categoria or '',
                    'url_origem': str(company.url_origem) if company.url_origem else '',
                    'data_coleta': company.data_coleta.isoformat(),
                    'email': company.contato.email if company.contato else '',
                    'telefone': company.contato.telefone if company.contato else '',
                    'website': str(company.contato.website) if company.contato and company.contato.website else '',
                    'endereco': company.contato.endereco if company.contato else '',
                    'servicos_count': len(company.servicos),
                    'precos_count': len(company.precos)
                }
                writer.writerow(row)
        
        logger.info(f"Dados salvos em CSV: {filepath} ({len(data)} registros)")
        return str(filepath)
    
    def _save_sqlite(self, data: List[Company], filename: str) -> str:
        """Salva dados em SQLite."""
        filepath = self.output_path / filename
        
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        
        try:
            # Cria tabela de empresas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    descricao TEXT,
                    categoria TEXT,
                    url_origem TEXT,
                    data_coleta TEXT,
                    email TEXT,
                    telefone TEXT,
                    website TEXT,
                    endereco TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Cria tabela de serviços
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER,
                    nome TEXT NOT NULL,
                    descricao TEXT,
                    preco_valor REAL,
                    preco_moeda TEXT,
                    categoria TEXT,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            ''')
            
            # Cria tabela de preços
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER,
                    valor REAL NOT NULL,
                    moeda TEXT,
                    formato_original TEXT,
                    tipo TEXT,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            ''')
            
            # Insere empresas
            for company in data:
                cursor.execute('''
                    INSERT INTO companies (nome, descricao, categoria, url_origem, data_coleta, 
                                          email, telefone, website, endereco, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    company.nome,
                    company.descricao,
                    company.categoria,
                    str(company.url_origem) if company.url_origem else None,
                    company.data_coleta.isoformat(),
                    company.contato.email if company.contato else None,
                    company.contato.telefone if company.contato else None,
                    str(company.contato.website) if company.contato and company.contato.website else None,
                    company.contato.endereco if company.contato else None,
                    json.dumps(company.metadata) if company.metadata else None
                ))
                
                company_id = cursor.lastrowid
                
                # Insere serviços
                for service in company.servicos:
                    cursor.execute('''
                        INSERT INTO services (company_id, nome, descricao, preco_valor, preco_moeda, categoria)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        company_id,
                        service.nome,
                        service.descricao,
                        service.preco.valor if service.preco else None,
                        service.preco.moeda if service.preco else None,
                        service.categoria
                    ))
                
                # Insere preços
                for price in company.precos:
                    cursor.execute('''
                        INSERT INTO prices (company_id, valor, moeda, formato_original, tipo)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        company_id,
                        price.valor,
                        price.moeda,
                        price.formato_original,
                        price.tipo
                    ))
            
            conn.commit()
            logger.info(f"Dados salvos em SQLite: {filepath} ({len(data)} empresas)")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro ao salvar em SQLite: {e}")
            raise
        finally:
            conn.close()
        
        return str(filepath)
    
    def init_database(self, db_path: str) -> None:
        """
        Inicializa banco de dados para inserção incremental.
        
        Args:
            db_path: Caminho do banco de dados SQLite
        """
        self._db_path = Path(db_path)
        self._db_connection = sqlite3.connect(db_path)
        
        cursor = self._db_connection.cursor()
        
        # Cria tabelas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                descricao TEXT,
                categoria TEXT,
                url_origem TEXT,
                data_coleta TEXT,
                email TEXT,
                telefone TEXT,
                website TEXT,
                endereco TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(nome, url_origem)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawl_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                status_code INTEGER,
                empresas_extraidas INTEGER,
                tempo_processamento REAL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_company_nome ON companies(nome)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_company_categoria ON companies(categoria)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_crawl_url ON crawl_log(url)')
        
        self._db_connection.commit()
        logger.info(f"Banco de dados inicializado: {db_path}")
    
    def insert_company(self, company: Company) -> Optional[int]:
        """
        Insere empresa no banco de dados (se já não existir).
        
        Args:
            company: Empresa para inserir
        
        Returns:
            ID da empresa inserida ou existente
        """
        if not self._db_connection:
            raise RuntimeError("Banco de dados não inicializado. Chame init_database primeiro.")
        
        cursor = self._db_connection.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO companies (nome, descricao, categoria, url_origem, data_coleta,
                                                  email, telefone, website, endereco, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                company.nome,
                company.descricao,
                company.categoria,
                str(company.url_origem) if company.url_origem else None,
                company.data_coleta.isoformat(),
                company.contato.email if company.contato else None,
                company.contato.telefone if company.contato else None,
                str(company.contato.website) if company.contato and company.contato.website else None,
                company.contato.endereco if company.contato else None,
                json.dumps(company.metadata) if company.metadata else None
            ))
            
            self._db_connection.commit()
            
            # Obtém ID (inserido ou existente)
            cursor.execute('''
                SELECT id FROM companies WHERE nome = ? AND url_origem = ?
            ''', (company.nome, str(company.url_origem) if company.url_origem else None))
            
            result = cursor.fetchone()
            return result[0] if result else None
            
        except sqlite3.Error as e:
            logger.error(f"Erro ao inserir empresa: {e}")
            return None
    
    def log_crawl(self, page: CrawledPage) -> None:
        """
        Loga entrada de crawl no banco de dados.
        
        Args:
            page: Página crawlada
        """
        if not self._db_connection:
            return
        
        cursor = self._db_connection.cursor()
        
        cursor.execute('''
            INSERT INTO crawl_log (url, status_code, empresas_extraidas, tempo_processamento)
            VALUES (?, ?, ?, ?)
        ''', (
            str(page.url),
            page.status_code,
            page.total_empresas,
            page.tempo_processamento
        ))
        
        self._db_connection.commit()
    
    def close(self) -> None:
        """Fecha conexão com banco de dados."""
        if self._db_connection:
            self._db_connection.close()
            self._db_connection = None
            logger.debug("Conexão com banco de dados fechada")
    
    def _company_to_dict(self, company: Company) -> Dict[str, Any]:
        """Converte Company para dicionário serializável."""
        return {
            'id': company.id,
            'nome': company.nome,
            'descricao': company.descricao,
            'categoria': company.categoria,
            'contato': {
                'email': company.contato.email if company.contato else None,
                'telefone': company.contato.telefone if company.contato else None,
                'website': str(company.contato.website) if company.contato and company.contato.website else None,
                'endereco': company.contato.endereco if company.contato else None,
                'redes_sociais': company.contato.redes_sociais if company.contato else {}
            } if company.contato else None,
            'servicos': [
                {
                    'nome': s.nome,
                    'descricao': s.descricao,
                    'preco': {
                        'valor': s.preco.valor,
                        'moeda': s.preco.moeda,
                        'formato_original': s.preco.formato_original
                    } if s.preco else None,
                    'categoria': s.categoria
                }
                for s in company.servicos
            ],
            'precos': [
                {
                    'valor': p.valor,
                    'moeda': p.moeda,
                    'formato_original': p.formato_original,
                    'tipo': p.tipo
                }
                for p in company.precos
            ],
            'url_origem': str(company.url_origem) if company.url_origem else None,
            'data_coleta': company.data_coleta.isoformat(),
            'metadata': company.metadata
        }
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def export_companies(
    companies: List[Company],
    output_dir: str = "./output",
    formats: Optional[List[StorageFormat]] = None
) -> List[str]:
    """
    Função utilitária para exportar empresas em múltiplos formatos.
    
    Args:
        companies: Lista de empresas para exportar
        output_dir: Diretório de saída
        formats: Lista de formatos (padrão: [JSON])
    
    Returns:
        Lista de caminhos dos arquivos criados
    """
    if formats is None:
        formats = [StorageFormat.JSON]
    
    storage = Storage(output_dir)
    files_created = []
    
    for fmt in formats:
        filepath = storage.save(companies, format=fmt)
        files_created.append(filepath)
    
    return files_created
