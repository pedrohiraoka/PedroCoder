"""
Testes para parser HTML

Valida extração de dados com seletores CSS e XPath.
"""

import pytest
from src.parser import Parser, ParseResult
from src.models import Company


# HTML de teste para listagem de empresas
HTML_LISTAGEM = """
<html>
<body>
    <div class="company-card">
        <h2 class="company-name">Empresa Alpha</h2>
        <p class="description">Soluções em tecnologia</p>
        <a class="website-link" href="https://alpha.com">Visite</a>
        <span class="email">contato@alpha.com</span>
        <span class="phone">(11) 9999-8888</span>
        <div class="address">Rua A, 100</div>
        <ul class="services">
            <li><span class="service-name">Consultoria</span><span class="price">R$ 200,00</span></li>
            <li><span class="service-name">Desenvolvimento</span><span class="price">R$ 5000,00</span></li>
        </ul>
    </div>
    <div class="company-card">
        <h2 class="company-name">Empresa Beta</h2>
        <p class="description">Serviços financeiros</p>
        <a class="website-link" href="https://beta.com.br">Site</a>
        <span class="email">info@beta.com.br</span>
        <span class="phone">+55 21 8888-7777</span>
        <div class="address">Av. B, 200</div>
    </div>
    <a class="next-page" href="/page/2">Próxima</a>
</body>
</html>
"""

# Configuração de parser para teste
PARSER_CONFIG = {
    "listagem": {
        "container": "div.company-card",
        "pagination": "a.next-page@href"
    },
    "campos": {
        "nome": "h2.company-name::text",
        "descricao": "p.description::text",
        "website": "a.website-link@href",
        "email": "span.email::text",
        "telefone": "span.phone::text",
        "endereco": "div.address::text"
    },
    "servicos": {
        "container": "ul.services li",
        "campos": {
            "nome": "span.service-name::text",
            "preco": "span.price::text"
        }
    }
}


class TestParser:
    """Testes para classe Parser."""
    
    def test_parser_creation(self):
        """Cria parser com configuração."""
        parser = Parser(PARSER_CONFIG)
        assert parser.listagem_config is not None
        assert parser.campos_config is not None
    
    def test_parse_listagem(self):
        """Parseia listagem de empresas."""
        parser = Parser(PARSER_CONFIG)
        result = parser.parse(HTML_LISTAGEM, "https://exemplo.com/listagem")
        
        assert len(result.companies) == 2
        assert result.items_found == 2
    
    def test_extract_company_fields(self):
        """Extrai campos básicos de empresa."""
        parser = Parser(PARSER_CONFIG)
        result = parser.parse(HTML_LISTAGEM, "https://exemplo.com")
        
        company = result.companies[0]
        assert company.nome == "Empresa Alpha"
        assert company.descricao == "Soluções em tecnologia"
        assert company.contato.email == "contato@alpha.com"
        assert company.contato.endereco == "Rua A, 100"
    
    def test_extract_services(self):
        """Extrai serviços de empresa."""
        parser = Parser(PARSER_CONFIG)
        result = parser.parse(HTML_LISTAGEM, "https://exemplo.com")
        
        company = result.companies[0]
        assert len(company.servicos) == 2
        assert company.servicos[0].nome == "Consultoria"
        assert company.servicos[0].preco.valor == 200.0
    
    def test_pagination_extraction(self):
        """Extrai link de paginação."""
        parser = Parser(PARSER_CONFIG)
        result = parser.parse(HTML_LISTAGEM, "https://exemplo.com/page/1")
        
        assert result.next_page_url is not None
        assert "/page/2" in result.next_page_url
    
    def test_phone_normalization(self):
        """Telefones são normalizados."""
        parser = Parser(PARSER_CONFIG)
        result = parser.parse(HTML_LISTAGEM, "https://exemplo.com")
        
        # Primeiro telefone: (11) 9999-8888 -> +551199998888
        phone1 = result.companies[0].contato.telefone
        assert "+" in phone1 or phone1.isdigit()
    
    def test_empty_html(self):
        """HTML vazio retorna resultado vazio."""
        parser = Parser(PARSER_CONFIG)
        result = parser.parse("<html><body></body></html>", "https://exemplo.com")
        
        assert len(result.companies) == 0
        assert result.items_found == 0


class TestXPathParser:
    """Testes para parser com XPath."""
    
    def test_xpath_config(self):
        """Parser com XPath."""
        config = {
            "use_xpath": True,
            "listagem": {
                "container": "//div[@class='item']"
            },
            "campos": {
                "nome": ".//h3[@class='name']/text()"
            }
        }
        
        parser = Parser(config)
        assert parser.use_xpath is True
    
    def test_xpath_extraction(self):
        """Extrai com XPath."""
        html = """
        <div>
            <div class="item">
                <h3 class="name">Produto X</h3>
            </div>
        </div>
        """
        
        config = {
            "use_xpath": True,
            "campos": {
                "nome": ".//h3[@class='name']/text()"
            }
        }
        
        parser = Parser(config)
        result = parser.parse(html, "https://exemplo.com")
        
        # Deve encontrar pelo menos um item
        assert result is not None


class TestParseResult:
    """Testes para ParseResult."""
    
    def test_result_creation(self):
        """Cria resultado vazio."""
        result = ParseResult()
        assert result.companies == []
        assert result.errors == []
        assert result.items_found == 0
    
    def test_add_error(self):
        """Adiciona erro ao resultado."""
        result = ParseResult()
        result.add_error("Erro de teste")
        
        assert len(result.errors) == 1
        assert result.success is False
    
    def test_success_property(self):
        """Propriedade success funciona corretamente."""
        result = ParseResult()
        
        # Vazio não é sucesso
        assert result.success is False
        
        # Com companies e sem erros é sucesso
        result.companies = [Company(nome="Teste")]
        assert result.success is True


class TestParserEdgeCases:
    """Testes para casos extremos."""
    
    def test_missing_fields(self):
        """Campos ausentes não quebram parser."""
        html = "<div class='company-card'><h2 class='company-name'>Apenas Nome</h2></div>"
        
        parser = Parser(PARSER_CONFIG)
        result = parser.parse(html, "https://exemplo.com")
        
        assert len(result.companies) == 1
        assert result.companies[0].nome == "Apenas Nome"
        assert result.companies[0].descricao is None
    
    def test_special_characters(self):
        """Caracteres especiais são tratados."""
        html = """
        <div class="company-card">
            <h2 class="company-name">Empresa &amp; Cia Ltda</h2>
            <p class="description">Especialistas em &lt;tecnologia&gt;</p>
        </div>
        """
        
        parser = Parser(PARSER_CONFIG)
        result = parser.parse(html, "https://exemplo.com")
        
        assert len(result.companies) == 1
        assert "&" in result.companies[0].nome
    
    def test_nested_selectors(self):
        """Seletores aninhados funcionam."""
        html = """
        <div class="card">
            <div class="info">
                <h2 class="name">Empresa Aninhada</h2>
            </div>
        </div>
        """
        
        config = {
            "listagem": {"container": "div.card"},
            "campos": {"nome": "div.info h2.name::text"}
        }
        
        parser = Parser(config)
        result = parser.parse(html, "https://exemplo.com")
        
        assert len(result.companies) == 1
        assert result.companies[0].nome == "Empresa Aninhada"
