# Gomoku Defense Guide

<p align="right">
  <a href="#gomoku-defense-guide-繁體中文">
    <img src="https://img.shields.io/badge/中文-sienna?style=for-the-badge" />
  </a>
</p>

This document covers the core concepts, algorithm theory, heuristic design, performance optimizations, and game rule details for the Gomoku AI project. Use this as your reference when explaining the project during a Defense session.

---

## 0. Language Choice

This project uses **Python + Pygame**.

| Language | GUI | AI Performance | Dev Speed | Verdict |
|---|---|---|---|---|
| **Python + Pygame** | ✅ Cross-platform | ⭐⭐ | ⭐⭐⭐ | **Best balance of speed and quality** |
| **C++ + SFML** | ✅ High performance | ⭐⭐⭐ | ⭐ | Stronger but higher development cost |

The Subject allows any language and GUI library. Python with Pygame delivers a fully functional product (AI + GUI) quickest, and the performance constraints are addressed through algorithmic optimization rather than language-level speed.

---

## 1. Workflow & Core Logic

**Goal**: On a 19×19 board, find the best move to beat a human opponent.

**Key Rules**:
1. **Win condition**: Five or more stones in a row, OR capturing 10 opponent stones (5 pairs).
2. **Capture**: Flank an opponent *pair* (`X O O X`) to remove them. You cannot capture singles or more than 2. Moving into a flanked position does NOT get captured.
3. **Double Free-Three (Forbidden)**: A move that simultaneously creates two free-three alignments is illegal — unless it results from a capture.
4. **Endgame Capture**: If a player completes five-in-a-row but the opponent can immediately capture to break it, the win does not count.

**Program Flow**:
1. Launch Pygame window and render the 19×19 board.
2. Player selects mode (Human vs AI / Human vs Human).
3. Each turn: Human clicks to place → or AI runs Minimax to find best move.
4. After each move: check win, apply captures, validate forbidden moves.

---

## 2. Search Algorithm: Minimax + Alpha-Beta Pruning

### What is Minimax?
Minimax is an adversarial search algorithm that assumes *both players always play optimally*.
- **Max layers** (AI's turn): maximize the board score.
- **Min layers** (opponent's turn): minimize the board score.

The AI builds a game tree, evaluates terminal/leaf nodes with a heuristic, and propagates values back up to choose the best root move.

### What is Alpha-Beta Pruning?
Alpha-Beta eliminates branches that cannot possibly affect the final result.
- **Alpha (α)**: the best (highest) score that the maximizer can guarantee so far.
- **Beta (β)**: the best (lowest) score that the minimizer can guarantee so far.

When $\beta \le \alpha$, the current branch is **pruned** — no need to search further.

> **💡 Defense answer**: "In the best case, Alpha-Beta reduces the effective branching factor from $b$ to $\sqrt{b}$, which is equivalent to searching **twice as deep** in the same time. This depends heavily on move ordering quality."

---

## 3. Heuristic Evaluation Function

The heuristic is called when Minimax reaches its maximum depth. It is the hardest and most important part of the project.

### Pattern Recognition
We scan the board in 4 directions (horizontal, vertical, and both diagonals) to identify stone sequences:

| Pattern | Description | Score |
|---|---|---|
| **Five** | Win condition (5+ in a row) | 1,000,000 |
| **Open Four** | 4 stones, both ends open — unblockable | 100,000 |
| **Closed Four** | 4 stones, one end blocked | 10,000 |
| **Open Three** | 3 stones, both ends open → becomes Open Four | 5,000 |
| **Closed Three** | 3 stones, one end blocked | 500 |
| **Open Two** | 2 stones, both ends open | 100 |

### Combined Offense + Defense Score
$$\text{Board Score} = \sum \text{AI patterns} - \sum \text{Opponent patterns}$$

This formula naturally forces the AI to:
- **Attack**: maximize its own high-scoring patterns.
- **Defend**: the opponent's high-scoring patterns subtract from the score, so blocking them is rewarded.

> **💡 Defense answer**: "The heuristic quality directly determines the AI's strength. A precise heuristic at shallow depth outperforms a naive heuristic even at great depth. This is why the Subject calls it 'the hardest part.'"

---

## 4. Performance Optimizations

### A. Candidate Move Filtering
19×19 = 361 intersections. Evaluating all of them is too slow.
**Solution**: Only consider empty squares within 2 cells of any existing stone. This reduces candidates to ~20–40.

### B. Move Ordering
Alpha-Beta pruning is most effective when the best moves are searched first.
**Approach**: Before recursing, score each candidate move with a cheap heuristic evaluation and sort descending. This dramatically increases the number of pruned branches.

### C. Iterative Deepening
Start searching at depth 2, increase by 1 each iteration. At each level, the best move from the previous level is searched first (improving move ordering). If the 0.5s time limit is reached, the last completed depth's best move is returned.

### D. Transposition Table (Zobrist Hashing)
Assign each (position, color) pair a random 64-bit number. XOR them together to produce a unique hash for any board state. Store evaluated states in a hash map to avoid recalculating the same position.

---

## 5. Capture & Forbidden Move Rules (Details)

### Capture
`X O O X` — if a placement results in flanking an opponent pair, those stones are removed.
- Only pairs are captured (not singles, not 3+).
- Placing between two opponent stones (`O _ O`) does NOT result in being captured.
- Capturing 5 pairs (10 stones total) wins the game.

### Free-Three
A free-three is three stones in a row where both ends are open, and which can form an "unblockable" open four next turn.

### Double Free-Three (Forbidden Move)
A move that creates **two simultaneous free-threes** is illegal.
**Exception**: If the double-three is created by a capturing move, it is allowed.

---

## 6. Code Reading Guide

1. **`constants.py`**: Start here — board size, colors, pattern score weights.
2. **`game.py`** (Game Engine): Board structure, move validation, capture detection, win conditions, free-three detection.
3. **`heuristic.py`** (Heuristic): Pattern scanning logic, scoring formula, combined attack/defense evaluation.
4. **`ai.py`** (AI Engine): Minimax with Alpha-Beta, move candidate generation, move ordering, iterative deepening, transposition table.
5. **`gui.py`** (GUI): Pygame event handling, board drawing, AI timer display, result screen.
6. **`main.py`** (Entry Point): How the GUI, Game Engine, and AI Engine are wired together.

---

## 7. Emoji Validation Script

Linux pygame environments (especially inside School/42 Unix environments without `Noto Color Emoji`) often struggle to render Unicode emojis. 

To easily test emoji rendering at school, run the standalone script `test_emoji.py` in the root folder:

```bash
python3 test_emoji.py
```

If emojis appear correctly in the pop-up window, you can rely on the system's fonts to display mode icons properly. Otherwise, the GUI uses fallback vector-drawn shapes to ensure the UI remains fully functional.

---

## 8. Aide Popup (UNO / Threat)

The game provides real-time threat alerts:

- **UNO**: Deep red background, pale gold text. Indicates an immediate win threat.
- **Threat**: Bright yellow-orange background, dark orange text. Indicates a strong threat (e.g., open four).

**Display Location**:
- The popup now appears at the bottom-right of the board area (not in the side panel), so it never covers the status line or suggestion messages.

**Color Reference**:
- UNO: `bg_col = (140, 20, 20)`, `txt_col = (255, 230, 180)`
- Threat: `bg_col = (255, 220, 80)`, `txt_col = (120, 60, 0)`

This ensures maximum readability and avoids overlap with other UI elements.

---

<br/>

---

<br/>

<p align="right">
  <a href="#gomoku-defense-guide">
    <img src="https://img.shields.io/badge/-TOP-sienna?style=for-the-badge" />
  </a>
</p>

# Gomoku Defense Guide (繁體中文)

這份文件涵蓋了 Gomoku AI 專案的核心概念、演算法設計、啟發式函數原理、效能優化策略，以及各種 Defense 可能被詢問的技術細節。

---

## 0. 語言選擇

本專案選擇使用 **Python + Pygame** 實作。

| 語言 | GUI 支援 | AI 效能 | 開發速度 | 綜合評估 |
|---|---|---|---|---|
| **Python + Pygame** | ✅ 原生跨平台 | ⭐⭐ | ⭐⭐⭐ | **開發效率最優** |
| **C++ + SFML** | ✅ 高效能 | ⭐⭐⭐ | ⭐ | 效能最強但開發成本高 |

Subject 指出「你可以自由選擇語言與圖形介面庫」。Python 搭配 Pygame 能最快速地產出可運作的完整成品（AI + GUI），而效能問題則透過演算法優化來解決。

---

## 1. 核心概念與執行流程

**目標**：在 19×19 棋盤上，讓 AI 判斷最佳走法以擊敗人類玩家。

**遊戲規則重點摘要**：
1. **勝利條件**：五子（含以上）連珠，或吃滿對手 10 顆棋子（5 對）。
2. **吃子 (Capture)**：用自己的兩顆棋子夾住對手的「一對」棋子（`X O O X`），即可移除。只能吃「對」，不能吃單顆或三顆。主動走進夾擊位置不會被吃。
3. **禁手 (Double Free-Three)**：如果某一手棋會同時製造兩個「活三 (Free-three)」，則為禁手，但吃子造成的例外。
4. **終局吃子 (Endgame Capture)**：五連時若對手能透過吃子破壞連線，則不算勝利。

---

## 2. 搜尋演算法：Minimax + Alpha-Beta 剪枝

### Minimax 是什麼？
Minimax 是一種「假設對手永遠下最聰明的那一步」的博弈搜尋演算法。
- **Max 層**（AI 的回合）：最大化分數。
- **Min 層**（對手的回合）：最小化分數。

AI 建構博弈樹，用啟發式函數評估葉節點，再將值向上傳遞以選出最佳根走法。

### Alpha-Beta 剪枝是什麼？
- **Alpha (α)**：Max 層目前已知的最佳下界。
- **Beta (β)**：Min 層目前已知的最佳上界。

當 $\beta \le \alpha$ 時，直接**剪掉**當前分支（不再搜尋）。

> **💡 Defense 對答**：「在最理想情況下，Alpha-Beta 可以把有效分支因子從 $b$ 降至 $\sqrt{b}$，等同於在相同時間內搜尋**兩倍深度**。效果取決於走法排序的品質。」

---

## 3. 啟發式評估函數

這是整個專案最困難也最重要的部分。棋型掃描方向：水平、垂直、正對角、反對角（共 4 方向）。

| 棋型 | 描述 | 分數（參考） |
|---|---|---|
| **Five (連五)** | 已勝利 | 1,000,000 |
| **Open Four (活四)** | 兩端皆空，無法防守 | 100,000 |
| **Closed Four (死四)** | 一端被擋 | 10,000 |
| **Open Three (活三)** | 兩端皆空 | 5,000 |
| **Closed Three (死三)** | 一端被擋 | 500 |
| **Open Two (活二)** | 兩端皆空 | 100 |

$$\text{Board Score} = \sum \text{AI 棋型分數} - \sum \text{對手棋型分數}$$

---

## 4. 效能優化策略

| 策略 | 描述 |
|---|---|
| **候選走法過濾** | 只搜尋已有棋子周圍 2 格內空位，縮小分支因子 |
| **走法排序** | 以啟發分數排序候選，讓 Alpha-Beta 剪枝更有效率 |
| **漸進式深化** | 從深度 2 逐漸加深，時間到則回傳當前最佳結果 |
| **Transposition Table** | Zobrist Hash 快取盤面評分，避免重複計算 |

---

## 5. 吃子與禁手規則詳解

### 吃子 (Capture)
`X O O X`：夾住對手一對棋子即移除。吃滿 5 對（10子）勝利。

### 活三 (Free-Three)
三子連線且兩端皆空的排列，若不阻擋，下一手可形成不可防守的活四。

### 禁手：雙活三
某手棋若同時製造兩個活三，即為禁手。**例外**：透過吃子製造的雙活三不受限制。

---

## 6. 程式碼閱讀順序建議

1. **`constants.py`**：所有常數定義（棋盤大小、顏色、棋型分數表）。
2. **`game.py`**：棋盤邏輯、落子驗證、吃子偵測、勝負判定、禁手檢查。
3. **`heuristic.py`**：棋型掃描邏輯、評分公式、攻守雙面評估。
4. **`ai.py`**：Minimax 搜尋、Alpha-Beta 剪枝、走法排序、漸進式深化、Transposition Table。
5. **`gui.py`**：Pygame 事件處理、棋盤繪製、AI 計時器顯示。
6. **`main.py`**：整合進入點，將所有模組串接。

---

<br/>

---

<br/>

<p align="right">
  <a href="#gomoku-defense-guide">
    <img src="https://img.shields.io/badge/-TOP-sienna?style=for-the-badge" />
  </a>
</p>
