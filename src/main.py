import pygame
import sys
import threading
import i18n
from constants import BLACK, WHITE, WINDOW_WIDTH, WINDOW_HEIGHT
from game import Game
from ai import AI
from gui import GUI

MODE_AI    = "ai"
MODE_HUMAN = "human"

# ──────────────────────────────────────────────
# Main game loop
# ──────────────────────────────────────────────

def run_game(mode=MODE_AI, gui=None):
    """
    Main game loop.
    mode: 'ai'    → Human (Black) vs AI (White)
          'human' → Human vs Human with AI move suggestion for Black
    gui:  pass an existing GUI to reuse window (prevents resize on restart).
    """
    game = Game()
    if gui is None:
        gui = GUI(WINDOW_WIDTH, WINDOW_HEIGHT)
    else:
        # Reuse existing GUI: just reset its state
        gui.hover_pos = None

    ai                   = AI(WHITE)
    ai_suggestion_engine = AI(BLACK)
    ai_time              = 0.0
    ai_thinking          = False
    ai_result            = [None]
    suggestion           = None
    go_to_menu           = False

    gui.set_status(i18n.get("game_started"))

    def compute_ai_move():
        ai_result[0] = ai.get_best_move(game)

    clock = pygame.time.Clock()

    while True:
        # ── Events ──────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.VIDEORESIZE:
                gui.handle_resize(event.w, event.h)

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.quit()
                    sys.exit()

                if event.key == pygame.K_r:
                    # Restart: reset game state WITHOUT recreating the GUI window
                    game = Game()
                    ai.transposition_table.clear()
                    ai_time     = 0.0
                    ai_thinking = False
                    ai_result   = [None]
                    suggestion  = None
                    gui.set_status(i18n.get("game_started"))
                    continue

                if event.key == pygame.K_m:
                    go_to_menu = True

                if event.key == pygame.K_l:
                    i18n.cycle()
                    gui.set_status(i18n.get("language") + ": " + i18n.current())

            if event.type == pygame.MOUSEMOTION:
                gui.update_hover(event.pos)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Language button click
                lang = gui.check_lang_click(event.pos)
                if lang:
                    i18n.set_lang(lang)
                    gui.set_status(i18n.get("language") + ": " + i18n.current())
                    continue

                # Menu button click
                if gui.check_menu_click(event.pos):
                    go_to_menu = True
                    continue

                # Board click (ignored when game over or AI thinking)
                if game.is_game_over() or ai_thinking:
                    continue
                if mode == MODE_AI and game.current_player == WHITE:
                    continue

                cell = gui.handle_click(event.pos)
                if cell:
                    row, col = cell
                    if game.place_stone(row, col):
                        suggestion = None
                        if game.is_game_over():
                            name = i18n.get("black") if game.winner == BLACK else i18n.get("white")
                            gui.set_status(f'{name} {i18n.get("wins")}')
                        elif mode == MODE_AI and game.current_player == WHITE:
                            ai_thinking = True
                            ai_result[0] = None
                            threading.Thread(target=compute_ai_move, daemon=True).start()
                            gui.set_status(i18n.get("ai_thinking"))
                        elif mode == MODE_HUMAN:
                            suggestion = ai_suggestion_engine.suggest_move(game)
                            gui.set_status(i18n.get("suggest"))

        if go_to_menu:
            return select_mode(gui)

        # ── AI move collection ───────────────────────────
        if ai_thinking and ai_result[0] is not None:
            row, col = ai_result[0]
            if not game.is_game_over():
                game.place_stone(row, col, WHITE)
                ai_time     = ai.last_think_time
                ai_thinking = False
                if game.is_game_over():
                    name = i18n.get("black") if game.winner == BLACK else i18n.get("white")
                    gui.set_status(f'{name} {i18n.get("wins")}')
                else:
                    gui.set_status(f'AI ({row},{col}) {ai_time:.3f}s')
            else:
                ai_thinking = False

        # ── Render (single flip inside gui.draw) ─────────
        gui.draw(game, ai_time, mode, suggestion)
        clock.tick(60)


# ──────────────────────────────────────────────
# Mode selection screen
# ──────────────────────────────────────────────

def select_mode(gui=None):
    """
    Mode selection screen. Reuses existing GUI window if provided.
    All elements scale dynamically on resize.
    """
    if gui is None:
        pygame.init()
        gui_screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Gomoku - Select Mode")
        own_display = True
    else:
        gui_screen = gui.screen
        own_display = False

    options = [(i18n.get("vs_ai"), MODE_AI), (i18n.get("vs_human"), MODE_HUMAN)]

    def get_layout(screen):
        w, h = screen.get_size()
        scale   = min(w / WINDOW_WIDTH, h / WINDOW_HEIGHT)
        f_title = pygame.font.SysFont("dejavusans", max(16, int(32 * scale)), bold=True)
        f_btn   = pygame.font.SysFont("dejavusans", max(12, int(22 * scale)))
        f_small = pygame.font.SysFont("dejavusans", max(10, int(14 * scale)))
        btn_w, btn_h = int(260 * scale), int(54 * scale)
        btn_x = w // 2 - btn_w // 2
        btns = [pygame.Rect(btn_x, int(h * 0.38) + i * int(74 * scale), btn_w, btn_h)
                for i in range(len(options))]
        # Language buttons
        lw, lh = int(55 * scale), int(26 * scale)
        gap   = 6
        langs = i18n.LANGS
        total = len(langs) * lw + (len(langs) - 1) * gap
        lx    = w // 2 - total // 2
        lang_btns = {lang: pygame.Rect(lx + i * (lw + gap), int(h * 0.82), lw, lh)
                     for i, lang in enumerate(langs)}
        return f_title, f_btn, f_small, btns, lang_btns

    # Use gui.screen OR the fresh surface
    screen = gui.screen if gui else gui_screen
    f_title, f_btn, f_small, buttons, lang_btns = get_layout(screen)
    clock = pygame.time.Clock()

    while True:
        w, h = screen.get_size()
        screen.fill((30, 22, 14))

        # Title
        t_surf = f_title.render(i18n.get("title"), True, (200, 130, 50))
        screen.blit(t_surf, (w // 2 - t_surf.get_width() // 2, int(h * 0.1)))

        sub = f_btn.render(i18n.get("mode_select"), True, (160, 140, 110))
        screen.blit(sub, (w // 2 - sub.get_width() // 2, int(h * 0.24)))

        # Mode buttons
        mx, my = pygame.mouse.get_pos()
        # Rebuild option labels (language may have changed)
        option_labels = [i18n.get("vs_ai"), i18n.get("vs_human")]
        for i, (label, _) in enumerate(options):
            rect    = buttons[i]
            hovered = rect.collidepoint(mx, my)
            bg      = (200, 130, 50) if hovered else (60, 45, 28)
            border  = (240, 180, 80) if hovered else (100, 75, 45)
            pygame.draw.rect(screen, bg, rect, border_radius=8)
            pygame.draw.rect(screen, border, rect, 2, border_radius=8)
            txt = f_btn.render(option_labels[i], True, (230, 220, 200))
            screen.blit(txt, txt.get_rect(center=rect.center))

        # Language selector label
        lang_label = f_small.render(i18n.get("language") + ":", True, (160, 140, 110))
        screen.blit(lang_label, (w // 2 - lang_label.get_width() // 2, int(h * 0.76)))

        # Language buttons — use ASCII short labels (EN/FR/ZH) for universal font support
        for lang, rect in lang_btns.items():
            active  = (lang == i18n.current())
            hovered = rect.collidepoint(mx, my)
            bg      = (200, 130, 50) if active else ((85, 62, 25) if hovered else (55, 42, 25))
            border  = (255, 200, 80) if active else (95, 72, 42)
            pygame.draw.rect(screen, bg, rect, border_radius=5)
            pygame.draw.rect(screen, border, rect, 1, border_radius=5)
            lsurf = f_small.render(i18n.LANG_LABELS.get(lang, lang), True, (235, 225, 210))
            screen.blit(lsurf, lsurf.get_rect(center=rect.center))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_l:
                    i18n.cycle()
                    f_title, f_btn, f_small, buttons, lang_btns = get_layout(screen)

            if event.type == pygame.VIDEORESIZE:
                if gui:
                    gui.handle_resize(event.w, event.h)
                    screen = gui.screen
                else:
                    screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                f_title, f_btn, f_small, buttons, lang_btns = get_layout(screen)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Language click
                for lang, rect in lang_btns.items():
                    if rect.collidepoint(event.pos):
                        i18n.set_lang(lang)
                        f_title, f_btn, f_small, buttons, lang_btns = get_layout(screen)
                        break
                # Mode click
                for i, (_, mode) in enumerate(options):
                    if buttons[i].collidepoint(event.pos):
                        if gui:
                            return run_game(mode, gui)
                        else:
                            new_gui = GUI(screen.get_width(), screen.get_height())
                            return run_game(mode, new_gui)


if __name__ == "__main__":
    select_mode()
