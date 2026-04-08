"""
short_circuit_analysis.py  -  Analise de Curto-Circuito por Componentes Simetricas
===================================================================================

COMO USAR:
  1. Edite SOMENTE o bloco "DADOS DO SISTEMA" abaixo (linhas ~20-120)
  2. Execute:   python short_circuit_analysis.py
  3. Pronto.

Nao precisa mexer em nada abaixo da linha "NAO MEXA DAQUI PRA BAIXO".

Tipos de falta:  '3F'  |  '1FT'  |  'FF'  |  '2FT'
"""

import numpy as np, math, cmath
from collections import deque

CONEXOES_TRAFO_VALIDAS = ('Yat', 'Y', 'D')
TIPOS_FALTA_VALIDOS = ('3F', '1FT', 'FF', '2FT')


def gerador(barra, potencia_mva, tensao_kv, x1_pu, x0_pu, xn_pu=0.0, aterrado=True, nome=None):
    return {
        'barra': barra,
        'potencia_mva': potencia_mva,
        'tensao_kv': tensao_kv,
        'x1_pu': x1_pu,
        'x0_pu': x0_pu,
        'xn_pu': xn_pu,
        'aterrado': aterrado,
        'nome': nome or barra,
    }


def barramento_infinito(barra, aterrado=True, nome=None):
    return {
        'barra': barra,
        'aterrado': aterrado,
        'nome': nome or barra,
    }


def transformador(barra_primario, barra_secundario, potencia_mva, tensao_primario_kv,
                  tensao_secundario_kv, x_pu, conexao_primario, conexao_secundario, nome=None):
    return {
        'barra_primario': barra_primario,
        'barra_secundario': barra_secundario,
        'potencia_mva': potencia_mva,
        'tensao_primario_kv': tensao_primario_kv,
        'tensao_secundario_kv': tensao_secundario_kv,
        'x_pu': x_pu,
        'conexao_primario': conexao_primario,
        'conexao_secundario': conexao_secundario,
        'nome': nome or f"{barra_primario}_{barra_secundario}",
    }


def linha(barra_de, barra_para, x1_ohm, x0_ohm=None, nome=None):
    return {
        'barra_de': barra_de,
        'barra_para': barra_para,
        'x1_ohm': x1_ohm,
        'x0_ohm': x0_ohm,
        'nome': nome or f"{barra_de}_{barra_para}",
    }


def carga(barra, potencia_mva, tensao_kv, x1_pu, x0_pu=None, nome=None):
    return {
        'barra': barra,
        'potencia_mva': potencia_mva,
        'tensao_kv': tensao_kv,
        'x1_pu': x1_pu,
        'x0_pu': x0_pu,
        'nome': nome or barra,
    }


def falta_em_linha(nome_linha, barra_falta='FALTA', posicao=0.5):
    return {
        'nome_linha': nome_linha,
        'barra_falta': barra_falta,
        'posicao': posicao,
    }


def _bool_entrada(valor, campo):
    if isinstance(valor, bool):
        return valor
    if valor in (0, 1):
        return bool(valor)
    raise ValueError(f"O campo '{campo}' deve ser True/False (ou 1/0).")


def _normalizar_gerador(item):
    if isinstance(item, dict):
        if 'potencia_mva' in item:
            return dict(
                barra=item['barra'],
                s=item['potencia_mva'],
                v=item['tensao_kv'],
                x1=item['x1_pu'],
                x0=item['x0_pu'],
                xn=item.get('xn_pu', 0.0),
                at=_bool_entrada(item.get('aterrado', True), 'aterrado'),
                nome=item.get('nome') or item['barra'],
            )
        if all(ch in item for ch in ('barra', 's', 'v', 'x1', 'x0', 'xn', 'at', 'nome')):
            return dict(
                barra=item['barra'],
                s=item['s'],
                v=item['v'],
                x1=item['x1'],
                x0=item['x0'],
                xn=item['xn'],
                at=_bool_entrada(item['at'], 'at'),
                nome=item['nome'],
            )
    if isinstance(item, (list, tuple)) and len(item) == 8:
        return dict(
            barra=item[0], s=item[1], v=item[2], x1=item[3], x0=item[4], xn=item[5],
            at=_bool_entrada(item[6], 'aterrado'), nome=item[7]
        )
    raise ValueError("Gerador invalido. Use gerador(...) ou o formato legado [barra, S, V, X1, X0, Xn, aterrado, nome].")


def _normalizar_bus_infinito(item):
    if isinstance(item, dict):
        if 'aterrado' in item:
            return dict(
                barra=item['barra'],
                at=_bool_entrada(item.get('aterrado', True), 'aterrado'),
                nome=item.get('nome') or item['barra'],
            )
        if all(ch in item for ch in ('barra', 'at', 'nome')):
            return dict(
                barra=item['barra'],
                at=_bool_entrada(item['at'], 'at'),
                nome=item['nome'],
            )
    if isinstance(item, (list, tuple)) and len(item) == 3:
        return dict(barra=item[0], at=_bool_entrada(item[1], 'aterrado'), nome=item[2])
    raise ValueError("Barramento infinito invalido. Use barramento_infinito(...) ou o formato legado [barra, aterrado, nome].")


def _normalizar_trafo(item):
    if isinstance(item, dict):
        if 'potencia_mva' in item:
            return dict(
                bp=item['barra_primario'],
                bs=item['barra_secundario'],
                s=item['potencia_mva'],
                vp=item['tensao_primario_kv'],
                vs=item['tensao_secundario_kv'],
                x=item['x_pu'],
                cp=item['conexao_primario'],
                cs=item['conexao_secundario'],
                nome=item.get('nome') or f"{item['barra_primario']}_{item['barra_secundario']}",
            )
        if all(ch in item for ch in ('bp', 'bs', 's', 'vp', 'vs', 'x', 'cp', 'cs', 'nome')):
            return dict(
                bp=item['bp'], bs=item['bs'], s=item['s'], vp=item['vp'], vs=item['vs'],
                x=item['x'], cp=item['cp'], cs=item['cs'], nome=item['nome']
            )
    if isinstance(item, (list, tuple)) and len(item) == 9:
        return dict(
            bp=item[0], bs=item[1], s=item[2], vp=item[3], vs=item[4],
            x=item[5], cp=item[6], cs=item[7], nome=item[8]
        )
    raise ValueError("Transformador invalido. Use transformador(...) ou o formato legado [pri, sec, S, Vpri, Vsec, X, conn_pri, conn_sec, nome].")


def _normalizar_linha(item):
    if isinstance(item, dict):
        if 'x1_ohm' in item:
            x0 = item['x1_ohm'] if item.get('x0_ohm') is None else item['x0_ohm']
            return dict(
                de=item['barra_de'],
                para=item['barra_para'],
                x1=item['x1_ohm'],
                x0=x0,
                nome=item.get('nome') or f"{item['barra_de']}_{item['barra_para']}",
            )
        if all(ch in item for ch in ('de', 'para', 'x1', 'x0', 'nome')):
            x0 = item['x1'] if item['x0'] is None else item['x0']
            return dict(de=item['de'], para=item['para'], x1=item['x1'], x0=x0, nome=item['nome'])
    if isinstance(item, (list, tuple)) and len(item) == 5:
        x0 = item[2] if item[3] is None else item[3]
        return dict(de=item[0], para=item[1], x1=item[2], x0=x0, nome=item[4])
    raise ValueError("Linha invalida. Use linha(...) ou o formato legado [de, para, X1, X0, nome].")


def _normalizar_carga(item):
    if isinstance(item, dict):
        if 'potencia_mva' in item:
            x0 = item['x1_pu'] if item.get('x0_pu') is None else item['x0_pu']
            return dict(
                barra=item['barra'],
                s=item['potencia_mva'],
                v=item['tensao_kv'],
                x1=item['x1_pu'],
                x0=x0,
                nome=item.get('nome') or item['barra'],
            )
        if all(ch in item for ch in ('barra', 's', 'v', 'x1', 'x0', 'nome')):
            x0 = item['x1'] if item['x0'] is None else item['x0']
            return dict(barra=item['barra'], s=item['s'], v=item['v'], x1=item['x1'], x0=x0, nome=item['nome'])
    if isinstance(item, (list, tuple)) and len(item) == 6:
        x0 = item[3] if item[4] is None else item[4]
        return dict(barra=item[0], s=item[1], v=item[2], x1=item[3], x0=x0, nome=item[5])
    raise ValueError("Carga invalida. Use carga(...) ou o formato legado [barra, S, V, X1, X0, nome].")


def _normalizar_falta_em_linha(item):
    if not item:
        return {}
    if isinstance(item, dict) and all(ch in item for ch in ('nome_linha', 'barra_falta', 'posicao')):
        return {
            'nome_linha': item['nome_linha'],
            'barra_falta': item['barra_falta'],
            'posicao': item['posicao'],
        }
    raise ValueError("FALTA_NA_LINHA invalida. Use falta_em_linha(...) ou um dict com nome_linha, barra_falta e posicao.")


def _nomes_duplicados(registros):
    contagem = {}
    for registro in registros:
        nome = registro['nome']
        contagem[nome] = contagem.get(nome, 0) + 1
    return sorted(nome for nome, qtd in contagem.items() if qtd > 1)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                        DADOS DO SISTEMA                                  ║
# ║               (EDITE SOMENTE ESTE BLOCO)                                 ║
# ╚════════════════════════════════════════════════════════════════════════════╝

# DICA:
#   - Para adicionar um novo elemento, copie uma linha existente e troque os valores.
#   - Os nomes dos campos foram escritos por extenso para ficar facil para alunos/professores.
#   - O script continua aceitando o formato antigo em listas, para nao quebrar casos antigos.

# --- Base do sistema ---
Sb_MVA = 30.0           # Potencia base (MVA)
BARRA_REF = 'G1'        # Barra de referencia para tensao base
Vb_REF_kV = 6.0         # Tensao base LL na barra de referencia (kV)

# --- Barras adicionais (opcional) ---
# Use somente se quiser cadastrar uma barra antes de conectar elementos nela.
BARRAS_ADICIONAIS = [
    # 'NOVA_BARRA',
]

# --- Geradores ---
# Xn_pu = reatancia de neutro na base propria. Use 0 se solidamente aterrado.
GERADORES = [
    gerador(barra='G1', potencia_mva=30, tensao_kv=6.6, x1_pu=0.15, x0_pu=0.16, xn_pu=0,   aterrado=True, nome='G1'),
    gerador(barra='G3', potencia_mva=35, tensao_kv=6.6, x1_pu=0.12, x0_pu=0.14, xn_pu=2.0, aterrado=True, nome='G3'),
]

# --- Barramentos infinitos ---
BUS_INFINITOS = [
    barramento_infinito(barra='B00', aterrado=True, nome='B_infinito'),
]

# --- Transformadores ---
# Conexoes validas: 'Yat' (Y aterrado), 'Y' (Y flutuante), 'D' (Delta)
# Para banco 3x1F em Y: V_LL = sqrt(3) * V_fase
TRAFOS = [
    transformador(barra_primario='G1',   barra_secundario='AT_E', potencia_mva=24, tensao_primario_kv=math.sqrt(3)*10, tensao_secundario_kv=119.51, x_pu=0.10, conexao_primario='Yat', conexao_secundario='D',   nome='T1'),
    transformador(barra_primario='AT_E', barra_secundario='B00',  potencia_mva=30, tensao_primario_kv=138,             tensao_secundario_kv=6.9,    x_pu=0.05, conexao_primario='Yat', conexao_secundario='Yat', nome='T2'),
    transformador(barra_primario='AT_D', barra_secundario='G3',   potencia_mva=30, tensao_primario_kv=138,             tensao_secundario_kv=6.9,    x_pu=0.05, conexao_primario='D',   conexao_secundario='Yat', nome='T3'),
    transformador(barra_primario='T4_P', barra_secundario='L1',   potencia_mva=30, tensao_primario_kv=120,             tensao_secundario_kv=12,     x_pu=0.07, conexao_primario='Yat', conexao_secundario='Yat', nome='T4'),
]

# --- Linhas de transmissao ---
# Se x0_ohm=None, o script assume x0_ohm = x1_ohm.
LINHAS = [
    linha(barra_de='AT_E', barra_para='AT_M', x1_ohm=90, x0_ohm=90, nome='LT1'),
    linha(barra_de='AT_M', barra_para='AT_D', x1_ohm=50, x0_ohm=50, nome='LT3'),
    linha(barra_de='AT_M', barra_para='T4_P', x1_ohm=60, x0_ohm=60, nome='LT2'),   # vai ate o primario do T4
]

# --- Cargas (opcional, geralmente desprezadas em curto) ---
CARGAS = [
    # carga(barra='L1', potencia_mva=25, tensao_kv=10, x1_pu=0.08, x0_pu=0.10, nome='Carga_L1'),
]

# --- Falta ---
# Se a falta for no meio de uma linha, use FALTA_NA_LINHA.
# Senao, deixe FALTA_NA_LINHA = {} e coloque a barra diretamente em BARRA_FALTA.
FALTA_NA_LINHA = falta_em_linha(nome_linha='LT1', barra_falta='FALTA', posicao=0.5)
# FALTA_NA_LINHA = {}

BARRA_FALTA = 'FALTA'   # barra onde ocorre a falta
TIPO_FALTA = '2FT'      # '3F', '1FT', 'FF', '2FT'
ZF = 0                  # impedancia de falta (0 = curto franco)

# --- Saidas extras (opcional) ---
# Corrente em ramos especificos (lista de [barra_de, barra_para])
CORRENTES_RAMOS = [
    ['B00', 'AT_E'],    # contribuicao do barramento infinito via T2
]

# SCC em barras especificas
SCC_BARRAS = [
    'AT_E',             # SCC na barra AT do barramento infinito
]

# Mostrar tensoes detalhadas nestas barras (alem da barra de falta)
TENSOES_BARRAS = [
    'AT_E',             # tensoes na barra AT do B00
]


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║              NAO MEXA DAQUI PRA BAIXO                                    ║
# ║              (motor de calculo)                                          ║
# ╚════════════════════════════════════════════════════════════════════════════╝

j = 1j
INF_Z = 1e12

def _fjx(z, nd=3):
    return f"j{round(z.imag, nd)}"

def _fmt(z, nd=3):
    a, b = z.real, z.imag
    return f"{a:.{nd}f} {'+' if b >= 0 else '-'} {abs(b):.{nd}f}j"

def _polar(z):
    return abs(z), math.degrees(cmath.phase(z))

def _header(t):
    print("\n" + "=" * 78)
    print(f"  {t}")
    print("=" * 78)


class _Motor:
    def __init__(self):
        self.sb = Sb_MVA
        self._ger = []
        self._bi = []
        self._trf = []
        self._lt = []
        self._cg = []
        self._barras_adicionais = []
        self.barras = []
        self.vb = {}
        self.zb = {}
        self.ib = {}
        self._idx = {}
        self.n = 0
        self.Zbus = {0: None, 1: None, 2: None}
        self._elem_pu = []
        self._ramos = {0: [], 1: [], 2: []}
        self._shunts = {0: [], 1: [], 2: []}

    def carregar_dados(self):
        self._ger = [_normalizar_gerador(g) for g in GERADORES]
        self._bi = [_normalizar_bus_infinito(b) for b in BUS_INFINITOS]
        self._trf = [_normalizar_trafo(t) for t in TRAFOS]
        self._lt = [_normalizar_linha(l) for l in LINHAS]
        self._cg = [_normalizar_carga(c) for c in CARGAS]
        self._barras_adicionais = [str(b) for b in BARRAS_ADICIONAIS]

        self._validar_dados_entrada()

        # Falta em linha
        falta_linha = _normalizar_falta_em_linha(FALTA_NA_LINHA)
        if falta_linha:
            nl = falta_linha['nome_linha']
            bf = falta_linha['barra_falta']
            pos = falta_linha['posicao']
            idx = None
            for i, lt in enumerate(self._lt):
                if lt['nome'] == nl:
                    idx = i
                    break
            if idx is None:
                raise ValueError(f"Linha '{nl}' nao encontrada")
            lt = self._lt.pop(idx)
            self._lt.append(dict(de=lt['de'], para=bf, x1=lt['x1']*pos, x0=lt['x0']*pos, nome=f"{nl}_esq"))
            self._lt.append(dict(de=bf, para=lt['para'], x1=lt['x1']*(1-pos), x0=lt['x0']*(1-pos), nome=f"{nl}_dir"))
            if BARRA_FALTA != bf:
                raise ValueError("Quando usar FALTA_NA_LINHA, BARRA_FALTA deve ser igual a barra_falta.")

        duplicadas = _nomes_duplicados(self._lt)
        if duplicadas:
            raise ValueError(f"Existem nomes de linhas repetidos: {', '.join(duplicadas)}")

    def _validar_dados_entrada(self):
        if self.sb <= 0:
            raise ValueError("Sb_MVA deve ser maior que zero.")
        if Vb_REF_kV <= 0:
            raise ValueError("Vb_REF_kV deve ser maior que zero.")
        if not BARRA_REF:
            raise ValueError("Defina uma BARRA_REF valida.")

        for tipo, registros in (
            ('geradores', self._ger),
            ('barramentos infinitos', self._bi),
            ('transformadores', self._trf),
            ('linhas', self._lt),
            ('cargas', self._cg),
        ):
            duplicadas = _nomes_duplicados(registros)
            if duplicadas:
                raise ValueError(f"Existem nomes repetidos em {tipo}: {', '.join(duplicadas)}")

        duplicadas = sorted(nome for nome in set(self._barras_adicionais) if self._barras_adicionais.count(nome) > 1)
        if duplicadas:
            raise ValueError(f"Existem barras adicionais repetidas: {', '.join(duplicadas)}")

        for g in self._ger:
            if g['s'] <= 0 or g['v'] <= 0:
                raise ValueError(f"Gerador '{g['nome']}' deve ter potencia e tensao positivas.")

        for t in self._trf:
            if t['bp'] == t['bs']:
                raise ValueError(f"Transformador '{t['nome']}' liga a mesma barra nos dois lados.")
            if t['s'] <= 0 or t['vp'] <= 0 or t['vs'] <= 0:
                raise ValueError(f"Transformador '{t['nome']}' deve ter potencia e tensoes positivas.")
            if t['cp'] not in CONEXOES_TRAFO_VALIDAS or t['cs'] not in CONEXOES_TRAFO_VALIDAS:
                raise ValueError(
                    f"Transformador '{t['nome']}' usa conexao invalida. Use apenas: {', '.join(CONEXOES_TRAFO_VALIDAS)}."
                )

        for l in self._lt:
            if l['de'] == l['para']:
                raise ValueError(f"Linha '{l['nome']}' liga a mesma barra nas duas pontas.")

        for c in self._cg:
            if c['s'] <= 0 or c['v'] <= 0:
                raise ValueError(f"Carga '{c['nome']}' deve ter potencia e tensao positivas.")

        tipo_falta = TIPO_FALTA.upper().replace('-', '')
        if tipo_falta not in TIPOS_FALTA_VALIDOS:
            raise ValueError(f"TIPO_FALTA invalido: '{TIPO_FALTA}'. Use apenas: {', '.join(TIPOS_FALTA_VALIDOS)}.")

        if FALTA_NA_LINHA:
            pos = _normalizar_falta_em_linha(FALTA_NA_LINHA)['posicao']
            if pos <= 0 or pos >= 1:
                raise ValueError("Em FALTA_NA_LINHA, 'posicao' deve ficar entre 0 e 1 (exclusivo). Para falta na extremidade, use a barra terminal.")

    def _descobrir_barras(self):
        bb = set()
        for b in self._barras_adicionais: bb.add(b)
        for g in self._ger: bb.add(g['barra'])
        for b in self._bi: bb.add(b['barra'])
        for t in self._trf: bb.add(t['bp']); bb.add(t['bs'])
        for l in self._lt: bb.add(l['de']); bb.add(l['para'])
        for c in self._cg: bb.add(c['barra'])
        self.barras = sorted(bb)
        self.n = len(self.barras)
        self._idx = {nome: i for i, nome in enumerate(self.barras)}

    def _validar_consultas(self):
        if BARRA_REF not in self._idx:
            raise ValueError(f"BARRA_REF '{BARRA_REF}' nao foi encontrada no sistema.")
        if BARRA_FALTA not in self._idx:
            raise ValueError(f"BARRA_FALTA '{BARRA_FALTA}' nao foi encontrada no sistema.")

        for barra in SCC_BARRAS:
            if barra not in self._idx:
                raise ValueError(f"A barra '{barra}' em SCC_BARRAS nao existe no sistema.")

        for barra in TENSOES_BARRAS:
            if barra not in self._idx:
                raise ValueError(f"A barra '{barra}' em TENSOES_BARRAS nao existe no sistema.")

        for de, para in CORRENTES_RAMOS:
            if de not in self._idx or para not in self._idx:
                raise ValueError(f"O ramo [{de}, {para}] em CORRENTES_RAMOS usa barra inexistente.")

    def _propagar_bases(self):
        self.vb = {BARRA_REF: Vb_REF_kV}
        adj = {}
        for t in self._trf:
            r = t['vs'] / t['vp']
            adj.setdefault(t['bp'], []).append((t['bs'], r))
            adj.setdefault(t['bs'], []).append((t['bp'], 1/r))
        for l in self._lt:
            adj.setdefault(l['de'], []).append((l['para'], 1.0))
            adj.setdefault(l['para'], []).append((l['de'], 1.0))
        fila = deque([BARRA_REF])
        vis = {BARRA_REF}
        while fila:
            at = fila.popleft()
            for viz, r in adj.get(at, []):
                if viz not in vis:
                    self.vb[viz] = self.vb[at] * r
                    vis.add(viz)
                    fila.append(viz)
        for b in self.barras:
            if b not in self.vb:
                raise ValueError(f"Barra '{b}' desconectada do sistema")
            v = self.vb[b] * 1e3
            self.zb[b] = v**2 / (self.sb * 1e6)
            self.ib[b] = (self.sb * 1e6) / (math.sqrt(3) * v)

    def _mbase(self, x, s, v, barra):
        return j * x * (self.sb / s) * (v / self.vb[barra])**2

    def _converter_pu(self):
        self._elem_pu = []
        for g in self._ger:
            g['_z1'] = self._mbase(g['x1'], g['s'], g['v'], g['barra'])
            g['_z0'] = self._mbase(g['x0'], g['s'], g['v'], g['barra'])
            g['_zn'] = self._mbase(g['xn'], g['s'], g['v'], g['barra']) if g['xn'] > 0 else 0
            self._elem_pu.append((g['nome'], f"Z1={_fjx(g['_z1'])}, Z0={_fjx(g['_z0'])}" + (f", 3Zn={_fjx(3*g['_zn'])}" if g['_zn'] else "")))
        for b in self._bi:
            b['_z1'] = j*1e-10
            b['_z0'] = j*1e-10 if b['at'] else j*INF_Z
            self._elem_pu.append((b['nome'], "Z1~0, Z0~0" if b['at'] else "Z1~0, Z0=inf"))
        for t in self._trf:
            t['_z'] = self._mbase(t['x'], t['s'], t['vp'], t['bp'])
            self._elem_pu.append((t['nome'], f"Z={_fjx(t['_z'])}, {t['cp']}/{t['cs']}"))
        for l in self._lt:
            l['_z1'] = j * (l['x1'] / self.zb[l['de']])
            l['_z0'] = j * (l['x0'] / self.zb[l['de']])
            self._elem_pu.append((l['nome'], f"Z1={_fjx(l['_z1'])}, Z0={_fjx(l['_z0'])}"))
        for c in self._cg:
            c['_z1'] = self._mbase(c['x1'], c['s'], c['v'], c['barra'])
            c['_z0'] = self._mbase(c['x0'], c['s'], c['v'], c['barra'])
            self._elem_pu.append((c['nome'], f"Z1={_fjx(c['_z1'])}, Z0={_fjx(c['_z0'])}"))

    def _montar_zbus(self):
        for seq in (1, 2, 0):
            Y = np.zeros((self.n, self.n), dtype=complex)
            ramos, shunts = [], []

            for g in self._ger:
                i = self._idx[g['barra']]
                if seq in (1, 2):
                    Y[i,i] += 1/g['_z1']
                    shunts.append((i, g['_z1'], g['nome']))
                else:
                    if g['at']:
                        z = g['_z0'] + 3*g['_zn']
                        Y[i,i] += 1/z
                        shunts.append((i, z, g['nome']))

            for b in self._bi:
                i = self._idx[b['barra']]
                z = b['_z1'] if seq in (1,2) else b['_z0']
                if abs(z.imag) < INF_Z/2:
                    Y[i,i] += 1/z
                    shunts.append((i, z, b['nome']))

            for t in self._trf:
                ip, is_ = self._idx[t['bp']], self._idx[t['bs']]
                zt = t['_z']
                if seq in (1, 2):
                    Y[ip,ip] += 1/zt; Y[is_,is_] += 1/zt
                    Y[ip,is_] -= 1/zt; Y[is_,ip] -= 1/zt
                    ramos.append((ip, is_, zt, t['nome']))
                else:
                    cp, cs = t['cp'], t['cs']
                    if cp == 'Yat' and cs == 'Yat':
                        Y[ip,ip] += 1/zt; Y[is_,is_] += 1/zt
                        Y[ip,is_] -= 1/zt; Y[is_,ip] -= 1/zt
                        ramos.append((ip, is_, zt, t['nome']))
                    elif cp == 'Yat' and cs in ('D','Y'):
                        Y[ip,ip] += 1/zt
                        shunts.append((ip, zt, t['nome']))
                    elif cp in ('D','Y') and cs == 'Yat':
                        Y[is_,is_] += 1/zt
                        shunts.append((is_, zt, t['nome']))

            for l in self._lt:
                ide, ipa = self._idx[l['de']], self._idx[l['para']]
                z = l['_z1'] if seq in (1,2) else l['_z0']
                Y[ide,ide] += 1/z; Y[ipa,ipa] += 1/z
                Y[ide,ipa] -= 1/z; Y[ipa,ide] -= 1/z
                ramos.append((ide, ipa, z, l['nome']))

            for c in self._cg:
                i = self._idx[c['barra']]
                z = c['_z1'] if seq in (1,2) else c['_z0']
                Y[i,i] += 1/z
                shunts.append((i, z, c['nome']))

            if seq == 0:
                for i in range(self.n):
                    if abs(Y[i,i]) < 1e-15:
                        Y[i,i] = 1/(j*INF_Z)

            self._ramos[seq] = ramos
            self._shunts[seq] = shunts
            self.Zbus[seq] = np.linalg.inv(Y)

    def preparar(self):
        self.carregar_dados()
        self._descobrir_barras()
        self._validar_consultas()
        self._propagar_bases()
        self._converter_pu()
        self._montar_zbus()

    def falta(self, barra, tipo, zf=0):
        f = self._idx[barra]
        z1 = self.Zbus[1][f,f]
        z2 = self.Zbus[2][f,f]
        z0 = self.Zbus[0][f,f]
        tipo = tipo.upper().replace('-','')

        if tipo == '3F':
            i1f = 1/(z1+zf); i2f = 0j; i0f = 0j
        elif tipo == '1FT':
            i1f = 1/(z1+z2+z0+3*zf); i2f = i1f; i0f = i1f
        elif tipo == 'FF':
            i1f = 1/(z1+z2+zf); i2f = -i1f; i0f = 0j
        elif tipo == '2FT':
            zp = (z2*(z0+3*zf))/(z2+z0+3*zf)
            i1f = 1/(z1+zp)
            i2f = -i1f*(z0+3*zf)/(z2+z0+3*zf)
            i0f = -i1f*z2/(z2+z0+3*zf)
        else:
            raise ValueError(f"Tipo invalido: '{tipo}'")

        a = complex(-0.5, math.sqrt(3)/2)
        ia = i0f + i1f + i2f
        ib = i0f + a**2*i1f + a*i2f
        ic = i0f + a*i1f + a**2*i2f

        V1 = np.ones(self.n, dtype=complex) - self.Zbus[1][:,f]*i1f
        V2 = -self.Zbus[2][:,f]*i2f
        V0 = -self.Zbus[0][:,f]*i0f
        Va = V0+V1+V2
        Vb = V0 + a**2*V1 + a*V2
        Vc = V0 + a*V1 + a**2*V2

        return dict(barra=barra, tipo=tipo, zf=zf,
                    Zeq1=z1, Zeq2=z2, Zeq0=z0,
                    I1F=i1f, I2F=i2f, I0F=i0f,
                    IaF=ia, IbF=ib, IcF=ic,
                    V1=V1, V2=V2, V0=V0, Va=Va, Vb=Vb, Vc=Vc)

    def corrente_ramo(self, de, para, res):
        a = complex(-0.5, math.sqrt(3)/2)
        id_, ip = self._idx[de], self._idx[para]
        i_seq = {}
        for seq in (1, 2, 0):
            V = [res['V1'], res['V2'], res['V0']][[1,2,0].index(seq)]
            vd, vp = V[id_], V[ip]
            itot = 0j
            for t in self._trf:
                bpb, bsb = t['bp'], t['bs']
                if (bpb==de and bsb==para) or (bsb==de and bpb==para):
                    if seq in (1,2):
                        itot += (vd-vp)/t['_z']
                    else:
                        cp, cs = t['cp'], t['cs']
                        if cp=='Yat' and cs=='Yat':
                            itot += (vd-vp)/t['_z']
            for l in self._lt:
                if (l['de']==de and l['para']==para) or (l['para']==de and l['de']==para):
                    z = l['_z1'] if seq in (1,2) else l['_z0']
                    itot += (vd-vp)/z
            i_seq[seq] = itot

        ia = i_seq[0]+i_seq[1]+i_seq[2]
        ib = i_seq[0]+a**2*i_seq[1]+a*i_seq[2]
        ic = i_seq[0]+a*i_seq[1]+a**2*i_seq[2]
        return dict(de=de, para=para, I1=i_seq[1], I2=i_seq[2], I0=i_seq[0],
                    Ia=ia, Ib=ib, Ic=ic)

    def scc(self, barra):
        f = self._idx[barra]
        z1 = self.Zbus[1][f,f]
        return dict(barra=barra, Zeq1=z1, SCC_pu=1/abs(z1), SCC_MVA=self.sb/abs(z1))

    # --- Impressao ---
    def imprimir_bases(self):
        _header("BASES DO SISTEMA")
        print(f"  Sb = {self.sb:.1f} MVA")
        for b in self.barras:
            print(f"  {b:12s}:  Vb={self.vb[b]:9.3f} kV   Zb={self.zb[b]:9.3f} ohm   Ib={self.ib[b]:10.3f} A")

    def imprimir_elementos(self):
        _header("ELEMENTOS EM pu")
        for n, d in self._elem_pu:
            print(f"  {n:20s}:  {d}")

    def imprimir_zbus(self, seq=1):
        nm = {1:'positiva', 2:'negativa', 0:'zero'}
        Z = self.Zbus[seq]
        _header(f"Zbus - Seq. {nm[seq]}")
        h = "          " + "".join(f"{b:>12s}" for b in self.barras)
        print(h)
        for i, bi in enumerate(self.barras):
            r = f"  {bi:8s}" + "".join(f"  {_fjx(Z[i,k]):>10s}" for k in range(self.n))
            print(r)

    def imprimir_falta(self, res):
        b = res['barra']
        f = self._idx[b]
        nomes = {'3F':'Trifasico','1FT':'Monofasico-terra','FF':'Bifasico (b-c)','2FT':'Bifasico-terra (b-c-T)'}
        _header(f"FALTA {nomes.get(res['tipo'],res['tipo'])} em {b}  (Zf={res['zf']})")
        print(f"  Zeq1 = {_fjx(res['Zeq1'])} pu")
        print(f"  Zeq2 = {_fjx(res['Zeq2'])} pu")
        print(f"  Zeq0 = {_fjx(res['Zeq0'])} pu")
        print(f"\n  Correntes de sequencia:")
        print(f"    Ia1F = {_fmt(res['I1F'])} pu")
        print(f"    Ia2F = {_fmt(res['I2F'])} pu")
        print(f"    Ia0F = {_fmt(res['I0F'])} pu")
        ib_a = self.ib[b]
        print(f"\n  Correntes de fase:")
        for n, v in [('Ia',res['IaF']),('Ib',res['IbF']),('Ic',res['IcF'])]:
            m, a = _polar(v)
            print(f"    {n} = {_fmt(v)} pu -> |{n}|={m:.3f} pu = {m*ib_a:.3f} A, ang={a:.2f} deg")
        print(f"\n  Tensoes na barra {b}:")
        vb_kv = self.vb[b]
        for n, v in [('Va',res['Va'][f]),('Vb',res['Vb'][f]),('Vc',res['Vc'][f])]:
            m, a = _polar(v)
            print(f"    {n} = {_fmt(v)} pu -> |{n}|={m:.3f} pu = {m*vb_kv:.3f} kV, ang={a:.2f} deg")
        print(f"\n  Tensoes (|pu|) em todas as barras:")
        for i, bb in enumerate(self.barras):
            print(f"    {bb:12s}: |Va|={abs(res['Va'][i]):.3f}  |Vb|={abs(res['Vb'][i]):.3f}  |Vc|={abs(res['Vc'][i]):.3f}")

    def imprimir_ramo(self, r):
        ib_a = self.ib[r['de']]
        _header(f"CORRENTE NO RAMO {r['de']} -> {r['para']}")
        print(f"  Ia1 = {_fmt(r['I1'])} pu")
        print(f"  Ia2 = {_fmt(r['I2'])} pu")
        print(f"  Ia0 = {_fmt(r['I0'])} pu")
        for n, v in [('Ia',r['Ia']),('Ib',r['Ib']),('Ic',r['Ic'])]:
            m, a = _polar(v)
            print(f"  {n} = {_fmt(v)} pu -> {m:.3f} pu = {m*ib_a:.3f} A, ang={a:.2f} deg")

    def imprimir_scc(self, s):
        _header(f"SCC em {s['barra']}")
        print(f"  Zeq1 = {_fjx(s['Zeq1'])} pu")
        print(f"  SCC  = {s['SCC_pu']:.3f} pu = {s['SCC_MVA']:.3f} MVA")

    def imprimir_tensoes_barra(self, barra, res):
        f = self._idx[barra]
        vb_kv = self.vb[barra]
        _header(f"TENSOES EM {barra}")
        # Sequencia
        print(f"  Va1 = {_fmt(res['V1'][f])} pu")
        print(f"  Va2 = {_fmt(res['V2'][f])} pu")
        print(f"  Va0 = {_fmt(res['V0'][f])} pu")
        print()
        for n, v in [('Va',res['Va'][f]),('Vb',res['Vb'][f]),('Vc',res['Vc'][f])]:
            m, a = _polar(v)
            print(f"  {n} = {_fmt(v)} pu -> |{n}|={m:.3f} pu = {m*vb_kv:.3f} kV, ang={a:.2f} deg")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                          EXECUCAO                                        ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def main():
    m = _Motor()
    m.preparar()

    m.imprimir_bases()
    m.imprimir_elementos()

    # Descomente para ver Zbus:
    # m.imprimir_zbus(1)
    # m.imprimir_zbus(0)

    # Falta
    res = m.falta(BARRA_FALTA, TIPO_FALTA, ZF)
    m.imprimir_falta(res)

    # Correntes em ramos
    for de, para in CORRENTES_RAMOS:
        r = m.corrente_ramo(de, para, res)
        m.imprimir_ramo(r)

    # Tensoes detalhadas
    for b in TENSOES_BARRAS:
        m.imprimir_tensoes_barra(b, res)

    # SCC
    for b in SCC_BARRAS:
        s = m.scc(b)
        m.imprimir_scc(s)

    print("\n" + "=" * 78)
    print("  CONCLUIDO")
    print("=" * 78)


if __name__ == '__main__':
    main()
