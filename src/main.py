import pygame
import sys
import threading
from ui import i18n
from config.game import (BLACK, WHITE, MODE_STANDARD, MODE_DECAY, MODE_POWER, MODE_STAR, MODE_LIMITLESS, MODE_EVERYTHING)
from config.ui import (WINDOW_WIDTH, WINDOW_HEIGHT)
from config.bonus import (POWER_BOMB, POWER_CROSS, POWER_DIAGONAL)
from core.game import Game
from ai.ai import AI
from ui.gui import GUI, _load_font
from rules.bonus import get_rules_for_mode

MODE_AI    = "ai"
MODE_HUMAN = "human"

# ──────────────────────────────────────────────
# Main game loop
# ──────────────────────────────────────────────

def run_game(mode_name=MODE_STANDARD, vs_mode=MODE_AI, gui=None):
    """
    Main game loop.
    vs_mode: 'ai'    → Human (Black) vs AI (White)
             'human' → Human vs Human with AI move suggestion for Black
    gui:  pass an existing GUI to reuse window.
    """
    rules = get_rules_for_mode(mode_name)
    game = Game(rules)

    if gui is None:
        gui = GUI(WINDOW_WIDTH, WINDOW_HEIGHT)
    else:
        gui.hover_pos = None

    ai                   = AI(WHITE)
    ai_suggestion_engine = AI(BLACK)
    ai_time              = 0.0
    ai_thinking          = False
    ai_result            = [None]
    suggestion           = None
    go_to_menu           = False

    # Bonus Feature States
    aide_on = False
    power_active = False
    power_types = [POWER_BOMB, POWER_CROSS, POWER_DIAGONAL]
    power_idx = 0

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

                if event.key == pygame.K_n:
                    # New Game / Restart
                    game = Game(rules)
                    ai.transposition_table.clear()
                    ai_time     = 0.0
                    ai_thinking = False
                    ai_result   = [None]
                    suggestion  = None
                    power_active = False
                    gui.set_status(i18n.get("game_started"))
                    continue

                if event.key == pygame.K_r:
                    # Undo Move
                    if game.history and not ai_thinking:
                        success = False
                        if vs_mode == MODE_AI and len(game.history) >= 2 and game.current_player == BLACK:
                            game.undo() # Pop AI move
                            game.undo() # Pop Human move
                            success = True
                        elif vs_mode == MODE_HUMAN and len(game.history) >= 1:
                            game.undo()
                            success = True

                        if success:
                            suggestion = None
                            power_active = False
                            gui.set_status(i18n.get("undo"))
                            ai_time = 0.0
                    continue

                if event.key == pygame.K_m:
                    go_to_menu = True

                if event.key == pygame.K_g:
                    # Show guide for current mode
                    guide_key = "guide_" + game.rules.name
                    guide_text = i18n.get(guide_key)
                    gui.show_guide(guide_text)

                if event.key == pygame.K_l:
                    i18n.cycle()
                    gui.set_status(i18n.get("language") + ": " + i18n.current())

            if event.type == pygame.MOUSEMOTION:
                gui.update_hover(event.pos)

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Scroll wheel cycling for power types
                if power_active and event.button in (4, 5):
                    power_idx = (power_idx + (1 if event.button == 5 else -1)) % len(power_types)
                    continue

                if event.button == 3:  # Right click
                    if game.rules.power_stones and game.individual_captures.get(game.current_player, 0) >= 5:
                        # In PvP, allow both black and white to activate power
                        power_active = not power_active
                    else:
                        power_active = False
                    continue

                if event.button == 1:
                    # Guide overlay click detection
                    if gui.guide_open:
                        if gui._guide_overlay_rect.collidepoint(event.pos):
                            # Click inside guide box - consume click
                            continue
                        else:
                            # Click outside guide box - close it
                            gui.close_guide()
                            continue

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

                    # Aide button click
                    if gui.check_aide_click(event.pos):
                        aide_on = not aide_on
                        continue

                    # Guide button click
                    if gui.check_guide_click(event.pos):
                        guide_key = "guide_" + game.rules.name
                        guide_text = i18n.get(guide_key)
                        gui.show_guide(guide_text)
                        continue

                    # Board click (ignored when game over or AI thinking)
                    if game.is_game_over() or ai_thinking:
                        continue
                    if vs_mode == MODE_AI and game.current_player == WHITE:
                        continue

                    cell = gui.handle_click(event.pos)
                    if cell:
                        row, col = cell
                        p_type = power_types[power_idx] if power_active else None

                        if game.place_stone(row, col, power_type=p_type):
                            suggestion = None
                            power_active = False
                            # Reset Aide instantly on board change
                            gui.aide_timer = 0

                            if game.is_game_over():
                                name = i18n.get("black") if game.winner == BLACK else i18n.get("white")
                                gui.set_status(f'{name} {i18n.get("wins")}')
                            elif vs_mode == MODE_AI and game.current_player == WHITE:
                                ai_thinking = True
                                ai_result[0] = None
                                threading.Thread(target=compute_ai_move, daemon=True).start()
                                gui.set_status(f'{i18n.get("ai_thinking")} (Depth: 10)')
                            elif vs_mode == MODE_HUMAN:
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

        # ── Aide Checks ──────────────────────────────────
        if aide_on and not game.is_game_over() and not ai_thinking:
            # Determine the opponent (who just played) to check their threats
            from ai.heuristic import evaluate_board, quick_score_move
            opponent = WHITE if game.current_player == BLACK else BLACK

            # Show Aide if it's PvP, OR if it's vs AI and it's currently the human's turn (BLACK)
            if vs_mode == MODE_HUMAN or (vs_mode == MODE_AI and game.current_player == BLACK):
                opp_score = heuristic._score_player(game.board, opponent, 0)
                if opp_score >= 10000:
                    gui.show_aide_popup("UNO!", 3000)
                elif opp_score >= 5000:
                     gui.show_aide_popup("Threat", 3000)

        # ── Render (single flip inside gui.draw) ─────────
        curr_p_type = power_types[power_idx] if power_active else None
        gui.draw(game, ai_time, vs_mode, suggestion, aide_on,
                 power_type=curr_p_type, power_hover=gui.hover_pos if power_active else None)
        clock.tick(60)


# ──────────────────────────────────────────────
# Mode selection screen
# ──────────────────────────────────────────────

# Record the last vs index to remember player preference
GLOBAL_VS_IDX = 0

def select_mode(gui=None):
    """
    Mode selection screen. Layout: 3x2 grid of buttons + AI/PvP Slider.
    """
    if gui is None:
        pygame.init()
        gui_screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Gomoku - Select Mode")
    else:
        gui_screen = gui.screen

    screen = gui_screen

    # Modes layout: 3x2 with your custom emojis!
    mode_options = [
        (MODE_STANDARD, "■ □ ■"), (MODE_LIMITLESS, "♾️"), (MODE_DECAY, "🪫"),
        (MODE_POWER, "🪄"), (MODE_STAR, "🌠"), (MODE_EVERYTHING, "🔥")
    ]

    global GLOBAL_VS_IDX
    vs_options = [("AI", MODE_AI), ("PvP", MODE_HUMAN)]
    current_vs_idx = GLOBAL_VS_IDX

    def get_layout(screen):
        w, h = screen.get_size()
        scale   = min(w / WINDOW_WIDTH, h / WINDOW_HEIGHT)
        f_title = _load_font(max(16, int(32 * scale)), bold=True)
        # We MUST use a specific font list that likely contains Emojis
        f_icon  = pygame.font.SysFont("segoeuiemoji,notocoloremoji,applecoloremoji,symbola,dejavusans,freesans", max(30, int(42 * scale)))
        f_btn   = _load_font(max(12, int(18 * scale)), bold=True)
        f_small = _load_font(max(12, int(14 * scale)), bold=True)

        # 3x2 grid buttons
        btn_w, btn_h = int(180 * scale), int(140 * scale)
        gap_x, gap_y = int(20 * scale), int(20 * scale)
        # Grid bounds
        grid_w = 3 * btn_w + 2 * gap_x
        start_x = w // 2 - grid_w // 2
        start_y = int(h * 0.35)

        btns = []
        for i in range(2):
            for j in range(3):
                idx = i * 3 + j
                rect = pygame.Rect(start_x + j * (btn_w + gap_x), start_y + i * (btn_h + gap_y), btn_w, btn_h)
                btns.append(rect)

        # Slider rect below title, above grid
        sw, sh = int(300 * scale), int(40 * scale)
        s_rect = pygame.Rect(w // 2 - sw // 2, int(h * 0.22), sw, sh)

        # Language buttons top right (wider to fit flags and text)
        lw, lh = int(110 * scale), int(35 * scale)
        lgap   = 10
        langs = i18n.LANGS
        total = len(langs) * lw + (len(langs) - 1) * lgap
        lx    = w - total - 20
        ly    = 20
        lang_btns = {lang: pygame.Rect(lx + i * (lw + lgap), ly, lw, lh)
                     for i, lang in enumerate(langs)}

        return f_title, f_icon, f_btn, f_small, btns, s_rect, lang_btns

    f_title, f_icon, f_btn, f_small, buttons, s_rect, lang_btns = get_layout(screen)
    clock = pygame.time.Clock()

    while True:
        w, h = screen.get_size()
        screen.fill((30, 22, 14))

        # Title
        t_surf = f_title.render(i18n.get("title"), True, (200, 130, 50))
        screen.blit(t_surf, (w // 2 - t_surf.get_width() // 2, int(h * 0.08)))

        mx, my = pygame.mouse.get_pos()

        # Slider rendering
        pygame.draw.rect(screen, (50, 40, 30), s_rect, border_radius=20)
        s_hovered = s_rect.collidepoint(mx, my)
        slider_half = pygame.Rect(s_rect.x if current_vs_idx == 0 else s_rect.x + s_rect.width//2,
                                  s_rect.y, s_rect.width//2, s_rect.height)
        pygame.draw.rect(screen, (200, 130, 50) if not s_hovered else (220, 150, 70), slider_half, border_radius=20)
        pygame.draw.rect(screen, (100, 80, 50), s_rect, 2, border_radius=20)

        # Slider texts
        ltxt = f_btn.render("AI", True, (40, 20, 10) if current_vs_idx == 0 else (150, 140, 120))
        rtxt = f_btn.render("PvP", True, (40, 20, 10) if current_vs_idx == 1 else (150, 140, 120))
        screen.blit(ltxt, ltxt.get_rect(center=(s_rect.x + s_rect.width//4, s_rect.centery)))
        screen.blit(rtxt, rtxt.get_rect(center=(s_rect.x + 3*s_rect.width//4, s_rect.centery)))

        # Mode buttons (3x2 grid)
        for i, (m_id, icon_txt) in enumerate(mode_options):
            rect = buttons[i]
            hovered = rect.collidepoint(mx, my)
            bg = (70, 50, 30) if hovered else (50, 35, 20)
            bdr = (250, 180, 70) if hovered else (120, 90, 50)
            pygame.draw.rect(screen, bg, rect, border_radius=10)
            pygame.draw.rect(screen, bdr, rect, 3 if hovered else 1, border_radius=10)

            # Draw Hand-Crafted Vector Icons (Emoji-like)
            ix, iy = rect.centerx, rect.centery - 20

            if m_id == MODE_STANDARD:
                pygame.draw.circle(screen, (10, 10, 10), (ix-12, iy), 9)
                pygame.draw.circle(screen, (180, 180, 180), (ix-12, iy), 9, 1) # visible rim for black stone
                pygame.draw.circle(screen, (245, 245, 245), (ix+12, iy), 9)
            elif m_id == MODE_DECAY:
                # 🪫 Battery Icon
                pygame.draw.rect(screen, (100, 100, 100), (ix-12, iy-6, 24, 12), 2, border_radius=2)
                pygame.draw.rect(screen, (100, 100, 100), (ix+12, iy-3, 3, 6))
                pygame.draw.rect(screen, (200, 50, 50), (ix-10, iy-4, 5, 8)) # Low charge red
            elif m_id == MODE_POWER:
                # 🪄 Magic Wand
                pygame.draw.line(screen, (100, 70, 50), (ix-10, iy+10), (ix+5, iy-5), 4) # handle
                pygame.draw.circle(screen, (255, 255, 255), (ix+8, iy-8), 4) # tip
                pygame.draw.circle(screen, (255, 255, 0), (ix+8, iy-8), 6, 1) # glow
            elif m_id == MODE_STAR:
                # 🌠 Shooting Star
                pygame.draw.polygon(screen, (255, 150, 50), [(ix-5,iy+5), (ix-25,iy+20), (ix-10,iy+30), (ix,iy+10)])
                import math
                pts = []
                for j in range(10):
                    rr = 12 if j % 2 == 0 else 5
                    ang = math.radians(j * 36 - 90)
                    pts.append((ix + rr * math.cos(ang), iy + rr * math.sin(ang)))
                pygame.draw.polygon(screen, (255, 230, 50), pts)
            elif m_id == MODE_LIMITLESS:
                # ♾️ Infinity symbol
                pygame.draw.circle(screen, (150, 210, 255), (ix-10, iy), 10, 2)
                pygame.draw.circle(screen, (150, 210, 255), (ix+10, iy), 10, 2)
            elif m_id == MODE_EVERYTHING:
                # 🔥 Fire Emoji Replica
                pygame.draw.ellipse(screen, (220, 50, 20), (ix-12, iy-10, 24, 30))
                pygame.draw.ellipse(screen, (255, 150, 20), (ix-8, iy-2, 16, 20))
                pygame.draw.ellipse(screen, (255, 230, 50), (ix-4, iy+6, 8, 10))

            t_surf = f_btn.render(i18n.get("mode_" + m_id), True, (210, 200, 180))
            screen.blit(t_surf, t_surf.get_rect(center=(rect.centerx, rect.centery + 30)))

        # Language buttons (Top right)
        for lang, rect in lang_btns.items():
            active  = (lang == i18n.current())
            hovered = rect.collidepoint(mx, my)
            bg      = (200, 130, 50) if active else ((85, 62, 25) if hovered else (55, 42, 25))
            border  = (255, 200, 80) if active else (95, 72, 42)
            pygame.draw.rect(screen, bg, rect, border_radius=5)
            pygame.draw.rect(screen, border, rect, 1, border_radius=5)

            # Manually Draw Flag before Text to guarantee visibility
            fx, fy = rect.x + 8, rect.centery - 8
            if lang == "EN":  # US Flag
                pygame.draw.rect(screen, (200, 50, 50), (fx, fy, 22, 16)) # base red
                pygame.draw.rect(screen, (255, 255, 255), (fx, fy+2, 22, 3)) # stripes
                pygame.draw.rect(screen, (255, 255, 255), (fx, fy+7, 22, 3))
                pygame.draw.rect(screen, (255, 255, 255), (fx, fy+12, 22, 3))
                pygame.draw.rect(screen, (50, 50, 150), (fx, fy, 11, 8)) # blue canton
            elif lang == "FR": # France Flag
                pygame.draw.rect(screen, (40, 80, 180), (fx, fy, 7, 16))
                pygame.draw.rect(screen, (255, 255, 255), (fx+7, fy, 8, 16))
                pygame.draw.rect(screen, (220, 40, 50), (fx+15, fy, 7, 16))
            elif lang == "ZH": # Taiwan Flag
                pygame.draw.rect(screen, (220, 30, 30), (fx, fy, 22, 16))
                pygame.draw.rect(screen, (30, 40, 160), (fx, fy, 11, 8))
                pygame.draw.circle(screen, (255, 255, 255), (fx+5, fy+4), 3)

            lsurf = f_small.render(i18n.LANG_LABELS.get(lang, lang), True, (235, 225, 210))
            screen.blit(lsurf, lsurf.get_rect(midleft=(fx + 28, rect.centery)))

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
                    f_title, f_icon, f_btn, f_small, buttons, s_rect, lang_btns = get_layout(screen)

            if event.type == pygame.VIDEORESIZE:
                if gui:
                    gui.handle_resize(event.w, event.h)
                    screen = gui.screen
                else:
                    screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                f_title, f_icon, f_btn, f_small, buttons, s_rect, lang_btns = get_layout(screen)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Language click
                for lang, rect in lang_btns.items():
                    if rect.collidepoint(event.pos):
                        i18n.set_lang(lang)
                        f_title, f_icon, f_btn, f_small, buttons, s_rect, lang_btns = get_layout(screen)
                        break

                # Slider click
                if s_rect.collidepoint(event.pos):
                    current_vs_idx = 1 - current_vs_idx
                    GLOBAL_VS_IDX = current_vs_idx

                # Mode click
                for i, (m_id, _) in enumerate(mode_options):
                    if buttons[i].collidepoint(event.pos):
                        vs_mode = vs_options[current_vs_idx][1]
                        if gui:
                            return run_game(m_id, vs_mode, gui)
                        else:
                            new_gui = GUI(screen.get_width(), screen.get_height())
                            return run_game(m_id, vs_mode, new_gui)

if __name__ == "__main__":
    select_mode()
