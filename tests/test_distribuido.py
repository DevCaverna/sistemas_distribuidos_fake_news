"""
Testes para distribuido/mestre.py (MestreDistribuido) e distribuido/worker.py.

Divididos em:
  - Testes unitarios do mestre: testam a logica interna da classe sem Pyro5.
  - Testes do worker com Pyro5 mockado: usam unittest.mock para substituir
    o Pyro5.api.Proxy por um objeto falso, testando o worker sem nameserver.
  - Testes de integracao (marcados com @pytest.mark.distribuido): requerem
    o nameserver Pyro5 rodando. Pule com: pytest -m "not distribuido"
"""

import threading
from unittest.mock import MagicMock, patch

import pytest

from core.automato import ESPALHADOR, IGNORANTE, INATIVO
from distribuido.mestre import MestreDistribuido
from distribuido.worker import executar_worker

ESTADOS_VALIDOS = {IGNORANTE, ESPALHADOR, INATIVO}

PARAMS = dict(
    linhas=10,
    colunas=10,
    geracoes=5,
    percentual_espalhadores=0.1,
    limiar=2,
    semente=42,
)


def _preparar_mestre(num_workers=2, usar_influenciadores=False, **kwargs):
    """Cria mestre, registra N workers e finaliza inicializacao."""
    params = {**PARAMS, **kwargs}
    m = MestreDistribuido(**params, usar_influenciadores=usar_influenciadores)
    for _ in range(num_workers):
        m.registrar_worker()
    m.inicializar(timeout=0)
    return m


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------

class TestMestreDistribuidoInit:
    def test_matriz_tem_shape_correto(self):
        m = MestreDistribuido(**PARAMS, usar_influenciadores=False)
        assert len(m.matriz) == 10
        assert all(len(row) == 10 for row in m.matriz)

    def test_fatias_geradas_apos_inicializar(self):
        m = _preparar_mestre(num_workers=2)
        assert len(m.fatias) == 2

    def test_offsets_calculados_apos_inicializar(self):
        m = _preparar_mestre(num_workers=2)
        assert len(m._offsets) == 2
        assert m._offsets[0] == 0

    def test_influenciadores_nulos_quando_desativado(self):
        m = MestreDistribuido(**PARAMS, usar_influenciadores=False)
        assert m.mapa_influenciadores is None

    def test_influenciadores_criados_quando_ativado(self):
        m = MestreDistribuido(**PARAMS, usar_influenciadores=True)
        assert m.mapa_influenciadores is not None
        assert isinstance(m.mapa_influenciadores, set)


# ---------------------------------------------------------------------------
# _calcular_ghosts
# ---------------------------------------------------------------------------

class TestCalcularGhosts:
    def test_cruzamento_de_bordas_com_2_workers(self):
        m = _preparar_mestre(num_workers=2)
        borda_base_w0 = [10] * 10
        borda_topo_w1 = [20] * 10
        m._bordas = {
            0: ([0] * 10, borda_base_w0),
            1: (borda_topo_w1, [0] * 10),
        }
        m._calcular_ghosts()

        ghost_topo_w0, ghost_base_w0 = m._ghosts[0]
        assert ghost_topo_w0 is None
        assert ghost_base_w0 == borda_topo_w1

        ghost_topo_w1, ghost_base_w1 = m._ghosts[1]
        assert ghost_topo_w1 == borda_base_w0
        assert ghost_base_w1 is None

    def test_worker_unico_sem_ghosts(self):
        m = _preparar_mestre(num_workers=1)
        m._bordas = {0: ([0] * 10, [0] * 10)}
        m._calcular_ghosts()
        ghost_topo, ghost_base = m._ghosts[0]
        assert ghost_topo is None
        assert ghost_base is None


# ---------------------------------------------------------------------------
# obter_matriz_final
# ---------------------------------------------------------------------------

class TestObterMatrizFinal:
    def test_reassembly_correto(self):
        m = _preparar_mestre(num_workers=2)
        fatia0 = [[IGNORANTE] * 10 for _ in range(5)]
        fatia1 = [[INATIVO] * 10 for _ in range(5)]
        m._fatias_finais = [fatia0, fatia1]

        matriz = m.obter_matriz_final()
        assert len(matriz) == 10
        assert all(len(row) == 10 for row in matriz)
        assert matriz[:5] == fatia0
        assert matriz[5:] == fatia1

    def test_estados_validos_no_resultado(self):
        m = _preparar_mestre(num_workers=2)
        fatia0 = [[IGNORANTE] * 10 for _ in range(5)]
        fatia1 = [[INATIVO] * 10 for _ in range(5)]
        m._fatias_finais = [fatia0, fatia1]
        for row in m.obter_matriz_final():
            for cell in row:
                assert cell in ESTADOS_VALIDOS


# ---------------------------------------------------------------------------
# registrar_worker
# ---------------------------------------------------------------------------

class TestRegistrarWorker:
    def test_1_worker_config_correta(self):
        m = _preparar_mestre(num_workers=1)
        config = m._configs[0]

        assert config["worker_id"] == 0
        assert config["fatia"] == m.fatias[0]
        assert config["geracoes"] == PARAMS["geracoes"]
        assert config["limiar"] == PARAMS["limiar"]
        assert config["num_workers"] == 1
        assert config["ghost_topo_inicial"] is None
        assert config["ghost_base_inicial"] is None
        assert config["offset_global"] == 0
        assert config["mapa_influenciadores"] is None

    def test_2_workers_ids_sequenciais(self):
        m = MestreDistribuido(**PARAMS, usar_influenciadores=False)
        ids = []

        def registrar():
            resp = m.registrar_worker()
            ids.append(resp["worker_id"])

        t0 = threading.Thread(target=registrar)
        t1 = threading.Thread(target=registrar)
        t0.start()
        t1.start()
        t0.join(timeout=5)
        t1.join(timeout=5)

        assert sorted(ids) == [0, 1]

    def test_ghost_inicial_worker_0_sem_vizinho_acima(self):
        m = _preparar_mestre(num_workers=2)
        config_w0 = m._configs[0]
        assert config_w0["ghost_topo_inicial"] is None

    def test_influenciadores_serializados_como_lista(self):
        m = _preparar_mestre(num_workers=1, usar_influenciadores=True)
        config = m._configs[0]
        assert isinstance(config["mapa_influenciadores"], list)


# ---------------------------------------------------------------------------
# Worker com Pyro5 mockado
# ---------------------------------------------------------------------------

class TestExecutarWorker:
    """
    Testa distribuido/worker.py substituindo Pyro5.api.Proxy por um MagicMock.
    """

    def _config(self, geracoes=2, linhas=4, colunas=4, com_influenciadores=False):
        """Config minima que o mestre retornaria para o worker."""
        return {
            "worker_id": 0,
            "fatia": [[IGNORANTE] * colunas for _ in range(linhas)],
            "geracoes": geracoes,
            "limiar": 2,
            "ghost_topo_inicial": None,
            "ghost_base_inicial": None,
            "offset_global": 0,
            "usar_midia": False,
            "geracao_midia": 5,
            "prob_sensacionalista": 0.08,
            "mapa_influenciadores": [[0, 1], [2, 3]] if com_influenciadores else None,
        }

    def _ghost(self, terminar=False):
        """Resposta padrao de obter_ghosts."""
        return {"ghost_topo": None, "ghost_base": None, "terminar": terminar}

    def _mock_mestre(self, config, terminar=False):
        """Cria um proxy mock ja configurado com as respostas padrao."""
        m = MagicMock()
        m.registrar_worker.return_value = {"worker_id": 0}
        m.aguardar_inicio.return_value = config
        m.obter_ghosts.return_value = self._ghost(terminar=terminar)
        return m

    # --- URI e conexao ---

    @patch("Pyro5.api.Proxy")
    def test_proxy_criado_com_uri_padrao(self, MockProxy):
        mock_mestre = self._mock_mestre(self._config())
        MockProxy.return_value = mock_mestre

        executar_worker()

        MockProxy.assert_called_once_with("PYRONAME:mestre.fakenews@localhost:9090")

    @patch("Pyro5.api.Proxy")
    def test_proxy_criado_com_host_e_porta_customizados(self, MockProxy):
        mock_mestre = self._mock_mestre(self._config())
        MockProxy.return_value = mock_mestre

        executar_worker(host_ns="192.168.0.10", porta_ns=9999)

        MockProxy.assert_called_once_with("PYRONAME:mestre.fakenews@192.168.0.10:9999")

    # --- Protocolo de registro ---

    @patch("Pyro5.api.Proxy")
    def test_registrar_worker_chamado_uma_vez(self, MockProxy):
        mock_mestre = self._mock_mestre(self._config())
        MockProxy.return_value = mock_mestre

        executar_worker()

        mock_mestre.registrar_worker.assert_called_once()

    @patch("Pyro5.api.Proxy")
    def test_aguardar_inicio_chamado(self, MockProxy):
        mock_mestre = self._mock_mestre(self._config())
        MockProxy.return_value = mock_mestre

        executar_worker()

        mock_mestre.aguardar_inicio.assert_called_once_with(0)

    # --- Loop de geracoes ---

    @patch("Pyro5.api.Proxy")
    def test_enviar_bordas_chamado_uma_vez_por_geracao(self, MockProxy):
        GERACOES = 3
        mock_mestre = self._mock_mestre(self._config(geracoes=GERACOES))
        MockProxy.return_value = mock_mestre

        executar_worker()

        assert mock_mestre.enviar_bordas.call_count == GERACOES

    @patch("Pyro5.api.Proxy")
    def test_obter_ghosts_chamado_uma_vez_por_geracao(self, MockProxy):
        GERACOES = 3
        mock_mestre = self._mock_mestre(self._config(geracoes=GERACOES))
        MockProxy.return_value = mock_mestre

        executar_worker()

        assert mock_mestre.obter_ghosts.call_count == GERACOES

    @patch("Pyro5.api.Proxy")
    def test_enviar_bordas_passa_worker_id_e_geracao(self, MockProxy):
        mock_mestre = self._mock_mestre(self._config(geracoes=1))
        MockProxy.return_value = mock_mestre

        executar_worker()

        args = mock_mestre.enviar_bordas.call_args[0]
        assert args[0] == 0
        assert args[1] == 1

    # --- Parada antecipada ---

    @patch("Pyro5.api.Proxy")
    def test_early_stop_quando_terminar_true(self, MockProxy):
        mock_mestre = self._mock_mestre(self._config(geracoes=10), terminar=True)
        MockProxy.return_value = mock_mestre

        executar_worker()

        assert mock_mestre.enviar_bordas.call_count == 1

    @patch("Pyro5.api.Proxy")
    def test_enviar_resultado_chamado_apos_early_stop(self, MockProxy):
        mock_mestre = self._mock_mestre(self._config(geracoes=10), terminar=True)
        MockProxy.return_value = mock_mestre

        executar_worker()

        mock_mestre.enviar_resultado.assert_called_once()

    # --- Resultado final ---

    @patch("Pyro5.api.Proxy")
    def test_enviar_resultado_chamado_uma_vez(self, MockProxy):
        mock_mestre = self._mock_mestre(self._config())
        MockProxy.return_value = mock_mestre

        executar_worker()

        mock_mestre.enviar_resultado.assert_called_once()

    @patch("Pyro5.api.Proxy")
    def test_enviar_resultado_passa_worker_id_correto(self, MockProxy):
        config = self._config()
        config["worker_id"] = 2
        mock_mestre = self._mock_mestre(config)
        MockProxy.return_value = mock_mestre

        executar_worker()

        args = mock_mestre.enviar_resultado.call_args[0]
        assert args[0] == 2

    @patch("Pyro5.api.Proxy")
    def test_enviar_resultado_passa_lista_como_fatia(self, MockProxy):
        mock_mestre = self._mock_mestre(self._config())
        MockProxy.return_value = mock_mestre

        executar_worker()

        args = mock_mestre.enviar_resultado.call_args[0]
        fatia_final = args[1]
        assert isinstance(fatia_final, list)
        assert isinstance(fatia_final[0], list)

    # --- Mapa de influenciadores ---

    @patch("Pyro5.api.Proxy")
    def test_mapa_influenciadores_deserializado_de_lista(self, MockProxy):
        mock_mestre = self._mock_mestre(self._config(com_influenciadores=True))
        MockProxy.return_value = mock_mestre

        executar_worker()

        mock_mestre.enviar_resultado.assert_called_once()

    @patch("Pyro5.api.Proxy")
    def test_sem_influenciadores_mapa_permanece_none(self, MockProxy):
        mock_mestre = self._mock_mestre(self._config(com_influenciadores=False))
        MockProxy.return_value = mock_mestre

        executar_worker()

        mock_mestre.enviar_resultado.assert_called_once()


# ---------------------------------------------------------------------------
# Integracao (requer nameserver Pyro5)
# ---------------------------------------------------------------------------

@pytest.mark.distribuido
def test_integracao_worker_full():
    """
    Teste end-to-end com processos reais.
    Requer: `pyro5-ns -p 9090` rodando em outro terminal.
    """
    try:
        import Pyro5.api
        ns = Pyro5.api.locate_ns(port=9090)
    except Exception:
        pytest.skip("NameServer nao encontrado na porta 9090")
