# Assistente Pessoal de Observação Astronômica

MVP de um sistema Python que gera planos de observação astronômica otimizados e personalizados com base em critérios como data, local de observação e tipo de objeto de interesse.

## 🌟 Funcionalidades

- **Consulta a Catálogos Astronômicos**: Busca alvos (asteroides, estrelas variáveis, galáxias) via simulação de catálogos online (VizieR, Gaia, SIMBAD).
- **Cálculo de Posição e Visibilidade**: Determina coordenadas, altitude, azimute e janelas de observação usando `astropy` e `astroplan`.
- **Ranqueamento Inteligente com ML**: Utiliza `scikit-learn` para classificar e priorizar alvos com base em magnitude, altura no céu e critérios científicos.
- **Otimização da Sequência**: Ordena os alvos para minimizar movimento do telescópio e maximizar condições de observação.
- **Relatório Detalhado**: Gera plano de observação com nome do alvo, coordenadas (RA, Dec), horários, altitude máxima e score do modelo.

## 📦 Requisitos

- Python 3.8+
- Bibliotecas:
  - `astropy`
  - `astroplan`
  - `scikit-learn`
  - `numpy`
  - `pandas`

### Instalação das Dependências

```bash
pip install astropy astroplan scikit-learn numpy pandas
```

## 🚀 Como Usar

### Execução Rápida

O script já inclui dados de exemplo. Basta executar:

```bash
python assistente_observacao.py
```

### Uso Personalizado

Edite a seção `if __name__ == "__main__":` no final do script para alterar:

```python
# Data da observação
data_obs = Time("2024-06-15 22:00:00")

# Local do observatório (ex: Pico dos Dias, Brasil)
observatorio = Observatorio(
    nome="Pico dos Dias",
    latitude=-22.5344,
    longitude=-45.5825,
    altitude=1864
)

# Tipo de alvo: "asteroides", "estrelas_variaveis" ou "galaxias"
tipo_alvo = "asteroides"
```

## 📊 Saída Esperada

O sistema imprime no console:

1. **Configurações da Sessão**: Data, local e tipo de alvo.
2. **Alvos Encontrados**: Quantidade de objetos recuperados do catálogo.
3. **Janelas de Observação**: Horário de início/fim, altitude e azimute máximos.
4. **Ranking ML**: Score de prioridade para cada alvo.
5. **Plano Otimizado**: Sequência recomendada de observação.

Exemplo de saída:

```
========================================
ASSISTENTE PESSOAL DE OBSERVAÇÃO ASTRONÔMICA
========================================
Data: 2024-06-15 22:00:00
Local: Pico dos Dias (Lat: -22.53°, Lon: -45.58°, Alt: 1864m)
Tipo de Alvo: asteroides

--- Alvos Encontrados: 5 ---

[1] 2024 AA1
  Coordenadas: RA 10h23m45s, Dec -12°34'56"
  Janela: 2024-06-15 23:15 até 2024-06-16 02:45
  Altitude Máx: 67.3° | Azimute: 145.2°
  Score ML: 0.89 (Alta Prioridade)

...

=== Plano de Observação Otimizado ===
Ordem recomendada: 2024 AA1 → 2024 BB2 → ...
```

## 🏗️ Estrutura do Código

| Classe/Função | Descrição |
|---------------|-----------|
| `Observatorio` | Representa as coordenadas geográficas do local de observação. |
| `AlvoAstronomico` | Armazena dados de um objeto celeste (nome, RA, Dec, magnitude, etc.). |
| `CatalogoSimulado` | Simula consultas a catálogos astronômicos online. |
| `ModeloRankingML` | Modelo de Machine Learning para ranquear alvos. |
| `PlanejadorObservacao` | Calcula janelas de visibilidade e otimiza a sequência. |
| `gerar_plano_observacao()` | Função principal que orquestra todo o fluxo. |

## 🧪 Dados Mockados (MVP)

Para este MVP, os catálogos são simulados com dados artificiais para demonstrar o conceito sem dependência de APIs externas ou conexão com a internet. Em uma versão futura, a classe `CatalogoSimulado` pode ser substituída por consultas reais via `astroquery`.

## 📝 Próximos Passos (Futuras Melhorias)

- [ ] Integração real com `astroquery` (VizieR, SIMBAD, Gaia).
- [ ] Suporte a efemérides de asteroides via `poliastro` ou JPL Horizons.
- [ ] Interface gráfica (GUI) ou web com Streamlit/Flask.
- [ ] Exportação do plano em formatos padrão (PDF, JSON, FITS).
- [ ] Treinamento do modelo ML com dados históricos reais de observação.
- [ ] Suporte a restrições personalizadas (lua, crepúsculo, poluição luminosa).

## 📄 Licença

Este projeto é destinado para fins educacionais e de demonstração. Sinta-se à vontade para modificar e distribuir.

## 👨‍💻 Autor

Desenvolvido como MVP para demonstração de integração de bibliotecas astronômicas em Python.

---

**Bons céus e boas observações! 🔭✨**
