"""
i18n.py — Simple translation system for Gomoku.
Supported languages: EN (English), FR (Français), ZH (繁體中文).
"""

LANGS = ["EN", "FR", "繁中"]

# Short ASCII labels used on buttons (fonts may not support CJK glyphs)
LANG_LABELS = {"EN": "EN", "FR": "FR", "繁中": "ZH"}

STRINGS = {
    "EN": {
        "title":        "GOMOKU",
        "mode_select":  "Select a game mode",
        "vs_ai":        "Human vs AI",
        "vs_human":     "Human vs Human",
        "mode":         "Mode",
        "captured":     "Captured pairs:",
        "black":        "Black",
        "white":        "White",
        "turn":         "Turn:",
        "ai_time":      "AI Move Time:",
        "restart":      "[R] Restart",
        "menu":         "[M] Menu",
        "quit":         "[Q] Quit",
        "wins":         "WINS!",
        "play_again":   "Press [R] to play again",
        "ai_thinking":  "AI is thinking...",
        "game_started": "Game started",
        "suggest":      "Suggestion shown",
        "language":     "Language",
    },
    "FR": {
        "title":        "GOMOKU",
        "mode_select":  "Choisir un mode de jeu",
        "vs_ai":        "Humain vs IA",
        "vs_human":     "Humain vs Humain",
        "mode":         "Mode",
        "captured":     "Paires capturees:",
        "black":        "Noir",
        "white":        "Blanc",
        "turn":         "Tour:",
        "ai_time":      "Temps IA:",
        "restart":      "[R] Rejouer",
        "menu":         "[M] Menu",
        "quit":         "[Q] Quitter",
        "wins":         "GAGNE!",
        "play_again":   "Appuyez [R] pour rejouer",
        "ai_thinking":  "L'IA reflechit...",
        "game_started": "Partie commencee",
        "suggest":      "Suggestion affichee",
        "language":     "Langue",
    },
    "繁中": {
        "title":        "五目棋",
        "mode_select":  "選擇遊戲模式",
        "vs_ai":        "人類 vs AI",
        "vs_human":     "人類 vs 人類",
        "mode":         "模式",
        "captured":     "吃子對數：",
        "black":        "黑方",
        "white":        "白方",
        "turn":         "輪到：",
        "ai_time":      "AI 思考時間：",
        "restart":      "[R] 重新開始",
        "menu":         "[M] 選單",
        "quit":         "[Q] 離開",
        "wins":         "獲勝！",
        "play_again":   "按 [R] 再玩一局",
        "ai_thinking":  "AI 思考中...",
        "game_started": "遊戲開始",
        "suggest":      "建議走法已顯示",
        "language":     "語言",
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
