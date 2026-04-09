# PedroCoder

# DataHarvest Streamlit - MVP

Aplicação web local para pesquisa e download em lote de arquivos específicos da web.

## 📋 Requisitos

### Dependências Python
Instale as dependências listadas no arquivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

### wget (Obrigatório para downloads)

A aplicação requer o utilitário `wget` instalado no sistema. Veja como instalar:

#### Linux (Debian/Ubuntu)
```bash
sudo apt-get update
sudo apt-get install wget
```

#### Linux (RedHat/CentOS/Fedora)
```bash
sudo yum install wget
# ou
sudo dnf install wget
```

#### macOS (com Homebrew)
```bash
brew install wget
```

#### Windows
- **Opção 1:** Baixe o executável em [https://eternallybored.org/misc/wget/](https://eternallybored.org/misc/wget/)
- **Opção 2:** Use Chocolatey (se instalado): `choco install wget`
- **Opção 3:** Use WSL (Windows Subsystem for Linux) e siga as instruções do Linux

## 🚀 Como Usar

1. **Inicie a aplicação:**
   ```bash
   streamlit run app.py
   ```

2. **Configure sua busca na sidebar:**
   - Digite o termo de busca (ex: "relatório financeiro 2024")
   - Selecione os tipos de arquivo desejados (PDF, DOCX, XLSX, etc.)
   - Ajuste o número máximo de resultados (10-200)
   - Defina a pasta de download (padrão: `./downloads`)

3. **Clique em "🔍 Buscar e Preparar Downloads"**

4. **Selecione os arquivos** que deseja baixar usando as checkboxes na tabela

5. **Clique em "🚀 Baixar Selecionados (Wget)"** para iniciar o download

## 🔒 Segurança

- A aplicação usa `shlex.quote()` para escapar URLs e caminhos, prevenindo injeção de comandos
- Os downloads são feitos localmente, sem envio de dados para servidores externos
- O filtro de extensões garante que apenas arquivos dos tipos selecionados sejam processados

## 📁 Estrutura do Projeto

```
/workspace/
├── app.py              # Script principal da aplicação
├── requirements.txt    # Dependências Python
└── README.md          # Este arquivo
```

## ⚠️ Notas Importantes

- A aplicação é executada localmente no seu navegador (geralmente em `http://localhost:8501`)
- Certifique-se de ter espaço em disco suficiente para os downloads
- Alguns sites podem bloquear downloads automatizados
- Respeite os termos de uso e direitos autorais dos arquivos baixados
