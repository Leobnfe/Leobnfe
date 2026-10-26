
import colorsys
import hashlib
import math
import os
from pathlib import Path
from xml.sax.saxutils import escape

import requests


# ==========================================
# CONFIGURAÇÕES
# ==========================================

USERNAME = "Leobnfe"
TOKEN = os.getenv("GH_TOKEN")
OUTPUT = Path("estatisticas.svg")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


# ==========================================
# CORES DAS LINGUAGENS
# ==========================================

COLORS = {
    "HTML": "#FF6B35",
    "CSS": "#3B82F6",
    "JavaScript": "#FACC15",
    "Python": "#4ADE80",
    "TypeScript": "#8B5CF6",
    "C": "#94A3B8",
    "C++": "#F472B6",
    "C#": "#22C55E",
    "Java": "#FB923C",
    "Go": "#38BDF8",
    "Rust": "#C08457",
    "PHP": "#818CF8",
    "Ruby": "#F43F5E",
    "Kotlin": "#E879F9",
    "Swift": "#F97316",
    "Dart": "#06B6D4",
    "Shell": "#84CC16",
    "PowerShell": "#60A5FA",
    "SQL": "#F59E0B",
    "Lua": "#6366F1",
    "R": "#0EA5E9",
    "SCSS": "#EC4899",
    "Vue": "#10B981",
    "Svelte": "#F97316",
    "Dockerfile": "#64748B",
    "Jupyter Notebook": "#F97316",
    "Batchfile": "#A3A300",
}


# ==========================================
# CONSULTAR REPOSITÓRIOS DO GITHUB
# ==========================================

def obter_dados_linguagens():

    if not TOKEN:
        raise RuntimeError(
            "GH_TOKEN ausente. Confira o Secret no GitHub Actions."
        )

    totais = {}
    publicos = 0
    privados = 0

    url = "https://api.github.com/user/repos"

    params = {
        "visibility": "all",
        "affiliation": "owner",
        "per_page": 100,
    }

    with requests.Session() as session:

        session.headers.update(HEADERS)

        while url:

            resposta = session.get(
                url,
                params=params,
                timeout=30,
            )

            resposta.raise_for_status()
            repositorios = resposta.json()

            if not isinstance(repositorios, list):
                raise RuntimeError(
                    "Resposta inesperada ao listar os repositórios."
                )

            for repo in repositorios:

                if repo.get("fork"):
                    continue

                language_url = repo.get("languages_url")

                if not language_url:
                    continue

                resposta_linguagens = session.get(
                    language_url,
                    timeout=30,
                )

                resposta_linguagens.raise_for_status()
                linguagens_repo = resposta_linguagens.json()

                if not isinstance(linguagens_repo, dict):
                    raise RuntimeError(
                        "Resposta inesperada ao buscar linguagens."
                    )

                if repo.get("private"):
                    privados += 1
                else:
                    publicos += 1

                for linguagem, bytes_codigo in linguagens_repo.items():

                    if isinstance(bytes_codigo, int) and bytes_codigo > 0:

                        totais[linguagem] = (
                            totais.get(linguagem, 0) + bytes_codigo
                        )

            url = resposta.links.get("next", {}).get("url")
            params = None

    print(
        f"Repositórios analisados de {USERNAME}: "
        f"{publicos} públicos e {privados} privados (sem forks)."
    )

    return totais


# ==========================================
# DEFINIR CORES AUTOMÁTICAS
# ==========================================

def cor_linguagem(nome):

    if nome in COLORS:
        return COLORS[nome]

    digest = hashlib.sha256(
        nome.encode("utf-8")
    ).digest()

    hue = int.from_bytes(
        digest[:2], "big"
    ) / 65535

    saturation = 0.45 + (digest[2] / 255) * 0.20
    value = 0.75 + (digest[3] / 255) * 0.15

    rgb = colorsys.hsv_to_rgb(
        hue,
        saturation,
        value,
    )

    return "#" + "".join(
        f"{round(c * 255):02X}" for c in rgb
    )


# ==========================================
# FORMATAR PERCENTUAIS
# ==========================================

def percentual_formatado(valor):

    if valor < 0.01:
        return "&lt;0.01%"

    if valor < 1:
        return f"{valor:.2f}%"

    return f"{valor:.1f}%"


# ==========================================
# GERAR GRÁFICO SVG
# ==========================================

def gerar_svg(linguagens, arquivo=OUTPUT):

    itens = sorted(
        [
            (nome, qtd)
            for nome, qtd in linguagens.items()
            if isinstance(qtd, int) and qtd > 0
        ],
        key=lambda item: (
            -item[1],
            item[0].casefold()
        ),
    )

    if not itens:
        raise RuntimeError(
            "Nenhuma linguagem identificada; gráfico anterior preservado."
        )

    total = sum(qtd for _, qtd in itens)

    # Dimensões do card
    largura = 700

    colunas = (
        3 if max(len(nome) for nome, _ in itens) <= 19
        else 2
    )

    linhas = math.ceil(len(itens) / colunas)

    largura_coluna = 636 / colunas

    inicio_legenda = 128
    passo = 28

    altura = max(
        180,
        inicio_legenda + (linhas - 1) * passo + 30
    )

    # ======================================
    # ESTRUTURA VISUAL
    # ======================================

    partes = [f'''<svg xmlns="http://www.w3.org/2000/svg"
    width="{largura}"
    height="{altura}"
    viewBox="0 0 {largura} {altura}"
    role="img"
    aria-label="Estatísticas de linguagens do GitHub">

  <title>Distribuição de código por linguagem — {len(itens)} linguagens</title>

  <style>
    .title {{
      font: 700 20px 'Segoe UI', Arial, sans-serif;
      fill: #ffffff;
    }}

    .subtitle {{
      font: 12px 'Segoe UI', Arial, sans-serif;
      fill: #a1a1aa;
    }}

    .name {{
      font: 12px 'Segoe UI', Arial, sans-serif;
      fill: #f4f4f5;
    }}

    .pct {{
      font: 11px 'Segoe UI', Arial, sans-serif;
      fill: #a1a1aa;
    }}
  </style>

  <!-- Fundo do card -->
  <rect
    x="10"
    y="10"
    width="680"
    height="{altura - 20}"
    rx="14"
    fill="#0d1117"
    stroke="#30363d"
    stroke-width="1"
  />

  <!-- Título -->
  <text x="36" y="42" class="title">
    Análise do Repositório
  </text>

  <!-- Subtítulo -->
  <text x="36" y="62" class="subtitle">
    Percentual de código por linguagem · {len(itens)} linguagens
  </text>

  <!-- Barra arredondada -->
  <defs>
    <clipPath id="barra-arredondada">
      <rect
        x="36"
        y="82"
        width="608"
        height="14"
        rx="7"
      />
    </clipPath>
  </defs>

  <!-- Fundo da barra -->
  <rect
    x="36"
    y="82"
    width="608"
    height="14"
    rx="7"
    fill="#21262d"
  />

  <g clip-path="url(#barra-arredondada)">''']

    # ======================================
    # BARRA DE LINGUAGENS
    # ======================================

    largura_barra = 608.0
    inicio_barra = 36.0
    atual = inicio_barra

    # Linguagens com menos de 1% aparecem
    # na legenda, mas não na barra.
    itens_barra = [
        (nome, qtd)
        for nome, qtd in itens
        if (qtd / total * 100) >= 1
    ]

    # Caso todas estejam abaixo de 1%,
    # mantém todas as linguagens na barra.
    if not itens_barra:
        itens_barra = itens

    total_barra = sum(
        qtd for _, qtd in itens_barra
    )

    for idx, (nome, qtd) in enumerate(itens_barra):

        tamanho = largura_barra * qtd / total_barra

        # Última linguagem ocupa exatamente
        # o espaço restante da barra.
        if idx == len(itens_barra) - 1:
            tamanho = (
                inicio_barra + largura_barra
            ) - atual

        partes.append(
            f'  <rect '
            f'x="{atual:.5f}" '
            f'y="82" '
            f'width="{tamanho:.5f}" '
            f'height="14" '
            f'fill="{cor_linguagem(nome)}"/>'
        )

        atual += tamanho

    partes.append("  </g>")

    # ======================================
    # LEGENDA - TODAS AS LINGUAGENS
    # ======================================

    for i, (nome, qtd) in enumerate(itens):

        coluna = i % colunas
        linha = i // colunas

        x = 36 + largura_coluna * coluna
        y = inicio_legenda + passo * linha

        pct = qtd / total * 100

        nome_xml = escape(nome)

        partes.extend([
            (
                f'  <rect '
                f'x="{x:.2f}" '
                f'y="{y - 10:.2f}" '
                f'width="9" '
                f'height="9" '
                f'rx="2" '
                f'fill="{cor_linguagem(nome)}"/>'
            ),
            (
                f'  <text '
                f'x="{x + 16:.2f}" '
                f'y="{y:.2f}" '
                f'class="name">{nome_xml}</text>'
            ),
            (
                f'  <text '
                f'x="{x + largura_coluna - 12:.2f}" '
                f'y="{y:.2f}" '
                f'text-anchor="end" '
                f'class="pct">{percentual_formatado(pct)}</text>'
            ),
        ])

    # ======================================
    # FINALIZAR SVG
    # ======================================

    partes.append("</svg>")

    caminho = Path(arquivo)

    caminho.write_text(
        "\n".join(partes),
        encoding="utf-8",
    )

    print(
        f"Linguagens exibidas: {len(itens)} (todas). "
        f"SVG: {largura}x{altura}px."
    )

    print("Gráfico SVG gerado com sucesso!")


# ==========================================
# EXECUÇÃO PRINCIPAL
# ==========================================

if __name__ == "__main__":

    dados = obter_dados_linguagens()

    gerar_svg(dados)
