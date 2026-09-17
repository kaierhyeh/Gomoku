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
        "guide":        "[G] Guide",
        "menu":         "[M] Menu",
        "quit":         "[Q] Quit",
        "wins":         "WINS!",
        "play_again":   "Press [N] to play again",
        "ai_thinking":  "AI is thinking...",
        "game_started": "Game started",
        "suggest":      "Suggestion shown",
        "language":     "Language",
        "power":        "Power",
        "activate_right_click": "(Right Click / Tab: Activate)",
        "cycle_hint":           "(Wheel / Tab / 1-3: Switch)",

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
        # Warnings
        "warn_occupied":      "Position already occupied",
        "warn_double_three":  "Forbidden: Double Free-Three!",
        "warn_ai_thinking":   "AI is thinking, please wait...",
        "warn_not_your_turn": "Not your turn yet",
        "warn_game_over":     "Game over, press [N] for new game",
        "warn_hole_forecast": "Meteor forecast zone!",
        "warn_meteor_crater": "Crater hole blocked!",
        "guide_title":    "Game Mode Guide",
        "guide_close":    "[Click outside or press G to close]",
        "guide_Standard": (
            "[Standard Rules (42 Subject)]\n"
            "• Win Conditions:\n"
            "  - Align 5 consecutive stones of your color, OR\n"
            "  - Capture 10 opponent stones (5 pairs).\n"
            "• Custodian Capture Rule:\n"
            "  - Flank a pair of opponent stones between two of your stones:\n"
            "    e.g., [X] [O] [O] [X] -> the two [O] stones are captured and removed!\n"
            "  - Only exact pairs of 2 stones can be captured (never 1, never 3+).\n"
            "  - Moving between opponent stones does NOT capture yourself.\n"
            "• Double Free-Three (Double-Three) Restriction:\n"
            "  - Creating two simultaneous free-threes is strictly forbidden.\n"
            "  - Exception: Legal if the move also performs a capture!\n"
            "• Endgame Capture (Breaking 5-in-a-Row):\n"
            "  - Aligning 5 stones only wins if the opponent cannot break the line\n"
            "    by capturing a pair from it, or counter-win with their 10th capture.\n"
            "  - If opponent has no such counter, the 5-in-a-row wins immediately."
        ),
        "guide_Decay": (
            "[Decay Mode]\n"
            "• Stone Lifespan:\n"
            "  - Every stone placed has a limited lifespan of 10 turns.\n"
            "  - Stones gradually age and fade, vanishing when expired!\n"
            "• Tactical Tip:\n"
            "  - Strike swiftly before your constructed winning lines dissolve!"
        ),
        "guide_Power": (
            "[Power Stones Mode]\n"
            "• Unlock Super Powers:\n"
            "  - Capture 5 individual stones to unlock devastating abilities!\n"
            "• Controls & Switching:\n"
            "  - Right-Click: Toggle activate / cancel current power.\n"
            "  - Mouse Wheel or Tab: Cycle through available powers.\n"
            "  - Keys [1], [2], [3]: Select a power directly.\n"
            "• Power Arsenal:\n"
            "  - [1] 💣 Bomb (*): Blasts a 3x3 square, clearing all stones & craters.\n"
            "  - [2] ➕ Cross (+): Clears enemy stones along cross lines (range 2).\n"
            "  - [3] ✖️ Diagonal (X): Clears enemy stones along diagonals (range 2)."
        ),
        "guide_Star": (
            "[Shooting Star Mode]\n"
            "• Cosmic Events:\n"
            "  - Every few turns, a shooting star impacts at random locations!\n"
            "• Impact Types:\n"
            "  - 🕳️ Meteor Crater: Blasts a hole blocking stone placement.\n"
            "    (Can be repaired by placing a stone directly onto it).\n"
            "  - 💫 Color-Flip Stone: A volatile cosmic stone that periodically\n"
            "    inverts its own color (Black ↔ White) every 3 turns!"
        ),
        "guide_Standard Unlimited": (
            "[Standard Unlimited Mode]\n"
            "• Objective:\n"
            "  - Align 5 stones in a row or capture 10 opponent stones.\n"
            "• Unlimited Rules:\n"
            "  - Classic Gomoku without the Double Free-Three restriction.\n"
            "  - Freely place stones and create open threes without penalties."
        ),
        "guide_Everything": (
            "[Everything Mode (Chaos Battle)]\n"
            "• The Ultimate Gomoku Showdown!\n"
            "  All special mechanics are simultaneously active:\n"
            "  1. 🪫 Decay: Stones fade and vanish after 10 turns.\n"
            "  2. 🪄 Power Stones: Capture 5 stones to unlock Bomb, Cross & Diag!\n"
            "  3. 🌠 Shooting Star: Meteors create craters & color-flipping stones!\n"
            "• Tactical Tip:\n"
            "  - Balance rapid attacks, power stones, and vanishing chains to win!"
        ),
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
        "restart":      "[N] Nouveau Jeu",
        "undo":         "[R] Annuler",
        "guide":        "[G] Guide",
        "menu":         "[M] Menu",
        "quit":         "[Q] Quitter",
        "wins":         "GAGNE!",
        "play_again":   "Appuyez [N] pour rejouer",
        "ai_thinking":  "L'IA reflechit...",
        "game_started": "Partie commencee",
        "suggest":      "Suggestion affichee",
        "language":     "Langue",
        "power":        "Pouvoir",
        "activate_right_click": "(Clic droit / Tab: Activer)",
        "cycle_hint":           "(Molette / Tab / 1-3: Changer)",

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
        # Warnings
        "warn_occupied":      "Case déjà occupée",
        "warn_double_three":  "Interdit : Double-trois libre !",
        "warn_ai_thinking":   "L'IA réfléchit, veuillez patienter...",
        "warn_not_your_turn": "Ce n'est pas votre tour",
        "warn_game_over":     "Partie terminée, appuyez sur [N]",
        "warn_hole_forecast": "Zone d'impact de météore !",
        "warn_meteor_crater": "Cratère de météore bloqué !",
        "guide_title":    "Guide des Modes",
        "guide_close":    "[Cliquer à l'extérieur ou appuyer sur G pour fermer]",
        "guide_Standard": (
            "[Règles Standard (Sujet 42)]\n"
            "• Conditions de Victoire :\n"
            "  - Aligner 5 pierres consécutives de votre couleur, OU\n"
            "  - Capturer 10 pierres adverses (5 paires).\n"
            "• Règle de Capture (Prise par Encadrement) :\n"
            "  - Encadrez exactement une paire ennemie entre deux de vos pierres :\n"
            "    ex. [X] [O] [O] [X] -> les deux pierres [O] sont capturées et retirées !\n"
            "  - Seules les paires exactes de 2 pierres peuvent être capturées.\n"
            "  - Se poser volontairement entre deux pierres ennemies ne vous capture pas.\n"
            "• Règle des Deux Trois Libres (Double-Trois) :\n"
            "  - Il est interdit de poser une pierre créant deux trois libres simultanés.\n"
            "  - Exception : Coup autorisé s'il réalise une capture en même temps !\n"
            "• Capture de Fin de Partie (Casser le 5-en-Ligne) :\n"
            "  - Aligner 5 pierres ne gagne que si l'adversaire ne peut pas le casser\n"
            "    en capturant une paire, ou contre-attaquer avec sa 10e pierre.\n"
            "  - Sans contre-attaque possible, la victoire est immédiate."
        ),
        "guide_Decay": (
            "[Mode Décadence]\n"
            "• Durée de Vie des Pierres :\n"
            "  - Chaque pierre posée a une durée de vie limitée à 10 tours.\n"
            "  - Les pierres vieillissent et disparaissent automatiquement !\n"
            "• Conseil Tactique :\n"
            "  - Attaquez vite avant que vos alignements gagnants ne s'effacent !"
        ),
        "guide_Power": (
            "[Mode Pierres de Pouvoir]\n"
            "• Déblocage des Compétences :\n"
            "  - Capturez 5 pierres pour débloquer des super pouvoirs !\n"
            "• Commandes & Changement :\n"
            "  - Clic droit : Activer / annuler le pouvoir sélectionné.\n"
            "  - Molette ou Tab : Faire défiler les pouvoirs disponibles.\n"
            "  - Touches [1], [2], [3] : Sélectionner directement un pouvoir.\n"
            "• Arsenal de Pouvoirs :\n"
            "  - [1] 💣 Bombe (*) : Détruit un carré 3x3 (pierres et cratères).\n"
            "  - [2] ➕ Croix (+) : Élimine les pierres ennemies en croix (portée 2).\n"
            "  - [3] ✖️ Diagonale (X) : Élimine les pierres ennemies en diagonale (portée 2)."
        ),
        "guide_Star": (
            "[Mode Étoile Filante]\n"
            "• Événements Cosmiques :\n"
            "  - Des étoiles filantes s'écrasent régulièrement sur le plateau !\n"
            "• Types d'Impacts :\n"
            "  - 🕳️ Cratère de Météore : Crée un trou infranchissable.\n"
            "    (Peut être réparé en y posant une pierre directement).\n"
            "  - 💫 Pierre d'Inversion : Une pierre cosmique instable qui inverse\n"
            "    sa propre couleur (Noir ↔ Blanc) tous les 3 tours !"
        ),
        "guide_Standard Unlimited": (
            "[Mode Standard Sans Limite]\n"
            "• Objectif :\n"
            "  - Aligner 5 pierres ou capturer 10 pierres adverses.\n"
            "• Règles Sans Limite :\n"
            "  - Gomoku classique sans restriction de Double-Trois libre.\n"
            "  - Posez librement vos pierres sans pénalité de coup interdit."
        ),
        "guide_Everything": (
            "[Mode Tout (Bataille Chaotique)]\n"
            "• L'Épreuve Ultime de Gomoku !\n"
            "  Toutes les mécaniques spéciales sont actives en même temps :\n"
            "  1. 🪫 Décadence : Les pierres s'effacent après 10 tours.\n"
            "  2. 🪄 Pierres de Pouvoir : 5 captures débloquent Bombe, Croix & Diag !\n"
            "  3. 🌠 Étoile Filante : Cratères de météores et pierres qui changent de couleur !\n"
            "• Conseil Tactique :\n"
            "  - Jonglez entre attaques vives, pouvoirs et pierres éphémères pour vaincre !"
        ),
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
        "guide":        "[G] 新手指南",
        "menu":         "[M] 選單",
        "quit":         "[Q] 離開",
        "wins":         "獲勝！",
        "play_again":   "按 [N] 再玩一局",
        "ai_thinking":  "AI 思考中...",
        "game_started": "遊戲開始",
        "suggest":      "建議走法已顯示",
        "language":     "語言",
        "power":        "技能",
        "activate_right_click": "（右鍵或按 Tab 啟用）",
        "cycle_hint":           "（滾輪 / Tab / 1-3 切換）",

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
        # Warnings
        "warn_occupied":      "此處已有棋子！",
        "warn_double_three":  "禁手：雙活三限制！",
        "warn_ai_thinking":   "AI 思考中，請稍候...",
        "warn_not_your_turn": "尚未輪到您的回合！",
        "warn_game_over":     "對局已結束，請按 [N] 新局",
        "warn_hole_forecast": "流星撞擊預測區！",
        "warn_meteor_crater": "隕石坑洞無法直接落子！",
        "guide_title":    "遊戲模式指南",
        "guide_close":    "（點擊任意處或按 G 鍵關閉）",
        "guide_Standard": (
            "[標準模式規則（42 官方規範）]\n"
            "• 獲勝條件：\n"
            "  - 連續連成 5 顆同色棋子，或\n"
            "  - 吃掉對手 10 顆棋子（累計 5 對）。\n"
            "• 夾吃吃子規則（Custodian Capture）：\n"
            "  - 用兩顆己方棋子緊緊夾住對手的「恰好一對（2顆）」棋子：\n"
            "    例如：[黑] [白] [白] [黑] -> 兩顆被夾住的 [白] 棋將被吃掉並移出棋盤！\n"
            "  - 每次只能夾吃 2 顆（單顆或 3 顆以上無法被吃）。\n"
            "  - 自己主動走進對手兩子之間不會被吃。\n"
            "• 雙活三禁手（雙三限制）：\n"
            "  - 嚴禁一手棋同時形成兩個活三（兩端皆有成五空間的連續或跳三）。\n"
            "  - 豁免條款：若該步伴隨吃子，則不受雙三禁手限制！\n"
            "• 終局破五連（吃子反殺機制）：\n"
            "  - 連成五子時，若對手下一步能藉由夾吃破壞五連線，或藉此吃滿 10 子反殺，\n"
            "    對局將保留一步給對手防守反擊；若對手無法反制，則連五方立即獲勝。"
        ),
        "guide_Decay": (
            "[風化模式]\n"
            "• 棋子壽命限制：\n"
            "  - 盤面上落下的每顆棋子皆有 10 回合的有效壽命。\n"
            "  - 棋子會隨著時間逐漸風化褪色，到達 10 回合後會自動從棋盤上消失！\n"
            "• 戰術提示：\n"
            "  - 把握進攻節奏，若拖延太久，已構建的連線優勢將化為烏有！"
        ),
        "guide_Power": (
            "[超能石模式]\n"
            "• 技能解鎖：\n"
            "  - 累計吃掉 5 顆棋子，即可解鎖威力強大的超能技能！\n"
            "• 操作與切換方式：\n"
            "  - 滑鼠右鍵：切換啟用 / 取消當前選取的技能。\n"
            "  - 滑鼠滾輪 或 Tab 鍵：循環切換不同的超能技能。\n"
            "  - 數字鍵 [1]、[2]、[3]：直接選取對應技能。\n"
            "• 技能效果清單：\n"
            "  - [1] 💣 炸彈 (*)：引爆 3×3 範圍，摧毀內部所有棋子與隕石坑。\n"
            "  - [2] ➕ 十字 (+)：摧毀十字方向距離 2 範圍內的所有敵方棋子。\n"
            "  - [3] ✖️ 斜向 (X)：摧毀對角方向距離 2 範圍內的所有敵方棋子。"
        ),
        "guide_Star": (
            "[流星模式]\n"
            "• 天體隨機事件：\n"
            "  - 每隔數個回合，天外流星將隨機劃破天際撞擊棋盤！\n"
            "• 撞擊產物類型：\n"
            "  - 🕳️ 隕石坑：在落點形成無法直接通行的凹坑（可透過主動落子填補修復）。\n"
            "  - 💫 變色石：不穩定的星石，每隔 3 回合會變換黑白顏色！"
        ),
        "guide_Standard Unlimited": (
            "[標準無限制模式]\n"
            "• 獲勝目標：\n"
            "  - 連成 5 顆同色棋子，或吃掉對手 10 顆棋子。\n"
            "• 無限制規則特性：\n"
            "  - 回歸最純粹的五子棋對弈，完全移除「雙活三（雙三）」禁手限制！\n"
            "  - 您可以不受拘束自由落子，隨意構造雙活三進行多線進攻。"
        ),
        "guide_Everything": (
            "[大亂鬥模式（終極混戰）]\n"
            "• 五子棋的終極極限對決！\n"
            "  三大特殊機制在棋盤上同時全面啟用：\n"
            "  1. 🪫 風化機制：每顆落下的棋子在 10 回合後會自動消散。\n"
            "  2. 🪄 超能石機制：吃滿 5 顆子可解鎖使用炸彈 (*)、十字 (+) 與斜向 (X) 毀滅技能！\n"
            "  3. 🌠 流星機制：宇宙天體隨機墜落，砸出隕石坑或落下變色石！\n"
            "• 戰術提示：\n"
            "  - 在瞬息萬變的棋盤上，必須同時兼顧快速進攻、技能釋放與消失時間才能存活獲勝！"
        ),
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
