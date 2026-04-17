# Milkomeda - Simulador de Fusão Via Láctea & Andrômeda

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Simulador computacional da colisão entre a Via Láctea e a galáxia de Andrômeda (M31), 
resultando na formação da "Milkomeda". Ferramenta educativa e de divulgação científica 
com base física rigorosa.

## 🌌 Visão Geral

O Milkomeda é um simulador N-corpos simplificado que:

1. **Calcula órbitas** usando potenciais gravitacionais realistas (gala)
2. **Gera partículas** representando estrelas e matéria escura
3. **Simula evolução** temporal com integração leapfrog
4. **Renderiza visualizações** 2D/3D em vídeo MP4
5. **Exporta relatórios** científicos com parâmetros da simulação

## 📦 Instalação

### Requisitos do Sistema

- Python 3.9 ou superior
- ffmpeg (para compilação de vídeo)
- ~1GB de espaço em disco para dependências

### Passo a Passo

```bash
# Clonar ou navegar até o diretório do projeto
cd milkomeda-sim

# Criar ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências Python
pip install -r requirements.txt

# Verificar instalação do ffmpeg
ffmpeg -version

# Se ffmpeg não estiver instalado:
# Ubuntu/Debian:
sudo apt-get install ffmpeg

# macOS:
brew install ffmpeg

# Windows:
# Baixe em https://ffmpeg.org/download.html
```

## 🚀 Uso Básico

### Executar Simulação Completa

```bash
# Com parâmetros padrão (765 kpc, -110 km/s, 10 Gyr)
python main.py --run

# Ver ajuda completa
python main.py --help
```

### Personalizar Parâmetros

```bash
# Distância e velocidade personalizadas
python main.py --distance 800kpc --velocity -120km/s --run

# Mais partículas para melhor resolução
python main.py --n-particles 20000 --n-steps 200 --run

# Vídeo em alta definição
python main.py --run --resolution 1920x1080 --fps 60

# Apenas cálculo orbital (rápido)
python main.py --orbit-only --distance 765kpc

# Gerar relatório científico
python main.py --run --report
```

### Opções da Linha de Comando

```
Parâmetros Orbitais:
  --distance, -d        Distância inicial MW-M31 (default: 765kpc)
  --velocity, -v        Velocidade radial (default: -110km/s)
  --tangential-velocity Velocidade tangencial (default: 17km/s)
  --duration, -t        Duração da simulação (default: 10Gyr)

Parâmetros de Simulação:
  --n-particles, -n     Partículas por galáxia (default: 10000)
  --n-steps             Passos de integração (default: 100)
  --dt                  Passo de tempo em Myr (default: 100)
  --seed                Seed aleatória para reproducibilidade

Renderização:
  --resolution, -r      Resolução do vídeo (default: 1280x720)
  --fps                 Frames por segundo (default: 30)
  --render-mode         Modo: 2d, 3d, density (default: 2d)
  --no-video            Não compilar vídeo, apenas frames

Execução:
  --run                 Executar simulação completa
  --orbit-only          Apenas calcular órbita
  --output-dir, -o      Diretório de saída
  --verbose             Logs detalhados (DEBUG)
  --quiet               Suprimir logs
  --report              Gerar relatório JSON
```

## 📁 Estrutura do Projeto

```
milkomeda-sim/
├── main.py                      # Entry point CLI
├── config.py                    # Constantes e configurações
├── requirements.txt             # Dependências Python
├── README.md                    # Este arquivo
│
├── src/
│   ├── __init__.py
│   ├── dynamics/
│   │   ├── orbit_solver.py      # Integração orbital com gala
│   │   └── collision_estimator.py # Estimativa de colisão
│   ├── simulation/
│   │   ├── particle_generator.py # Geração de discos/halos
│   │   └── nbody_integrator.py   # Integrador leapfrog
│   ├── rendering/
│   │   ├── frame_renderer.py    # Renderização 2D/3D
│   │   └── video_compiler.py    # Compilação MP4
│   └── utils/
│       ├── logger.py            # Logging estruturado
│       └── unit_handler.py      # Manipulação de unidades
│
├── outputs/
│   ├── snapshots/               # Snapshots .npz
│   ├── frames/                  # Frames PNG
│   └── milkomeda_simulation.mp4 # Vídeo final
│
└── tests/
    └── test_dynamics.py         # Testes unitários
```

## 🔬 Base Física

### Potenciais Gravitacionais

- **Via Láctea**: Disco Miyamoto-Nagai + Bulbo Hernquist + Halo NFW
- **Andrômeda**: Componentes similares com massas escaladas

### Parâmetros Padrão (Gaia DR3)

| Parâmetro | Valor |
|-----------|-------|
| Distância MW-M31 | 765 kpc |
| Velocidade Radial | -110 km/s |
| Velocidade Tangencial | 17 km/s |
| Massa Total MW | ~1.0 × 10¹² M☉ |
| Massa Total M31 | ~1.5 × 10¹² M☉ |

### Resultados Esperados

Com os parâmetros padrão:
- **Tempo até primeira colisão**: ~4-5 Gyr
- **Fusão completa**: ~10-12 Gyr
- **Encontros próximos**: 2-3 antes da fusão

## 📊 Exemplos de Saída

### Relatório Orbital (apenas órbita)

```
$ python main.py --orbit-only

==================================================
RESULTADO ORBITAL
==================================================
Tempo até colisão: 4.52 Gyr
Distância de periapsis: 23.5 kpc
Velocidade no periapsis: 485.3 km/s
==================================================
```

### Vídeo Final

O vídeo MP4 gerado mostra:
- Evolução temporal das duas galáxias
- Legenda com tempo cosmológico e distância
- Projeção 2D (vista de topo) ou 3D

## 🧪 Testes

```bash
# Executar testes unitários
python -m pytest tests/ -v

# Ou com unittest
python -m unittest tests.test_dynamics -v
```

## ⚠️ Limitações do MVP

Este é um modelo simplificado que:
- Usa potenciais estáticos (sem evolução de massa)
- Não inclui hidrodinâmica ou formação estelar
- Partículas são tratadas como pontos de teste
- Interações de maré são aproximadas

Para simulações de pesquisa, considere:
- [GADGET](https://wwwmpa.mpa-garching.mpg.de/gadget/)
- [AREIPO](https://arepo-code.org/)
- [RAMSES](http://www.ramses-lib.org/)

## 📝 Licença

MIT License - ver arquivo LICENSE para detalhes.

## 🙏 Agradecimentos

- Dados orbitais: Gaia DR3 (ESA)
- Potenciais: pacote `gala` (Adrian Price-Whelan et al.)
- Inspirado em simulações de Cox & Loeb (2008)

## 📚 Referências

1. Gaia Collaboration et al. (2018), "Gaia Data Release 2"
2. McMillan, P. J. (2017), "Mass models of the Milky Way"
3. Patel, E. et al. (2018), "The Mass of the Large Magellanic Cloud"
4. Cox, T. J., & Loeb, A. (2008), "The Collision Between the Milky Way and Andromeda"

## 🤝 Contribuições

Contribuições são bem-vindas! Sugerimos:
1. Fork do projeto
2. Branch para feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push (`git push origin feature/nova-funcionalidade`)
5. Pull Request

---

**Desenvolvido para divulgação científica e educação em astrofísica.**

🌠 *A colisão MW-M31 é um evento inevitável que ocorrerá muito depois do Sol se tornar uma anã branca. A humanidade (ou seus descendentes) testemunhará este espetáculo cósmico.*
