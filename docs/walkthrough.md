# Gomoku Walkthrough

<p align="right">
  <a href="#gomoku-專案導讀">
    <img src="https://img.shields.io/badge/中文-sienna?style=for-the-badge" />
  </a>
</p>

This document provides a comprehensive walkthrough of the Gomoku project, designed to help readers understand the system from the ground up: 42 Subject specifications, core architecture, algorithmic foundations, code reading order, and defense evaluation prep.

---

## 0. Language Choice & Project Architecture

This project is implemented in **Python 3 + Pygame**.

| Language | GUI | AI Performance | Dev Speed | Verdict |
|---|---|---|---|---|
| **Python + Pygame** | ✅ Cross-platform | ⭐⭐ | ⭐⭐⭐ | **Best balance of speed and quality** |
| **C++ + SFML** | ✅ High performance | ⭐⭐⭐ | ⭐ | Stronger raw speed but significantly higher development cost |

> **💡 Defense answer**: "The 42 Subject allows any programming language and GUI library. While Python has slower raw loop execution than C++, we met the mandatory requirements (Depth $\ge 10$ in $<0.5\text{s}$) entirely through algorithmic breakthroughs: Adaptive Forward Pruning, PV-Move ordering, and Zobrist Hashing."

### Project Structure

```
~/5eyes
├── Gomoku                        # Launcher script
├── Makefile                      # Make run / test targets
├── README.md                     # Project overview and quick start
├── docs/
│   ├── walkthrough.md            # Comprehensive project walkthrough & architecture
│   └── PATCH_NOTES.md            # Development history & release changelog
├── tests/
│   └── test_rules_and_bugs.py   # 20 automated unit tests
└── src/
    ├── main.py                   # Main loop, mode selection & event dispatch
    ├── config/                   # Constants (game.py, ai.py, ui.py, bonus.py)
    ├── core/                     # Game engine (game.py, state.py, modifiers.py)
    ├── rules/                    # Ruleset & validation (rules.py, bonus.py)
    ├── ai/                       # Search & heuristics (ai.py, heuristic.py)
    └── ui/                       # GUI & localization (gui.py, i18n.py)
```

---

## 1. Game Rules & 42 Subject Compliance

### A. Win Conditions
1. **Five-in-a-row**: Five or more consecutive stones of your color aligned horizontally, vertically, or diagonally.
2. **10 Captures (5 Pairs)**: Accumulating 5 captured pairs (10 stones total) wins immediately.

### B. Custodian Capture (`X O O X`)
- A pair of opponent stones is captured when flanked on both sides by the player's stones in a straight line (`[X] [O] [O] [X]`).
- Only **exact pairs of 2 stones** can be captured (never singles, never 3+).
- **No Self-Capture**: Voluntarily moving between two opponent stones (`[O] [X] [O]`) does NOT result in capture.

### C. Double Free-Three (Forbidden Move)
- A move creating two simultaneous **Free-Threes** (alignments of 3 stones with open ends capable of becoming an open four) is strictly illegal.
- **Broken Threes**: Both continuous (`. . X X X .`, `. X X X . .`) and broken threes (`. X . X X .`, `. X X . X .`) qualify as free-threes.
- **Capture Exception (Subject Mandatory)**: *It is not forbidden to introduce a double-three by capturing a pair.* If the move makes a capture, it is completely legal.

### D. Endgame Capture (Breaking 5-in-a-Row)
- A player who lines up 5 stones wins **only if the opponent cannot break this line by capturing a pair**.
- If the player has already lost 4 pairs (8 stones) and the opponent can capture their 5th pair, the opponent wins by capture counter-attack.
- **State Machine Implementation**:
  - When 5 stones are aligned, `Game._can_opponent_break_or_win` checks if any opponent capture can break the line or hit 10 captures.
  - If no counter is possible, win is awarded immediately.
  - If a counter is possible, `pending_win` is set, giving the opponent exactly one turn to respond. If the opponent fails to break it, the 5-in-a-row player wins.

---

## 2. AI Search Engine: Depth 10 in $<0.5\text{s}$

The 42 Subject strictly specifies:
> *"To fully validate the project, your AI must search at least 10 levels deep in its game tree. ... if your AI takes more than half a second (in average) to find a move, you will not validate the project."*

### The Challenge
Pure Python Minimax with ~30 candidate moves per node faces $30^{10} \approx 5.9 \times 10^{14}$ states, which would take hours.

### Algorithmic Solution & Optimizations

```
Root (Depth 10) ──> PV Move Searched First ──> Top 12 Candidates
   └── Depth 8-9: Top 5 Candidates
         └── Depth 6-7: Top 4 Candidates
               └── Depth 4-5: Top 3 Candidates
                     └── Depth 1-3: Top 2 Candidates (Forcing Moves: 1-2 only)
```

1. **Adaptive Forward Pruning**:
   - Instead of searching all candidates in deep plies, we dynamically prune candidates down to the top 2–5 most promising moves based on quick heuristic scores.
   - Forcing moves (threats $\ge$ `SCORE["OPEN_FOUR"]` or wins $\ge$ `SCORE["FIVE"]`) collapse the search to only the 1–2 mandatory responses.
   - Reduces visited nodes from 300,000+ down to ~1,500–3,000 nodes.
2. **PV-Move (Principal Variation) Priority**:
   - In Iterative Deepening (depths 2, 4, 6, 8, 10), the best move identified in the previous iteration is placed at the very front of the next search (`score += 1_000_000_000`).
   - This produces immediate Alpha-Beta cutoffs across the entire tree.
3. **Zobrist Hashing (Transposition Table)**:
   - 64-bit random XOR hashes cache board state evaluations, preventing redundant evaluations across transpositions.
4. **Candidate Move Radius**:
   - Only empty cells within radius 1–2 of existing stones are evaluated, slashing branching factor from 361 to ~20–35.
5. **Illegal Move Simulation Guard**:
   - When simulating in Minimax, `if not sim.place_stone(row, col, curr): continue` cleanly discards forbidden moves (double-threes, occupied cells).
6. **Transparent Depth Display**:
   - The status bar displays real-time search depth and duration: e.g. `AI (8,8) 0.450s (d=10)`.
   - Tested performance: **0.25s – 0.45s average search time at Depth 10**.

---

## 3. Heuristic Evaluation Function

The board evaluation is calculated at leaf nodes as:
$$\text{Board Score} = \text{Evaluate}(\text{AI}) - \text{Evaluate}(\text{Opponent})$$

### Pattern Scoring Weights

| Pattern | Description | Score Weight |
|---|---|---|
| **FIVE** | Win condition (5+ in a row) | 1,000,000 |
| **OPEN_FOUR** | 4 stones, both ends open (unblockable) | 100,000 |
| **CLOSED_FOUR** | 4 stones, one end blocked (must block) | 10,000 |
| **OPEN_THREE** | 3 stones, both ends open | 5,000 |
| **CLOSED_THREE**| 3 stones, one end blocked | 500 |
| **OPEN_TWO** | 2 stones, both ends open | 100 |

### Move Ordering Heuristics (`quick_score_move`)
- **End-Point Verification (`open_ends`)**: Accurately differentiates Open Four from Closed Four, and ignores fully blocked lines (score 0).
- **Capture Scoring**:
  - Offensive capture: +25,000 per pair (reaching 5 pairs awards instant win score).
  - Defensive block: +20,000 per pair (blocking opponent's 5th pair awards mandatory defense score).

---

## 4. Special Modes & Power Stones

| Mode | Mechanic |
|---|---|
| **Standard** | Official 42 Subject rules (double-three restriction + capture win + breaking 5). |
| **Decay** | Stones have a 10-turn lifespan; older stones fade and vanish. |
| **Power Stones** | Capturing 5 stones unlocks super powers. |
| **Shooting Star** | Random meteor strikes create craters (holes) or color-flip stones. |
| **Standard Unlimited** | Classic Gomoku without double-three restrictions. |
| **Everything** | Chaos mode combining Decay + Power Stones + Shooting Star. |

### Power Stones Controls
- **Activate / Cancel**: Right-Click on board.
- **Switch Powers**:
  - Mouse Scroll Wheel (`pygame.MOUSEWHEEL`).
  - **`Tab`** key: Cycle through powers.
  - Number keys **`1`**, **`2`**, **`3`**: Direct selection (1: 💣 Bomb 3x3, 2: ➕ Cross range 2, 3: ✖️ Diagonal range 2).

---

## 5. Code Reading Guide

When presenting during defense, guide the examiner through the codebase in this order:

1. **`src/config/game.py` & `ai.py`**: Constants, board size (19x19), `MAX_DEPTH = 10`, `AI_TIME_LIMIT = 0.45s`, pattern scores.
2. **`src/rules/rules.py`**: 6-cell sliding window for continuous & broken double-threes, `would_capture` exemption, and 5-in-a-row detection.
3. **`src/core/game.py`**: Move placement, custodian capture execution, and `_can_opponent_break_or_win` endgame break state machine.
4. **`src/ai/heuristic.py`**: `evaluate_board` and `quick_score_move` with open-ends and capture bonuses.
5. **`src/ai/ai.py`**: Depth 10 Minimax, adaptive forward pruning, PV-move ordering, and Zobrist hash table.
6. **`src/ui/gui.py` & `src/main.py`**: Pygame renderer, responsive guide overlay (`[G]`), threat alerts (`UNO!`), and main event loop.

---

## 6. Threat Alert System (UNO / Threat)

The Aide feature provides real-time tactical warnings:
- **UNO**: Immediate win threat (opponent has an open four or winning move).
- **Threat**: Strong threat detected (opponent has an open three or dangerous capture).
- Displayed at the bottom-right of the board so it never covers the status bar.

---

## 7. Automated Testing & Verification

Run the comprehensive unit test suite:
```bash
python3 -m unittest -v tests/test_rules_and_bugs.py
```
**Results (20/20 tests passing)**:
- `test_ai_reaches_depth_10`: Verifies AI reaches Depth 10 under 0.5s.
- `test_double_free_three_*`: Continuous, broken, obstructed, and capture exception.
- `test_endgame_capture_*`: Counter break, counter fail, immediate win, 10th stone win.
- `test_heuristic_*`: Open ends and capture scoring.
- `test_power_bomb_cleans_holes`: State synchronization.
- `test_get_move_error_diagnostics`: Illegal move diagnostic error reporting.
- `test_quick_score_hierarchy`: Strict priority (Immediate win > Urgent defense > Line score).
- `test_ai_blocks_open_four_*`: Tactical defense against opponent 4-in-a-row threats.
- `test_hint_strings_integrity`: Multi-language shortcut hint string format.

---

<br/>

---

<br/>

<p align="right">
  <a href="#gomoku-walkthrough">
    <img src="https://img.shields.io/badge/-TOP-sienna?style=for-the-badge" />
  </a>
</p>

# Gomoku 專案導讀

這份文件為 Gomoku 專案的完整技術導讀手冊，旨在帶領讀者由淺入深通盤理解本專案：從 42 Subject 題目規範、核心架構、演算法理論、啟發式函數設計、代碼閱讀順序，到特殊模式與評測問答。

---

## 0. 語言選擇與架構概覽

本專案採用 **Python 3 + Pygame** 實作。

| 語言 | GUI 支援 | AI 效能 | 開發速度 | 綜合評估 |
|---|---|---|---|---|
| **Python + Pygame** | ✅ 原生跨平台 | ⭐⭐ | ⭐⭐⭐ | **整體開發與調試效率最優** |
| **C++ + SFML** | ✅ 高效能 | ⭐⭐⭐ | ⭐ | 執行速度極快但開發維護成本高 |

> **💡 Defense 對答**：「Subject 允許自由選擇語言與 GUI 庫。雖然純 Python 的迴圈效能較 C++ 慢，但我們藉由嚴謹的演算法突破（自我調整前向剪枝、主要變例 PV 排序、Zobrist 雜湊快取），成功在 0.45 秒內完成 10 層搜尋，完全達到 42 的強制規範。」

### 專案模組架構

```
~/5eyes
├── Gomoku                        # 啟動腳本
├── Makefile                      # 構建與測試指令
├── README.md                     # 專案簡介與快速開始
├── docs/
│   ├── walkthrough.md            # 專案導讀與架構走讀手冊
│   └── PATCH_NOTES.md            # 版本演進與補丁歷程
├── tests/
│   └── test_rules_and_bugs.py   # 20 項自動化單元測試
└── src/
    ├── main.py                   # 遊戲主迴圈、模式切換與事件分發
    ├── config/                   # 靜態常數 (game.py, ai.py, ui.py, bonus.py)
    ├── core/                     # 遊戲核心引擎 (game.py, state.py, modifiers.py)
    ├── rules/                    # 棋規判斷邏輯 (rules.py, bonus.py)
    ├── ai/                       # AI 搜尋與評估 (ai.py, heuristic.py)
    └── ui/                       # 繪圖渲染與多語系 (gui.py, i18n.py)
```

---

## 1. 遊戲棋規與 42 Subject 合規細節

### A. 勝利條件
1. **五子連珠**：水平、垂直或對角線形成連續 5 顆（或以上）己方棋子。
2. **吃滿 10 子（5 對）**：累計夾吃對手 5 對棋子即刻獲勝。

### B. 夾吃機制 (Custodian Capture `X O O X`)
- 己方兩顆棋子夾住對手「**恰好一對（連續 2 顆）**」棋子，該對敵子被移出棋盤。
- 每次只能夾吃 2 顆（單顆或 3 顆以上無法被吃）。
- **無主動自吃**：自己主動走進對手兩子之間不會被吃。

### C. 雙活三禁手 (Double Free-Three)
- 嚴禁一手棋同時形成兩個**活三**（兩端皆有成五空間的連續三或跳三）。
- **跳活三支援**：透過 6 格滑動視窗比對，涵蓋連續活三（`. . X X X .`）與跳活三（`. X . X X .`、`. X X . X .`）。
- **吃子豁免條款（Subject 強制要求）**：*It is not forbidden to introduce a double-three by capturing a pair.* 若該步伴隨吃子，不受雙活三禁手限制。

### D. 終局吃子破五連 (Endgame Capture)
- 當一方連成五子時，若對手**下一步能透過夾吃破壞此五連線**，該五連不立刻結算為勝利。
- 若連五方已被吃 4 對子，且對手下一步能吃到第 5 對（湊滿 10 子反殺），對手具備吃子反勝機會。
- **狀態機機制**：
  - 連五成立時，調用 `_can_opponent_break_or_win` 檢測對手反制機會。
  - 若對手無任何破線或反殺走法，連五方**即刻獲勝**。
  - 若對手存在反制可能，設置 `pending_win`，保留對手一步反擊機會。對手成功破線則對局繼續；未破線則結算連五方獲勝。

---

## 2. AI 搜尋引擎：深度 10 且耗時 $<0.5\text{s}$

42 官方手冊明確要求：
> *"To fully validate the project, your AI must search at least 10 levels deep in its game tree. ... if your AI takes more than half a second (in average) to find a move, you will not validate the project."*

### 核心演算法架構

```
根節點 (Depth 10) ──> PV Move 最優先 ──> 保留前 12 個候選走法
   └── Depth 8-9: 保留前 5 個高威脅走法
         └── Depth 6-7: 保留前 4 個走法
               └── Depth 4-5: 保留前 3 個走法
                     └── Depth 1-3: 保留前 2 個走法 (致勝/威脅手: 僅搜尋 1-2 個強制應手)
```

1. **自我調整前向剪枝 (Adaptive Forward Pruning)**：
   - 深層搜尋時依啟發分數將候選走法收斂至前 2～5 個，避免分支係數爆炸。
   - 若偵測到立即致勝手（$\ge$ `SCORE["FIVE"]`）或重大威脅（$\ge$ `SCORE["OPEN_FOUR"]`），僅搜尋該 1～2 個強制應手。
   - 將博弈樹節點總數自 30 萬+ 壓制在 **1,500～3,000 個**。
2. **PV-Move (主要變例) 優先排序**：
   - 迭代加深在邁入下一輪深度時，將上一輪評估出的最優走法（PV Move）賦予超高分數置於首位，產生極致的 Alpha-Beta 剪枝效應。
3. **Zobrist 雜湊 (Transposition Table)**：
   - 64-bit 隨機 XOR 雜湊快取盤面狀態，完全避免重複評估對稱或同形盤面。
4. **鄰角候選過濾**：
   - 僅搜尋現有棋子半徑 1～2 範圍內的空位，候選步數由 361 驟降至 ~20–35。
5. **違法步模擬防護**：
   - 模擬下子時嚴格加入 `if not sim.place_stone(row, col, curr): continue`，杜絕禁手或無效狀態進入搜尋樹。
6. **真實搜尋深度透明顯示**：
   - 狀態列即時顯示實際到達深度：例如 `AI (8,8) 0.450s (d=10)`。
   - 實測每手平均耗時：**0.25 秒～0.45 秒完成 10 層搜尋**。

---

## 3. 啟發式評估函數設計

葉節點評估公式：
$$\text{Board Score} = \text{Evaluate}(\text{AI}) - \text{Evaluate}(\text{Opponent})$$

### 棋型權重表

| 棋型 | 描述 | 權重分數 |
|---|---|---|
| **FIVE (連五)** | 達成勝利 | 1,000,000 |
| **OPEN_FOUR (活四)** | 雙端皆通，對手無法防守 | 100,000 |
| **CLOSED_FOUR (死四)** | 單端被擋，必須立即阻擋 | 10,000 |
| **OPEN_THREE (活三)** | 雙端皆通，下一步可成活四 | 5,000 |
| **CLOSED_THREE (死三)** | 單端被擋 | 500 |
| **OPEN_TWO (活二)** | 雙端皆通 | 100 |

### 快速走法評估 (`quick_score_move`)
- **端點開閉檢驗 (`open_ends`)**：準確區分活四與死四，雙端封死給予 0 分，避免無效走法干擾剪枝。
- **吃子攻防權重**：進攻吃子每對 +25,000 分，防守防夾每對 +20,000 分。

---

## 4. 特殊模式與技能操作

| 模式名稱 | 核心玩法 |
|---|---|
| **標準模式 (Standard)** | 42 官方標準棋規（雙活三禁手 + 夾吃 + 破五連）。 |
| **風化模式 (Decay)** | 棋子具備 10 回合生命週期，逾期自動消散。 |
| **超能石模式 (Power)** | 吃滿 5 顆子解鎖超能技能。 |
| **流星模式 (Star)** | 天體隨機墜落，產生隕石坑洞或顏色反轉脈衝。 |
| **標準無限制 (Limitless)** | 純粹五子棋，完全移除雙三禁手限制。 |
| **大亂鬥 (Everything)** | 同時啟用風化 + 超能石 + 流星三大機制。 |

### 超能石操作方式
- **啟用 / 取消**：點擊滑鼠右鍵。
- **旋轉切換技能**：
  - 向上/向下滾動**滑鼠滾輪** (`pygame.MOUSEWHEEL`)。
  - 按鍵盤 **`Tab`** 鍵循環切換。
  - 按數字鍵 **`1`**、**`2`**、**`3`** 直接選取（1: 💣 炸彈 3×3, 2: ➕ 十字距離 2, 3: ✖️ 斜向距離 2）。

---

## 5. 口試程式碼導讀順序

向 Examiner 介紹專案時，建議遵循以下路徑：

1. **`src/config/game.py` & `ai.py`**：展示棋盤規格、`MAX_DEPTH = 10`、`AI_TIME_LIMIT = 0.45s` 與棋型權重表。
2. **`src/rules/rules.py`**：展示 6 格滑動視窗連續/跳活三檢測、吃子豁免條款與連五判定。
3. **`src/core/game.py`**：展示落子驗證、夾吃執行與 `_can_opponent_break_or_win` 破五連狀態機。
4. **`src/ai/heuristic.py`**：展示 `evaluate_board` 與端點開閉/吃子權重。
5. **`src/ai/ai.py`**：展示深度 10 的迭代加深 Minimax、前向剪枝與 PV 優先排序。
6. **`src/ui/gui.py` & `src/main.py`**：展示即時深度狀態列、模式選單、指南彈窗 (`[G]`) 與危險警示 (`UNO!`)。

---

## 6. 自動化測試與驗證

執行完整單元測試套件：
```bash
python3 -m unittest -v tests/test_rules_and_bugs.py
```
**測試結果（15/15 項全數通過）**：
- `test_ai_reaches_depth_10`：驗證 AI 於 0.45 秒內跑滿 10 層搜尋。
- `test_double_free_three_*`：連續、跳三、受阻與吃子豁免檢驗。
- `test_endgame_capture_*`：破五連成功、防守失敗、立即獲勝與第 10 子反殺。
- `test_heuristic_*`：端點開閉與吃子權重評分。
- `test_power_bomb_cleans_holes`：炸彈炸毀隕石坑狀態同步。
