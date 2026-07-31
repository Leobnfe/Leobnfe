import os
import requests

USERNAME = "Leobnfe"
TOKEN = os.getenv("GH_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"}

def obter_dados_linguagens():
    url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100"
    response = requests.get(url, headers=HEADERS)
    repos = response.json()
    
    linguagens = {}
    for repo in repos:
        # Pula repositórios que você apenas clonou de outras pessoas
        if repo.get('fork'):
            continue
            
        lang_url = repo.get('languages_url')
        if not lang_url:
            continue
            
        lang_res = requests.get(lang_url, headers=HEADERS).json()
        
        for lang, bytes_count in lang_res.items():
            # Aqui está a regra que banimenta o Jupyter e foca no seu front-end
            if lang == "Jupyter Notebook":
                continue
            linguagens[lang] = linguagens.get(lang, 0) + bytes_count
            
    return linguagens

def gerar_svg(linguagens):
    total_bytes = sum(linguagens.values())
    
    # Pega as 4 linguagens mais usadas
    top_langs = sorted(linguagens.items(), key=lambda x: x[1], reverse=True)[:4]
    
    # Cores inspiradas no tema Tokyo Night para manter a identidade do seu perfil
    cores = {"HTML": "#E34F26", "CSS": "#1572B6", "JavaScript": "#F7DF1E", "Python": "#3776AB"}
    
    # Desenhando o componente com estilo puro
    svg = '''<svg width="320" height="230" viewBox="0 0 320 230" xmlns="http://www.w3.org/2000/svg">
    <style>
        .bg { fill: #1a1b26; rx: 10px; }
        .title { font: bold 16px 'Segoe UI', Arial, sans-serif; fill: #c0caf5; }
        .text { font: 13px 'Segoe UI', Arial, sans-serif; fill: #a9b1d6; }
        .bar-bg { fill: #24283b; rx: 5px; }
    </style>
    <rect width="100%" height="100%" class="bg"/>
    <text x="25" y="35" class="title">Linguagens e Tecnologias</text>
    '''
    
    y_pos = 70
    for lang, bytes_count in top_langs:
        porcentagem = (bytes_count / total_bytes) * 100
        cor = cores.get(lang, "#7aa2f7") 
        
        svg += f'''
        <text x="25" y="{y_pos}" class="text">{lang}</text>
        <text x="260" y="{y_pos}" class="text">{porcentagem:.1f}%</text>
        <rect x="25" y="{y_pos + 10}" width="270" height="10" class="bar-bg"/>
        <rect x="25" y="{y_pos + 10}" width="{2.7 * porcentagem}" height="10" fill="{cor}" rx="5"/>
        '''
        y_pos += 45
        
    svg += '</svg>'
    
    # Salva o arquivo final
    with open("estatisticas.svg", "w") as f:
        f.write(svg)

if __name__ == "__main__":
    dados = obter_dados_linguagens()
    if dados:
        gerar_svg(dados)
