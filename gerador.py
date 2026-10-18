import colorsys
import hashlib
import math
import os
from pathlib import Path
from xml.sax.saxutils import escape

import requests

USERNAME = "Leobnfe"
TOKEN = os.getenv("GH_TOKEN")
OUTPUT = Path("estatisticas.svg")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

COLORS = {
    "HTML": "#E34F26", "CSS": "#1572B6", "JavaScript": "#F7DF1E",
    "Python": "#4CC38A", "TypeScript": "#A78BFA", "C": "#A8B9CC",
    "C++": "#F34B7D", "C#": "#178600", "Java": "#B07219",
    "Go": "#00ADD8", "Rust": "#DEA584", "PHP": "#4F5D95",
    "Ruby": "#CC342D", "Kotlin": "#E879F9", "Swift": "#F05138",
    "Dart": "#00B4AB", "Shell": "#89E051", "PowerShell": "#5391FE",
    "SQL": "#E38C00", "Lua": "#000080", "R": "#198CE7",
    "SCSS": "#C6538C", "Vue": "#41B883", "Svelte": "#FF3E00",
    "Dockerfile": "#384D54", "Jupyter Notebook": "#DA5B0B",
}


def obter_dados_linguagens():
    
    if not TOKEN:
        raise RuntimeError("GH_TOKEN ausente. Confira o Secret no GitHub Actions.")

    totais = {}
    publicos = privados = 0
    url = "https://api.github.com/user/repos"
    params = {"visibility": "all", "affiliation": "owner", "per_page": 100}

    with requests.Session() as session:
        session.headers.update(HEADERS)
        while url:
            resposta = session.get(url, params=params, timeout=30)
            resposta.raise_for_status()
            repositorios = resposta.json()
            if not isinstance(repositorios, list):
                raise RuntimeError("Resposta inesperada ao listar os repositórios.")

            for repo in repositorios:
                if repo.get("fork"):
                    continue
                language_url = repo.get("languages_url")
                if not language_url:
                    continue

                resposta_linguagens = session.get(language_url, timeout=30)
                resposta_linguagens.raise_for_status()
                linguagens_repo = resposta_linguagens.json()
                if not isinstance(linguagens_repo, dict):
                    raise RuntimeError("Resposta inesperada ao buscar linguagens.")

                if repo.get("private"):
                    privados += 1
                else:
                    publicos += 1

                for linguagem, bytes_codigo in linguagens_repo.items():
                    if isinstance(bytes_codigo, int) and bytes_codigo > 0:
                        totais[linguagem] = totais.get(linguagem, 0) + bytes_codigo

            url = resposta.links.get("next", {}).get("url")
            params = None

    print(f"Repositórios analisados de {USERNAME}: "
          f"{publicos} públicos e {privados} privados (sem forks).")
    return totais


def cor_linguagem(nome):
    
    if nome in COLORS:
        return COLORS[nome]
    digest = hashlib.sha256(nome.encode("utf-8")).digest()
    hue = int.from_bytes(digest[:2], "big") / 65535
    saturation = 0.52 + (digest[2] / 255) * 0.25
    value = 0.80 + (digest[3] / 255) * 0.17
    rgb = colorsys.hsv_to_rgb(hue, saturation, value)
    return "#" + "".join(f"{round(c * 255):02X}" for c in rgb)


def percentual_formatado(valor):
    if valor < 0.01:
        return "&lt;0.01%"
    if valor < 1:
        return f"{valor:.2f}%"
    return f"{valor:.1f}%"


def gerar_svg(linguagens, arquivo=OUTPUT):
    
    itens = sorted(
        [(nome, qtd) for nome, qtd in linguagens.items() if isinstance(qtd, int) and qtd > 0],
        key=lambda item: (-item[1], item[0].casefold()),
    )
    if not itens:
        raise RuntimeError("Nenhuma linguagem identificada; gráfico anterior preservado.")

    total = sum(qtd for _, qtd in itens)
    largura = 700
    
    colunas = 3 if max(len(nome) for nome, _ in itens) <= 19 else 2
    linhas = math.ceil(len(itens) / colunas)
    largura_coluna = 636 / colunas
    inicio_legenda = 122
    passo = 26
    altura = max(170, inicio_legenda + (linhas - 1) * passo + 26)

    partes = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}"
    viewBox="0 0 {largura} {altura}" role="img" aria-label="Estatísticas de linguagens do GitHub">
  <title>Distribuição de código por linguagem — {len(itens)} linguagens</title>
  <style>
    .title {{ font: 600 17px 'Segoe UI', Arial, sans-serif; fill: #c0caf5; }}
    .subtitle {{ font: 12px 'Segoe UI', Arial, sans-serif; fill: #a9b1d6; }}
    .name {{ font: 12px 'Segoe UI', Arial, sans-serif; fill: #c0caf5; }}
    .pct {{ font: 11px 'Segoe UI', Arial, sans-serif; fill: #a9b1d6; }}
  </style>
  <rect width="700" height="{altura}" rx="12" fill="#1a1b26"/>
  <text x="32" y="35" class="title">Análise do Repositório</text>
  <text x="32" y="55" class="subtitle">Percentual de código por linguagem · {len(itens)} linguagens</text>
  <defs><clipPath id="barra-arredondada"><rect x="32" y="74" width="636" height="12" rx="6"/></clipPath></defs>
  <rect x="32" y="74" width="636" height="12" rx="6" fill="#24283b"/>
  <g clip-path="url(#barra-arredondada)">''']

    atual = 32.0
    for idx, (nome, qtd) in enumerate(itens):
        tamanho = 636 * qtd / total
        if idx == len(itens) - 1:
            tamanho = 668.0 - atual
        partes.append(f'    <rect x="{atual:.5f}" y="74" width="{tamanho:.5f}" height="12" fill="{cor_linguagem(nome)}"/>')
        atual += tamanho
    partes.append("  </g>")

    for i, (nome, qtd) in enumerate(itens):
        coluna, linha = i % colunas, i // colunas
        x = 32 + largura_coluna * coluna
        y = inicio_legenda + passo * linha
        pct = qtd / total * 100
        nome_xml = escape(nome)
        partes.extend([
            f'  <rect x="{x:.2f}" y="{y - 9:.2f}" width="8" height="8" rx="2" fill="{cor_linguagem(nome)}"/>',
            f'  <text x="{x + 16:.2f}" y="{y:.2f}" class="name">{nome_xml}</text>',
            f'  <text x="{x + largura_coluna - 10:.2f}" y="{y:.2f}" text-anchor="end" class="pct">{percentual_formatado(pct)}</text>',
        ])

    partes.append("</svg>")
    caminho = Path(arquivo)
    caminho.write_text("\n".join(partes), encoding="utf-8")
    print(f"Linguagens exibidas: {len(itens)} (todas). SVG: {largura}x{altura}px.")


if __name__ == "__main__":
    dados = obter_dados_linguagens()
    gerar_svg(dados)
