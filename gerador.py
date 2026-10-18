import math
import os
import requests

USERNAME = "Leobnfe"
TOKEN = os.getenv("GH_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def obter_dados_linguagens():
    if not TOKEN:
        raise RuntimeError(
            "GH_TOKEN ausente. Configure um token com acesso aos repositórios no GitHub Actions."
        )

    url = "https://api.github.com/user/repos"
    params = {"visibility": "all", "affiliation": "owner", "per_page": 100}
    linguagens = {}
    publicos = 0
    privados = 0

    while url:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        repos = response.json()
        if not isinstance(repos, list):
            raise RuntimeError("A API não retornou uma lista de repositórios.")

        for repo in repos:
            if repo.get("fork"):
                continue
            lang_url = repo.get("languages_url")
            if not lang_url:
                continue

            lang_response = requests.get(lang_url, headers=HEADERS, timeout=30)
            lang_response.raise_for_status()
            dados_repo = lang_response.json()
            if not isinstance(dados_repo, dict):
                raise RuntimeError("A API não retornou as linguagens esperadas.")

            if repo.get("private"):
                privados += 1
            else:
                publicos += 1

            for lang, bytes_count in dados_repo.items():
                if lang == "Jupyter Notebook":
                    continue
                if isinstance(bytes_count, int) and bytes_count > 0:
                    linguagens[lang] = linguagens.get(lang, 0) + bytes_count

       
        url = response.links.get("next", {}).get("url")
        params = None

    print(
        f"Repositórios analisados de {USERNAME}: "
        f"{publicos} públicos e {privados} privados (sem forks)."
    )
    return linguagens


def gerar_svg(linguagens):
    total_bytes = sum(linguagens.values())
    if total_bytes <= 0:
        raise RuntimeError("Nenhuma linguagem encontrada; gráfico anterior preservado.")

    top_langs = sorted(linguagens.items(), key=lambda x: x[1], reverse=True)[:5]
    cores = {
        "HTML": "#E34F26",
        "CSS": "#1572B6",
        "JavaScript": "#F7DF1E",
        "Python": "#306998",
        "TypeScript": "#3178C6",
        "C": "#A8B9CC",
        "C++": "#F34B7D",
        "Java": "#B07219",
        "Go": "#00ADD8",
        "Rust": "#DEA584",
    }

    svg = '''<svg width="700" height="280" viewBox="0 0 700 280" xmlns="http://www.w3.org/2000/svg">
    <style>
        .bg { fill: #1a1b26; rx: 10px; }
        .title { font: bold 18px 'Segoe UI', Arial, sans-serif; fill: #c0caf5; }
        .subtitle { font: 14px 'Segoe UI', Arial, sans-serif; fill: #a9b1d6; }
        .text { font: 14px 'Segoe UI', Arial, sans-serif; fill: #a9b1d6; }
        .bar-bg { fill: #24283b; rx: 5px; }
        .chart { transform: rotate(-90deg); transform-origin: 530px 150px; }
    </style>
    <rect width="100%" height="100%" class="bg"/>
    <text x="35" y="40" class="title">Análise do Repositório</text>
    <text x="35" y="60" class="subtitle">Percentual de código por linguagem.</text>
    '''

    raio = 65
    circunferencia = 2 * math.pi * raio
    svg += '<g class="chart">\n'
    offset_atual = 0
    y_pos = 100
    side_bars = ""

    for lang, bytes_count in top_langs:
        porcentagem = (bytes_count / total_bytes) * 100
        cor = cores.get(lang, "#7aa2f7")
        tamanho_fatia = (porcentagem / 100) * circunferencia
        resto = circunferencia - tamanho_fatia
        dash_offset = -offset_atual

        svg += (
            f'  <circle cx="530" cy="150" r="{raio}" fill="none" '
            f'stroke="{cor}" stroke-width="35" '
            f'stroke-dasharray="{tamanho_fatia} {resto}" '
            f'stroke-dashoffset="{dash_offset}" />\n'
        )
        offset_atual += tamanho_fatia

        side_bars += f'''
        <text x="35" y="{y_pos}" class="text">{lang}</text>
        <text x="315" y="{y_pos}" class="text">{porcentagem:.1f}%</text>
        <rect x="35" y="{y_pos + 10}" width="315" height="10" class="bar-bg"/>
        <rect x="35" y="{y_pos + 10}" width="{3.15 * porcentagem}" height="10" fill="{cor}" rx="5"/>
        '''
        y_pos += 38

    svg += '</g>\n'
    svg += side_bars
    svg += '</svg>'

    with open("estatisticas.svg", "w", encoding="utf-8") as f:
        f.write(svg)


if __name__ == "__main__":
    dados = obter_dados_linguagens()
    if dados:
        gerar_svg(dados)
    else:
        raise RuntimeError("Nenhum código identificado; gráfico anterior preservado.")
