# Arquitetura Técnica: Acelerador de Downloads CLI (MVP 2026)

## Documento de Design de Software
**Versão:** 1.0  
**Data:** Janeiro 2026  
**Autor:** Arquiteto de Software Sênior & Especialista Python  

---

## 1. Stack Tecnológica Moderna e Validada para 2026

Para garantir performance máxima, leveza e uma experiência de usuário superior, a seguinte stack foi selecionada com base em maturidade, suporte assíncrono nativo e eficiência de recursos:

### 1.1 Núcleo Assíncrono e Rede
- **`httpx` (Versão Estável 2026):** Escolhido como cliente HTTP primário. Diferentemente do `aiohttp`, o `httpx` oferece uma API unificada que suporta tanto síncrono quanto assíncrono nativamente, com suporte robusto a HTTP/2 e experimental a HTTP/3 (via `quic`). Sua gestão de conexões (Connection Pooling) é altamente otimizada, reduzindo a latência de handshake TLS em downloads segmentados.
- **`asyncio` (Nativo):** Utilização direta da biblioteca padrão para o loop de eventos. Nenhuma dependência externa é necessária para o core assíncrono, garantindo compatibilidade total e menor overhead.

### 1.2 Interface de Linha de Comando (CLI) e UX Visual
- **`typer`:** Selecionado sobre `click` por sua sintaxe moderna baseada em type hints do Python. Isso reduz drasticamente o código boilerplate e garante que a definição da CLI esteja sempre sincronizada com a lógica de tipos do negócio.
- **`rich`:** Biblioteca essencial para renderização no terminal. Será utilizada para criar barras de progresso multi-segmento, tabelas dinâmicas de métricas e spinners de status. O uso de `rich.live` permite atualizações de tela eficientes (delta rendering), evitando flickering e reduzindo o consumo de CPU na renderização da UI.

### 1.3 Configuração e Serialização
- **`pydantic` (Versão V3 ou superior):** Para validação rigorosa de configurações e modelos de dados. Garante que qualquer arquivo de configuração ou argumento de CLI seja tipado e validado antes de atingir a lógica de download, prevenindo erros em tempo de execução.
- **`tomllib` (Nativo Python 3.11+):** Para leitura de arquivos de configuração. Sendo nativo, elimina a necessidade de dependências externas como `pyyaml` ou `tomli`, mantendo a aplicação leve.

### Justificativa de Leveza
Esta stack minimiza dependências externas críticas. Ao usar bibliotecas nativas (`asyncio`, `tomllib`) e escolher pacotes maduros (`httpx`, `rich`, `typer`), evitamos o "bloatware" comum em frameworks web completos. A aplicação final terá um footprint de memória inicial baixo, crescendo apenas conforme a alocação de buffers de download.

---

## 2. Motor de Aceleração de Download (Core Logic)

O coração da aplicação reside no algoritmo de download paralelo segmentado. A lógica deve seguir estritamente os seguintes passos:

### 2.1 Verificação de Suporte a Ranges (Handshake Inicial)
Antes de iniciar o download, uma requisição HEAD assíncrona deve ser enviada ao URL alvo.
- **Validação:** Verificar a presença do cabeçalho `Accept-Ranges: bytes`.
- **Fallback:** Se ausente, o sistema deve degradar automaticamente para um download sequencial simples (single-threaded), notificando o usuário que a aceleração não está disponível para este servidor específico.
- **Tamanho do Arquivo:** Extrair o tamanho total (`Content-Length`) neste estágio para cálculo prévio dos segmentos.

### 2.2 Cálculo Dinâmico de Concorrência
Em vez de um número fixo de threads, implementar um algoritmo adaptativo:
- **Fórmula Base:** `N_conexoes = min(Maximo_Global, (Largura_de_Banda_Estimada / Latencia_Media))`.
- **Heurística:** Iniciar com um número conservador (ex: 4 conexões). Durante os primeiros 5% do download, medir o throughput e a latência. Se o throughput estabilizar e a latência não disparar, incrementar gradualmente as conexões até um teto seguro (ex: 16 ou 32), evitando sobrecarga que cause packet loss ou bloqueio pelo servidor (HTTP 429).

### 2.3 Segmentação Inteligente (Chunking)
- **Cálculo de Intervalos:** Dividir o arquivo em $N$ segmentos matemáticos precisos `[start_byte, end_byte]`.
- **Tamanho Mínimo:** Garantir que nenhum segmento seja menor que um threshold mínimo (ex: 64KB) para evitar overhead de requisições HTTP desproporcional ao dado transferido em arquivos pequenos.
- **Balanceamento:** Os segmentos devem ser distribuídos uniformemente, mas o último segmento deve absorver qualquer resto de divisão de bytes para garantir integridade.

### 2.4 Download Paralelo em Memória/Temporário
- Cada tarefa assíncrona será responsável por um segmento específico.
- **Bufferização:** Os dados não devem ser escritos imediatamente no disco final. Cada tarefa mantém um buffer em memória.
- **Estratégia Híbrida:** Para arquivos > 1GB, escrever segmentos em arquivos temporários nomeados pelo índice do segmento (ex: `.part.0`, `.part.1`) para evitar estouro de RAM. Para arquivos menores, manter em `bytearray` na memória para merge instantâneo.

### 2.5 Merge Eficiente (Reunião)
- **Fluxo de Escrita:** Após o download de todos os segmentos, abrir o arquivo final em modo binário.
- **Otimização de I/O:** Utilizar cópias de buffer diretas (zero-copy se o SO permitir, ou `shutil.copyfileobj` com buffer grande) para concatenar os segmentos na ordem exata.
- **Limpeza Atômica:** Apenas após a confirmação de escrita de todos os bytes e validação de checksum, o arquivo temporário é renomeado para o nome final, garantindo que arquivos corrompidos não sejam entregues ao usuário.

---

## 3. Gerenciamento de Recursos e Performance Assíncrona

### 3.1 Loop de Eventos e Concorrência
- Utilizar `asyncio.Semaphore` para limitar estritamente o número de conexões TCP simultâneas abertas. Isso previne a exaustão de descritores de arquivo (socket limits) do sistema operacional.
- Implementar um `Timeout` global e por conexão para evitar que tarefas travadas (hung connections) bloqueiem a fila de download indefinidamente.

### 3.2 Bufferização Inteligente de Escrita
- **Problema:** Múltiplas tarefas tentando escrever no mesmo arquivo simultaneamente causam contenção de lock e degradação de performance.
- **Solução:** Padrão Produtor-Consumidor. As tarefas de rede (Produtores) colocam os chunks baixados em uma `asyncio.Queue`. Uma única tarefa dedicada (Consumidor/Escritor) lê dessa fila e escreve sequencialmente no disco. Isso serializa a operação de I/O de disco (que é lenta) enquanto mantém a rede saturada (que é rápida e paralela).

---

## 4. Experiência do Usuário (UX) em Modo Texto Inovadora

A interface deve ser "Viva" e responsiva, utilizando a área de console de forma dinâmica.

### 4.1 Dashboard em Tempo Real
Utilizar `rich.live` para exibir um painel único que atualiza a cada 200ms:
- **Barra de Progresso Principal:** Visualização gráfica macro do progresso total.
- **Barras Secundárias (Opcional):** Mini-barras mostrando o status de cada segmento ativo (útil para debug visual de gargalos).
- **Métricas Chave:**
    - Velocidade Instantânea (MB/s) com média móvel de 3 segundos para suavizar flutuações.
    - Velocidade Pico atingida na sessão.
    - ETA (Tempo Restante) calculado baseado na velocidade média ponderada.
    - Contagem de Conexões Ativas/Recuperando.
- **Indicadores de Saúde:** Ícones visuais indicando estabilidade da conexão (ex: verde para estável, amarelo para retry, vermelho para falha crítica).

### 4.2 Interatividade e Controle
- **Captura de Sinais:** Implementar listeners para sinais de teclado não bloqueantes.
    - `Ctrl+C`: Deve acionar um handler gracioso. Salvar o estado atual dos segmentos baixados, fechar conexões limpas e sair. Não matar o processo abruptamente.
    - `p`: Pausar o download (cancela tarefas pendentes, mantém as concluídas).
    - `r`: Retomar download (verifica o que falta e reinicia tarefas).
    - `q`: Cancelar e limpar arquivos temporários (aborto total).
- A interface deve confirmar visualmente a ação ("Pausando...", "Salvando estado...") antes de executar.

---

## 5. Robustez, Segurança e Recuperação de Erros

### 5.1 Resiliência de Rede (Retry Logic)
- **Backoff Exponencial com Jitter:** Em caso de falha de download de um segmento (timeout, erro 5xx), re-tentar a requisição aguardando um tempo crescente ($2^n$ segundos) somado a um valor aleatório (jitter) para evitar tempestades de requisições sincronizadas ao servidor.
- **Limite de Retentativas:** Definir um máximo de tentativas por segmento (ex: 5). Se excedido, marcar o segmento como falho crítico e abortar o download geral, reportando o erro exato.

### 5.2 Funcionalidade de Resume (Retomada)
- **Metadados de Estado:** Manter um arquivo oculto de metadados (ex: `.download_state.json`) ao lado do arquivo em download. Ele registra: URL, tamanho total, ETag, e lista de intervalos de bytes já confirmados como baixados com sucesso.
- **Validação Pré-Resume:** Ao retomar, verificar se o arquivo remoto ainda possui o mesmo `ETag` ou `Content-Length`. Se o arquivo mudou no servidor, invalidar o resume e alertar o usuário para evitar corrupção de dados.
- **Download Delta:** Reiniciar apenas as tarefas correspondentes aos intervalos de bytes missing.

### 5.3 Integridade e Segurança
- **Hash Verification:** Se o servidor fornecer um hash (via cabeçalho customizado ou conhecido previamente), calcular o hash do arquivo montado (streaming hash calculation para não carregar tudo na RAM) e comparar.
- **Sanitização de URL:** Validar esquemas (apenas http/https) e prevenir redirecionamentos para domínios não confiáveis (SSRF protection).

---

## 6. Facilidade de Instalação e Configuração Zero

### 6.1 Distribuição
- **PyPI + pipx:** O método primário de instalação deve ser `pipx install fast-downloader-2026`. Isso isola as dependências da aplicação do sistema global do usuário, garantindo que atualizações do Python do SO não quebrem a ferramenta.
- **Binários Standalone (Opcional):** Para ambientes restritos, fornecer builds compilados via `Nuitka` ou `PyInstaller` (single file) nas releases do GitHub, detectando automaticamente o OS (Linux x64, ARM64, Windows, macOS).

### 6.2 Configuração Automática
- **Zero-Config:** Por padrão, a aplicação deve auto-detectar limites de rede e usar valores seguros.
- **Config Override:** Permitir um arquivo `~/.config/fastdl/config.toml` para usuários avançados ajustarem:
    - Número máximo de conexões globais.
    - Limite de taxa (rate limit) para não saturar a rede local.
    - Diretório padrão de download.
- A aplicação deve ler esse arquivo silenciosamente na inicialização; se não existir, usa defaults otimizados.

---

## 7. Estrutura de Projeto e Boas Práticas de Código

A organização do código deve seguir princípios de arquitetura limpa e separação de preocupações (SoC):

```text
projeto/
├── src/
│   ├── cli/            # Interface de linha de comando (Typer commands)
│   ├── core/           # Lógica de negócios e orquestração
│   │   ├── downloader.py   # Motor principal de download
│   │   ├── scheduler.py    # Gestão de filas e semáforos
│   │   └── state.py        # Gerenciamento de estado e resume
│   ├── network/        # Abstração de rede
│   │   ├── client.py       # Wrapper do httpx
│   │   └── inspector.py    # Análise de headers e ranges
│   ├── storage/        # Abstração de I/O
│   │   ├── writer.py       # Lógica de merge e escrita em disco
│   │   └── checker.py      # Validação de hashes e integridade
│   └── utils/          # Helpers (formatting, logging)
├── tests/              # Testes unitários e de integração (pytest)
├── pyproject.toml      # Definição de projeto e dependências
└── README.md
```

### Boas Práticas Obrigatórias
- **Type Hinting Rigoroso:** Todo o código deve ser anotado com tipos estáticos (`typing`, `mypy` compatible). Isso serve como documentação viva e previne erros de tipo em operações matemáticas de bytes.
- **Documentação de Strings:** Docstrings no formato Google ou NumPy para todas as classes e métodos públicos.
- **Testabilidade:** Uso intensivo de `unittest.mock` ou `pytest-mock` para simular respostas HTTP lentas, falhas de rede e timeouts, garantindo que a lógica de retry e resume funcione sem necessidade de rede real nos testes CI/CD.

---

## 8. Inovação e Diferenciais Competitivos (2026)

Para posicionar esta ferramenta como líder de mercado em 2026, dois recursos inovadores serão implementados:

### 8.1 Detecção e Adaptação a Throttling Dinâmico
A maioria dos downloaders ignora quando o servidor limita intencionalmente a velocidade por conexão.
- **Inovação:** O módulo de rede monitorará a taxa de transferência de cada segmento individualmente. Se detectar que a velocidade de um segmento caiu drasticamente enquanto outros permanecem rápidos (indicativo de throttling por IP/Conexão), o sistema automaticamente:
    1. Fecha a conexão limitada.
    2. Abre duas novas conexões para cobrir o mesmo intervalo de bytes restantes.
    3. Ajusta o User-Agent ou headers para tentar contornar filtros básicos.
Isso transforma o downloader em uma entidade "viva" que luta ativamente contra limitações de banda impostas pelo servidor.

### 8.2 Suporte Híbrido HTTP/3 (QUIC) com Fallback Inteligente
Com a adoção massiva do HTTP/3 em 2026:
- **Inovação:** O cliente tentará inicialmente estabelecer conexões via QUIC (UDP) se o servidor suportar (detectado via DNS HTTPS records ou ALPN). O QUIC reduz significativamente a latência em redes instáveis (Wi-Fi público, 4G/5G) devido à eliminação do head-of-line blocking do TCP.
- **Fallback Transparente:** Se o handshake QUIC falhar ou apresentar perda de pacotes excessiva, o sistema muda instantaneamente para HTTP/2 over TCP sem interromper o fluxo de download perceptivelmente para o usuário, garantindo a melhor performance possível para qualquer condição de rede.

---

## Conclusão

Esta arquitetura propõe um equilíbrio preciso entre a brutalidade de performance necessária para downloads de alta velocidade e a sofisticação de UX esperada em ferramentas modernas. Ao alavancar o modelo assíncrono do Python com bibliotecas maduras e focar em resiliência inteligente, o MVP estará pronto não apenas para competir, mas para definir o padrão de downloaders CLI em 2026.
