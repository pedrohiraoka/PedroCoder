# Website Cloner MVP

Um script Python que clona websites públicos de forma recursiva usando `wget`, gera User-Agent aleatório para privacidade e compacta o resultado em um arquivo ZIP.

## 🚀 Funcionalidades

- **Clone Recursivo**: Baixa todo o conteúdo de um website de forma recursiva
- **Navegação Offline**: Converte links para navegação local após o download
- **User-Agent Aleatório**: Gera automaticamente um User-Agent de navegadores populares para ofuscar a identidade do script
- **Compactação Automática**: Cria um arquivo ZIP com todo o conteúdo baixado
- **Feedback Detalhado**: Exibe logs claros durante todo o processo
- **Tratamento de Erros**: Captura e informa falhas na execução

## 📋 Requisitos

- **Python 3.x** (testado com Python 3.8+)
- **wget** instalado no sistema
- Bibliotecas padrão do Python (nenhuma dependência externa necessária)

### Verificando os requisitos

```bash
# Verificar Python
python3 --version

# Verificar wget
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
Baixe em [https://eternallybored.org/misc/wget/](https://eternallybored.org/misc/wget/) ou use Chocolatey:
```bash
choco install wget
```

## 🛠️ Instalação

1. Clone ou baixe este repositório:
```bash
git clone <url-do-repositorio>
cd website-cloner-mvp
```

2. Verifique se o script tem permissão de execução (Linux/macOS):
```bash
chmod +x website_cloner.py
```

## 💻 Uso

### Execução Básica

```bash
python3 website_cloner.py
```

### Ou como executável (Linux/macOS)

```bash
./website_cloner.py
```

### Passo a Passo

1. Execute o script
2. Digite a URL do website quando solicitado (ex: `https://exemplo.com`)
3. Aguarde o download e compactação
4. O arquivo ZIP será gerado no diretório atual

### Exemplo de Saída

```
============================================================
WEBSITE CLONER MVP - Python
============================================================

Este script clona um website público e o compacta em um arquivo ZIP.
Nota: Respeite os termos de uso e robots.txt de cada website.

Digite a URL base do website (ex: https://exemplo.com): https://exemplo.com

[1/4] Gerando User-Agent aleatório...
✓ User-Agent selecionado:
  Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36

[2/4] Domínio identificado: exemplo.com
✓ Comando wget preparado com 11 argumentos

============================================================
INICIANDO DOWNLOAD COM WGET
============================================================
--2024-01-15 10:30:00--  https://exemplo.com/
Resolving exemplo.com... 93.184.216.34
Connecting to exemplo.com|93.184.216.34|:443... connected.
HTTP request sent, awaiting response... 200 OK
...

Download concluído com sucesso!

[3/4] Procurando diretório baixado...
✓ Diretório encontrado: /workspace/exemplo.com

[4/4] Criando arquivo ZIP...
============================================================
COMPACTANDO DIRETÓRIO: exemplo.com
============================================================
Arquivos a serem compactados: 45
  Adicionado: exemplo.com/index.html
  Adicionado: exemplo.com/style.css
  ...

============================================================
✅ PROCESSO CONCLUÍDO COM SUCESSO!
============================================================

📦 Arquivo ZIP gerado: backup_exemplo_com_20240115_103045.zip
📁 Diretório clonado: exemplo.com

O arquivo ZIP contém toda a estrutura do website clonado.
Você pode extrair o ZIP e navegar offline pelo site.

Arquivo de cookies limpo.
```

## 📁 Estrutura de Saída

Após a execução, você terá:

```
diretório-atual/
├── website_cloner.py          # O script
├── exemplo.com/               # Diretório com o site clonado
│   ├── index.html
│   ├── style.css
│   ├── images/
│   └── ...
└── backup_exemplo_com_20240115_103045.zip  # Arquivo compactado
```

## 🔧 Como Funciona

### 1. Geração de User-Agent

O script seleciona aleatoriamente um User-Agent de uma lista predefinida contendo:
- Chrome (Windows, macOS, Linux, Android)
- Firefox (Windows, macOS, Linux)
- Safari (macOS, iOS)
- Edge (Windows)

### 2. Comando wget Utilizado

```bash
wget --mirror --page-requisites --convert-links --adjust-extension --no-parent \
  --save-cookies cookies.txt --keep-session-cookies \
  --user-agent="<USER_AGENT_ALEATORIO>" <url_base>
```

**Parâmetros:**
- `--mirror`: Download recursivo completo
- `--page-requisites`: Baixa CSS, imagens, JS necessários
- `--convert-links`: Converte links para navegação offline
- `--adjust-extension`: Adiciona `.html` quando necessário
- `--no-parent`: Não sobe para diretórios pais
- `--save-cookies`: Salva cookies para sessões
- `--keep-session-cookies`: Mantém cookies de sessão

### 3. Compactação

O diretório criado pelo wget é compactado em um arquivo ZIP com timestamp:
```
backup_<dominio>_<YYYYMMDD_HHMMSS>.zip
```

## ⚠️ Considerações Importantes

### Legalidade e Ética

- **Respeite os Termos de Uso**: Verifique os termos de serviço do website antes de clonar
- **Robots.txt**: O script respeita as regras do `robots.txt` através do wget
- **Direitos Autorais**: O conteúdo clonado é de responsabilidade do usuário
- **Uso Pessoal**: Este script foi desenvolvido para fins educacionais e de backup pessoal

### Limitações

- Sites com JavaScript pesado podem não funcionar completamente offline
- Conteúdo dinâmico carregado via AJAX pode não ser baixado
- Alguns sites podem bloquear downloads automatizados
- O wget não executa JavaScript

## 🐛 Solução de Problemas

### "wget não encontrado"

Instale o wget conforme instruções na seção [Requisitos](#-requisitos).

### "Permission denied" ao criar ZIP

Verifique as permissões do diretório atual:
```bash
ls -la
chmod 755 .
```

### Download incompleto ou falhou

- Verifique sua conexão com a internet
- Alguns sites podem bloquear downloads em massa
- Tente novamente mais tarde
- Verifique se o site está acessível no navegador

### Arquivo ZIP muito grande

- O site pode ter muitos recursos (imagens, vídeos)
- Considere usar filtros adicionais no wget
- Limite a profundidade de recursão se necessário

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commitar suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abrir um Pull Request

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👤 Autor

**PedroCoder**

## 🙏 Agradecimentos

- [GNU Wget](https://www.gnu.org/software/wget/) pela excelente ferramenta de download
- Comunidade Python pelas bibliotecas padrão

---

**Nota**: Este script é fornecido "como está", sem garantias de qualquer tipo. Use por sua própria conta e risco e sempre respeite os direitos de propriedade intelectual de terceiros.
