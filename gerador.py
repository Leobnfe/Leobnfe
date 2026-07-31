import os
import requests
import math

USERNAME = "Leobnfe"
TOKEN = os.getenv("GH_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"}

def obter_dados_linguagens():
    url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100"
    response = requests.get(url, headers=HEADERS)
    repos = response.json()
    
    linguagens = {}
    for repo in repos:
        if repo.get('fork'):
            continue
            
        lang_url = repo.get('languages_url')
        if not lang_url:
            continue
            
        lang_res = requests.get(lang_url, headers=HEADERS).json()
        
        for lang, bytes_count in lang_res.items():
            if lang == "Jupyter Notebook":
                continue
            linguagens[lang] = linguagens.get(lang, 0) + bytes_count
            
    return linguagens

def gerar_svg(linguagens):
    total_bytes = sum(linguagens.values())
    
    # Mantendo o Top 5 para encaixar bem no layout lateral
    top_langs = sorted(linguagens.items(), key=lambda x: x[1], reverse=True)[:5]
    
    cores = {"HTML": "#E34F26", "CSS": "#1572B6", "JavaScript": "#F7DF1E"}
    
    # SVG mais largo (700x250) para caber tudo lado a lado
    svg = '''<svg width="700" height="250" viewBox="0 0 700 250" xmlns="http://www.w3.org/2000/svg">
    <style>
        .bg { fill: #1a1b26; rx: 10px; }
        .title { font: bold 18px 'Segoe UI', Arial, sans-serif; fill: #c0caf5; }
        .text { font: 14px 'Segoe UI', Arial, sans-serif; fill: #a9b1d6; }
        .bar-bg { fill: #24283b; rx: 5px; }
        /* Rotaciona o gráfico de pizza para a primeira fatia começar do topo */
        .chart { transform: rotate(-90deg); transform-origin: 170px 140px; }
    </style>
    <rect width="100%" height="100%" class="bg"/>
    <text x="35" y="40" class="title">Linguagens e Tecnologias</text>
    '''
    
    # Matemática do gráfico de rosca
    raio = 65
    circunferencia = 2 * math.pi * raio
    
    svg += '<g class="chart">\n'
    offset_atual = 0
    y_pos = 60
    side_bars = ""
    
    for lang, bytes_count in top_langs:
        porcentagem = (bytes_count / total_bytes) * 100
        cor = cores.get(lang, "#7aa2f7")
        
        # 1. Desenhando a fatia circular (Donut Chart)
        tamanho_fatia = (porcentagem / 100) * circunferencia
        resto = circunferencia - tamanho_fatia
        dash_offset = -offset_atual
        
        svg += f'  <circle cx="170" cy="140" r="{raio}" fill="none" stroke="{cor}" stroke-width="35" stroke-dasharray="{tamanho_fatia} {resto}" stroke-dashoffset="{dash_offset}" />\n'
        
        offset_atual += tamanho_fatia
        
        # 2. Desenhando os textos e as barras retas na lateral direita
        side_bars += f'''
        <text x="350" y="{y_pos}" class="text">{lang}</text>
        <text x="630" y="{y_pos}" class="text">{porcentagem:.1f}%</text>
        <rect x="350" y="{y_pos + 10}" width="315" height="10" class="bar-bg"/>
        <rect x="350" y="{y_pos + 10}" width="{3.15 * porcentagem}" height="10" fill="{cor}" rx="5"/>
        '''
        y_pos += 38
        
    svg += '</g>\n'
    svg += side_bars
    svg += '</svg>'
    
    with open("estatisticas.svg", "w") as f:
        f.write(svg)

if __name__ == "__main__":
    dados = obter_dados_linguagens()
    if dados:
        gerar_svg(dados)
