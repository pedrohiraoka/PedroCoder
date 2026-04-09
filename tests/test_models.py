"""
Testes para modelos Pydantic

Valida schemas de Company, Contact, Service, Price.
"""

import pytest
from datetime import datetime
from src.models import Company, Contact, Service, Price


class TestPrice:
    """Testes para modelo Price."""
    
    def test_price_valid(self):
        """Cria preço válido."""
        price = Price(valor=99.99, moeda="BRL")
        assert price.valor == 99.99
        assert price.moeda == "BRL"
    
    def test_price_currency_uppercase(self):
        """Moeda é normalizada para maiúsculas."""
        price = Price(valor=50.0, moeda="usd")
        assert price.moeda == "USD"
    
    def test_price_negative_value_invalid(self):
        """Valor negativo deve falhar."""
        with pytest.raises(ValueError):
            Price(valor=-10.0)
    
    def test_price_default_currency(self):
        """Moeda padrão é BRL."""
        price = Price(valor=100.0)
        assert price.moeda == "BRL"


class TestContact:
    """Testes para modelo Contact."""
    
    def test_contact_email_valid(self):
        """Email válido é aceito."""
        contact = Contact(email="teste@exemplo.com")
        assert contact.email == "teste@exemplo.com"
    
    def test_contact_email_invalid(self):
        """Email inválido deve falhar."""
        with pytest.raises(ValueError):
            Contact(email="email-invalido")
    
    def test_contact_phone_normalization(self):
        """Telefone é normalizado."""
        contact = Contact(telefone="(11) 99999-8888")
        # Telefone deve ser limpo (apenas dígitos e +)
        assert contact.telefone is not None
        assert contact.telefone.replace('+', '').isdigit()
    
    def test_contact_phone_with_plus(self):
        """Telefone com + é mantido."""
        contact = Contact(telefone="+1 555 123 4567")
        assert "+" in contact.telefone
    
    def test_contact_empty(self):
        """Contato vazio é válido."""
        contact = Contact()
        assert contact.email is None
        assert contact.telefone is None


class TestService:
    """Testes para modelo Service."""
    
    def test_service_valid(self):
        """Serviço válido."""
        service = Service(nome="Consultoria", categoria="Profissional")
        assert service.nome == "Consultoria"
        assert service.categoria == "Profissional"
    
    def test_service_with_price(self):
        """Serviço com preço."""
        price = Price(valor=150.0)
        service = Service(nome="Aula", preco=price)
        assert service.preco.valor == 150.0
    
    def test_service_required_name(self):
        """Nome é obrigatório."""
        with pytest.raises(Exception):
            Service()


class TestCompany:
    """Testes para modelo Company."""
    
    def test_company_valid(self):
        """Empresa válida."""
        company = Company(nome="Empresa XYZ")
        assert company.nome == "Empresa XYZ"
        assert company.servicos == []
        assert company.precos == []
    
    def test_company_name_stripped(self):
        """Nome tem espaços removidos."""
        company = Company(nome="  Empresa   com  espaços  ")
        assert company.nome == "Empresa com espaços"
    
    def test_company_description_cleaned(self):
        """Descrição é limpa."""
        company = Company(
            nome="Teste",
            descricao="Descrição\ncom\nquebras\tde linha"
        )
        assert "\n" not in company.descricao
        assert "\t" not in company.descricao
    
    def test_company_with_contact(self):
        """Empresa com contato completo."""
        contact = Contact(
            email="contato@empresa.com",
            telefone="+5511999998888",
            website="https://empresa.com"
        )
        company = Company(nome="Empresa", contato=contact)
        assert company.contato.email == "contato@empresa.com"
    
    def test_company_with_services(self):
        """Empresa com serviços."""
        services = [
            Service(nome="Serviço 1"),
            Service(nome="Serviço 2")
        ]
        company = Company(nome="Empresa", servicos=services)
        assert len(company.servicos) == 2
    
    def test_company_metadata(self):
        """Metadata é dicionário vazio por padrão."""
        company = Company(nome="Teste")
        assert company.metadata == {}
    
    def test_company_timestamp(self):
        """Data de coleta é gerada automaticamente."""
        company = Company(nome="Teste")
        assert isinstance(company.data_coleta, datetime)


class TestModelValidation:
    """Testes de validação integrada."""
    
    def test_full_company_creation(self):
        """Cria empresa completa com todos os campos."""
        company = Company(
            nome="Empresa Completa Ltda",
            descricao="Empresa de tecnologia especializada em soluções inovadoras",
            contato=Contact(
                email="contato@empresa.com",
                telefone="+5511999998888",
                website="https://www.empresa.com",
                endereco="Rua Exemplo, 123 - São Paulo, SP"
            ),
            servicos=[
                Service(
                    nome="Desenvolvimento Web",
                    descricao="Criação de sites e aplicações web",
                    preco=Price(valor=5000.0, moeda="BRL")
                ),
                Service(
                    nome="Consultoria",
                    categoria="Profissional",
                    preco=Price(valor=200.0, moeda="BRL", tipo="hora")
                )
            ],
            precos=[
                Price(valor=10000.0, moeda="BRL", tipo="projeto")
            ],
            categoria="Tecnologia",
            metadata={"fonte": "crawler_test"}
        )
        
        assert company.nome == "Empresa Completa Ltda"
        assert company.contato.email == "contato@empresa.com"
        assert len(company.servicos) == 2
        assert len(company.precos) == 1
        assert company.servicos[0].preco.valor == 5000.0
    
    def test_model_serialization(self):
        """Modelos podem ser serializados para dict."""
        company = Company(nome="Teste", categoria="Exemplo")
        data = company.model_dump()
        
        assert data["nome"] == "Teste"
        assert data["categoria"] == "Exemplo"
        assert "data_coleta" in data
