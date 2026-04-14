# PedroCoder

# NASA Media Search - Busca de Imagens e Vídeos da NASA

Aplicação Python MVP que permite buscar e visualizar imagens e vídeos do acervo público da NASA através da API oficial.

## Funcionalidades

- ✅ Busca por palavra-chave ou frase
- ✅ Filtros opcionais: tipo de mídia (imagem/vídeo)
- ✅ Exibição organizada dos resultados com thumbnail, título, descrição
- ✅ Abertura de links no navegador
- ✅ Salvamento de resultados em JSON ou CSV
- ✅ Tratamento de erros básico
- ✅ Paginação suportada pela API

## Requisitos

- Python 3.7+
- requests >= 2.28.0

## Instalação

1. Clone o repositório ou baixe os arquivos
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

## Uso

### Executar a aplicação

```bash
python nasa_media_search.py
```

### Fluxo de uso:

1. Digite o termo de busca (ex: "Mars rover", "Jupiter", "Space station")
2. Opcionalmente, aplique filtros:
   - Tipo de mídia: `image` ou `video`
3. Visualize os resultados numerados
4. Digite o número do item para abrir no navegador (ou 0 para sair)
5. Opcionalmente, salve os resultados em JSON ou CSV

### Exemplo de sessão:

```
======================================================================
NASA MEDIA SEARCH - Busca de Imagens e Vídeos da NASA
======================================================================

Busque no acervo público da NASA por imagens e vídeos.

Digite o termo de busca (ou 'sair' para encerrar): Mars rover

Filtros opcionais (deixe em branco para pular):
  Tipo de mídia (image/video): 

Buscando por 'Mars rover'...

======================================================================
Resultados encontrados: 150 (mostrando 20)
======================================================================

[1] Curiosity Rover's Self-Portrait at 'Big Sky' Drill Site
    Tipo: IMAGE | Centro: JPL
    Data: 2016-01-12
    Descrição: This view of NASA's Curiosity Mars rover shows the robot...
    Thumbnail: https://www.jpl.nasa.gov/spaceimages/images/large/...

...

Digite o número do item para abrir no navegador (0 para sair): 
```

## Estrutura do Projeto

```
/workspace
├── nasa_media_search.py    # Código principal da aplicação
├── requirements.txt        # Dependências Python
└── README.md              # Este arquivo
```

## API Utilizada

- **Endpoint**: https://images-api.nasa.gov/search
- **Método**: GET
- **Parâmetros**:
  - `q`: Termo de busca (obrigatório)
  - `media_type`: Tipo de mídia (opcional: 'image', 'video')
  - `page`: Número da página (opcional)
- **Autenticação**: Não requer API key para uso básico

## Dados Retornados

Para cada item de mídia, a aplicação extrai:
- ID da NASA
- Título
- Descrição
- Data de criação
- Centro da NASA responsável
- Tipo de mídia
- URL da thumbnail
- URL da mídia (imagem ou vídeo)
- Link para visualização

## Critérios de Aceitação

- ✅ Aplicação executa sem erros
- ✅ Retorna resultados relevantes para busca
- ✅ Links funcionam e abrem no navegador
- ✅ Interface clara e responsiva (CLI)
- ✅ Tratamento de erros para API indisponível

## Funcionalidades Bônus

- ✅ Paginação (suportada via parâmetro `page`)
- ✅ Download/Salvamento de resultados em JSON/CSV
- ⏳ Filtros avançados (centro da NASA - pode ser implementado)

## Notas

Esta é uma aplicação MVP focada em funcionalidade básica. A prioridade foi dada à simplicidade e usabilidade.

## Licença

Projeto desenvolvido para fins educacionais e de demonstração.
Dados fornecidos pela NASA Image and Video Library API.
