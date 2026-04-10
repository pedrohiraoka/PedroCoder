#!/usr/bin/env python3
"""
Assistente Pessoal de Observação Astronômica - MVP

Este módulo implementa um sistema para gerar planos de observação astronômica
otimizados e personalizados com base em critérios como data, local de observação
e tipo de objeto de interesse.

Autor: Assistente de Programação Python
Versão: 1.0.0 (MVP)
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal, Optional

import numpy as np
from astropy import units as u
from astropy.coordinates import (
    AltAz,
    Angle,
    EarthLocation,
    SkyCoord,
    get_body,
)
from astropy.time import Time
from astroplan import Observer, FixedTarget
from astroplan.constraints import (
    AltitudeConstraint,
    AtNightConstraint,
    Constraint,
    MoonSeparationConstraint,
)
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

# Ignorar warnings não críticos para melhor legibilidade da saída
warnings.filterwarnings("ignore", category=DeprecationWarning)


@dataclass
class Observatorio:
    """Representa um observatório com suas coordenadas geográficas."""

    nome: str
    latitude: float  # graus
    longitude: float  # graus
    altitude: float  # metros

    def to_earth_location(self) -> EarthLocation:
        """Converte para EarthLocation do astropy."""
        return EarthLocation(
            lat=self.latitude * u.deg,
            lon=self.longitude * u.deg,
            height=self.altitude * u.m,
        )

    def to_observer(self) -> Observer:
        """Converte para Observer do astroplan."""
        location = self.to_earth_location()
        return Observer(location=location, name=self.nome)


@dataclass
class AlvoAstronomico:
    """Representa um alvo astronômico com suas propriedades."""

    nome: str
    ra: float  # Right Ascension em graus
    dec: float  # Declination em graus
    magnitude: float
    tipo: str
    score_ml: float = 0.0
    janela_inicio: Optional[Time] = None
    janela_fim: Optional[Time] = None
    altitude_max: float = 0.0
    azimute_max: float = 0.0

    def to_skycoord(self) -> SkyCoord:
        """Converte para SkyCoord do astropy."""
        return SkyCoord(ra=self.ra * u.deg, dec=self.dec * u.deg, frame="icrs")

    def to_fixed_target(self) -> FixedTarget:
        """Converte para FixedTarget do astroplan."""
        return FixedTarget(coord=self.to_skycoord(), name=self.nome)


class CatalogoSimulado:
    """
    Simula consultas a catálogos astronômicos online.
    
    No MVP, usamos dados mockados para demonstrar o conceito sem depender
    de conexões externas que podem falhar ou ser lentas.
    """

    @staticmethod
    def buscar_alvos(
        tipo_alvo: Literal["asteroides", "estrelas_variaveis", "galaxias"],
        ra_centro: float = 180.0,
        dec_centro: float = 0.0,
        raio_graus: float = 30.0,
        magnitude_max: float = 12.0,
        quantidade: int = 10,
    ) -> list[AlvoAstronomico]:
        """
        Busca alvos astronômicos simulados do tipo especificado.

        Args:
            tipo_alvo: Tipo de objeto ("asteroides", "estrelas_variaveis", "galaxias").
            ra_centro: Right Ascension central em graus.
            dec_centro: Declination central em graus.
            raio_graus: Raio de busca em graus.
            magnitude_max: Magnitude aparente máxima.
            quantidade: Número máximo de alvos a retornar.

        Returns:
            Lista de AlvoAstronomico com os objetos encontrados.
        """
        np.random.seed(42)  # Reprodutibilidade

        # Dados mockados baseados em catálogos reais
        if tipo_alvo == "asteroides":
            prefixo = "AST"
            magnitudes = np.random.uniform(8.0, magnitude_max, quantidade)
            # Asteroides têm movimento próprio, simulado por pequenas variações
            ras = ra_centro + np.random.uniform(-raio_graus, raio_graus, quantidade)
            decs = dec_centro + np.random.uniform(-raio_graus / 2, raio_graus / 2, quantidade)
            nomes = [f"{prefixo}-{i:04d}" for i in range(quantidade)]

        elif tipo_alvo == "estrelas_variaveis":
            prefixo = "VAR"
            magnitudes = np.random.uniform(6.0, magnitude_max, quantidade)
            ras = ra_centro + np.random.uniform(-raio_graus, raio_graus, quantidade)
            decs = dec_centro + np.random.uniform(-raio_graus / 2, raio_graus / 2, quantidade)
            nomes = [f"{prefixo} {i:04d}" for i in range(quantidade)]

        elif tipo_alvo == "galaxias":
            prefixo = "GAL"
            magnitudes = np.random.uniform(9.0, magnitude_max, quantidade)
            ras = ra_centro + np.random.uniform(-raio_graus, raio_graus, quantidade)
            decs = dec_centro + np.random.uniform(-raio_graus / 2, raio_graus / 2, quantidade)
            nomes = [f"{prefixo}-{i:04d}" for i in range(quantidade)]
        else:
            raise ValueError(f"Tipo de alvo desconhecido: {tipo_alvo}")

        alvos = []
        for i in range(quantidade):
            alvo = AlvoAstronomico(
                nome=nomes[i],
                ra=float(ras[i]) % 360,
                dec=float(decs[i]),
                magnitude=float(magnitudes[i]),
                tipo=tipo_alvo,
            )
            alvos.append(alvo)

        return alvos


class ModeloRankingML:
    """
    Modelo de Machine Learning para ranquear alvos astronômicos.
    
    Usa scikit-learn para criar um modelo simples que considera:
    - Altura no céu
    - Magnitude do objeto
    - Separação da Lua
    - Interesse científico (pesos definidos)
    """

    def __init__(self):
        """Inicializa o modelo de ranking."""
        self.scaler = StandardScaler()
        self.modelo = LogisticRegression(random_state=42, max_iter=1000)
        self.treinado = False

    def preparar_dados_treino(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Prepara dados de treino mockados para o modelo.
        
        Returns:
            Tuple com features (X) e labels (y).
        """
        np.random.seed(42)
        n_samples = 100

        # Features: [altitude_normalizada, magnitude_invertida, separacao_lua, interesse]
        X = np.random.rand(n_samples, 4)
        X[:, 1] = 1 - X[:, 1]  # Inverte magnitude (menor é melhor)

        # Labels: 1 = bom alvo, 0 = alvo ruim
        # Criando labels baseados em regras simples
        y = (X[:, 0] > 0.3).astype(int) & (X[:, 1] > 0.3).astype(int)
        y = y.astype(int)

        return X, y

    def treinar(self) -> None:
        """Treina o modelo com dados mockados."""
        X, y = self.preparar_dados_treino()
        X_scaled = self.scaler.fit_transform(X)
        self.modelo.fit(X_scaled, y)
        self.treinado = True

    def calcular_score(
        self,
        altitude: float,
        magnitude: float,
        separacao_lua: float = 90.0,
        interesse_cientifico: float = 0.5,
    ) -> float:
        """
        Calcula o score ML para um alvo baseado em suas características.

        Args:
            altitude: Altitude do alvo em graus (0-90).
            magnitude: Magnitude aparente do alvo.
            separacao_lua: Separação angular da Lua em graus.
            interesse_cientifico: Peso de interesse científico (0-1).

        Returns:
            Score entre 0 e 1 indicando qualidade do alvo.
        """
        if not self.treinado:
            self.treinar()

        # Normalizar inputs
        altitude_norm = altitude / 90.0
        magnitude_norm = 1 - (magnitude / 15.0)  # Assume mag máx ~15
        separacao_norm = separacao_lua / 180.0

        features = np.array([[
            altitude_norm,
            magnitude_norm,
            separacao_norm,
            interesse_cientifico,
        ]])

        features_scaled = self.scaler.transform(features)
        probabilidade = self.modelo.predict_proba(features_scaled)[0][1]

        return float(probabilidade)


class PlanejadorObservacao:
    """
    Classe principal que coordena o planejamento de observações.
    
    Integra todas as funcionalidades:
    - Consulta de catálogos
    - Cálculo de posições
    - Ranqueamento ML
    - Geração do plano final
    """

    def __init__(
        self,
        observatorio: Observatorio,
        data_obs: datetime,
        tipo_alvo: str,
        duracao_horas: float = 8.0,
    ):
        """
        Inicializa o planejador de observação.

        Args:
            observatorio: Objeto Observatorio com coordenadas.
            data_obs: Data e hora da observação.
            tipo_alvo: Tipo de objeto a observar.
            duracao_horas: Duração da sessão em horas.
        """
        self.observatorio = observatorio
        self.data_obs = Time(data_obs)
        self.tipo_alvo = tipo_alvo
        self.duracao_horas = duracao_horas
        self.observer = observatorio.to_observer()
        self.modelo_ml = ModeloRankingML()
        self.alvos_processados: list[AlvoAstronomico] = []

    def buscar_alvos(self, **kwargs) -> list[AlvoAstronomico]:
        """
        Busca alvos do catálogo baseado no tipo especificado.

        Args:
            **kwargs: Argumentos adicionais para a busca.

        Returns:
            Lista de alvos encontrados.
        """
        print(f"\n🔭 Buscando {self.tipo_alvo}...")
        alvos = CatalogoSimulado.buscar_alvos(
            tipo_alvo=self.tipo_alvo,
            quantidade=kwargs.get("quantidade", 10),
            magnitude_max=kwargs.get("magnitude_max", 12.0),
        )
        print(f"   Encontrados {len(alvos)} alvos potenciais.")
        return alvos

    def calcular_visibilidade(
        self,
        alvo: AlvoAstronomico,
    ) -> dict:
        """
        Calcula a visibilidade de um alvo durante a noite.

        Args:
            alvo: Objeto AlvoAstronomico.

        Returns:
            Dicionário com informações de visibilidade.
        """
        target = alvo.to_fixed_target()

        # Definir janela de tempo da observação
        tempo_inicio = self.data_obs
        tempo_fim = self.data_obs + self.duracao_horas * u.hour
        tempos = Time(np.linspace(tempo_inicio.jd, tempo_fim.jd, 100), format="jd")

        # Calcular coordenadas altazimutais
        frame_altaz = AltAz(obstime=tempos, location=self.observer.location)
        altaz_coords = target.coord.transform_to(frame_altaz)

        # Calcular nascer/pôr do sol para restrições
        try:
            pôr_sol = self.observer.sun_set_time(
                tempo_inicio, which="next"
            ).to_datetime()
            nascer_sol = self.observer.sun_rise_time(
                tempo_inicio, which="next"
            ).to_datetime()
        except Exception:
            pôr_sol = tempo_inicio.to_datetime()
            nascer_sol = tempo_fim.to_datetime()

        # Encontrar altitude máxima
        altitudes = altaz_coords.alt.deg
        altitude_max_idx = np.argmax(altitudes)
        altitude_max = float(altitudes[altitude_max_idx])
        azimute_max = float(altaz_coords.az.deg[altitude_max_idx])
        tempo_altitude_max = tempos[altitude_max_idx]

        # Determinar janela de observação (altitude > 30 graus)
        mask_altitude = altitudes > 30
        if np.any(mask_altitude):
            indices_validos = np.where(mask_altitude)[0]
            janela_inicio = tempos[indices_validos[0]]
            janela_fim = tempos[indices_validos[-1]]
        else:
            janela_inicio = tempo_altitude_max
            janela_fim = tempo_altitude_max

        # Calcular separação da Lua
        try:
            lua_pos = get_body("moon", tempo_inicio)
            separacao_lua = float(target.coord.separation(lua_pos).deg)
        except Exception:
            separacao_lua = 90.0

        return {
            "altitude_max": altitude_max,
            "azimute_max": azimute_max,
            "tempo_transito": tempo_altitude_max,
            "janela_inicio": janela_inicio,
            "janela_fim": janela_fim,
            "separacao_lua": separacao_lua,
            "pôr_sol": pôr_sol,
            "nascer_sol": nascer_sol,
        }

    def ranquear_alvos(
        self,
        alvos: list[AlvoAstronomico],
    ) -> list[AlvoAstronomico]:
        """
        Ranqueia alvos usando o modelo ML.

        Args:
            alvos: Lista de alvos a serem ranqueados.

        Returns:
            Lista de alvos ordenada por score ML.
        """
        print("\n🤖 Aplicando modelo de Machine Learning para ranqueamento...")

        for alvo in alvos:
            visibilidade = self.calcular_visibilidade(alvo)

            # Calcular score ML
            score = self.modelo_ml.calcular_score(
                altitude=visibilidade["altitude_max"],
                magnitude=alvo.magnitude,
                separacao_lua=visibilidade["separacao_lua"],
                interesse_cientifico=np.random.uniform(0.5, 1.0),  # Mockado
            )

            alvo.score_ml = score
            alvo.altitude_max = visibilidade["altitude_max"]
            alvo.azimute_max = visibilidade["azimute_max"]
            alvo.janela_inicio = visibilidade["janela_inicio"]
            alvo.janela_fim = visibilidade["janela_fim"]

        # Ordenar por score ML (decrescente)
        alvos_ordenados = sorted(alvos, key=lambda x: x.score_ml, reverse=True)

        scores = [a.score_ml for a in alvos_ordenados]
        print(f"   Scores ML: min={min(scores):.3f}, max={max(scores):.3f}, "
              f"média={np.mean(scores):.3f}")

        return alvos_ordenados

    def otimizar_sequencia(
        self,
        alvos: list[AlvoAstronomico],
        max_alvos: int = 5,
    ) -> list[AlvoAstronomico]:
        """
        Otimiza a sequência de observação considerando movimento do telescópio.

        Args:
            alvos: Lista de alvos ranqueados.
            max_alvos: Número máximo de alvos na sequência.

        Returns:
            Lista otimizada de alvos para observação.
        """
        print(f"\n📋 Otimizando sequência de observação (top {max_alvos} alvos)...")

        if len(alvos) == 0:
            return []

        # Selecionar top alvos baseado no score ML
        selecionados = alvos[:max_alvos]

        # Ordenar por tempo de transito para minimizar movimento
        selecionados.sort(key=lambda x: x.janela_inicio.jd if x.janela_inicio else 0)

        print(f"   Sequência otimizada com {len(selecionados)} alvos.")
        return selecionados

    def gerar_plano(self) -> dict:
        """
        Gera o plano de observação completo.

        Returns:
            Dicionário contendo o plano de observação detalhado.
        """
        print("\n" + "=" * 60)
        print("🌟 ASSISTENTE PESSOAL DE OBSERVAÇÃO ASTRONÔMICA 🌟")
        print("=" * 60)
        print(f"\n📍 Observatório: {self.observatorio.nome}")
        print(f"   Coordenadas: {self.observatorio.latitude:.2f}°, "
              f"{self.observatorio.longitude:.2f}°, "
              f"{self.observatorio.altitude:.0f}m")
        print(f"📅 Data: {self.data_obs.to_datetime().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"🎯 Tipo de alvo: {self.tipo_alvo}")

        # Passo 1: Buscar alvos
        alvos = self.buscar_alvos()

        # Passo 2: Ranquear com ML
        alvos_ranqueados = self.ranquear_alvos(alvos)

        # Passo 3: Otimizar sequência
        alvos_otimizados = self.otimizar_sequencia(alvos_ranqueados)

        # Gerar relatório
        plano = self._gerar_relatorio(alvos_otimizados)

        self.alvos_processados = alvos_otimizados

        return plano

    def _gerar_relatorio(self, alvos: list[AlvoAstronomico]) -> dict:
        """
        Gera o relatório final do plano de observação.

        Args:
            alvos: Lista de alvos processados.

        Returns:
            Dicionário com o relatório detalhado.
        """
        print("\n" + "=" * 60)
        print("📊 PLANO DE OBSERVAÇÃO GERADO")
        print("=" * 60)

        relatorio = {
            "observatorio": {
                "nome": self.observatorio.nome,
                "latitude": self.observatorio.latitude,
                "longitude": self.observatorio.longitude,
                "altitude": self.observatorio.altitude,
            },
            "data_obs": self.data_obs.iso,
            "tipo_alvo": self.tipo_alvo,
            "alvos": [],
            "resumo": {
                "total_alvos": len(alvos),
                "score_medio": np.mean([a.score_ml for a in alvos]) if alvos else 0,
                "score_maximo": max([a.score_ml for a in alvos]) if alvos else 0,
            },
        }

        print(f"\n{'Ordem':<6} {'Nome':<15} {'RA (°)':<10} {'Dec (°)':<10} "
              f"{('Mag'):<6} {'Score ML':<10} {'Alt Max':<10}")
        print("-" * 70)

        for i, alvo in enumerate(alvos, 1):
            info_alvo = {
                "ordem": i,
                "nome": alvo.nome,
                "coordenadas": {
                    "ra_graus": alvo.ra,
                    "dec_graus": alvo.dec,
                    "ra_hms": str(alvo.to_skycoord().ra.to_string(unit=u.hour, sep=":")),
                    "dec_dms": str(alvo.to_skycoord().dec.to_string(sep=":")),
                },
                "magnitude": alvo.magnitude,
                "score_ml": alvo.score_ml,
                "janela_observacao": {
                    "inicio": alvo.janela_inicio.to_datetime().strftime("%Y-%m-%d %H:%M:%S")
                    if alvo.janela_inicio else "N/A",
                    "fim": alvo.janela_fim.to_datetime().strftime("%Y-%m-%d %H:%M:%S")
                    if alvo.janela_fim else "N/A",
                },
                "posicao_maxima": {
                    "altitude_graus": alvo.altitude_max,
                    "azimute_graus": alvo.azimute_max,
                },
            }
            relatorio["alvos"].append(info_alvo)

            print(f"{i:<6} {alvo.nome:<15} {alvo.ra:<10.2f} {alvo.dec:<10.2f} "
                  f"{alvo.magnitude:<6.2f} {alvo.score_ml:<10.3f} "
                  f"{alvo.altitude_max:<10.2f}")

        print("-" * 70)
        print(f"\n✅ Plano de observação gerado com sucesso!")
        print(f"   Total de alvos: {relatorio['resumo']['total_alvos']}")
        print(f"   Score ML médio: {relatorio['resumo']['score_medio']:.3f}")
        print(f"   Melhor score: {relatorio['resumo']['score_maximo']:.3f}")

        return relatorio


def main():
    """Função principal que executa o fluxo completo do MVP."""
    # Configurar parâmetros de entrada
    data_observacao = datetime(2025, 6, 15, 22, 0, 0)  # 15 de Junho de 2025, 22:00 UTC

    observatorio = Observatorio(
        nome="Observatório Nacional",
        latitude=-22.5,  # Rio de Janeiro, Brasil
        longitude=-43.2,
        altitude=500,
    )

    tipo_alvo = "galaxias"  # Opções: "asteroides", "estrelas_variaveis", "galaxias"

    # Criar planejador e gerar plano
    planejador = PlanejadorObservacao(
        observatorio=observatorio,
        data_obs=data_observacao,
        tipo_alvo=tipo_alvo,
        duracao_horas=8.0,
    )

    plano = planejador.gerar_plano()

    # Retornar o plano para uso programático
    return plano


if __name__ == "__main__":
    plano_observacao = main()
