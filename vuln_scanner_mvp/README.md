# 🛡️ VulnScanner MVP

Ferramenta de Análise de Segurança Digital baseada em técnicas de Pentest descritas no livro **"Hacking com Kali Linux"**.

## ⚠️ Aviso Legal Importante

> **Esta ferramenta foi desenvolvida exclusivamente para fins EDUCACIONAIS e de TESTES AUTORIZADOS.**
> 
> Ao utilizar este scanner de vulnerabilidades, você declara que:
> - ✅ Possui **autorização explícita** do proprietário do sistema/alvo
> - ✅ Compreende que o uso não autorizado pode configurar **crime cibernético**
> - ✅ Assume total **responsabilidade** pelas ações realizadas
> - ✅ Não utilizará esta ferramenta para atividades maliciosas ou ilegais

**Os desenvolvedores NÃO se responsabilizam** por quaisquer danos, perdas ou consequências legais decorrentes do uso indevido desta ferramenta.

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Módulos](#-módulos)
- [Tecnologias](#-tecnologias)
- [Limitações](#-limitações)
- [Contribuição](#-contribuição)

---

## 🎯 Visão Geral

O **VulnScanner MVP** é uma aplicação web interativa desenvolvida em Python com Streamlit que permite realizar análises de segurança em aplicações web e servidores. A ferramenta segue o ciclo de vida tradicional de pentest:

1. **Reconhecimento** - Coleta passiva de informações
2. **Scanning** - Varredura de portas e serviços
3. **Verificação** - Detecção de vulnerabilidades comuns
4. **Relatório** - Geração de documentação completa

---

## ✨ Funcionalidades

### 🔍 Reconhecimento
- Consulta WHOIS para dados de registro de domínio
- DNS Lookup (registros A, AAAA, MX, NS, TXT, SOA, CNAME)
- Geolocalização de IP
- Google Hacking básico (técnicas de Dorking)

### 📡 Scanning
- Scan de portas com Nmap
- Fingerprinting de serviços
- Detecção de tecnologias web (CMS, frameworks, servidores)
- Verificação de headers de segurança HTTP
- Detecção de diretórios expostos

### 🔬 Verificação de Vulnerabilidades
- Verificação de arquivos sensíveis (.env, .git, backups)
- Detecção de possíveis backdoors por assinatura
- Análise de configurações inseguras
- Verificação de proteções XSS

### 📊 Dashboard Interativo
- Resumo executivo com métricas
- Gráficos de distribuição por severidade
- Lista detalhada de descobertas
- Tabela de serviços detectados

### 📥 Exportação de Relatórios
- PDF completo com sumário executivo
- CSV com lista de vulnerabilidades
- JSON com dados brutos do scan

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- nmap instalado no sistema

### Passo a Passo

1. **Clone ou navegue até o diretório do projeto:**

```bash
cd vuln_scanner_mvp
```

2. **Instale as dependências:**

```bash
pip install -r requirements.txt
```

3. **Instale o Nmap (se ainda não estiver instalado):**

**Ubuntu/Debian:**
```bash
sudo apt-get update && sudo apt-get install nmap
```

**macOS:**
```bash
brew install nmap
```

**Windows:**
Baixe em https://nmap.org/download.html

4. **Execute a aplicação:**

```bash
streamlit run app.py
```

5. **Acesse no navegador:**

A aplicação abrirá automaticamente em `http://localhost:8501`

---

## 💻 Uso

### Iniciando um Scan

1. **Leia e aceite os termos de uso** na tela inicial
2. **Digite o alvo** (IP ou domínio) no campo indicado
3. **Selecione o range de portas** desejado
4. **Escolha a profundidade** da análise
5. **Clique em "Iniciar Varredura"**

### Interpretando Resultados

#### Níveis de Severidade

| Severidade | Cor | Descrição |
|------------|-----|-----------|
| 🔴 CRITICAL | Vermelho | Requer ação imediata |
| 🟠 HIGH | Laranja | Deve ser resolvido em breve |
| 🟡 MEDIUM | Amarelo | Importante, mas não urgente |
| 🔵 LOW | Azul | Melhoria recomendada |
| ⚪ INFO | Cinza | Informação para conhecimento |

### Exportando Relatórios

Após completar o scan, use os botões de exportação para baixar:
- **PDF**: Relatório formal completo
- **CSV**: Lista de vulnerabilidades em planilha
- **JSON**: Dados brutos para integração

---

## 📁 Estrutura do Projeto

```
vuln_scanner_mvp/
├── app.py                  # Aplicação principal (Streamlit)
├── modules/
│   ├── __init__.py
│   ├── recon.py            # Módulo de reconhecimento
│   ├── scanner.py          # Módulo de scanning
│   ├── exploiter.py        # Módulo de verificação
│   └── reporter.py         # Módulo de relatórios
├── utils/
│   ├── __init__.py
│   ├── logger.py           # Configuração de logging
│   └── legal.py            # Avisos legais
├── wordlists/
│   └── common_dirs.txt     # Lista de diretórios comuns
├── reports/                # Diretório de saída dos relatórios
├── requirements.txt        # Dependências do projeto
└── README.md               # Este arquivo
```

---

## 🔧 Módulos

### `recon.py` - Reconhecimento
Realiza coleta passiva de informações:
- WHOIS lookup
- DNS enumeration
- IP geolocation
- Google dorking

### `scanner.py` - Scanning
Executa varredura ativa:
- Port scanning (Nmap)
- Service fingerprinting
- Web technology detection
- HTTP security headers check
- Directory brute-forcing

### `exploiter.py` - Verificação
Verifica vulnerabilidades comuns (**apenas passivamente**):
- Sensitive file exposure
- Backdoor detection
- SQL injection indicators
- XSS protection check

### `reporter.py` - Relatórios
Gera documentação:
- PDF reports
- CSV exports
- JSON data dumps

---

## 🛠️ Tecnologias

| Tecnologia | Versão | Finalidade |
|------------|--------|------------|
| Python | 3.8+ | Linguagem principal |
| Streamlit | 1.32+ | Interface web |
| python-nmap | 0.7+ | Scan de portas |
| requests | 2.31+ | Requisições HTTP |
| beautifulsoup4 | 4.12+ | Parsing HTML |
| dnspython | 2.6+ | Consultas DNS |
| whois | 0.9+ | Consulta WHOIS |
| fpdf2 | 2.7+ | Geração de PDF |
| matplotlib | 3.8+ | Gráficos |
| plotly | 5.20+ | Visualizações |

---

## ⚠️ Limitações

### O que esta ferramenta NÃO faz:

1. **Não executa exploits ativos** - Apenas verificações passivas
2. **Não realiza ataques de força bruta** intensivos
3. **Não testa autenticação** ou tenta quebrar senhas
4. **Não realiza testes de invasão completos**

### Considerações Importantes:

- Os resultados podem conter **falsos positivos**
- Algumas verificações dependem de APIs externas
- O scan de portas pode ser detectado por firewalls
- Sempre valide manualmente as descobertas críticas

---

## 🤝 Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Diretrizes de Desenvolvimento

- Mantenha o código documentado
- Adicione tratamento de erros adequado
- Respeite as diretrizes éticas de segurança
- Teste em ambiente controlado antes de commitar

---

## 📚 Referências

Este projeto foi inspirado nas técnicas descritas em:
- **Hacking com Kali Linux** - Livro de referência para metodologias de pentest
- **OWASP Testing Guide** - Padrões de teste de segurança web
- **PTES (Penetration Testing Execution Standard)** - Metodologia de pentest

---

## 📄 Licença

Este projeto é distribuído como software educacional. Use responsavelmente e apenas em sistemas autorizados.

---

## 📞 Suporte

Para dúvidas ou problemas:
- Verifique a documentação de cada módulo
- Consulte os logs em `reports/`
- Reporte issues no repositório

---

<div align="center">

**🛡️ VulnScanner MVP - Ferramenta Educacional de Segurança**

*Desenvolvido com foco em educação e testes autorizados*

⚠️ **Use com responsabilidade e sempre com autorização** ⚠️

</div>
