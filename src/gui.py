import pygame
import pygame.gfxdraw
import sys
import os
import i18n
from constants import (BOARD_SIZE, EMPTY, BLACK, WHITE, CELL_SIZE, BOARD_MARGIN,
                       WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_BG, COLOR_LINE,
                       COLOR_BLACK_STONE, COLOR_WHITE_STONE,
                       COLOR_PANEL_BG, COLOR_TEXT, COLOR_ACCENT,
                       DECAY_LIFESPAN, DECAY_WARN_THRESHOLD, DECAY_CRACK_THRESHOLD)

PANEL_X_DEFAULT = BOARD_MARGIN + CELL_SIZE * (BOARD_SIZE - 1) + BOARD_MARGIN

# ──────────────────────────────────────────────
# CJK-capable font loader
# ──────────────────────────────────────────────

def _load_font(size, bold=False):
    """
    Load a font that supports CJK characters (needed for Traditional Chinese).
    Tries common paths on Ubuntu/WSL, falls back to pygame default.
    """
    cjk_paths = [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in cjk_paths:
        if os.path.exists(path):
            try:
                f = pygame.font.Font(path, size)
                if bold:
                    # Pygame doesn't support bold for file fonts directly; simulate with SysFont
                    return pygame.font.SysFont("dejavusans", size, bold=True)
                return f
            except Exception:
                pass
    return pygame.font.SysFont("dejavusans", size, bold=bold)


class GUI:
    """
    Pygame graphical interface for Gomoku.
    Features: 3D marble stones, i18n panel, CJK font support, resizable window.
    """

    def __init__(self, win_w=WINDOW_WIDTH, win_h=WINDOW_HEIGHT):
        pygame.init()
        self.win_w = win_w
        self.win_h = win_h
        self.screen = pygame.display.set_mode((self.win_w, self.win_h), pygame.RESIZABLE)
        pygame.display.set_caption("Gomoku — 5eyes")
        self._load_fonts()
        self._panel_x   = PANEL_X_DEFAULT
        self.hover_pos  = None
        self.status_msg = ""
        # Clickable rects — pre-populated with empty defaults so first-frame clicks are safe
        self._lang_rects = {lang: pygame.Rect(0, 0, 0, 0) for lang in i18n.LANGS}
        self._menu_rect  = pygame.Rect(0, 0, 0, 0)

    # ──────────────────────────────────────────────
    # Fonts
    # ──────────────────────────────────────────────

    def _load_fonts(self):
        scale = min(self.win_w / WINDOW_WIDTH, self.win_h / WINDOW_HEIGHT)
        # Larger base sizes than before (user feedback: fonts too small)
        self.font_title = _load_font(max(16, int(28 * scale)), bold=True)
        self.font_med   = _load_font(max(12, int(20 * scale)))
        self.font_small = _load_font(max(10, int(15 * scale)))

    def handle_resize(self, new_w, new_h):
        self.win_w = max(new_w, 600)
        self.win_h = max(new_h, 500)
        self.screen = pygame.display.set_mode((self.win_w, self.win_h), pygame.RESIZABLE)
        self._load_fonts()

    # ──────────────────────────────────────────────
    # Scale helpers
    # ──────────────────────────────────────────────

    def _scale(self):
        scale  = min(self.win_w / WINDOW_WIDTH, self.win_h / WINDOW_HEIGHT)
        cell   = max(8, int(CELL_SIZE * scale))
        margin = max(10, int(BOARD_MARGIN * scale))
        return cell, margin

    def grid_to_pixel(self, row, col):
        cell, margin = self._scale()
        return (margin + col * cell, margin + row * cell)

    def pixel_to_grid(self, px, py):
        cell, margin = self._scale()
        col = round((px - margin) / cell)
        row = round((py - margin) / cell)
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            cx, cy = self.grid_to_pixel(row, col)
            if abs(px - cx) <= cell // 2 and abs(py - cy) <= cell // 2:
                return (row, col)
        return None

    # ──────────────────────────────────────────────
    # 3D marble stone renderer
    # ──────────────────────────────────────────────

    def _draw_stone(self, surface, cx, cy, radius, is_black,
                    age_label=None, cracked=False):
        """
        Render a 3D marble-style stone.
        Shadow radius is strictly < stone radius so it can never bleed outside.
        age_label: str rendered inside stone when lifespan countdown is active.
        cracked:   draw crack lines when stone is about to expire.
        """
        if is_black:
            base   = (28, 28, 38)
            rim    = (10, 10, 18)
            hl_col = (255, 255, 255, 100)
            glint  = (255, 255, 255, 190)
        else:
            base   = (245, 240, 228)
            rim    = (185, 168, 140)   # warm tan, NOT grey
            hl_col = (255, 255, 255, 130)
            glint  = (255, 255, 255, 220)

        # Drop shadow — MUST be strictly inside the stone's footprint.
        # With offset (ox, oy), shad_r <= radius - max(ox, oy) guarantees full coverage.
        ox, oy = 3, 4
        shad_r = max(1, radius - max(ox, oy) - 1)
        shad   = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(shad, radius - ox, radius - oy,
                                     shad_r, (0, 0, 0, 65))
        surface.blit(shad, (cx - radius + ox, cy - radius + oy))

        # Base stone
        pygame.gfxdraw.filled_circle(surface, cx, cy, radius, base)
        pygame.gfxdraw.aacircle(surface, cx, cy, radius, base)

        # Rim: two aa passes for a crisp edge (no blitted surface = no grey bleed)
        pygame.gfxdraw.aacircle(surface, cx, cy, radius,     rim)
        if radius > 8:
            pygame.gfxdraw.aacircle(surface, cx, cy, radius - 1, rim)

        # Specular oval (upper-left)
        hl_r = max(2, radius // 3)
        hl   = pygame.Surface((hl_r * 4, hl_r * 3), pygame.SRCALPHA)
        pygame.gfxdraw.filled_ellipse(hl, hl_r * 2, hl_r, hl_r * 2, hl_r, hl_col)
        surface.blit(hl, (cx - radius // 3 - hl_r * 2,
                          cy - radius // 3 - hl_r))

        # Micro glint
        gr = max(1, radius // 8)
        pygame.gfxdraw.filled_circle(surface,
                                     cx - radius // 4, cy - radius // 4, gr, glint)

        # Decay visuals
        if cracked and radius >= 6:
            self._draw_cracks(surface, cx, cy, radius, is_black)
        if age_label and radius >= 9:
            col = (200, 80, 80) if is_black else (150, 50, 50)
            try:
                fnt = pygame.font.SysFont("dejavusans", max(8, radius - 4), bold=True)
                ts  = fnt.render(age_label, True, col)
                surface.blit(ts, ts.get_rect(center=(cx, cy + radius // 4)))
            except Exception:
                pass

    def _draw_cracks(self, surface, cx, cy, radius, is_black):
        """Draw deterministic radiating crack lines for a dying stone."""
        import math
        col = (130, 70, 70) if is_black else (100, 60, 40)
        angles = [(cx * 7 + cy * 13 + i * 67) % 360 for i in range(4)]
        for a in angles:
            rad = math.radians(a)
            x1  = cx + int(radius * 0.15 * math.cos(rad))
            y1  = cy + int(radius * 0.15 * math.sin(rad))
            x2  = cx + int(radius * 0.82 * math.cos(rad))
            y2  = cy + int(radius * 0.82 * math.sin(rad))
            pygame.draw.line(surface, col, (x1, y1), (x2, y2), 1)

    # ──────────────────────────────────────────────
    # Main draw (single call per frame — one flip only)
    # ──────────────────────────────────────────────

    def draw(self, game, ai_time, mode, suggestion=None):
        """Render one complete frame. Includes win overlay if game is over."""
        cell, margin = self._scale()
        self._panel_x = margin + cell * (BOARD_SIZE - 1) + margin

        self.screen.fill(COLOR_BG)
        self._draw_grid(cell, margin)
        self._draw_star_points(cell, margin)
        self._draw_stones(game, cell, margin)
        if self.hover_pos and not game.is_game_over():
            self._draw_hover(self.hover_pos, cell)
        if suggestion and not game.is_game_over():
            self._draw_suggestion(suggestion, cell)

        self._draw_panel(game, ai_time, mode)

        # Win overlay rendered here (single flip, no flash)
        if game.is_game_over():
            self._draw_win_overlay(game)

        pygame.display.flip()

    # ──────────────────────────────────────────────
    # Board elements
    # ──────────────────────────────────────────────

    def _draw_grid(self, cell, margin):
        end_x = margin + (BOARD_SIZE - 1) * cell
        end_y = margin + (BOARD_SIZE - 1) * cell
        for i in range(BOARD_SIZE):
            x = margin + i * cell
            y = margin + i * cell
            pygame.draw.line(self.screen, COLOR_LINE, (x, margin), (x, end_y), 1)
            pygame.draw.line(self.screen, COLOR_LINE, (margin, y), (end_x, y), 1)

    def _draw_star_points(self, cell, margin):
        r = max(3, cell // 8)
        for row, col in [(3,3),(3,9),(3,15),(9,3),(9,9),(9,15),(15,3),(15,9),(15,15)]:
            x = margin + col * cell
            y = margin + row * cell
            pygame.gfxdraw.filled_circle(self.screen, x, y, r, COLOR_LINE)

    def _draw_stones(self, game, cell, margin):
        board = game.board
        last_move = game.last_move
        stone_r = max(4, cell // 2 - 2)
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] == EMPTY:
                    continue
                x = margin + c * cell
                y = margin + r * cell
                
                age_label = None
                cracked = False
                if (r, c) in game.stones_ply:
                    ply_remaining = DECAY_LIFESPAN - (game.ply_count - game.stones_ply[(r, c)])
                    if ply_remaining <= DECAY_WARN_THRESHOLD:
                        age_label = str(ply_remaining)
                    if ply_remaining <= DECAY_CRACK_THRESHOLD:
                        cracked = True

                self._draw_stone(self.screen, x, y, stone_r, board[r][c] == BLACK,
                                 age_label=age_label, cracked=cracked)
                
                if last_move and (r, c) == last_move:
                    dot = (160, 50, 50) if board[r][c] == BLACK else (50, 80, 200)
                    dr  = max(2, stone_r // 5)
                    pygame.gfxdraw.filled_circle(self.screen, x, y, dr, dot)

    def _draw_hover(self, pos, cell):
        row, col = pos
        x, y = self.grid_to_pixel(row, col)
        sr = max(4, cell // 2 - 2)
        s  = pygame.Surface((sr*2+4, sr*2+4), pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(s, sr+2, sr+2, sr, (30, 30, 30, 80))
        self.screen.blit(s, (x-sr-2, y-sr-2))

    def _draw_suggestion(self, pos, cell):
        row, col = pos
        x, y = self.grid_to_pixel(row, col)
        sr = max(4, cell // 2 - 2)
        pygame.gfxdraw.aacircle(self.screen, x, y, sr, (255, 140, 0))
        pygame.gfxdraw.aacircle(self.screen, x, y, sr - 1, (255, 140, 0))

    # ──────────────────────────────────────────────
    # Win overlay (drawn inside draw(), no extra flip)
    # ──────────────────────────────────────────────

    def _draw_win_overlay(self, game):
        winner = game.winner
        px = self._panel_x
        overlay = pygame.Surface((px, self.win_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        t    = i18n.get
        name = t("black") if winner == BLACK else t("white")
        msg  = f"{name} {t('wins')}"
        sub  = t("play_again")

        txt  = self.font_title.render(msg, True, (255, 220, 50))
        sub_s = self.font_med.render(sub, True, (210, 210, 210))
        cx   = px // 2
        cy   = self.win_h // 2
        self.screen.blit(txt,  txt.get_rect(center=(cx, cy - 24)))
        self.screen.blit(sub_s, sub_s.get_rect(center=(cx, cy + 24)))

    # ──────────────────────────────────────────────
    # Side panel
    # ──────────────────────────────────────────────

    def _draw_panel(self, game, ai_time, mode):
        px = self._panel_x
        pw = self.win_w - px
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, (px - 10, 0, pw + 10, self.win_h))

        t   = i18n.get
        y   = 16
        SEP = "-" * 19

        def label(text, color=COLOR_TEXT, font=None):
            nonlocal y
            f  = font or self.font_med
            s  = f.render(text, True, color)
            self.screen.blit(s, (px + 8, y))
            y += s.get_height() + 7

        label(t("title"), COLOR_ACCENT, self.font_title)
        label(SEP, COLOR_ACCENT)

        mode_str = t("vs_ai") if mode == "ai" else t("vs_human")
        label(f'{t("mode")}: {mode_str}')

        label(SEP, COLOR_ACCENT)
        label(t("captured"))
        label(f'  {t("black")}: {game.captures.get(BLACK, 0)}')
        label(f'  {t("white")}: {game.captures.get(WHITE, 0)}')

        label(SEP, COLOR_ACCENT)
        if game.is_game_over():
            name = t("black") if game.winner == BLACK else t("white")
            label(f'{name} {t("wins")}', (255, 220, 60), self.font_title)
        else:
            name = t("black") if game.current_player == BLACK else t("white")
            label(f'{t("turn")} {name}')

        label(SEP, COLOR_ACCENT)
        label(t("ai_time"), COLOR_ACCENT)
        tc = (255, 80, 80) if ai_time > 0.4 else COLOR_TEXT
        label(f"  {ai_time:.3f}s", tc, self.font_title)

        if self.status_msg:
            label(SEP, COLOR_ACCENT)
            label(self.status_msg, font=self.font_small)

        # ---- Language buttons (ASCII labels, always renderable) ----
        self._draw_lang_buttons(px, pw)

        # ---- Visible "Menu" button ----
        mb_h = 30
        mb_y = self.win_h - mb_h - 70
        self._menu_rect = pygame.Rect(px + 6, mb_y, pw - 14, mb_h)
        m_hovered = self._menu_rect.collidepoint(pygame.mouse.get_pos())
        m_bg  = (110, 70, 25) if m_hovered else (70, 50, 20)
        m_bdr = (200, 140, 50) if m_hovered else (130, 95, 40)
        pygame.draw.rect(self.screen, m_bg, self._menu_rect, border_radius=6)
        pygame.draw.rect(self.screen, m_bdr, self._menu_rect, 1, border_radius=6)
        mt = self.font_small.render(t("menu"), True, (230, 215, 185))
        self.screen.blit(mt, mt.get_rect(center=self._menu_rect.center))

        # ---- Quit hint ----
        y = self.win_h - 30
        label(t("quit"), font=self.font_small)

    def _draw_lang_buttons(self, px, pw):
        """
        Draw language switcher buttons using ASCII short-names (EN/FR/ZH).
        Storing rects here so click detection works on the very next event.
        """
        langs   = i18n.LANGS
        labels  = i18n.LANG_LABELS
        n       = len(langs)
        btn_w   = max(32, (pw - 14 - (n - 1) * 5) // n)
        btn_h   = 26
        gap     = 5
        total   = n * btn_w + (n - 1) * gap
        start_x = px + (pw - total) // 2
        y       = self.win_h - 38

        for i, lang in enumerate(langs):
            rx   = start_x + i * (btn_w + gap)
            rect = pygame.Rect(rx, y, btn_w, btn_h)
            self._lang_rects[lang] = rect   # update every frame

            active  = (lang == i18n.current())
            hovered = rect.collidepoint(pygame.mouse.get_pos())
            bg     = COLOR_ACCENT if active else ((85, 62, 25) if hovered else (52, 38, 16))
            border = (255, 200, 80) if active else (120, 88, 38)
            pygame.draw.rect(self.screen, bg, rect, border_radius=5)
            pygame.draw.rect(self.screen, border, rect, 1, border_radius=5)

            # ASCII label — renders correctly in DejaVu / any fallback font
            tf = self.font_small.render(labels.get(lang, lang), True, (245, 238, 218))
            self.screen.blit(tf, tf.get_rect(center=rect.center))

    # ──────────────────────────────────────────────
    # Input helpers
    # ──────────────────────────────────────────────

    def update_hover(self, pos):
        self.hover_pos = self.pixel_to_grid(*pos)

    def handle_click(self, pos):
        return self.pixel_to_grid(*pos)

    def check_lang_click(self, pos):
        """Return language string if a language button was clicked, else None."""
        for lang, rect in self._lang_rects.items():
            if rect.collidepoint(pos):
                return lang
        return None

    def check_menu_click(self, pos):
        """Return True if the menu button area was clicked."""
        return self._menu_rect is not None and self._menu_rect.collidepoint(pos)

    def set_status(self, msg):
        self.status_msg = msg

    def tick(self, fps=60):
        self.clock.tick(fps)
