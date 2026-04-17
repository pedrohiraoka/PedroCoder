# AstroWatch Dashboard - MVP

Um dashboard web local para monitoramento em tempo real de dados astronômicos, desenvolvido com PHP nativo e JavaScript moderno.

## 🌟 Funcionalidades

- **Painel de Alertas de Transientes**: Consulta a alertas astronômicos (VOEvent-style) com coordenadas celestes (RA/Dec) e tabela atualizada via polling (60s)
- **Condições do Observatório**: Dados de seeing, umidade, vento e temperatura com gráficos de tendência em tempo real (polling 30s)
- **Status de Instrumentos**: Cards de estado para telescópio, câmera, espectrógrafo e autoguider com cores semafóricas (polling 15s)
- **Atualização em Tempo Real**: Fetch API + setInterval para consumo de endpoints PHP
- **Resiliência**: Fallback automático para dados mock se APIs falharem

## 📁 Estrutura de Arquivos

```
astrowatch_mvp/
├── index.php                 # Layout principal + injeção de dados iniciais
├── config.php                # Constantes, coordenadas, intervalos, limites
├── api/
│   ├── alerts.php            # Endpoint JSON de alertas astronômicos
│   ├── weather.php           # Endpoint JSON de condições ambientais
│   └── instruments.php       # Endpoint JSON de status de instrumentos
├── assets/
│   ├── css/style.css         # Tema escuro, responsivo, indicadores visuais
│   └── js/dashboard.js       # Fetch polling, Chart.js, atualização DOM
└── README.md                 # Este arquivo
```

## 🚀 Instalação e Execução

### Pré-requisitos

- PHP 8.2+ (recomendado) ou PHP 7.4+
- Navegador moderno com suporte a ES6+

### Opção 1: Servidor PHP Embutido (Recomendado)

```bash
# Navegue até o diretório do projeto
cd astrowatch_mvp

# Inicie o servidor PHP
php -S localhost:8080

# Acesse no navegador
http://localhost:8080
```

### Opção 2: XAMPP/WAMP/MAMP

1. Copie a pasta `astrowatch_mvp` para o diretório do servidor:
   - **XAMPP**: `htdocs/astrowatch_mvp`
   - **WAMP**: `www/astrowatch_mvp`
   - **MAMP**: `htdocs/astrowatch_mvp`

2. Inicie o servidor Apache

3. Acesse no navegador:
   ```
   http://localhost/astrowatch_mvp
   ```

### Opção 3: Docker (Alternativa)

```bash
# Usando imagem PHP oficial
docker run -d -p 8080:80 -v $(pwd):/var/www/html php:8.2-apache

# Acesse no navegador
http://localhost:8080
```

## ⚙️ Configuração

Edite o arquivo `config.php` para personalizar:

```php
// Coordenadas do observatório
define('OBS_LATITUDE', -24.6275);
define('OBS_LONGITUDE', -70.4042);
define('OBS_ALTITUDE', 2635);
define('OBS_NAME', 'Cerro Paranal Observatory');

// Intervalos de polling (milissegundos)
define('POLLING_ALERTS_INTERVAL', 60000);    // 60 segundos
define('POLLING_WEATHER_INTERVAL', 30000);   // 30 segundos
define('POLLING_INSTRUMENTS_INTERVAL', 15000); // 15 segundos

// Limites operacionais
define('MAX_WIND_SPEED', 60);      // km/h
define('MAX_HUMIDITY', 85);        // %
define('MAX_SEEING', 2.5);         // arcseconds
```

## 🔌 Endpoints da API

Todos os endpoints retornam JSON com estrutura consistente:

### `/api/alerts.php`
Retorna alertas de transientes astronômicos:
```json
{
  "success": true,
  "timestamp": "2024-01-15T10:30:00-03:00",
  "count": 5,
  "alerts": [...]
}
```

### `/api/weather.php`
Retorna condições ambientais do observatório:
```json
{
  "success": true,
  "data": {
    "current": {
      "temperature": 12.5,
      "humidity": 35,
      "windSpeed": 15,
      "seeing": 1.2
    },
    "history": [...],
    "alerts": [...]
  }
}
```

### `/api/instruments.php`
Retorna status dos instrumentos:
```json
{
  "success": true,
  "system": {
    "status": "ok",
    "averageHealth": 95,
    "readyForObserving": true
  },
  "instruments": {
    "telescope": {...},
    "camera": {...},
    "spectrograph": {...}
  }
}
```

## 🎨 Recursos Visuais

- **Tema Escuro**: Otimizado para ambientes de baixo luminosidade
- **Cores Semafóricas**: Verde (OK), Amarelo (Atenção), Vermelho (Erro)
- **Gráficos Chart.js**: Visualização de tendências de temperatura, umidade e vento
- **Mapa Celeste**: Representação simplificada de coordenadas RA/Dec
- **Responsivo**: Adapta-se a diferentes tamanhos de tela

## 🔧 Personalização

### Adicionar Novos Instrumentos

1. Edite `api/instruments.php` e adicione o instrumento em `generateMockInstruments()`
2. Atualize `index.php` com o card HTML correspondente
3. Adicione a lógica de atualização em `assets/js/dashboard.js`

### Integrar APIs Reais

Substitua as funções `fetchReal*()` nos endpoints PHP:

```php
function fetchRealWeather(): ?array {
    $context = stream_context_create([
        'http' => [
            'method' => 'GET',
            'timeout' => 5,
        ]
    ]);
    
    $response = file_get_contents('https://api.weather.com/...');
    return json_decode($response, true);
}
```

### Alterar Intervalos de Polling

No frontend (`assets/js/dashboard.js`), os intervalos são lidos do `ASTROWATCH_CONFIG`:

```javascript
ASTROWATCH_CONFIG.pollingIntervals.weather // 30000ms
```

## 🐛 Solução de Problemas

### Dashboard não carrega

1. Verifique se o servidor PHP está rodando
2. Confirme que o arquivo `config.php` está legível
3. Verifique o console do navegador por erros

### Dados não atualizam

1. Verifique a aba Network do DevTools
2. Confirme que os endpoints retornam JSON válido
3. Verifique logs de erro em `error.log`

### Gráficos não aparecem

1. Verifique se Chart.js carregou (CDN)
2. Confirme conexão com a internet para CDN
3. Alternativamente, baixe Chart.js localmente

## 📊 Performance

- **Cache-Control**: Headers configurados para reduzir requisições
- **Polling Eficiente**: Apenas dados alterados são atualizados no DOM
- **Fallback Automático**: Dados mock garantem funcionamento offline
- **Sem Banco de Dados**: Arquitetura stateless para máximo desempenho

## 🔒 Segurança

- Error logging em arquivo (não exibido no navegador)
- Headers de segurança (X-Content-Type-Options)
- Validação de entrada nos endpoints
- Type hints e strict types no PHP

## 📝 Licença

Este projeto é fornecido como-is para fins educacionais e de demonstração.

## 🤝 Contribuição

Para extensões futuras, considere:

- Integração com GCN/TAN para alertas GRB em tempo real
- Conexão com APIs de meteorologia reais (OpenWeatherMap, Meteoblue)
- Suporte a WebSockets para updates push
- Autenticação e controle de acesso
- Exportação de dados em CSV/FITS

---

**AstroWatch Dashboard v1.0.0**  
Desenvolvido com ❤️ para astronomia
