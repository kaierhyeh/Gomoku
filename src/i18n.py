"""
i18n.py — Simple translation system for Gomoku.
Supported languages: EN (English), FR (Français), ZH (繁體中文).
"""

LANGS = ["EN", "FR", "ZH"]

# Pure ASCII labels (we will draw flags manually to guarantee visibility)
LANG_LABELS = {
    "EN": "EN",
    "FR": "FR",
    "ZH": "中文"
}

STRINGS = {
    "EN": {
        "title":        "GOMOKU",
        "mode_select":  "Select a game mode",
        "mode":         "Mode",
        "captured":     "Captured:",
        "pieces":       "pieces",
        "black":        "Black",
        "white":        "White",
        "turn":         "Turn:",
        "ai_time":      "AI Move Time:",
        "restart":      "[N] New Game",
        "undo":         "[R] Undo",
        "menu":         "[M] Menu",
        "quit":         "[Q] Quit",
        "wins":         "WINS!",
        "play_again":   "Press [N] to play again",
        "ai_thinking":  "AI is thinking...",
        "game_started": "Game started",
        "suggest":      "Suggestion shown",
        "language":     "Language",
        "power":        "Power",
        "activate_right_click": "(Right Click to Activate)",

        # New Modes & Features
        "mode_Standard":  "Standard",
        "mode_Decay":     "Decay (10 turns)",
        "mode_Power":     "Power Stones",
        "mode_Star":      "Shooting Star",
        "mode_Standard Unlimited": "Standard Unlimited",
        "mode_Everything":"Everything",
        "power_ready":    "! POWER READY !",
        "power_Bomb":     "Power: BOMB (*)",
        "power_Cross":    "Power: CROSS (+)",
        "power_Diagonal": "Power: DIAGONAL (X)",
        "aide_on":        "  AIDE: ON  ",
        "aide_off":       "   AIDE: OFF   ",
        "hole_warning":   " Meteor inbound!",
    },
    "FR": {
        "title":        "GOMOKU",
        "mode_select":  "Choisir un mode de jeu",
        "mode":         "Mode",
        "captured":     "Capturés:",
        "pieces":       "pions",
        "black":        "Noir",
        "white":        "Blanc",
        "turn":         "Tour:",
        "ai_time":      "Temps IA:",
        "restart":      "[N] Nouvelle Partie",
        "undo":         "[R] Annuler",
        "menu":         "[M] Menu",
        "quit":         "[Q] Quitter",
        "wins":         "GAGNE!",
        "play_again":   "Appuyez [N] pour rejouer",
        "ai_thinking":  "L'IA reflechit...",
        "game_started": "Partie commencee",
        "suggest":      "Suggestion affichee",
        "language":     "Langue",
        "power":        "Pouvoir",
        "activate_right_click": "(Clic droit pour activer)",

        # New Modes & Features
        "mode_Standard":  "Standard",
        "mode_Decay":     "Decadence (10 tours)",
        "mode_Power":     "Pierres de Pouvoir",
        "mode_Star":      "Etoile Filante",
        "mode_Standard Unlimited": "Standard Sans Limite",
        "mode_Everything":"Tout",
        "power_ready":    "! POUVOIR PRET !",
        "power_Bomb":     "Pouvoir: BOMBE (*)",
        "power_Cross":    "Pouvoir: CROIX (+)",
        "power_Diagonal": "Pouvoir: DIAGONALE (X)",
        "aide_on":        "  AIDE: ON  ",
        "aide_off":       "   AIDE: OFF   ",
        "hole_warning":   " Meteore en approche!",
    },
    "ZH": {
        "title":        "五子棋",
        "mode_select":  "選擇模式",
        "mode":         "模式",
        "captured":     "吃子：",
        "pieces":       "子",
        "black":        "黑",
        "white":        "白",
        "turn":         "輪到：",
        "ai_time":      "AI 思考時間：",
        "restart":      "[N] 新局",
        "undo":         "[R] 悔棋",
        "menu":         "[M] 選單",
        "quit":         "[Q] 離開",
        "wins":         "獲勝！",
        "play_again":   "按 [N] 再玩一局",
        "ai_thinking":  "AI 思考中...",
        "game_started": "遊戲開始",
        "suggest":      "建議走法已顯示",
        "language":     "語言",
        "power":        "技能",
        "activate_right_click": "（右鍵啟用）",

        # New Modes & Features
        "mode_Standard":  "標準模式",
        "mode_Decay":     "風化模式 (10回合)",
        "mode_Power":     "超能石模式",
        "mode_Star":      "流星模式",
        "mode_Standard Unlimited": "標準無限制模式",
        "mode_Everything":"大亂鬥模式",
        "power_ready":    "! 技能就緒 !",
        "power_Bomb":     "技能: 炸彈 (*)",
        "power_Cross":    "技能: 十字 (+)",
        "power_Diagonal": "技能: 斜角 (X)",
        "aide_on":        "  輔助: 開啟  ",
        "aide_off":       "   輔助: 關閉   ",
        "hole_warning":   " 流星接近中!",
    },
}

_current = "EN"


def get(key):
    """Return the translated string for the current language."""
    return STRINGS.get(_current, STRINGS["EN"]).get(key, key)


def set_lang(lang):
    global _current
    if lang in STRINGS:
        _current = lang


def cycle():
    """Cycle to the next language."""
    global _current
    idx = LANGS.index(_current) if _current in LANGS else 0
    _current = LANGS[(idx + 1) % len(LANGS)]


def current():
    return _current
