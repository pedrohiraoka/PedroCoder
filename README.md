# FastDL 🚀

**Acelerador de Downloads de Alta Performance para Terminal (2026)**

FastDL é um downloader de arquivos via linha de comando extremamente rápido, seguro e leve, projetado para maximizar a velocidade de transferência através de paralelismo avançado e otimização de I/O.

## ✨ Destaques

- **🚀 Velocidade Extrema**: Download paralelo segmentado com múltiplas conexões simultâneas
- **🎯 Inteligente**: Ajuste dinâmico de threads baseado na latência e largura de banda
- **💻 UX Moderna**: Interface visual em tempo real com barras de progresso, métricas e atalhos
- **🔄 Resume Automático**: Retome downloads interrompidos sem perder progresso
- **🛡️ Seguro**: Validação de integridade com hashes e retry exponencial
- **⚡ Leve**: Zero dependências complexas, instalação em segundos
- **🌐 HTTP/1.1, HTTP/2 e HTTP/3**: Suporte híbrido com fallback automático

---

## 📦 Instalação

### Opção 1: Via pipx (Recomendado - Isolamento Total)

```bash
# Instalar pipx (se não tiver)
python -m pip install --user pipx
python -m pipx ensurepath

# Instalar FastDL
pipx install fastdl

# Recarregar shell ou executar
source ~/.bashrc  # ou ~/.zshrc
```

### Opção 2: Via pip (Ambiente Virtual)

```bash
# Criar e ativar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# Instalar
pip install fastdl
```

### Opção 3: Desenvolvimento (Editable)

```bash
git clone https://github.com/seu-usuario/fastdl.git
cd fastdl
pip install -e ".[dev]"
```

### Opção 4: Binário Standalone (Em breve)

Binários compilados para Linux, macOS e Windows estarão disponíveis nas releases.

---

## 🚀 Uso Básico

### Download Simples

```bash
fastdl download https://exemplo.com/arquivo.zip
```

### Download com Nome Personalizado

```bash
fastdl download https://exemplo.com/arquivo.zip -o meu-arquivo.zip
```

### Download com Número Específico de Conexões

```bash
fastdl download https://exemplo.com/arquivo.zip --connections 16
```

### Download com Limite de Velocidade (por conexão)

```bash
fastdl download https://exemplo.com/arquivo.zip --limit-rate 5MB
```

### Retomar Download Interrompido

```bash
# O FastDL detecta automaticamente arquivos parciais
fastdl download https://exemplo.com/arquivo.zip --resume
```

### Verificar Integridade com Hash

```bash
# Se o servidor fornecer hash nos cabeçalhos
fastdl download https://exemplo.com/arquivo.zip --verify

# Ou especificar hash manualmente
fastdl download https://exemplo.com/arquivo.zip --sha256 abc123...
```

### Modo Verbose (Debug)

```bash
fastdl download https://exemplo.com/arquivo.zip -v
```

---

## ⚙️ Configuração

O FastDL funciona com **configuração zero** na maioria dos casos, detectando automaticamente as configurações ótimas de rede. Porém, você pode personalizar comportamentos através de um arquivo de configuração.

### Arquivo de Configuração

Crie o arquivo `~/.config/fastdl/config.toml`:

```toml
# ~/.config/fastdl/config.toml

[geral]
# Diretório padrão para downloads
diretorio_padrao = "~/Downloads"

# Número máximo de conexões simultâneas (0 = auto)
max_conexoes = 0

# Timeout para requisições em segundos
timeout = 30

[network]
# Habilitar HTTP/3 (QUIC) se disponível
http3_habilitado = true

# Tamanho do buffer de leitura (bytes)
buffer_leitura = 32768

# Tamanho do buffer de escrita (bytes)
buffer_escrita = 65536

[ui]
# Atualizar dashboard a cada X milissegundos
atualizacao_ui = 100

# Mostrar uso de CPU/RAM
mostrar_recursos = true

[retry]
# Número máximo de tentativas
max_tentativas = 5

# Backoff inicial em segundos
backoff_inicial = 1.0

# Backoff máximo em segundos
backoff_maximo = 60.0
```

### Variáveis de Ambiente

Também é possível configurar via environment variables:

```bash
export FASTDL_MAX_CONNECTIONS=16
export FASTDL_OUTPUT_DIR=~/Downloads
export FASTDL_TIMEOUT=60
```

---

## 🎮 Atalhos de Teclado (Durante Download)

Durante um download ativo, use os seguintes atalhos:

| Tecla | Ação |
|-------|------|
| `p` | Pausar download |
| `r` | Retomar download |
| `c` | Cancelar download (mantém progresso) |
| `q` | Sair imediatamente |
| `+` | Aumentar número de conexões |
| `-` | Diminuir número de conexões |
| `h` | Mostrar ajuda |

---

## 📊 Exemplo de Saída

```
╔══════════════════════════════════════════════════════════╗
║  FastDL - Download Accelerator                           ║
╠══════════════════════════════════════════════════════════╣
║  Arquivo: ubuntu-24.04-desktop-amd64.iso                 ║
║  Tamanho: 5.2 GB                                         ║
║  Conexões: 12/16                                         ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  ████████████████████████░░░░░░░░░░  67%                 ║
║                                                          ║
║  ⚡ Velocidade: 45.3 MB/s  (Pico: 89.7 MB/s)             ║
║  ⏱️  Restante: 1m 23s                                    ║
║  📥 Baixado: 3.5 GB / 5.2 GB                            ║
║  🌐 Conexões ativas: 12                                  ║
║  💾 Escrita: 42.1 MB/s                                   ║
╠══════════════════════════════════════════════════════════╣
║  [p] Pausar  [r] Retomar  [c] Cancelar  [+] Mais [-] Menos║
╚══════════════════════════════════════════════════════════╝
```

---

## 🔧 Troubleshooting

### Download lento com muitas conexões

Alguns servidores limitam a velocidade por IP. Reduza o número de conexões:

```bash
fastdl download https://exemplo.com/arquivo.zip --connections 4
```

### Erro "Accept-Ranges not supported"

O servidor não suporta downloads segmentados. O FastDL automaticamente reverte para download single-thread. Para forçar:

```bash
fastdl download https://exemplo.com/arquivo.zip --single-connection
```

### Download não retoma corretamente

Verifique se o arquivo `.fastdl.json` na mesma pasta do download não foi corrompido. Delete-o para reiniciar do zero.

### Problemas com HTTP/3

Desabilite HTTP/3 se encontrar instabilidade:

```toml
# ~/.config/fastdl/config.toml
[network]
http3_habilitado = false
```

---

## 🧪 Testes

Para rodar a suite de testes:

```bash
# Instalar dependências de desenvolvimento
pip install -e ".[dev]"

# Rodar testes unitários
pytest tests/ -v

# Com coverage
pytest tests/ --cov=src --cov-report=html

# Rodar type checker
mypy src/

# Rodar linter
ruff check src/
```

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Siga os passos:

1. Fork o repositório
2. Crie uma branch (`git checkout -b feature/minha-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push (`git push origin feature/minha-feature`)
5. Abra um Pull Request

### Requisitos de Código

- Type hints em todas as funções
- Testes unitários para novas features
- Documentação atualizada
- Seguir padrões PEP 8

---

## 📄 Licença

MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 🙏 Agradecimentos

- [httpx](https://www.python-httpx.org/) - Cliente HTTP assíncrono
- [rich](https://rich.readthedocs.io/) - Terminal formatting
- [typer](https://typer.tiangolo.com/) - CLI framework
- [pydantic](https://docs.pydantic.dev/) - Validação de dados

---

## 📬 Contato

- **Issues**: https://github.com/seu-usuario/fastdl/issues
- **Discussões**: https://github.com/seu-usuario/fastdl/discussions
- **Email**: contato@fastdl.dev

---

**FastDL** - Downloads mais rápidos, simplicidade máxima. 🚀
