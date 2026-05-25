from __future__ import annotations

import io
import os
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import streamlit as st


# ============================================================
# Configuração geral
# ============================================================

REQUIRED_INPUT_COLUMNS = ["docs", "simple_doc"]

MODULES = {
    "1 — Revisor Linguístico": {
        "prefix": "linguistic",
        "disabled_questions": [5],
        "description": "Avaliação linguística: simplicidade, léxico, estrutura, fluência e qualidade textual.",
    },
    "2 — Revisor Técnico": {
        "prefix": "technical",
        "disabled_questions": [2, 3, 4],
        "description": "Avaliação técnica: qualidade geral da simplificação e preservação do significado principal.",
    },
}

QUESTIONS = {
    1: (
        "O texto simplificado é mais simples que o texto original, sob a condição de garantia "
        "de qualidade? Ou seja, ele também deve ser fluido na leitura e preservar o significado "
        "principal do texto original."
    ),
    2: (
        "Qual é o grau de simplificação lexical, ou seja, o quanto as palavras originais foram "
        "substituídas por termos mais simples?"
    ),
    3: (
        "Qual é o grau de simplificação estrutural, ou seja, o quanto a organização e a complexidade "
        "sintática das sentenças foram reduzidas?"
    ),
    4: (
        "O texto simplificado é gramaticalmente correto e fluente, garantindo que as sentenças sejam "
        "naturais e bem formadas?"
    ),
    5: (
        "O documento simplificado preservou o significado principal do texto original? Fatores que "
        "podem impactar nessa métrica são a remoção de conteúdo indispensável ou a inserção de "
        "informações novas não contidas no documento original e que não são de senso comum."
    ),
}


@dataclass
class LoadedData:
    df: pd.DataFrame
    path: Optional[str] = None
    filename: str = "respostas.parquet"


# ============================================================
# Funções utilitárias
# ============================================================

def safe_str(value) -> str:
    if pd.isna(value):
        return ""
    return str(value)


def validate_input_df(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_INPUT_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "O arquivo parquet precisa conter as colunas: "
            + ", ".join(REQUIRED_INPUT_COLUMNS)
            + f". Colunas ausentes: {', '.join(missing)}"
        )


def answer_columns(prefix: str) -> list[str]:
    return [f"{prefix}_q{i}" for i in range(1, 6)]


def all_answer_columns() -> list[str]:
    return answer_columns("linguistic") + answer_columns("technical")


def ensure_answer_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "record_id" not in df.columns:
        df.insert(0, "record_id", range(len(df)))

    for col in all_answer_columns():
        if col not in df.columns:
            df[col] = pd.NA

    return df


def read_parquet_from_path(path: str) -> LoadedData:
    df = pd.read_parquet(path)
    validate_input_df(df)
    df = ensure_answer_columns(df)
    return LoadedData(
        df=df,
        path=path,
        filename=os.path.basename(path).replace(".parquet", "_respostas.parquet"),
    )


def read_parquet_from_upload(uploaded_file) -> LoadedData:
    df = pd.read_parquet(uploaded_file)
    validate_input_df(df)
    df = ensure_answer_columns(df)
    original_name = getattr(uploaded_file, "name", "respostas.parquet")
    filename = original_name.replace(".parquet", "_respostas.parquet")
    return LoadedData(df=df, path=None, filename=filename)


def export_df(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["record_id", "docs", "simple_doc"] + all_answer_columns()
    available = [c for c in cols if c in df.columns]
    out = df[available].copy()

    # Garante que perguntas desabilitadas fiquem em branco no export final,
    # mesmo que alguma coluna tenha sido preenchida por engano.
    out["linguistic_q5"] = pd.NA
    out["technical_q2"] = pd.NA
    out["technical_q3"] = pd.NA
    out["technical_q4"] = pd.NA

    return out


def parquet_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    export_df(df).to_parquet(output, index=False)
    return output.getvalue()


def current_module_config() -> dict:
    return MODULES[st.session_state.active_module]


def current_index() -> int:
    return int(st.session_state.row_i)


def current_row() -> pd.Series:
    return st.session_state.loaded.df.iloc[current_index()]


def get_answer_value(row: pd.Series, col: str):
    value = row.get(col, pd.NA)
    if pd.isna(value):
        return None
    try:
        value = int(value)
    except Exception:
        return None
    if value < 1 or value > 5:
        return None
    return value


def save_current_answers(values: dict[int, Optional[int]]) -> None:
    ld: LoadedData = st.session_state.loaded
    prefix = current_module_config()["prefix"]
    row_i = current_index()

    for q_num, value in values.items():
        col = f"{prefix}_q{q_num}"
        if value is None:
            ld.df.at[row_i, col] = pd.NA
        else:
            ld.df.at[row_i, col] = int(value)


def answered_count_for_module(df: pd.DataFrame, prefix: str, enabled_questions: list[int]) -> int:
    cols = [f"{prefix}_q{i}" for i in enabled_questions]
    if not cols:
        return 0
    return int(df[cols].notna().all(axis=1).sum())


def module_enabled_questions(module_name: str) -> list[int]:
    disabled = set(MODULES[module_name]["disabled_questions"])
    return [i for i in range(1, 6) if i not in disabled]


# ============================================================
# Estado
# ============================================================

def init_state() -> None:
    if "screen" not in st.session_state:
        st.session_state.screen = "home"

    if "module_select" not in st.session_state:
        st.session_state.module_select = "1 — Revisor Linguístico"

    if "active_module" not in st.session_state:
        st.session_state.active_module = "1 — Revisor Linguístico"

    if "loaded" not in st.session_state:
        st.session_state.loaded = None

    if "row_i" not in st.session_state:
        st.session_state.row_i = 0


# ============================================================
# Componentes de interface
# ============================================================

def render_top_bar() -> None:
    ld: LoadedData = st.session_state.loaded

    st.markdown("### Avaliador de Textos Simplificados")

    col1, col2, col3, col4 = st.columns([2.2, 1.8, 1.2, 1.8])

    with col1:
        st.caption("Arquivo")
        if ld.path:
            st.code(ld.path, language="text")
        else:
            st.code(ld.filename, language="text")

    with col2:
        st.caption("Módulo ativo")
        st.info(st.session_state.active_module)

    with col3:
        st.caption("Início")
        if st.button("🏠 Trocar módulo/arquivo", use_container_width=True):
            st.session_state.module_select = st.session_state.active_module
            st.session_state.screen = "home"
            st.rerun()

    with col4:
        st.caption("Exportar respostas")
        st.download_button(
            "⬇️ Baixar respostas",
            data=parquet_bytes(ld.df),
            file_name=ld.filename,
            mime="application/octet-stream",
            use_container_width=True,
        )


def render_navigation() -> None:
    ld: LoadedData = st.session_state.loaded
    n = len(ld.df)
    i = current_index()

    st.progress((i + 1) / max(n, 1), text=f"Registro {i + 1} de {n}")

    col1, col2, col3, col4 = st.columns([1, 1, 1.2, 2])

    with col1:
        if st.button("◀ Anterior", disabled=i == 0, use_container_width=True):
            st.session_state.row_i -= 1
            st.rerun()

    with col2:
        if st.button("Próximo ▶", disabled=i >= n - 1, use_container_width=True):
            st.session_state.row_i += 1
            st.rerun()

    with col3:
        jump = st.number_input(
            "Ir para",
            min_value=1,
            max_value=max(n, 1),
            value=i + 1,
            step=1,
            label_visibility="collapsed",
        )
        if int(jump) != i + 1:
            st.session_state.row_i = int(jump) - 1
            st.rerun()

    with col4:
        prefix = current_module_config()["prefix"]
        enabled = module_enabled_questions(st.session_state.active_module)
        done = answered_count_for_module(ld.df, prefix, enabled)
        st.caption(f"Respondidos neste módulo: {done}/{n}")


def render_texts() -> None:
    row = current_row()

    st.subheader("Textos")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Documento original")
        st.text_area(
            "Documento original",
            value=safe_str(row["docs"]),
            height=420,
            disabled=True,
            label_visibility="collapsed",
            key=f"docs_{current_index()}",
        )

    with col2:
        st.markdown("#### Documento simplificado")
        st.text_area(
            "Documento simplificado",
            value=safe_str(row["simple_doc"]),
            height=420,
            disabled=True,
            label_visibility="collapsed",
            key=f"simple_doc_{current_index()}",
        )


def render_questions() -> None:
    st.subheader("Avaliação")

    cfg = current_module_config()
    prefix = cfg["prefix"]
    disabled_questions = set(cfg["disabled_questions"])
    row = current_row()

    st.caption(
        "Notas de 1 a 5. Perguntas desabilitadas aparecerão em branco no arquivo exportado."
    )

    values: dict[int, Optional[int]] = {}

    for q_num, question in QUESTIONS.items():
        col_name = f"{prefix}_q{q_num}"
        disabled = q_num in disabled_questions
        previous_value = get_answer_value(row, col_name)

        st.markdown(f"**P{q_num}.** {question}")

        key = f"{prefix}_q{q_num}_row_{current_index()}"

        if disabled:
            st.radio(
                f"Resposta P{q_num}",
                options=[1, 2, 3, 4, 5],
                index=None,
                horizontal=True,
                disabled=True,
                key=key,
                label_visibility="collapsed",
            )
            values[q_num] = None
            st.caption("Pergunta desabilitada neste módulo.")
        else:
            options = [1, 2, 3, 4, 5]
            index = options.index(previous_value) if previous_value in options else None

            selected = st.radio(
                f"Resposta P{q_num}",
                options=options,
                index=index,
                horizontal=True,
                key=key,
                label_visibility="collapsed",
            )
            values[q_num] = selected

        st.divider()

    col1, col2 = st.columns([1.2, 2])

    with col1:
        if st.button("💾 Salvar respostas", use_container_width=True):
            save_current_answers(values)
            st.toast("Respostas salvas.", icon="💾")
            st.rerun()

    with col2:
        if st.button("💾 Salvar e ir para o próximo", use_container_width=True):
            save_current_answers(values)
            if current_index() < len(st.session_state.loaded.df) - 1:
                st.session_state.row_i += 1
            st.toast("Respostas salvas.", icon="💾")
            st.rerun()


# ============================================================
# Telas
# ============================================================

def home_screen() -> None:
    st.title("Avaliador de Textos Simplificados")
    st.write(
        "Carregue um arquivo `.parquet` contendo as colunas `docs` e `simple_doc`, "
        "e escolha o módulo de avaliação."
    )

    st.selectbox(
        "Escolha o módulo",
        options=list(MODULES.keys()),
        key="module_select",
    )

    st.info(MODULES[st.session_state.module_select]["description"])

    st.divider()

    tab1, tab2 = st.tabs(["📁 Caminho local", "☁️ Upload do parquet"])

    loaded = None

    with tab1:
        st.write("Use esta opção quando estiver rodando o app no seu computador.")
        path = st.text_input(
            "Caminho para o arquivo parquet",
            placeholder="/caminho/para/arquivo.parquet",
        )

        if st.button("Carregar do caminho local", disabled=not bool(path.strip())):
            try:
                loaded = read_parquet_from_path(path.strip())
            except Exception as exc:
                st.error(f"Erro ao carregar o parquet: {exc}")

    with tab2:
        st.write("Use esta opção no deploy online.")
        uploaded_file = st.file_uploader("Arquivo parquet", type=["parquet"])

        if st.button("Carregar upload", disabled=uploaded_file is None):
            try:
                loaded = read_parquet_from_upload(uploaded_file)
            except Exception as exc:
                st.error(f"Erro ao carregar o parquet: {exc}")

    if loaded is not None:
        st.session_state.loaded = loaded
        st.session_state.active_module = st.session_state.module_select
        st.session_state.row_i = 0
        st.session_state.screen = "work"
        st.success("Arquivo carregado com sucesso.")
        st.rerun()


def work_screen() -> None:
    if st.session_state.loaded is None:
        st.session_state.screen = "home"
        st.rerun()

    render_top_bar()
    render_navigation()
    st.divider()
    render_texts()
    st.divider()
    render_questions()


# ============================================================
# Main
# ============================================================

def main() -> None:
    st.set_page_config(
        page_title="Avaliador de Textos Simplificados",
        layout="wide",
    )
    init_state()

    if st.session_state.screen == "home":
        home_screen()
    else:
        work_screen()


if __name__ == "__main__":
    main()
