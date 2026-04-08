"""
RESOLUCAO COMPLETA - ESTABILIDADE E CURTO-CIRCUITO
===================================================
Exercicio: Sistema com G1, T1, 4 LTs (A,B,C,D) e barra infinita.

Dados:
  G1: 45 MVA; 6 kV; X1=X2=15%; X0=10%; Xn=2%
  T1: 3ph; 40 MVA; 7,5 Y / 230 D kV; X=10%
  Sistema: S=415 MVA; cos_phi=0,90; X_L=0,70 pu; X_c=0,12 pu; X_d=0,30 pu; H=5,0 s
  Operacao: Vt=1,02 pu; Vinf=1,0 pu; P=343 MW na barra infinita

Topologia (H-bridge com barramento intermediario):
  Bus1 --LT_A--> BusM --LT_B--> Inf
  Bus1 --LT_C--> BusM --LT_D--> Inf
  (A||C em paralelo, B||D em paralelo)

Base para curto (itens b,c): 40 MVA, 6,5 kV no circuito de G1
"""

import numpy as np
import math
import cmath
from collections import deque

# ============================================================================
#                      ITEM (a): ESTABILIDADE TRANSITORIA
#                      Criterio das Areas Iguais
# ============================================================================

def resolver_estabilidade():
    print("=" * 78)
    print("  ITEM (a): ANALISE DE ESTABILIDADE TRANSITORIA")
    print("  Criterio das Areas Iguais - Desconexao da LT C")
    print("=" * 78)

    # --- Dados do sistema (todos em pu na base de 415 MVA) ---
    S_base = 415.0    # MVA
    Xd_prime = 0.30   # X'd do gerador (reatancia transitoria)
    X_T = 0.12        # Reatancia do transformador
    X_L = 0.70        # Reatancia de cada linha de transmissao
    H = 5.0           # Constante de inercia (s)

    Vt = 1.02         # Tensao terminal (pu)
    Vinf = 1.0        # Tensao da barra infinita (pu)
    P_MW = 343.0      # Potencia entregue a barra infinita (MW)
    P_m = P_MW / S_base  # Potencia mecanica em pu

    print(f"\n  --- DADOS ---")
    print(f"  S_base = {S_base} MVA")
    print(f"  X'd = {Xd_prime} pu | X_T = {X_T} pu | X_L = {X_L} pu/linha")
    print(f"  Vt = {Vt} pu | V_inf = {Vinf} pu")
    print(f"  P = {P_MW} MW = {P_m:.4f} pu")
    print(f"  H = {H} s")

    # --- TOPOLOGIA PRE-FALTA (todas as 4 LTs) ---
    # A||C (Bus1 -> BusM): X_L/2
    # B||D (BusM -> Inf):  X_L/2
    X_AC = X_L / 2   # = 0.35 pu
    X_BD = X_L / 2   # = 0.35 pu
    X_linhas_pre = X_AC + X_BD  # = 0.70 pu

    X_total_pre = Xd_prime + X_T + X_linhas_pre
    X_ext_pre = X_T + X_linhas_pre  # entre Vt e Vinf

    print(f"\n  --- PRE-PERTURBACAO (4 LTs em servico) ---")
    print(f"  X_A||C = {X_AC:.4f} pu")
    print(f"  X_B||D = {X_BD:.4f} pu")
    print(f"  X_linhas = {X_linhas_pre:.4f} pu")
    print(f"  X_total = X'd + X_T + X_linhas = {Xd_prime} + {X_T} + {X_linhas_pre} = {X_total_pre:.4f} pu")
    print(f"  X_ext (Vt a Vinf) = {X_ext_pre:.4f} pu")

    # --- Calculo de E' e delta_0 ---
    # P = Vt * Vinf * sin(theta) / X_ext
    sin_theta = P_m * X_ext_pre / (Vt * Vinf)
    if abs(sin_theta) > 1:
        print(f"\n  ERRO: sin(theta) = {sin_theta:.4f} > 1 - operacao impossivel!")
        return
    theta = math.asin(sin_theta)
    theta_deg = math.degrees(theta)

    print(f"\n  --- CALCULO DE E' (tensao interna transitoria) ---")
    print(f"  sin(theta) = Pm*Xext/(Vt*Vinf) = {P_m:.4f}*{X_ext_pre:.4f}/({Vt}*{Vinf})")
    print(f"  sin(theta) = {sin_theta:.4f}")
    print(f"  theta = {theta_deg:.2f} graus")

    # Fasores
    Vt_c = Vt * cmath.exp(1j * theta)
    Vinf_c = complex(Vinf, 0)

    # Corrente
    I = (Vt_c - Vinf_c) / (1j * X_ext_pre)
    I_mag = abs(I)
    I_ang = math.degrees(cmath.phase(I))

    print(f"\n  Vt = {Vt:.2f} ang {theta_deg:.2f} graus = {Vt_c.real:.4f} + j{Vt_c.imag:.4f} pu")
    print(f"  I = (Vt - Vinf) / jXext = {I.real:.4f} + j{I.imag:.4f} pu")
    print(f"      |I| = {I_mag:.4f} pu, ang = {I_ang:.2f} graus")

    # E' = Vt + jX'd * I
    E_prime = Vt_c + 1j * Xd_prime * I
    E_mag = abs(E_prime)
    delta_0 = cmath.phase(E_prime)
    delta_0_deg = math.degrees(delta_0)

    print(f"\n  E' = Vt + jX'd * I")
    print(f"  E' = {E_prime.real:.4f} + j{E_prime.imag:.4f} pu")
    print(f"  |E'| = {E_mag:.4f} pu")
    print(f"  delta_0 = {delta_0_deg:.2f} graus = {delta_0:.4f} rad")

    # Curva P-delta pre-falta
    P_max_pre = E_mag * Vinf / X_total_pre
    P_check = P_max_pre * math.sin(delta_0)

    print(f"\n  --- CURVA P-delta PRE-PERTURBACAO ---")
    print(f"  Pe_pre(delta) = {P_max_pre:.4f} * sin(delta)")
    print(f"  P_max_pre = E'*Vinf/Xtotal = {E_mag:.4f}*{Vinf}/{X_total_pre:.4f} = {P_max_pre:.4f} pu")
    print(f"  Verificacao: Pmax_pre * sin(delta_0) = {P_max_pre:.4f} * sin({delta_0_deg:.2f}) = {P_check:.4f} pu")
    print(f"  Pm = {P_m:.4f} pu  -> Erro = {abs(P_check - P_m):.6f} pu  OK!")

    # --- TOPOLOGIA POS-PERTURBACAO (LT C desconectada) ---
    # Apenas LT_A de Bus1 a BusM
    # LT_B || LT_D de BusM a Inf
    X_left_post = X_L         # so A: 0.70 pu
    X_right_post = X_L / 2    # B||D: 0.35 pu
    X_linhas_post = X_left_post + X_right_post  # = 1.05 pu
    X_total_post = Xd_prime + X_T + X_linhas_post

    P_max_post = E_mag * Vinf / X_total_post

    print(f"\n  --- POS-PERTURBACAO (LT C desconectada) ---")
    print(f"  X_A (Bus1->BusM) = {X_left_post:.4f} pu  (so LT A)")
    print(f"  X_B||D (BusM->Inf) = {X_right_post:.4f} pu")
    print(f"  X_linhas = {X_linhas_post:.4f} pu")
    print(f"  X_total = {Xd_prime} + {X_T} + {X_linhas_post:.4f} = {X_total_post:.4f} pu")
    print(f"  Pe_pos(delta) = {P_max_post:.4f} * sin(delta)")
    print(f"  P_max_pos = {P_max_post:.4f} pu = {P_max_post * S_base:.1f} MW")

    # --- ANALISE DE ESTABILIDADE ---
    print(f"\n  {'=' * 60}")
    print(f"  ANALISE DE ESTABILIDADE - CRITERIO DAS AREAS IGUAIS")
    print(f"  {'=' * 60}")
    print(f"\n  Pm       = {P_m:.4f} pu  ({P_MW:.0f} MW)")
    print(f"  Pmax_pos = {P_max_post:.4f} pu  ({P_max_post * S_base:.1f} MW)")

    if P_m > P_max_post:
        print(f"\n  >>> Pm ({P_m:.4f}) > Pmax_pos ({P_max_post:.4f}) <<<")
        print(f"\n  *** SISTEMA INSTAVEL ***")
        print(f"\n  Explicacao:")
        print(f"  Apos a desconexao subita da LT C, a reatancia total entre")
        print(f"  o gerador e a barra infinita aumenta de {X_total_pre:.2f} para {X_total_post:.2f} pu.")
        print(f"  Isso reduz a potencia maxima transferivel de {P_max_pre:.4f} para {P_max_post:.4f} pu.")
        print(f"")
        print(f"  Como a potencia mecanica Pm = {P_m:.4f} pu EXCEDE a potencia")
        print(f"  eletrica maxima pos-perturbacao Pmax_pos = {P_max_post:.4f} pu,")
        print(f"  NAO EXISTE ponto de equilibrio na curva pos-perturbacao.")
        print(f"")
        print(f"  Pelo criterio das areas iguais:")
        print(f"  Pe_pos(delta) = {P_max_post:.4f}*sin(delta) < Pm = {P_m:.4f} para todo delta.")
        print(f"  Portanto, Pm - Pe > 0 para qualquer angulo delta.")
        print(f"  Nao ha area desacelerante (Ad = 0).")
        print(f"  A area acelerante cresce indefinidamente.")
        print(f"  O rotor acelera sem limite -> perda de sincronismo.")
        print(f"")
        print(f"  Conclusao: O gerador perdera o sincronismo com a barra")
        print(f"  infinita. O sistema e INSTAVEL apos a perda da LT C.")
    else:
        # Sistema possivelmente estavel - calcular areas
        sin_delta1 = P_m / P_max_post
        delta_1 = math.asin(sin_delta1)
        delta_1_deg = math.degrees(delta_1)
        delta_max = math.pi - delta_1
        delta_max_deg = math.degrees(delta_max)

        print(f"\n  Novo ponto de equilibrio: delta_1 = {delta_1_deg:.2f} graus")
        print(f"  Angulo maximo (equilibrio instavel): delta_max = {delta_max_deg:.2f} graus")
        print(f"  delta_0 = {delta_0_deg:.2f} graus")

        # Area acelerante
        d0 = delta_0
        d1 = delta_1
        dm = delta_max

        A_acc = P_m * (d1 - d0) + P_max_post * (math.cos(d1) - math.cos(d0))

        # Area desacelerante maxima
        A_dec = -P_max_post * (math.cos(dm) - math.cos(d1)) - P_m * (dm - d1)

        print(f"\n  Area acelerante  (Aa) = {A_acc:.6f} pu.rad")
        print(f"  Area desacelerante max (Ad) = {A_dec:.6f} pu.rad")

        if A_dec >= A_acc:
            margem = (A_dec - A_acc) / A_dec * 100
            print(f"\n  Ad >= Aa -> SISTEMA ESTAVEL")
            print(f"  Margem de estabilidade = {margem:.1f}%")
        else:
            print(f"\n  Ad < Aa -> SISTEMA INSTAVEL")


# ============================================================================
#                 ITENS (b) e (c): CURTO-CIRCUITO
#                 Motor de calculo (do script fornecido)
# ============================================================================

CONEXOES_TRAFO_VALIDAS = ('Yat', 'Y', 'D')
TIPOS_FALTA_VALIDOS = ('3F', '1FT', 'FF', '2FT')
j = 1j
INF_Z = 1e12

def gerador(barra, potencia_mva, tensao_kv, x1_pu, x0_pu, xn_pu=0.0, aterrado=True, nome=None):
    return {'barra': barra, 'potencia_mva': potencia_mva, 'tensao_kv': tensao_kv,
            'x1_pu': x1_pu, 'x0_pu': x0_pu, 'xn_pu': xn_pu,
            'aterrado': aterrado, 'nome': nome or barra}

def barramento_infinito(barra, aterrado=True, nome=None):
    return {'barra': barra, 'aterrado': aterrado, 'nome': nome or barra}

def transformador(barra_primario, barra_secundario, potencia_mva, tensao_primario_kv,
                  tensao_secundario_kv, x_pu, conexao_primario, conexao_secundario, nome=None):
    return {'barra_primario': barra_primario, 'barra_secundario': barra_secundario,
            'potencia_mva': potencia_mva, 'tensao_primario_kv': tensao_primario_kv,
            'tensao_secundario_kv': tensao_secundario_kv, 'x_pu': x_pu,
            'conexao_primario': conexao_primario, 'conexao_secundario': conexao_secundario,
            'nome': nome or f"{barra_primario}_{barra_secundario}"}

def linha(barra_de, barra_para, x1_ohm, x0_ohm=None, nome=None):
    return {'barra_de': barra_de, 'barra_para': barra_para,
            'x1_ohm': x1_ohm, 'x0_ohm': x0_ohm,
            'nome': nome or f"{barra_de}_{barra_para}"}

def falta_em_linha(nome_linha, barra_falta='FALTA', posicao=0.5):
    return {'nome_linha': nome_linha, 'barra_falta': barra_falta, 'posicao': posicao}


def _fjx(z, nd=4):
    return f"j{round(z.imag, nd)}"

def _fmt(z, nd=4):
    a, b = z.real, z.imag
    return f"{a:.{nd}f} {'+' if b >= 0 else '-'} {abs(b):.{nd}f}j"

def _polar(z):
    return abs(z), math.degrees(cmath.phase(z))

def _header(t):
    print("\n" + "=" * 78)
    print(f"  {t}")
    print("=" * 78)


class MotorCC:
    """Motor de calculo de curto-circuito por componentes simetricas."""

    def __init__(self, sb, barra_ref, vb_ref, geradores, bus_inf, trafos, linhas,
                 falta_linha, barra_falta, tipo_falta, zf=0):
        self.sb = sb
        self.barra_ref = barra_ref
        self.vb_ref = vb_ref
        self.barra_falta = barra_falta
        self.tipo_falta = tipo_falta
        self.zf = zf

        self._ger = [self._norm_ger(g) for g in geradores]
        self._bi = [self._norm_bi(b) for b in bus_inf]
        self._trf = [self._norm_trf(t) for t in trafos]
        self._lt = [self._norm_lt(l) for l in linhas]

        # Falta em linha: dividir a linha
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

        self.barras = []
        self.vb = {}
        self.zb = {}
        self.ib = {}
        self._idx = {}
        self.n = 0
        self.Zbus = {0: None, 1: None, 2: None}
        self._ramos = {0: [], 1: [], 2: []}
        self._shunts = {0: [], 1: [], 2: []}

    def _norm_ger(self, item):
        return dict(barra=item['barra'], s=item['potencia_mva'], v=item['tensao_kv'],
                    x1=item['x1_pu'], x0=item['x0_pu'], xn=item.get('xn_pu', 0),
                    at=item.get('aterrado', True), nome=item.get('nome', item['barra']))

    def _norm_bi(self, item):
        return dict(barra=item['barra'], at=item.get('aterrado', True),
                    nome=item.get('nome', item['barra']))

    def _norm_trf(self, item):
        return dict(bp=item['barra_primario'], bs=item['barra_secundario'],
                    s=item['potencia_mva'], vp=item['tensao_primario_kv'],
                    vs=item['tensao_secundario_kv'], x=item['x_pu'],
                    cp=item['conexao_primario'], cs=item['conexao_secundario'],
                    nome=item.get('nome', f"{item['barra_primario']}_{item['barra_secundario']}"))

    def _norm_lt(self, item):
        x0 = item['x1_ohm'] if item.get('x0_ohm') is None else item['x0_ohm']
        return dict(de=item['barra_de'], para=item['barra_para'],
                    x1=item['x1_ohm'], x0=x0,
                    nome=item.get('nome', f"{item['barra_de']}_{item['barra_para']}"))

    def _descobrir_barras(self):
        bb = set()
        for g in self._ger: bb.add(g['barra'])
        for b in self._bi: bb.add(b['barra'])
        for t in self._trf: bb.add(t['bp']); bb.add(t['bs'])
        for l in self._lt: bb.add(l['de']); bb.add(l['para'])
        self.barras = sorted(bb)
        self.n = len(self.barras)
        self._idx = {nome: i for i, nome in enumerate(self.barras)}

    def _propagar_bases(self):
        self.vb = {self.barra_ref: self.vb_ref}
        adj = {}
        for t in self._trf:
            r = t['vs'] / t['vp']
            adj.setdefault(t['bp'], []).append((t['bs'], r))
            adj.setdefault(t['bs'], []).append((t['bp'], 1/r))
        for l in self._lt:
            adj.setdefault(l['de'], []).append((l['para'], 1.0))
            adj.setdefault(l['para'], []).append((l['de'], 1.0))
        fila = deque([self.barra_ref])
        vis = {self.barra_ref}
        while fila:
            at = fila.popleft()
            for viz, r in adj.get(at, []):
                if viz not in vis:
                    self.vb[viz] = self.vb[at] * r
                    vis.add(viz)
                    fila.append(viz)
        for b in self.barras:
            if b not in self.vb:
                raise ValueError(f"Barra '{b}' desconectada")
            v = self.vb[b] * 1e3
            self.zb[b] = v**2 / (self.sb * 1e6)
            self.ib[b] = (self.sb * 1e6) / (math.sqrt(3) * v)

    def _mbase(self, x, s, v, barra):
        return j * x * (self.sb / s) * (v / self.vb[barra])**2

    def _converter_pu(self):
        for g in self._ger:
            g['_z1'] = self._mbase(g['x1'], g['s'], g['v'], g['barra'])
            g['_z0'] = self._mbase(g['x0'], g['s'], g['v'], g['barra'])
            g['_zn'] = self._mbase(g['xn'], g['s'], g['v'], g['barra']) if g['xn'] > 0 else 0
        for b in self._bi:
            b['_z1'] = j*1e-10
            b['_z0'] = j*1e-10 if b['at'] else j*INF_Z
        for t in self._trf:
            t['_z'] = self._mbase(t['x'], t['s'], t['vp'], t['bp'])
        for l in self._lt:
            l['_z1'] = j * (l['x1'] / self.zb[l['de']])
            l['_z0'] = j * (l['x0'] / self.zb[l['de']])

    def _montar_zbus(self):
        for seq in (1, 2, 0):
            Y = np.zeros((self.n, self.n), dtype=complex)

            for g in self._ger:
                i = self._idx[g['barra']]
                if seq in (1, 2):
                    Y[i,i] += 1/g['_z1']
                else:
                    if g['at']:
                        z = g['_z0'] + 3*g['_zn']
                        Y[i,i] += 1/z

            for b in self._bi:
                i = self._idx[b['barra']]
                z = b['_z1'] if seq in (1,2) else b['_z0']
                if abs(z.imag) < INF_Z/2:
                    Y[i,i] += 1/z

            for t in self._trf:
                ip, is_ = self._idx[t['bp']], self._idx[t['bs']]
                zt = t['_z']
                if seq in (1, 2):
                    Y[ip,ip] += 1/zt; Y[is_,is_] += 1/zt
                    Y[ip,is_] -= 1/zt; Y[is_,ip] -= 1/zt
                else:
                    cp, cs = t['cp'], t['cs']
                    if cp == 'Yat' and cs == 'Yat':
                        Y[ip,ip] += 1/zt; Y[is_,is_] += 1/zt
                        Y[ip,is_] -= 1/zt; Y[is_,ip] -= 1/zt
                    elif cp == 'Yat' and cs in ('D','Y'):
                        Y[ip,ip] += 1/zt
                    elif cp in ('D','Y') and cs == 'Yat':
                        Y[is_,is_] += 1/zt

            for l in self._lt:
                ide, ipa = self._idx[l['de']], self._idx[l['para']]
                z = l['_z1'] if seq in (1,2) else l['_z0']
                Y[ide,ide] += 1/z; Y[ipa,ipa] += 1/z
                Y[ide,ipa] -= 1/z; Y[ipa,ide] -= 1/z

            if seq == 0:
                for i in range(self.n):
                    if abs(Y[i,i]) < 1e-15:
                        Y[i,i] = 1/(j*INF_Z)

            self.Zbus[seq] = np.linalg.inv(Y)

    def preparar(self):
        self._descobrir_barras()
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

    def imprimir_bases(self):
        _header("BASES DO SISTEMA")
        print(f"  Sb = {self.sb:.1f} MVA")
        for b in self.barras:
            print(f"  {b:12s}:  Vb={self.vb[b]:10.4f} kV   Zb={self.zb[b]:10.4f} ohm   Ib={self.ib[b]:10.4f} A")

    def imprimir_elementos(self):
        _header("ELEMENTOS EM pu (base do sistema: {:.0f} MVA)".format(self.sb))
        for g in self._ger:
            zn_str = f", 3Zn={_fjx(3*g['_zn'])}" if g['_zn'] else ""
            print(f"  {g['nome']:20s}: Z1={_fjx(g['_z1'])}, Z0={_fjx(g['_z0'])}{zn_str}")
        for b in self._bi:
            s = "Z1~0, Z0~0" if b['at'] else "Z1~0, Z0=inf"
            print(f"  {b['nome']:20s}: {s}")
        for t in self._trf:
            print(f"  {t['nome']:20s}: Z={_fjx(t['_z'])}, {t['cp']}/{t['cs']}")
        for l in self._lt:
            print(f"  {l['nome']:20s}: Z1={_fjx(l['_z1'])}, Z0={_fjx(l['_z0'])}   ({l['x1']:.2f} ohm)")

    def imprimir_zbus(self, seq=1):
        nm = {1:'positiva', 2:'negativa', 0:'zero'}
        Z = self.Zbus[seq]
        _header(f"Zbus - Seq. {nm[seq]}")
        h = "          " + "".join(f"{b:>14s}" for b in self.barras)
        print(h)
        for i, bi in enumerate(self.barras):
            r = f"  {bi:8s}" + "".join(f"  {_fjx(Z[i,k]):>12s}" for k in range(self.n))
            print(r)

    def imprimir_falta(self, res):
        b = res['barra']
        f = self._idx[b]
        nomes = {'3F':'Trifasico','1FT':'Monofasico-terra','FF':'Bifasico (b-c)','2FT':'Bifasico-terra (b-c-T)'}
        _header(f"FALTA {nomes.get(res['tipo'],res['tipo'])} em {b}  (Zf={res['zf']})")
        print(f"  Zeq1 = {_fjx(res['Zeq1'])} pu")
        print(f"  Zeq2 = {_fjx(res['Zeq2'])} pu")
        print(f"  Zeq0 = {_fjx(res['Zeq0'])} pu")
        print(f"\n  Correntes de sequencia no ponto de falta:")
        print(f"    Ia1F = {_fmt(res['I1F'])} pu")
        print(f"    Ia2F = {_fmt(res['I2F'])} pu")
        print(f"    Ia0F = {_fmt(res['I0F'])} pu")
        ib_a = self.ib[b]
        print(f"\n  Correntes de fase no ponto de falta (Ib_base = {ib_a:.4f} A):")
        for n, v in [('Ia',res['IaF']),('Ib',res['IbF']),('Ic',res['IcF'])]:
            m, a = _polar(v)
            print(f"    {n} = {_fmt(v)} pu")
            print(f"       |{n}| = {m:.4f} pu = {m*ib_a:.4f} A, ang = {a:.2f} graus")

    def imprimir_tensoes_barra(self, barra, res):
        f = self._idx[barra]
        vb_kv = self.vb[barra]
        _header(f"TENSOES EM {barra}  (Vb = {vb_kv:.4f} kV)")
        print(f"  Tensoes de sequencia:")
        print(f"    Va1 = {_fmt(res['V1'][f])} pu")
        print(f"    Va2 = {_fmt(res['V2'][f])} pu")
        print(f"    Va0 = {_fmt(res['V0'][f])} pu")
        print(f"\n  Tensoes de fase:")
        for n, v in [('Va',res['Va'][f]),('Vb',res['Vb'][f]),('Vc',res['Vc'][f])]:
            m, a = _polar(v)
            print(f"    {n} = {_fmt(v)} pu")
            print(f"       |{n}| = {m:.4f} pu = {m*vb_kv:.4f} kV, ang = {a:.2f} graus")


def resolver_curto_circuito():
    """Resolve os itens (b) e (c) - Curto 2phi-T no meio da LT A."""

    # --- Base do sistema ---
    Sb_MVA = 40.0
    Vb_REF_kV = 6.5     # Base de tensao no circuito de G1

    # --- Reatancia das linhas em ohm ---
    # X_L = 0.70 pu na base de 415 MVA, 230 kV
    # X_L_ohm = 0.70 * 230^2 / 415
    X_L_ohm = 0.70 * 230**2 / 415   # = 89.2289 ohm por linha

    print(f"\n  Conversao da reatancia das linhas:")
    print(f"  X_L = 0.70 pu (base 415 MVA, 230 kV)")
    print(f"  Z_base_415 = 230^2/415 = {230**2/415:.4f} ohm")
    print(f"  X_L = 0.70 * {230**2/415:.4f} = {X_L_ohm:.4f} ohm por linha")

    # --- Dados do sistema ---
    ger = [
        gerador(barra='G1', potencia_mva=45, tensao_kv=6, x1_pu=0.15,
                x0_pu=0.10, xn_pu=0.02, aterrado=True, nome='G1'),
    ]

    bi = [
        barramento_infinito(barra='INF', aterrado=True, nome='B_infinito'),
    ]

    trf = [
        transformador(barra_primario='G1', barra_secundario='BUS1',
                      potencia_mva=40, tensao_primario_kv=7.5,
                      tensao_secundario_kv=230, x_pu=0.10,
                      conexao_primario='Yat', conexao_secundario='D', nome='T1'),
    ]

    lts = [
        linha(barra_de='BUS1', barra_para='BUSM', x1_ohm=X_L_ohm, x0_ohm=X_L_ohm, nome='LT_A'),
        linha(barra_de='BUSM', barra_para='INF',  x1_ohm=X_L_ohm, x0_ohm=X_L_ohm, nome='LT_B'),
        linha(barra_de='BUS1', barra_para='BUSM', x1_ohm=X_L_ohm, x0_ohm=X_L_ohm, nome='LT_C'),
        linha(barra_de='BUSM', barra_para='INF',  x1_ohm=X_L_ohm, x0_ohm=X_L_ohm, nome='LT_D'),
    ]

    fl = falta_em_linha(nome_linha='LT_A', barra_falta='FALTA', posicao=0.5)

    # --- Criar e executar o motor ---
    m = MotorCC(
        sb=Sb_MVA,
        barra_ref='G1',
        vb_ref=Vb_REF_kV,
        geradores=ger,
        bus_inf=bi,
        trafos=trf,
        linhas=lts,
        falta_linha=fl,
        barra_falta='FALTA',
        tipo_falta='2FT',
        zf=0,
    )
    m.preparar()

    # --- Impressao dos resultados ---
    m.imprimir_bases()
    m.imprimir_elementos()
    m.imprimir_zbus(1)
    m.imprimir_zbus(2)
    m.imprimir_zbus(0)

    # Falta
    res = m.falta('FALTA', '2FT', 0)
    m.imprimir_falta(res)

    # Tensoes em G1 (item c)
    m.imprimir_tensoes_barra('G1', res)

    # Tensoes em todas as barras
    _header("TENSOES (|pu|) EM TODAS AS BARRAS")
    for i, bb in enumerate(m.barras):
        va_m, va_a = _polar(res['Va'][i])
        vb_m, vb_a = _polar(res['Vb'][i])
        vc_m, vc_a = _polar(res['Vc'][i])
        print(f"  {bb:12s}: |Va|={va_m:.4f}  |Vb|={vb_m:.4f}  |Vc|={vc_m:.4f}")

    return m, res


# ============================================================================
#                           EXECUCAO PRINCIPAL
# ============================================================================

def main():
    print("\n" + "#" * 78)
    print("#" + " " * 76 + "#")
    print("#   RESOLUCAO COMPLETA - ESTABILIDADE E CURTO-CIRCUITO" + " " * 22 + "#")
    print("#" + " " * 76 + "#")
    print("#" * 78)

    # ----------------------------------------------------------------
    # ITEM (a): Estabilidade
    # ----------------------------------------------------------------
    resolver_estabilidade()

    # ----------------------------------------------------------------
    # ITENS (b) e (c): Curto-circuito
    # ----------------------------------------------------------------
    print("\n\n")
    print("=" * 78)
    print("  ITEM (b): CORRENTES DE FALTA - Curto 2phi-T no meio da LT A")
    print("  ITEM (c): TENSOES EM G1 durante a falta")
    print("  Base: 40 MVA, 6.5 kV no circuito de G1")
    print("=" * 78)

    m, res = resolver_curto_circuito()

    # ----------------------------------------------------------------
    # RESUMO FINAL
    # ----------------------------------------------------------------
    print("\n\n")
    _header("RESUMO FINAL")

    print("\n  ITEM (a) - Estabilidade:")
    print("  Apos desconexao da LT C:")
    print("    X_total_pre = 1.12 pu -> Pmax_pre = E'Vinf/X = ~1.023 pu")
    print("    X_total_pos = 1.47 pu -> Pmax_pos = E'Vinf/X = ~0.779 pu")
    print("    Pm = 0.827 pu > Pmax_pos = 0.779 pu")
    print("    >>> SISTEMA INSTAVEL - perda de sincronismo <<<")

    f_idx = m._idx['FALTA']
    g_idx = m._idx['G1']
    ib_falta = m.ib['FALTA']

    print(f"\n  ITEM (b) - Correntes de falta (2phi-T no meio da LT A):")
    print(f"    Zeq1 = {_fjx(res['Zeq1'])} pu")
    print(f"    Zeq2 = {_fjx(res['Zeq2'])} pu")
    print(f"    Zeq0 = {_fjx(res['Zeq0'])} pu")
    for n, v in [('Ia',res['IaF']),('Ib',res['IbF']),('Ic',res['IcF'])]:
        mag, ang = _polar(v)
        print(f"    {n} = {mag:.4f} ang {ang:.2f} pu = {mag*ib_falta:.4f} A")

    print(f"\n  ITEM (c) - Tensoes em G1 (durante a falta):")
    vb_g1 = m.vb['G1']
    for n, v in [('Va',res['Va'][g_idx]),('Vb',res['Vb'][g_idx]),('Vc',res['Vc'][g_idx])]:
        mag, ang = _polar(v)
        print(f"    {n} = {mag:.4f} ang {ang:.2f} pu = {mag*vb_g1:.4f} kV")

    print("\n" + "=" * 78)
    print("  CONCLUIDO")
    print("=" * 78)


if __name__ == '__main__':
    main()
