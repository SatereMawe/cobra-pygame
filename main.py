import os
import random
import sys

import numpy as np
import pygame

# --- Configuracoes ---
LARGURA = 600
ALTURA = 400
TAMANHO_BLOCO = 20
FPS_INICIAL = 10
FPS_MAXIMO = 25
PONTOS_POR_NIVEL = 50
ARQUIVO_RECORDE = "recorde.txt"  # arquivo onde o recorde é salvo

# -- Cores --
PRETO = (0, 0, 0)
CINZA_GRID = (30, 30, 30)
VERDE = (0, 200, 0)
VERDE_CLARO = (0, 255, 0)
VERMELHO = (200, 0, 0)
BRANCO = (255, 255, 255)
VERDE_ESCURO = (0, 150, 0)
ROSA = (255, 105, 180)
CINZA = (100, 100, 100)
AMARELO = (255, 215, 0)
PRETO_ALPHA = (0, 0, 0, 160)


# -- Inicialização --
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Snake 🐍")
clock = pygame.time.Clock()

fonte_titulo = pygame.font.SysFont("monospace", 52, bold=True)
fonte_pontos = pygame.font.SysFont("monospace", 24, bold=True)
fonte_gameover = pygame.font.SysFont("monospace", 48, bold=True)
fonte_pausa = pygame.font.SysFont("monospace", 42, bold=True)
fonte_sub = pygame.font.SysFont("monospace", 22)
fonte_pequena = pygame.font.SysFont("monospace", 18)

# NOVO: Geração de sons via numpy


# ── Sons ──
def gerar_som(frequencia, duracao, volume=0.3):
    taxa = 44100
    amostras = int(taxa * duracao)
    t = np.linspace(0, duracao, amostras, False)
    onda = np.sin(2 * np.pi * frequencia * t)
    onda = (onda * volume * 32767).astype(np.int16)
    onda_stereo = np.column_stack((onda, onda))
    return pygame.sndarray.make_sound(onda_stereo)


som_comer = gerar_som(523, 0.08)
som_game_over = gerar_som(150, 0.5)
som_recorde = gerar_som(880, 0.3)
som_pausa = gerar_som(330, 0.08)


# Funções de recorde em arquivo
def carregar_recorde():
    if not os.path.exists(ARQUIVO_RECORDE):
        return 0
    try:
        with open(ARQUIVO_RECORDE, "r") as f:
            return int(f.read().strip())
    except:
        return 0  # se der qualquer erro, começa do zero


# Salva o recorde no arquivo
def salvar_recorde(recorde):
    with open(ARQUIVO_RECORDE, "w") as f:
        f.write(str(recorde))


# ── Cobra ──
cobra = [(300, 200), (280, 200), (260, 200)]
direcao = (TAMANHO_BLOCO, 0)  # começa indo para a direita (x+20, y+0)


# ── Gerar comida ──
def gerar_comida(cobra):
    colunas = LARGURA // TAMANHO_BLOCO
    linhas = ALTURA // TAMANHO_BLOCO
    while True:
        x = random.randint(0, colunas - 1) * TAMANHO_BLOCO
        y = random.randint(0, linhas - 1) * TAMANHO_BLOCO
        if (x, y) not in cobra:
            return (x, y)


# ── Grade ──
def desenha_grade():
    for x in range(0, LARGURA, TAMANHO_BLOCO):
        pygame.draw.line(tela, CINZA_GRID, (x, 0), (x, ALTURA))
    for y in range(0, ALTURA, TAMANHO_BLOCO):
        pygame.draw.line(tela, CINZA_GRID, (0, y), (LARGURA, y))


#  Desenho estilizado da cobra──


def desenha_cabeca(x, y, direcao):
    """Desenha a cabeça da cobra com olhos e língua conforme a direção."""
    B = TAMANHO_BLOCO

    # Corpo da cabeça
    pygame.draw.rect(tela, VERDE_CLARO, (x, y, B, B))
    pygame.draw.rect(tela, PRETO, (x, y, B, B), 1)

    cx, cy = x + B // 2, y + B // 2  # centro do bloco

    # ── Olhos e língua mudam conforme a direção ──
    if direcao == (B, 0):  # direita →
        olho1 = (x + 14, y + 4)
        olho2 = (x + 14, y + 13)
        lingua = [(x + B, cy), (x + B + 6, cy - 3), (x + B + 6, cy + 3)]

    elif direcao == (-B, 0):  # esquerda ←
        olho1 = (x + 4, y + 4)
        olho2 = (x + 4, y + 13)
        lingua = [(x, cy), (x - 6, cy - 3), (x - 6, cy + 3)]

    elif direcao == (0, -B):  # cima ↑
        olho1 = (x + 4, y + 4)
        olho2 = (x + 13, y + 4)
        lingua = [(cx, y), (cx - 3, y - 6), (cx + 3, y - 6)]

    else:  # baixo ↓
        olho1 = (x + 4, y + 13)
        olho2 = (x + 13, y + 13)
        lingua = [(cx, y + B), (cx - 3, y + B + 6), (cx + 3, y + B + 6)]

    # Língua bifurcada
    pygame.draw.line(tela, ROSA, lingua[0], lingua[1], 2)
    pygame.draw.line(tela, ROSA, lingua[0], lingua[2], 2)

    # Olhos (círculo branco + pupila preta)
    pygame.draw.circle(tela, BRANCO, olho1, 3)
    pygame.draw.circle(tela, PRETO, olho1, 1)
    pygame.draw.circle(tela, BRANCO, olho2, 3)
    pygame.draw.circle(tela, PRETO, olho2, 1)


def desenha_corpo(x, y, indice):
    """Desenha um bloco do corpo com escamas alternadas."""
    B = TAMANHO_BLOCO
    # Alterna verde escuro/normal para efeito de escama
    cor = VERDE_ESCURO if indice % 2 == 0 else VERDE
    pygame.draw.rect(tela, cor, (x, y, B, B))
    pygame.draw.rect(tela, PRETO, (x, y, B, B), 1)

    # Escama: pequeno círculo no centro de blocos pares
    if indice % 2 == 0:
        cx, cy = x + B // 2, y + B // 2
        pygame.draw.circle(tela, VERDE, (cx, cy), 4)


def desenha_cobra(cobra, direcao):
    """Desenha a cobra completa: cabeça estilizada + corpo com escamas."""
    for i, bloco in enumerate(cobra):
        x, y = bloco
        if i == 0:
            desenha_cabeca(x, y, direcao)
        else:
            desenha_corpo(x, y, i)


# ── Comida (maçã estilizada) ──
def desenha_comida(comida):
    x, y = comida
    B = TAMANHO_BLOCO
    cx, cy = x + B // 2, y + B // 2

    # Maçã redonda
    pygame.draw.circle(tela, VERMELHO, (cx, cy + 2), B // 2 - 1)
    # Cabinho
    pygame.draw.line(tela, VERDE_ESCURO, (cx, cy - 6), (cx + 3, cy - 10), 2)
    # Folhinha
    pygame.draw.ellipse(tela, VERDE, (cx, cy - 11, 6, 4))


# ── Mover cobra ──
def mover_cobra(cobra, direcao, crescer):
    cabeca_x, cabeca_y = cobra[0]
    nova_cabeca = (cabeca_x + direcao[0], cabeca_y + direcao[1])
    cobra.insert(0, nova_cabeca)
    if not crescer:
        cobra.pop()
    return cobra


# ── Colisões ──
def colidiu_parede(cobra):
    x, y = cobra[0]
    return x < 0 or x >= LARGURA or y < 0 or y >= ALTURA


def colidiu_si_mesma(cobra):
    return cobra[0] in cobra[1:]


# Calcula FPS baseado na pontuação
def calcular_fps(pontos):
    nivel = pontos // PONTOS_POR_NIVEL
    fps = FPS_INICIAL + (nivel * 3)  # aumentar3 FPS por nível
    return min(fps, FPS_MAXIMO)  # nunca passa do maximo


# ── HUD ──
def desenha_hud(pontos, recorde):
    txt_pontos = fonte_pontos.render(f"Pontos: {pontos}", True, BRANCO)
    txt_recorde = fonte_pontos.render(f"Recorde: {recorde}", True, AMARELO)
    nivel = pontos // PONTOS_POR_NIVEL + 1
    txt_nivel = fonte_pequena.render(f"Vel: {nivel}", True, CINZA)
    tela.blit(txt_pontos, (10, 10))
    tela.blit(txt_recorde, (LARGURA - txt_recorde.get_width() - 10, 10))
    tela.blit(txt_nivel, (LARGURA // 2 - txt_nivel.get_width() // 2, 10))

    #  NOVO: Overlay de pausa por cima do jogo


def desenha_pausa():
    # Cria uma surface semitransparente e cobre a tela
    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    overlay.fill(PRETO_ALPHA)
    tela.blit(overlay, (0, 0))

    txt1 = fonte_pausa.render("PAUSADO", True, BRANCO)
    txt2 = fonte_sub.render("P - Continuar  |  Q - Sair", True, CINZA)

    tela.blit(txt1, txt1.get_rect(center=(LARGURA // 2, ALTURA // 2 - 30)))
    tela.blit(txt2, txt2.get_rect(center=(LARGURA // 2, ALTURA // 2 + 25)))
    pygame.display.flip()


# ── Tela de Início ──
def mostrar_inicio(recorde):
    tela.fill(PRETO)
    desenha_grade()
    titulo = fonte_titulo.render("SNAKE", True, VERDE_CLARO)
    sub = fonte_sub.render("Use as setas para mover", True, BRANCO)
    enter = fonte_sub.render("Pressione ENTER para iniciar", True, CINZA)
    rec_txt = fonte_pequena.render(f"Melhor pontuação: {recorde}", True, AMARELO)
    pausa_txt = fonte_pequena.render("P - Pausar durante o jogo", True, CINZA)
    tela.blit(titulo, titulo.get_rect(center=(LARGURA // 2, ALTURA // 2 - 100)))
    tela.blit(sub, sub.get_rect(center=(LARGURA // 2, ALTURA // 2 - 15)))
    tela.blit(enter, enter.get_rect(center=(LARGURA // 2, ALTURA // 2 + 25)))
    tela.blit(rec_txt, rec_txt.get_rect(center=(LARGURA // 2, ALTURA // 2 + 60)))
    tela.blit(pausa_txt, pausa_txt.get_rect(center=(LARGURA // 2, ALTURA // 2 + 85)))
    pygame.display.flip()


# ── Tela de Game Over ──
def mostrar_game_over(pontos, recorde, novo_recorde):
    tela.fill(PRETO)
    txt1 = fonte_gameover.render("GAME OVER", True, VERMELHO)
    txt2 = fonte_sub.render(f"Pontuação: {pontos}", True, BRANCO)
    txt3 = fonte_sub.render(f"Recorde:   {recorde}", True, AMARELO)
    txt4 = fonte_pequena.render("R - Reiniciar  |  Q - Sair", True, CINZA)
    tela.blit(txt1, txt1.get_rect(center=(LARGURA // 2, ALTURA // 2 - 80)))
    tela.blit(txt2, txt2.get_rect(center=(LARGURA // 2, ALTURA // 2 - 10)))
    tela.blit(txt3, txt3.get_rect(center=(LARGURA // 2, ALTURA // 2 + 30)))
    tela.blit(txt4, txt4.get_rect(center=(LARGURA // 2, ALTURA // 2 + 75)))

    # Mensagem especial se bateu o recorde
    if novo_recorde:
        txt5 = fonte_sub.render("NOVO RECORDE!", True, AMARELO)
        tela.blit(txt5, txt5.get_rect(center=(LARGURA // 2, ALTURA // 2 - 45)))
    pygame.display.flip()


# ── Reiniciar ──
def reiniciar():
    cobra = [(300, 200), (280, 200), (260, 200)]
    direcao = (TAMANHO_BLOCO, 0)
    comida = gerar_comida(cobra)
    pontos = 0
    return cobra, direcao, comida, pontos


# ─────────────────────────────────────────
# INÍCIO DO JOGO
# ─────────────────────────────────────────
estado = "inicio"
recorde = carregar_recorde()
novo_recorde = False
pausado = False  #  controle de pausa
cobra, direcao, comida, pontos = reiniciar()

# -- Loop Principal --
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if estado == "inicio":
                if event.key == pygame.K_RETURN:
                    cobra, direcao, comida, pontos = reiniciar()
                    novo_recorde = False
                    pausado = False
                    estado = "jogando"

            elif estado == "jogando":
                #  Tecla P → pausar/despausar
                if event.key == pygame.K_p:
                    pausado = not pausado
                    som_pausa.play()

                # Q durante pausa → sair
                elif event.key == pygame.K_q and pausado:
                    pygame.quit()
                    sys.exit()

                # Só aceita direção se NÃO estiver pausado
                elif not pausado:
                    if event.key == pygame.K_UP and direcao != (0, TAMANHO_BLOCO):
                        direcao = (0, -TAMANHO_BLOCO)
                    elif event.key == pygame.K_DOWN and direcao != (0, -TAMANHO_BLOCO):
                        direcao = (0, TAMANHO_BLOCO)
                    elif event.key == pygame.K_LEFT and direcao != (TAMANHO_BLOCO, 0):
                        direcao = (-TAMANHO_BLOCO, 0)
                    elif event.key == pygame.K_RIGHT and direcao != (-TAMANHO_BLOCO, 0):
                        direcao = (TAMANHO_BLOCO, 0)

            elif estado == "game_over":
                if event.key == pygame.K_r:
                    cobra, direcao, comida, pontos = reiniciar()
                    novo_recorde = False
                    pausado = False
                    estado = "jogando"
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

    if estado == "inicio":
        mostrar_inicio(recorde)

    elif estado == "jogando":
        fps_atual = calcular_fps(pontos)

        # Só move e atualiza se NÃO estiver pausado
        if not pausado:
            crescer = cobra[0] == comida
            cobra = mover_cobra(cobra, direcao, crescer)

            if colidiu_parede(cobra) or colidiu_si_mesma(cobra):
                if pontos > recorde:
                    recorde = pontos
                    novo_recorde = True
                    salvar_recorde(recorde)
                    som_recorde.play()
                else:
                    som_game_over.play()
                estado = "game_over"

            if crescer:
                comida = gerar_comida(cobra)
                pontos += 10
                som_comer.play()

            tela.fill(PRETO)
            desenha_grade()
            desenha_cobra(cobra, direcao)
            desenha_comida(comida)
            desenha_hud(pontos, recorde)
            pygame.display.flip()

        else:
            # Pausa: redesenha o jogo e coloca o overlay por cima
            tela.fill(PRETO)
            desenha_grade()
            desenha_cobra(cobra, direcao)
            desenha_comida(comida)
            desenha_hud(pontos, recorde)
            desenha_pausa()  # overlay semitransparente com "PAUSADO"

        clock.tick(fps_atual)

    elif estado == "game_over":
        mostrar_game_over(pontos, recorde, novo_recorde)
        clock.tick(FPS_INICIAL)
