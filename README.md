# Site Cloner v1

Uma ferramenta de linha de comando (CLI) em Python para clonar/espelhar sites estáticos e dinâmicos utilizando `wget` como motor principal de download.

## 📋 Descrição

O **Site Cloner MVP** é um script Python robusto que encapsula o poder do `wget` para clonar websites completos. Ele permite especificar URLs, definir pastas de destino, aplicar configurações personalizadas e lidar com possíveis falhas de forma elegante.

### Funcionalidades Principais

- ✅ **Clonagem de sites estáticos** com parâmetros otimizados
- ✅ **Interface CLI intuitiva** com argumentos flexíveis
- ✅ **Validação de URLs** antes do download
- ✅ **Tratamento de erros** detalhado
- ✅ **Logs informativos** durante o processo
- ✅ **Suporte a User-Agent customizado**
- ✅ **Controle de retries** por requisição
- ✅ **Exclusão de tipos de arquivos** indesejados
- ✅ **Delay entre requisições** para ser gentil com o servidor
- ✅ **Modo dinâmico** (em desenvolvimento) para futura integração com Puppeteer/Playwright

## 🚀 Requisitos

- **Python 3.6+** (testado com Python 3.8+)
- **wget** instalado e disponível no PATH do sistema

### Verificando os requisitos

```bash
# Verificar versão do Python
python3 --version

# Verificar se wget está instalado
wget --version
```

### Instalando wget (se necessário)

**Ubuntu/Debian:**
```bash
sudo apt-get install wget
```

**macOS:**
```bash
brew install wget
```

**Windows:**
- Baixe em: https://eternallybored.org/misc/wget/
- Ou use Chocolatey: `choco install wget`

## 📦 Instalação

1. Clone ou baixe este repositório:
```bash
git clone <repositorio>
cd site-cloner-mvp
```

2. (Opcional) Crie um ambiente virtual:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. O script não possui dependências externas! Basta garantir que Python e wget estejam instalados.

## 💻 Uso

### Sintaxe Básica

```bash
python site_cloner.py <URL> [OPÇÕES]
```

### Argumentos Obrigatórios

| Argumento | Descrição |
|-----------|-----------|
| `url` | URL do site a ser clonado |

### Argumentos Opcionais

| Argumento | Descrição | Padrão |
|-----------|-----------|--------|
| `-o`, `--output-dir` | Diretório de saída para os arquivos clonados | Nome do domínio da URL |
| `--static-only` | Usa modo estático com parâmetros otimizados do wget | Ativado por padrão |
| `--dynamic-mode` | Ativa modo dinâmico (em desenvolvimento) | Desativado |
| `--user-agent` | Define um User-Agent customizado | User-Agent padrão do wget |
| `--max-retries N` | Número máximo de tentativas por requisição | `3` |
| `--exclude-types EXT1,EXT2` | Lista de extensões para excluir (ex: `zip,mp4,exe`) | Nenhuma exclusão |
| `--delay SEGUNDOS` | Intervalo em segundos entre requisições | `0` (sem delay) |
| `-v`, `--verbose` | Habilita output detalhado (debug) | Desativado |
| `--version` | Mostra a versão do programa | - |
| `-h`, `--help` | Mostra ajuda e sai | - |

## 📝 Exemplos de Uso

### Exemplo 1: Clonagem básica
```bash
python site_cloner.py https://exemplo.com
```
*Cria uma pasta com o nome do domínio e clona o site.*

### Exemplo 2: Clonagem com diretório personalizado
```bash
python site_cloner.py https://exemplo.com -o ./backup_site
```
*Salva os arquivos na pasta `./backup_site`.*

### Exemplo 3: Clonagem com exclusão de tipos de arquivo
```bash
python site_cloner.py https://exemplo.com/templates/painel-cliente/ -o ./backup_site --static-only --max-retries 3 --exclude-types zip,exe
```
*Clona excluindo arquivos .zip e .exe, com 3 retries máximos.*

### Exemplo 4: Clonagem com delay e User-Agent customizado
```bash
python site_cloner.py https://exemplo.com --delay 2 --user-agent "Mozilla/5.0 (compatible; SiteCloner/1.0)"
```
*Adiciona 2 segundos de delay entre requisições e usa User-Agent customizado.*

### Exemplo 5: Modo verbose para debug
```bash
python site_cloner.py https://exemplo.com -v
```
*Mostra logs detalhados durante o processo.*

### Exemplo 6: Modo dinâmico (experimental)
```bash
python site_cloner.py https://app-exemplo.com --dynamic-mode
```
*Avisa que o modo dinâmico está em desenvolvimento e prossegue com método estático.*

## 🔧 Parâmetros do wget Utilizados

Por padrão, o script utiliza os seguintes parâmetros do wget para clonagem eficiente:

| Parâmetro | Descrição |
|-----------|-----------|
| `--mirror` | Ativa opções adequadas para espelhamento |
| `--convert-links` | Converte links para visualização local |
| `--adjust-extension` | Salva documentos HTML com extensão `.html` |
| `--page-requisites` | Baixa todos os arquivos necessários para exibir a página |
| `--no-parent` | Não ascende ao diretório pai |
| `-e robots=off` | Ignora restrições do robots.txt |
| `--tries=N` | Número de retries configurável |
| `-P dir` | Diretório de saída |
| `--wait=N` | Delay entre requisições (opcional) |
| `--reject=EXT` | Exteensões a serem ignoradas (opcional) |
| `--user-agent=UA` | User-Agent customizado (opcional) |

## 📊 Estrutura do Projeto

```
site-cloner-mvp/
├── site_cloner.py      # Script principal da aplicação
├── README.md           # Este arquivo de documentação
└── venv/               # Ambiente virtual (opcional)
```

## 🐛 Tratamento de Erros

O script lida com os seguintes cenários de erro:

| Situação | Código de Saída | Mensagem |
|----------|----------------|----------|
| Sucesso | `0` | ✓ Clone completed successfully! |
| URL inválida | `1` | Invalid URL provided |
| wget não encontrado | `2` | wget is not installed or not in PATH |
| Erro ao criar diretório | `3` | Failed to create output directory |
| Interrupt pelo usuário | `-2` | Clone was interrupted by user |
| Outro erro | Outro valor | ✗ Clone failed with exit code: X |

## 🔮 Futuras Melhorias (Roadmap)

- [ ] **Modo Dinâmico Completo**: Integração com Puppeteer ou Playwright para sites SPA (Single Page Applications)
- [ ] **Autenticação**: Suporte a login/senha para sites protegidos
- [ ] **Cookies**: Gerenciamento de sessões via cookies
- [ ] **Relatórios Detalhados**: Geração de relatórios em JSON/CSV sobre arquivos baixados
- [ ] **Multi-threading**: Downloads paralelos para maior velocidade
- [ ] **Resumo de Download**: Estatísticas de tamanho total, número de arquivos, etc.
- [ ] **Config File**: Suporte a arquivo de configuração YAML/JSON
- [ ] **API REST**: Expôr funcionalidades via API HTTP

## ⚠️ Avisos Importantes

1. **Respeite os termos de serviço** dos sites que você estiver clonando
2. **Não sobrecarregue servidores** - use o parâmetro `--delay` para ser gentil
3. **Verifique robots.txt** - embora o script ignore por padrão (`-e robots=off`), é boa prática respeitar as regras do site
4. **Uso responsável** - Esta ferramenta deve ser usada apenas para fins legítimos (backup, arquivamento, desenvolvimento)

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commitar suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abrir um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT - veja o arquivo LICENSE para detalhes.

## 📞 Suporte

Para dúvidas, problemas ou sugestões, abra uma issue neste repositório.

---

**Desenvolvido com ❤️ usando Python e wget**

*Versão: 1.0.0*
