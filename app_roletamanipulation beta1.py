# app_roletamanipulation.py
import streamlit as st
from collections import Counter

# --- CLASSE PRINCIPAL: O CÉREBRO DO ANALISADOR ---
# Esta classe contém toda a lógica das 10 aulas.

class RoletaMestre:
    def __init__(self):
        # --- DADOS ESTRUTURAIS DA ROLETA ---
        self.CILINDRO_EUROPEU = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
        
        # --- MAPEAMENTOS PRÉ-CALCULADOS PARA EFICIÊNCIA ---
        self.NUMERO_INFO = self._mapear_info_numeros()
        self.VIZINHOS_MAPEADOS = self._mapear_vizinhos_do_cilindro()
        self.TERMINAIS_MAPEADOS = self._mapear_terminais()
        self.DEZENAS_MAPEADAS = {
            1: list(range(1, 13)),
            2: list(range(13, 25)),
            3: list(range(25, 37))
        }
        self.REGIOES_TERMINAIS = self._calcular_regioes_dos_terminais()
        self.ESPELHOS = {12: 21, 13: 31, 14: 41, 21: 12, 23: 32, 24: 42, 31: 13, 32: 23, 34: 43} # Mapeamento simplificado

        # --- ESTADO DINÂMICO DA ANÁLISE ---
        self.historico = []
        self.tendencia_atual = None # Ex: {'tipo': 'TERMINAL', 'valor': 4, 'contagem': 5, 'numeros_ja_vistos': {4, 14, 24}}
        self.modo_retorno = None    # Ex: {'tentativas': 1, 'alvo': {'tipo': 'TERMINAL', 'valor': 4}}

    # --- MÉTODOS DE INICIALIZAÇÃO E MAPEAMENTO ---
    def _mapear_info_numeros(self):
        info = {}
        for num in range(37):
            info[num] = {
                'terminal': num % 10,
                'duzia': 1 if 1 <= num <= 12 else 2 if 13 <= num <= 24 else 3 if 25 <= num <= 36 else 0,
                'dezena': (num // 10) * 10 if num > 0 else 0 # Agrupa em 0, 10, 20, 30
            }
        return info

    def _mapear_vizinhos_do_cilindro(self):
        vizinhos = {}
        tamanho = len(self.CILINDRO_EUROPEU)
        for i, num in enumerate(self.CILINDRO_EUROPEU):
            vizinhos[num] = {
                "v-2": self.CILINDRO_EUROPEU[(i - 2 + tamanho) % tamanho],
                "v-1": self.CILINDRO_EUROPEU[(i - 1 + tamanho) % tamanho],
                "num": num,
                "v+1": self.CILINDRO_EUROPEU[(i + 1) % tamanho],
                "v+2": self.CILINDRO_EUROPEU[(i + 2) % tamanho],
            }
        return vizinhos

    def _mapear_terminais(self):
        terminais = {i: [] for i in range(10)}
        for i in range(37):
            terminais[i % 10].append(i)
        return terminais

    def _calcular_regioes_dos_terminais(self):
        regioes = {}
        for terminal, numeros_do_terminal in self.TERMINAIS_MAPEADOS.items():
            regiao_completa = set()
            for num in numeros_do_terminal:
                regiao_completa.update(self.VIZINHOS_MAPEADOS[num].values())
            regioes[terminal] = sorted(list(regiao_completa))
        return regioes

    # --- MÉTODO PÚBLICO PRINCIPAL ---
    def adicionar_numero(self, numero):
        if 0 <= numero <= 36:
            self.historico.append(numero)
            if len(self.historico) > 20:
                self.historico.pop(0)

    # --- CAMADA 3: GERENCIAMENTO DO CICLO DE VIDA DA TENDÊNCIA ---
    def _gerenciar_ciclo_vida(self):
        # LÓGICA DE QUEBRA: A tendência ativa foi quebrada?
        if self.tendencia_atual:
            ultimo_num = self.historico[-1]
            tipo = self.tendencia_atual['tipo']
            valor = self.tendencia_atual['valor']
            
            quebrou = False
            if tipo == 'TERMINAL' and self.NUMERO_INFO[ultimo_num]['terminal'] != valor:
                quebrou = True
            elif tipo == 'DEZENA' and self.NUMERO_INFO[ultimo_num]['dezena'] != valor:
                quebrou = True

            if quebrou:
                diagnostico = f"**QUEBRA CONFIRMADA!** A tendência do {tipo} {valor} foi quebrada pelo número {ultimo_num}."
                estrategia = f"**Iniciar busca pelo RETORNO.** Apostar nos números do {tipo} {valor}, pois a mesa tende a voltar para a manipulação original."
                # Ativa o modo de retorno e reseta a tendência
                self.modo_retorno = {'tentativas': 1, 'alvo': {'tipo': tipo, 'valor': valor}}
                numeros_rec = self.TERMINAIS_MAPEADOS[valor] if tipo == 'TERMINAL' else [n for n, info in self.NUMERO_INFO.items() if info['dezena'] == valor]
                self.tendencia_atual = None
                return {"diagnostico": diagnostico, "estrategia": estrategia, "numeros_recomendados": numeros_rec}

        # LÓGICA DE RETORNO: Estamos buscando um retorno?
        if self.modo_retorno:
            alvo_tipo = self.modo_retorno['alvo']['tipo']
            alvo_valor = self.modo_retorno['alvo']['valor']
            ultimo_num = self.historico[-1]

            acertou_retorno = False
            if alvo_tipo == 'TERMINAL' and self.NUMERO_INFO[ultimo_num]['terminal'] == alvo_valor:
                acertou_retorno = True
            elif alvo_tipo == 'DEZENA' and self.NUMERO_INFO[ultimo_num]['dezena'] == alvo_valor:
                acertou_retorno = True
            
            if acertou_retorno:
                diagnostico = f"**RETORNO CONFIRMADO!** O número {ultimo_num} confirmou a volta para a manipulação do {alvo_tipo} {alvo_valor}."
                estrategia = "Retorno bem-sucedido. Aguardar a formação de um novo padrão."
                self.modo_retorno = None # Reseta o modo retorno
                return {"diagnostico": diagnostico, "estrategia": estrategia}
            else:
                self.modo_retorno['tentativas'] += 1
                if self.modo_retorno['tentativas'] > 3:
                    diagnostico = "**LIMITE DE TENTATIVAS ATINGIDO.** A busca pelo retorno falhou após 3 tentativas."
                    estrategia = "O padrão se desfez. **Pare de apostar** e aguarde uma nova tendência clara se formar."
                    self.modo_retorno = None # Reseta
                    return {"diagnostico": diagnostico, "estrategia": estrategia}
                else:
                    diagnostico = f"**Buscando Retorno (Tentativa {self.modo_retorno['tentativas']}/3).** A quebra persiste com o número {ultimo_num}."
                    estrategia = f"Continuar apostando no {alvo_tipo} {alvo_valor} para buscar o retorno."
                    numeros_rec = self.TERMINAIS_MAPEADOS[alvo_valor] if alvo_tipo == 'TERMINAL' else [n for n, info in self.NUMERO_INFO.items() if info['dezena'] == alvo_valor]
                    return {"diagnostico": diagnostico, "estrategia": estrategia, "numeros_recomendados": numeros_rec}

        return None # Nenhum estado de ciclo de vida ativo

    # --- CAMADA 1: IDENTIFICAÇÃO DAS MARÉS (TENDÊNCIAS PRINCIPAIS) ---
    def _identificar_mares(self):
        hist_10 = self.historico[-10:]
        if len(hist_10) < 5: return None

        # 1. Manipulação de Terminal (Predominância)
        terminais = [self.NUMERO_INFO[n]['terminal'] for n in hist_10]
        terminal_counts = Counter(terminais)
        t_comum, t_freq = terminal_counts.most_common(1)[0]
        if t_freq >= 4: # Pelo menos 40% do histórico recente
            return {'tipo': 'TERMINAL', 'valor': t_comum, 'contagem': t_freq, 'numeros_ja_vistos': set(self.TERMINAIS_MAPEADOS[t_comum]).intersection(set(hist_10))}

        # 2. Manipulação de Dezena
        dezenas = [self.NUMERO_INFO[n]['dezena'] for n in hist_10 if self.NUMERO_INFO[n]['dezena'] != 0]
        dezena_counts = Counter(dezenas)
        if dezena_counts:
            d_comum, d_freq = dezena_counts.most_common(1)[0]
            if d_freq >= 4:
                return {'tipo': 'DEZENA', 'valor': d_comum, 'contagem': d_freq, 'numeros_ja_vistos': set(n for n,i in self.NUMERO_INFO.items() if i['dezena'] == d_comum).intersection(set(hist_10))}

        return None

    # --- CAMADA 2: ANÁLISE DAS ONDAS (GATILHOS DE TEMPO DE TELA) ---
    def _analisar_ondas(self, mare_ativa):
        if len(self.historico) < 3: return None

        # Padrão de Retorno de Dúzia (A, B, B -> A)
        h = self.historico
        if self.NUMERO_INFO[h[-1]]['duzia'] == self.NUMERO_INFO[h[-2]]['duzia'] and self.NUMERO_INFO[h[-1]]['duzia'] != 0:
            duzia_alvo = self.NUMERO_INFO[h[-3]]['duzia']
            if duzia_alvo != 0:
                return {
                    "diagnostico": f"**Gatilho de Dúzia (A, B, B)!** Padrão {self.NUMERO_INFO[h[-3]]['duzia']}ª, {self.NUMERO_INFO[h[-2]]['duzia']}ª, {self.NUMERO_INFO[h[-1]]['duzia']}ª detectado.",
                    "estrategia": f"Apostar na Dúzia de retorno: **{duzia_alvo}ª Dúzia**.",
                    "numeros_recomendados": self.DEZENAS_MAPEADAS[duzia_alvo]
                }
        
        # Análises que dependem de uma maré ativa
        if mare_ativa:
            # Sequências numéricas (7, 8 -> 9 ou 6)
            if self.historico[-2] == self.historico[-1] - 1:
                num_crescente = self.historico[-1] + 1
                num_decrescente = self.historico[-2] - 1
                return {
                    "diagnostico": f"**Gatilho de Sequência!** Padrão {self.historico[-2]}, {self.historico[-1]} detectado.",
                    "estrategia": f"Apostar na continuação da sequência (região do {num_crescente}) ou na inversão para a quebra (região do {num_decrescente}).",
                    "numeros_recomendados": sorted(list(set(list(self.VIZINHOS_MAPEADOS[num_crescente].values()) + list(self.VIZINHOS_MAPEADOS[num_decrescente].values()))))
                }

        return None
    
    # --- MÉTODO DE ANÁLISE PRINCIPAL (ORQUESTRADOR) ---
    def analisar(self):
        if len(self.historico) < 3:
            return {"diagnostico": "Aguardando mais números...", "estrategia": "Insira pelo menos 3 números para iniciar a análise."}

        # 1. (PRIORIDADE MÁXIMA) Gerenciar o ciclo de vida: Estamos em Quebra ou Retorno?
        resultado_ciclo = self._gerenciar_ciclo_vida()
        if resultado_ciclo:
            return resultado_ciclo

        # 2. Analisar Ondas (Gatilhos rápidos e independentes)
        mare_atual = self._identificar_mares()
        resultado_ondas = self._analisar_ondas(mare_atual)
        if resultado_ondas:
            return resultado_ondas

        # 3. Analisar a Maré principal e seus refinamentos
        self.tendencia_atual = mare_atual
        if self.tendencia_atual:
            tipo = self.tendencia_atual['tipo']
            valor = self.tendencia_atual['valor']
            contagem = self.tendencia_atual['contagem']
            
            # LÓGICA DE SATURAÇÃO: A tendência está se repetindo demais?
            if contagem >= 6:
                diagnostico = f"**ALERTA DE SATURAÇÃO!** O {tipo} {valor} já apareceu {contagem} vezes recentemente."
                estrategia = f"**Apostar na QUEBRA.** A tendência está saturada e pode quebrar a qualquer momento. Focar em regiões opostas ao {tipo} {valor}."
                return {"diagnostico": diagnostico, "estrategia": estrategia}

            # LÓGICA DE TERMINAL/DEZENA FALTANTE (PRECISÃO)
            if 'numeros_ja_vistos' in self.tendencia_atual:
                todos_numeros_da_tendencia = set(self.TERMINAIS_MAPEADOS[valor] if tipo == 'TERMINAL' else [n for n,i in self.NUMERO_INFO.items() if i['dezena'] == valor])
                numeros_faltantes = todos_numeros_da_tendencia - self.tendencia_atual['numeros_ja_vistos']
                if 0 < len(numeros_faltantes) < len(todos_numeros_da_tendencia):
                     diagnostico = f"**Tendência de Precisão!** Manipulação do {tipo} {valor} ativa."
                     estrategia = f"Focar nos números **faltantes** da tendência: **{', '.join(map(str, sorted(list(numeros_faltantes))))}**."
                     return {"diagnostico": diagnostico, "estrategia": estrategia, "numeros_recomendados": sorted(list(numeros_faltantes))}

            # Análise padrão da Maré
            diagnostico = f"**Tendência Identificada:** Manipulação do {tipo} {valor}."
            estrategia = f"**Seguir a tendência.** Apostar nos números e regiões do {tipo} {valor}."
            numeros_rec = self.REGIOES_TERMINAIS[valor] if tipo == 'TERMINAL' else [n for n, info in self.NUMERO_INFO.items() if info['dezena'] == valor]
            return {"diagnostico": diagnostico, "estrategia": estrategia, "numeros_recomendados": numeros_rec}

        # 4. Se nada foi encontrado
        return {"diagnostico": "Nenhum padrão claro identificado.", "estrategia": "Aguardar a formação de uma tendência ou um gatilho."}

# --- INTERFACE DO APLICATIVO (STREAMLIT) ---

st.set_page_config(layout="wide", page_title="Roleta Mestre")

st.title("Roleta Mestre 🎲")
st.markdown("Analisador de estratégias e manipulações em tempo real. Desenvolvido com base nas aulas do Lê da Roleta.")

if 'analista' not in st.session_state:
    st.session_state.analista = RoletaMestre()

st.header("Clique no número sorteado para adicionar ao histórico:")

# Tabela de Roleta Interativa
col_zero, col_table = st.columns([1, 12])
if col_zero.button("0", key="num_0", use_container_width=True):
    st.session_state.analista.adicionar_numero(0)
    st.rerun()

with col_table:
    numeros = [[3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
               [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
               [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]]
    cols = st.columns(12)
    for i in range(12):
        for j in range(3):
            num = numeros[j][i]
            if cols[i].button(f"{num}", key=f"num_{num}", use_container_width=True):
                st.session_state.analista.adicionar_numero(num)
                st.rerun()

st.divider()

st.header("Painel de Análise")

# Obter e exibir histórico
historico_atual = st.session_state.analista.historico
if historico_atual:
    st.metric("Último Número Adicionado", historico_atual[-1])
historico_str = ", ".join(map(str, historico_atual))
st.write(f"**Histórico Analisado ({len(historico_atual)}/20):** `{historico_str or 'Vazio'}`")

# Realizar e exibir análise
resultado_analise = st.session_state.analista.analisar()
if resultado_analise:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Diagnóstico:")
        st.info(resultado_analise.get('diagnostico', ''))
    with col2:
        st.subheader("Estratégia Recomendada:")
        st.success(resultado_analise.get('estrategia', ''))
        
        numeros_rec = resultado_analise.get('numeros_recomendados')
        if numeros_rec:
            with st.expander(f"Ver os {len(numeros_rec)} números recomendados"):
                numeros_formatados = ' - '.join(map(str, numeros_rec))
                st.code(numeros_formatados, language=None)

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Controles")
    if st.button("Limpar Histórico e Reiniciar"):
        st.session_state.analista = RoletaMestre()
        st.rerun()

    st.markdown("---")
    st.subheader("Lembre-se:")
    st.warning("Este é um analisador de padrões e não garante vitórias. Jogue com responsabilidade. Nenhuma estratégia é 100% infalível.")