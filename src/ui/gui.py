import pygame
import pygame.gfxdraw
import sys
import os
from ui import i18n
from config.game import (BOARD_SIZE, EMPTY, BLACK, WHITE, HOLE)
from config.ui import (CELL_SIZE, BOARD_MARGIN, WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_BG, COLOR_LINE, COLOR_BLACK_STONE, COLOR_WHITE_STONE, COLOR_PANEL_BG, COLOR_TEXT, COLOR_ACCENT)
from config.bonus import (POWER_BOMB, POWER_CROSS, POWER_DIAGONAL, STAR_WARN_PLY)

PANEL_X_DEFAULT = BOARD_MARGIN + CELL_SIZE * (BOARD_SIZE - 1) + BOARD_MARGIN

# ──────────────────────────────────────────────
# CJK-capable font loader
# ──────────────────────────────────────────────

def _load_font(size, bold=False):
    """
    Load a font that supports CJK characters (needed for Traditional Chinese).
    Tries common paths on Ubuntu/WSL, falls back to pygame default.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cjk_paths = [
        os.path.join(base_dir, "assets", "fonts", "NotoSansTC-Regular.otf"),
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in cjk_paths:
        if os.path.exists(path):
            try:
                f = pygame.font.Font(path, size)
                # Pygame file-based fonts do not support bold easily without rendering issues,
                # but we MUST return the CJK font to support Chinese characters.
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
        self.aide_msg = ""
        self.aide_timer = 0

        # Clickable rects — pre-populated with empty defaults so first-frame clicks are safe
        self._lang_rects = {lang: pygame.Rect(0, 0, 0, 0) for lang in i18n.LANGS}
        self._menu_rect  = pygame.Rect(0, 0, 0, 0)
        self._aide_rect = pygame.Rect(0, 0, 0, 0)
        self._guide_rect = pygame.Rect(0, 0, 0, 0)
        self._guide_overlay_rect = pygame.Rect(0, 0, 0, 0)
        self.guide_msg = ""
        self.guide_open = False

    # ──────────────────────────────────────────────
    # Fonts
    # ──────────────────────────────────────────────

    def _load_fonts(self):
        scale = min(self.win_w / WINDOW_WIDTH, self.win_h / WINDOW_HEIGHT)
        # Larger base sizes than before (user feedback: fonts too small)
        self.font_title = _load_font(max(16, int(28 * scale)), bold=True)
        self.font_med   = _load_font(max(12, int(20 * scale)), bold=True)
        self.font_small = _load_font(max(10, int(15 * scale)), bold=True)

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
            base   = (240, 242, 245)
            rim    = (200, 200, 200)
            hl_col = (255, 255, 255, 180) # Stronger white glow
            glint  = (255, 255, 255, 255)

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

        # Soft Specular Highlight (Soft glow upper-left)
        hl_r = int(radius * 0.4)
        if is_black:
            pygame.gfxdraw.filled_circle(surface, cx - int(radius * 0.3), cy - int(radius * 0.3), hl_r, (255, 255, 255, 45))
            # No micro glint for black stones (match white style)
        else:
            # Drop the strip, just an inner soft gradient feel
            pygame.gfxdraw.filled_circle(surface, cx - int(radius * 0.2), cy - int(radius * 0.2), hl_r, (255, 255, 255, 180))
            # Micro glint (core brightness)
            gr = max(1, radius // 8)
            pygame.gfxdraw.filled_circle(surface, cx - int(radius * 0.35), cy - int(radius * 0.35), gr, (255, 255, 255, 240))

        # Decay visuals
        if cracked and radius >= 6:
            self._draw_cracks(surface, cx, cy, radius, is_black)
        if age_label and radius >= 9:
            col_txt = (255, 60, 60) if is_black else (220, 30, 30)
            try:
                # Use cached font for performance
                fnt = self.font_med
                ts  = fnt.render(age_label, True, col_txt)
                surface.blit(ts, ts.get_rect(center=(cx, cy + radius // 6)))
            except Exception:
                pass

    def _draw_cracks(self, surface, cx, cy, radius, is_black):
        """Draw a single grey thunder/lightning crack on one corner."""
        col = (110, 110, 110) if is_black else (140, 140, 140)

        # Tapering crack from top-right down to center
        # Creates a thick top right origin snapping inward to thinner cracks
        thick = max(2, radius // 4)
        pts = [
            (cx + int(radius * 0.6), cy - int(radius * 0.6)),
            (cx + int(radius * 0.6) + thick, cy - int(radius * 0.6)),
            (cx + int(radius * 0.3) + thick//2, cy - int(radius * 0.1)),
            (cx + int(radius * 0.4), cy + int(radius * 0.2)),
            (cx - int(radius * 0.1), cy + int(radius * 0.5)),
            (cx + int(radius * 0.3), cy - int(radius * 0.1))
        ]
        pygame.draw.polygon(surface, col, pts)

        # Small branch
        pygame.draw.line(surface, col, (cx + int(radius * 0.3), cy - int(radius * 0.1)),
                         (cx + int(radius * 0.6), cy + int(radius * 0.4)), 1)

    # ──────────────────────────────────────────────
    # Main draw (single call per frame — one flip only)
    # ──────────────────────────────────────────────

    def draw(self, game, ai_time, mode, suggestion=None, aide_on=False,
             power_type=None, power_hover=None):
        """Render one complete frame. Includes win overlay if game is over."""
        cell, margin = self._scale()
        self._panel_x = margin + cell * (BOARD_SIZE - 1) + margin

        self.screen.fill(COLOR_BG)
        self._draw_grid(cell, margin)
        self._draw_star_points(cell, margin)

        if game.rules.shooting_star:
            self._draw_holes(game, cell, margin)

        self._draw_stones(game, cell, margin)

        if self.hover_pos and not game.is_game_over() and not power_type:
            self._draw_hover(self.hover_pos, cell)

        # Area of effect for powers
        if power_type and power_hover and not game.is_game_over():
            self._draw_power_preview(game, power_type, power_hover, cell, margin)

        if suggestion and not game.is_game_over():
            self._draw_suggestion(suggestion, cell)

        self._draw_panel(game, ai_time, mode, aide_on, power_type)

        # Win overlay rendered here (single flip, no flash)
        if game.is_game_over():
            self._draw_win_overlay(game)

        # Aide popup on board corner to avoid covering panel status text
        if self.aide_msg and pygame.time.get_ticks() < self.aide_timer:
            self._draw_aide_on_board()

        # Guide popup
        if self.guide_open and self.guide_msg:
            self._draw_guide_overlay()

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
        hints_cache = game.render_hints  # Evaluate hints once per frame
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] in (EMPTY, HOLE):
                    continue
                x = margin + c * cell
                y = margin + r * cell

                age_label = None
                cracked = False
                blip_indicator = False
                blip_highlight = False
                hints = hints_cache.get((r, c), {})
                if "cracked" in hints: cracked = True
                if "age_label" in hints: age_label = hints["age_label"]
                if "blip" in hints:
                    blip_indicator = True
                    blip_highlight = True

                self._draw_stone(self.screen, x, y, stone_r, board[r][c] == BLACK,
                                 age_label=age_label, cracked=cracked)

                if blip_indicator:
                    # Stronger highlight for blipping stones
                    for r_offset in range(2, 8):
                        color = (255, 255, 80, max(60, 180 - r_offset * 20))
                        pygame.gfxdraw.aacircle(self.screen, x, y, stone_r + r_offset, color)
                    # Pulsing outer ring
                    import math
                    pulse = int(30 * (1 + math.sin(pygame.time.get_ticks() / 200)))
                    pygame.gfxdraw.aacircle(self.screen, x, y, stone_r + 8, (255, 255, 120, 80 + pulse))

                if last_move and (r, c) == last_move:
                    dot = (160, 50, 50) if board[r][c] == BLACK else (50, 80, 200)
                    dr  = max(2, stone_r // 5)
                    pygame.gfxdraw.filled_circle(self.screen, x, y, dr, dot)

    def _draw_holes(self, game, cell, margin):
        stone_r = max(4, cell // 2 - 2)
        # Permanent holes
        for r, c in game.holes:
            x = margin + c * cell
            y = margin + r * cell
            # Light grey fill, lighter border
            pygame.gfxdraw.filled_circle(self.screen, x, y, stone_r, (180, 180, 180))
            pygame.gfxdraw.aacircle(self.screen, x, y, stone_r, (210, 210, 210))
            # Bold multiplication sign (U+2715)
            fnt = self.font_med
            cross = fnt.render("✕", True, (120, 120, 120))
            cross_rect = cross.get_rect(center=(x, y))
            self.screen.blit(cross, cross_rect)

        # Hole Forecasts: same highlight style as blipping stones, but no stone in center.
        hints_cache = game.render_hints
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                hints = hints_cache.get((r, c), {})
                if "hole_forecast" in hints:
                    rem = hints["hole_forecast"]
                    x = margin + c * cell
                    y = margin + r * cell

                    for r_offset in range(2, 8):
                        color = (255, 255, 80, max(60, 180 - r_offset * 20))
                        pygame.gfxdraw.aacircle(self.screen, x, y, stone_r + r_offset, color)

                    import math
                    pulse = int(30 * (1 + math.sin(pygame.time.get_ticks() / 200)))
                    pygame.gfxdraw.aacircle(self.screen, x, y, stone_r + 8, (255, 255, 120, 80 + pulse))

                    # Keep center empty: draw only countdown text.
                    fnt = self.font_small
                    ts = fnt.render(str(rem), True, (180, 70, 10))
                    self.screen.blit(ts, ts.get_rect(center=(x, y)))

    def _draw_power_preview(self, game, power_type, pos, cell, margin):
        row, col = pos
        x, y = margin + col * cell, margin + row * cell
        stone_r = max(4, cell // 2 - 2)

        # Center target
        pygame.gfxdraw.aacircle(self.screen, x, y, stone_r + 2, (100, 255, 100))

        opponent = WHITE if game.current_player == BLACK else BLACK
        targets = []

        if power_type == POWER_BOMB:
            col_effect = (255, 50, 50, 100)
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    r, c = row+dr, col+dc
                    if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and (r, c) not in game.holes:
                        targets.append((r, c))
        elif power_type == POWER_CROSS:
            col_effect = (50, 100, 255, 100)
            for d in [-2, -1, 1, 2]:
                for r, c in [(row+d, col), (row, col+d)]:
                    if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and (r, c) not in game.holes:
                        targets.append((r, c))
        elif power_type == POWER_DIAGONAL:
            col_effect = (200, 50, 255, 100)
            for d in [-2, -1, 1, 2]:
                for r, c in [(row+d, col+d), (row+d, col-d)]:
                    if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and (r, c) not in game.holes:
                        targets.append((r, c))

        for r, c in targets:
            tx = margin + c * cell
            ty = margin + r * cell
            s = pygame.Surface((stone_r*2, stone_r*2), pygame.SRCALPHA)
            pygame.gfxdraw.filled_circle(s, stone_r, stone_r, stone_r - 1, col_effect)
            self.screen.blit(s, (tx - stone_r, ty - stone_r))

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
    # Popups & Overlays
    # ──────────────────────────────────────────────

    def show_aide_popup(self, msg, duration_ms=2000):
        self.aide_msg = msg
        self.aide_timer = pygame.time.get_ticks() + duration_ms

    def show_guide(self, msg):
        """Display a guide message. Closes when clicking outside the box."""
        self.guide_msg = msg
        self.guide_open = True

    def close_guide(self):
        """Close the guide overlay."""
        self.guide_open = False
        self.guide_msg = ""

    def _draw_aide_on_board(self):
        """Render a solid status block at the board's bottom-right corner."""
        px = self._panel_x

        # Colors based on message
        if "UNO" in self.aide_msg:
            bg_col = (140, 20, 20)  # Deep Red
            txt_col = (255, 230, 180) # Pale Gold / Cream
        elif "Threat" in self.aide_msg or "威脅" in self.aide_msg:
            bg_col = (255, 220, 80)  # Bright Yellow-Orange
            txt_col = (120, 60, 0)   # Darker Orange text
        else:
            bg_col = (210, 180, 40)  # Muted Darker Yellow
            txt_col = (40, 40, 40)   # Dark Grey

        txt = self.font_small.render(self.aide_msg, True, txt_col)

        bw = txt.get_width() + 16
        bh = txt.get_height() + 12
        # Keep this message in board area (left of side panel), near bottom-right.
        bx = max(10, px - bw - 18)
        by = self.win_h - bh - 18
        rect = pygame.Rect(bx, by, bw, bh)

        pygame.draw.rect(self.screen, bg_col, rect, border_radius=6)

        txt = self.font_small.render(self.aide_msg, True, txt_col)
        self.screen.blit(txt, txt.get_rect(center=rect.center))

    def _draw_guide_overlay(self):
        """Render a guide overlay in the center of the screen."""
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.win_w, self.win_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Draw guide box
        box_w = min(600, self.win_w - 40)
        box_h = min(250, self.win_h - 40)
        box_x = self.win_w // 2 - box_w // 2
        box_y = self.win_h // 2 - box_h // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        # Store rect for click detection
        self._guide_overlay_rect = box_rect

        pygame.draw.rect(self.screen, (60, 50, 35), box_rect, border_radius=10)
        pygame.draw.rect(self.screen, (200, 130, 50), box_rect, 3, border_radius=10)

        # Title
        title_surf = self.font_med.render(i18n.get("guide_title"), True, (200, 130, 50))
        self.screen.blit(title_surf, (box_x + 20, box_y + 15))

        # Guide text (multiple lines if needed)
        lines = self.guide_msg.split('\n')
        y_offset = box_y + 50
        for line in lines:
            if line.strip():
                txt_surf = self.font_small.render(line, True, (230, 220, 200))
                self.screen.blit(txt_surf, (box_x + 20, y_offset))
                y_offset += txt_surf.get_height() + 8

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

    def _draw_panel(self, game, ai_time, mode, aide_on, power_type):
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

        label(f'{t("mode")}: {t("mode_" + game.rules.name)}')

        label(SEP, COLOR_ACCENT)
        label(t("captured"))
        label(f'  {t("black")}: {game.captures.get(BLACK, 0) * 2} {t("pieces")}')
        label(f'  {t("white")}: {game.captures.get(WHITE, 0) * 2} {t("pieces")}')

        if game.rules.power_stones:
            label(SEP, COLOR_ACCENT)
            p_black = game.individual_captures.get(BLACK, 0)
            p_white = game.individual_captures.get(WHITE, 0)
            # Show both players' power status in PvP
            if mode == "human":
                label(f'{t("power")} ({t("black")}): {p_black} / 5', (150, 150, 150))
                label(f'{t("power")} ({t("white")}): {p_white} / 5', (180, 180, 255))
                if p_black >= 5:
                    txt_col = (255, 255, 50) if (pygame.time.get_ticks()//200) % 2 == 0 else (200, 150, 20)
                    label(t("power_ready") + f' ({t("black")})', txt_col, self.font_title)
                if p_white >= 5:
                    txt_col = (180, 220, 255) if (pygame.time.get_ticks()//200) % 2 == 0 else (120, 180, 255)
                    label(t("power_ready") + f' ({t("white")})', txt_col, self.font_title)
            else:
                if p_black >= 5:
                    txt_col = (255, 255, 50) if (pygame.time.get_ticks()//200) % 2 == 0 else (200, 150, 20)
                    label(t("power_ready"), txt_col, self.font_title)
                    label(t("activate_right_click"), (200, 200, 200), self.font_small)
                    if power_type:
                        label(t("power_" + power_type), (150, 255, 150), self.font_small)
                else:
                    label(f'{t("power")}: {p_black} / 5', (150, 150, 150))

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

        # ---- Controls layout: Guide (top-left), Aide (bottom-left), Menu (right) ----
        panel_pad = 8
        gap = 6
        btn_h = max(30, min(40, int(self.win_h * 0.05)))
        controls_bottom = self.win_h - 60
        top_y = controls_bottom - (2 * btn_h + gap)

        full_w = pw - 2 * panel_pad
        half_w = (full_w - gap) // 2
        left_x = px + panel_pad
        right_x = left_x + half_w + gap

        # Guide Button (top-left)
        self._guide_rect = pygame.Rect(left_x, top_y, half_w, btn_h)
        g_hovered = self._guide_rect.collidepoint(pygame.mouse.get_pos())
        g_bg = (60, 80, 100) if g_hovered else (40, 55, 75)
        g_bdr = (150, 180, 220) if g_hovered else (100, 130, 160)
        pygame.draw.rect(self.screen, g_bg, self._guide_rect, border_radius=6)
        pygame.draw.rect(self.screen, g_bdr, self._guide_rect, 1, border_radius=6)
        gt = self.font_small.render(t("guide"), True, (230, 215, 185))
        # Handle Text Overflow
        if gt.get_width() > self._guide_rect.width - 10:
            gt_w = self._guide_rect.width - 10
            gt = pygame.transform.smoothscale(gt, (gt_w, gt.get_height() * gt_w // gt.get_width()))
        self.screen.blit(gt, gt.get_rect(center=self._guide_rect.center))

        # Aide Button (bottom-left)
        self._aide_rect = pygame.Rect(left_x, top_y + btn_h + gap, half_w, btn_h)
        a_hovered = self._aide_rect.collidepoint(pygame.mouse.get_pos())
        a_bg = (60, 100, 60) if aide_on else ((80, 50, 50) if a_hovered else (50, 30, 30))
        a_bdr = (100, 150, 100) if aide_on else (120, 60, 60)
        pygame.draw.rect(self.screen, a_bg, self._aide_rect, border_radius=6)
        pygame.draw.rect(self.screen, a_bdr, self._aide_rect, 1, border_radius=6)
        atxt = t("aide_on") if aide_on else t("aide_off")
        asurf = self.font_small.render(atxt, True, (240, 240, 240))
        # Handle Text Overflow
        if asurf.get_width() > self._aide_rect.width - 10:
            a_w = self._aide_rect.width - 10
            asurf = pygame.transform.smoothscale(asurf, (a_w, asurf.get_height() * a_w // asurf.get_width()))
        self.screen.blit(asurf, asurf.get_rect(center=self._aide_rect.center))

        # Menu Button (right, spans two rows)
        menu_h = 2 * btn_h + gap
        self._menu_rect = pygame.Rect(right_x, top_y, full_w - half_w - gap, menu_h)
        m_hovered = self._menu_rect.collidepoint(pygame.mouse.get_pos())
        m_bg = (110, 70, 25) if m_hovered else (70, 50, 20)
        m_bdr = (200, 140, 50) if m_hovered else (130, 95, 40)
        pygame.draw.rect(self.screen, m_bg, self._menu_rect, border_radius=6)
        pygame.draw.rect(self.screen, m_bdr, self._menu_rect, 1, border_radius=6)
        mt = self.font_med.render(t("menu"), True, (230, 215, 185))
        # Handle Text Overflow
        if mt.get_width() > self._menu_rect.width - 10:
            m_w = self._menu_rect.width - 10
            mt = pygame.transform.smoothscale(mt, (m_w, mt.get_height() * m_w // mt.get_width()))
        self.screen.blit(mt, mt.get_rect(center=self._menu_rect.center))

        # ---- Responsive hints row: N, R, Q ----
        hint_y = self.win_h - 25
        hints = [t("restart"), t("undo"), t("quit")]

        h_surfs = [self.font_small.render(txt, True, COLOR_TEXT) for txt in hints]
        total_w = sum(s.get_width() for s in h_surfs)
        available_w = pw - 2 * panel_pad

        if total_w + 20 > available_w:
            # Wrap to multiple lines if they don't fit
            curr_y = self.win_h - 45
            for s in h_surfs:
                r = s.get_rect(center=(px + pw // 2, curr_y))
                self.screen.blit(s, r)
                curr_y += s.get_height() + 2
        else:
            # Left, Center, Right aligned
            self.screen.blit(h_surfs[0], h_surfs[0].get_rect(midleft=(px + panel_pad, hint_y)))
            self.screen.blit(h_surfs[1], h_surfs[1].get_rect(center=(px + pw // 2, hint_y)))
            self.screen.blit(h_surfs[2], h_surfs[2].get_rect(midright=(px + pw - panel_pad, hint_y)))

    def _draw_lang_buttons(self, px, pw):
        """
        Draw language switcher buttons using ASCII short-names (EN/FR/ZH).
        Positioned at the top right of the application window.
        """
        langs   = i18n.LANGS
        labels  = i18n.LANG_LABELS
        n       = len(langs)
        btn_w   = max(45, min(90, (pw - 14 - (n - 1) * 5) // n))
        btn_h   = 30
        gap     = 5
        total   = n * btn_w + (n - 1) * gap
        # Top right positioning
        start_x = self.win_w - total - 20
        y       = 10

        for i, lang in enumerate(langs):
            rx   = start_x + i * (btn_w + gap)
            rect = pygame.Rect(rx, y, btn_w, btn_h)
            self._lang_rects[lang] = rect   # update every frame

            active  = (lang == i18n.current())
            hovered = rect.collidepoint(pygame.mouse.get_pos())
            bg     = COLOR_ACCENT if active else ((85, 62, 25) if hovered else (52, 38, 16))
            border = (255, 200, 80) if active else (120, 88, 38)
            pygame.draw.rect(self.screen, bg, rect, border_radius=5)
            pygame.draw.rect(self.screen, bg, rect, border_radius=6)
            pygame.draw.rect(self.screen, border, rect, 1, border_radius=6)

            # Draw Flag to match the logic in main.py
            fx, fy = rect.x + 8, rect.centery - 8
            if lang == "EN":
                pygame.draw.rect(self.screen, (200, 50, 50), (fx, fy, 22, 16))
                pygame.draw.rect(self.screen, (255, 255, 255), (fx, fy+2, 22, 3))
                pygame.draw.rect(self.screen, (255, 255, 255), (fx, fy+7, 22, 3))
                pygame.draw.rect(self.screen, (255, 255, 255), (fx, fy+12, 22, 3))
                pygame.draw.rect(self.screen, (50, 50, 150), (fx, fy, 11, 8))
            elif lang == "FR":
                pygame.draw.rect(self.screen, (40, 80, 180), (fx, fy, 7, 16))
                pygame.draw.rect(self.screen, (255, 255, 255), (fx+7, fy, 8, 16))
                pygame.draw.rect(self.screen, (220, 40, 50), (fx+15, fy, 7, 16))
            elif lang == "ZH":
                pygame.draw.rect(self.screen, (220, 30, 30), (fx, fy, 22, 16))
                pygame.draw.rect(self.screen, (30, 40, 160), (fx, fy, 11, 8))
                pygame.draw.circle(self.screen, (255, 255, 255), (fx+5, fy+4), 3)

            lsurf = self.font_small.render(labels.get(lang, lang), True, (230, 220, 200))
            self.screen.blit(lsurf, lsurf.get_rect(midleft=(fx + 28, rect.centery)))

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

    def check_aide_click(self, pos):
        """Return True if the aide button area was clicked."""
        return self._aide_rect is not None and self._aide_rect.collidepoint(pos)

    def check_guide_click(self, pos):
        """Return True if the guide button area was clicked."""
        return self._guide_rect is not None and self._guide_rect.collidepoint(pos)

    def set_status(self, msg):
        self.status_msg = msg

    def tick(self, fps=60):
        self.clock.tick(fps)
