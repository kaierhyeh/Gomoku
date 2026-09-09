# Gomoku (5eyes) 專案分析與 Bug 診斷報告

本報告針對 [~/5eyes](file:///home/kyeh/5eyes) 專案進行全面性程式碼架構檢視，並對照 42 School Gomoku 官方規範（[en.subject.pdf](file:///home/kyeh/5eyes/en.subject.pdf)）梳理出目前存在的邏輯缺陷、運行期崩潰風險與規則不符之處。

---

## 目錄
1. [專案架構與模組概覽](#專案架構與模組概覽)
2. [重大缺陷與 Bug 診斷](#重大缺陷與-bug-診斷)
   - [A. 運行期崩潰問題 (Runtime Crash)](#a-運行期崩潰問題-runtime-crash)
   - [B. 42 Subject 規則合規性缺陷 (Subject Compliance)](#b-42-subject-規則合規性缺陷-subject-compliance)
   - [C. AI 搜尋引擎與啟發式評估缺陷 (AI Engine & Heuristics)](#c-ai-搜尋引擎與啟發式評估缺陷-ai-engine--heuristics)
   - [D. 特殊模式狀態同步與邊界問題 (Modifiers & Bonus Modes)](#d-特殊模式狀態同步與邊界問題-modifiers--bonus-modes)
3. [詳細修復建議與優先級](#詳細修復建議與優先級)

---

## 專案架構與模組概覽

專案採用 Python 3 + Pygame 實作，近期完成了由單檔向模組化架構的重構（Commit `cbca874`）：

```
~/5eyes
├── Makefile              # 構建與啟動腳本
├── Gomoku                # 入口 Bash wrapper
├── en.subject.pdf        # 42 官方規範手冊
├── defense_guide.md      # Defense 口試指南
├── PATCH_NOTES.md        # 架構重構補丁日誌
└── src/
    ├── main.py           # 遊戲主迴圈、事件派發與模式切換
    ├── config/           # 全域靜態設定
    │   ├── game.py       # 棋盤大小 (19x19)、棋子代號、獲勝長度
    │   ├── ai.py         # AI 搜尋上限、超時時間 (0.45s)、棋型權重
    │   ├── ui.py         # 視窗尺寸、顏色、邊界
    │   └── bonus.py      # 特殊模式參數 (Decay、Power Stones 等)
    ├── core/             # 遊戲核心引擎
    │   ├── state.py      # GameState 狀態資料類別 (Dataclass)
    │   ├── game.py       # Game 引擎 (下子、吃子、勝負判定、歷程管理)
    │   └── modifiers.py  # 特殊模式處理器 (Decay, ShootingStar, Power)
    ├── rules/            # 棋規判斷邏輯
    │   ├── rules.py      # 活三/雙活三禁手、連五、吃子判定
    │   └── bonus.py      # 規則組合管理 (RuleSet)
    ├── ai/               # 人工智慧決策系統
    │   ├── ai.py         # Minimax + Alpha-Beta 剪枝、Zobrist 雜湊、走法排序
    │   └── heuristic.py  # 盤面評估函數與走法快速預估
    └── ui/               # 繪圖與使用者介面
        ├── gui.py        # Pygame 棋盤渲染、動畫、提示框
        └── i18n.py       # 多語系支援 (EN / FR / ZH)
```

---

## 重大缺陷與 Bug 診斷

### A. 運行期崩潰問題 (Runtime Crash)

#### 1. Aide 戰況輔助開啟時拋出 `NameError` 閃退
* **問題位置**：[src/main.py:L215-L225](file:///home/kyeh/5eyes/src/main.py#L215-L225)
* **現象**：
  ```python
  if aide_on and not game.is_game_over() and not ai_thinking:
      from ai.heuristic import evaluate_board, quick_score_move
      opponent = WHITE if game.current_player == BLACK else BLACK

      if vs_mode == MODE_HUMAN or (vs_mode == MODE_AI and game.current_player == BLACK):
          opp_score = heuristic._score_player(game.board, opponent, 0) # ❌ heuristic 未定義
  ```
* **原因**：匯入時只引入了函式 `evaluate_board` 與 `quick_score_move`，並未匯入 `heuristic` 模組本體。玩家只要在 UI 點擊啟用 Aide，輪到黑棋回合時便會拋出 `NameError: name 'heuristic' is not defined` 導致遊戲直接崩潰。

---

### B. 42 Subject 規則合規性缺陷 (Subject Compliance)

> [!CAUTION]
> 42 Gomoku 專案評分標準極其嚴格，若 Mandatory 規則實作不完整或有誤，會直接導致評分失敗 (Grade: 0)。

#### 1. 終局吃子破五連 (Endgame Capture) 機制完全缺失
* **Subject 規範要求**：
  > "A player who manages to line up five stones wins only if the opponent cannot break this line by capturing a pair. If the player has already lost four pairs and the opponent can capture one more, the opponent wins by capture."
  1. 連成五子時，**若對手下一步能藉由夾吃破壞該五連線，則不判定立即獲勝**，必須給對手一步棋的機會反擊。
  2. 若連成五子的玩家已經被吃了 4 對子（8 顆），而對手下一步可以再吃一對湊滿 10 顆子，對手勝出。
* **問題位置**：[src/core/game.py:L186-L190](file:///home/kyeh/5eyes/src/core/game.py#L186-L190)
* **原因**：目前 `_check_winner` 只要偵測到 `has_five` 便立刻將 `self.winner` 設為該玩家並結束對局，完全略過了終局吃子破連線的驗證。

#### 2. 雙活三禁手 (Double Free-Three) 判定不精準
* **問題位置**：[src/rules/rules.py:L25-L48](file:///home/kyeh/5eyes/src/rules/rules.py#L25-L48) 及 [src/core/game.py:L162](file:///home/kyeh/5eyes/src/core/game.py#L162)
* **缺陷 1：遺漏跳活三 (Broken Threes)**
  - 現行程式碼使用長度為 5 的視窗比對 `cells.count(player) == 3 and cells.count(EMPTY) == 2 and cells[0] == EMPTY and cells[4] == EMPTY`。
  - 這只能辨識連續活三 `_XXX_`。但 Subject 附錄明確圖示規定：跳活三（如 `_X_XX_` 與 `_XX_X_`，總跨度為 6 格）同樣是活三。目前此類禁手均未被偵測。
* **缺陷 2：未實作吃子例外條款**
  - Subject 規範明訂：
    > "It is important to note that it is not forbidden to introduce a double-three by capturing a pair."
  - 如果玩家落子形成雙活三的同時「成功夾吃對手的棋子」，此走法為**合法走法**。現有程式碼在 `is_valid_move` 階段未檢查是否觸發吃子，直接將其判定為無效步。

---

### C. AI 搜尋引擎與啟發式評估缺陷 (AI Engine & Heuristics)

#### 1. 宣稱深度 10，實質深度不足 (Search Depth vs Time Limit)
* **Subject 規範要求**：
  > "To fully validate the project, your AI must search at least 10 levels deep in its game tree. ... if your AI takes more than half a second (in average) to find a move, you will not validate the project."
* **現狀問題**：
  - 目前在 [src/config/ai.py](file:///home/kyeh/5eyes/src/config/ai.py) 設定 `AI_TIME_LIMIT = 0.45`。
  - 純 Python 在 Minimax 的每個節點都執行 `game.clone()`，複製整個棋盤陣列與狀態。由於分支龐大，在 0.45 秒的時間限制下，AI 往往在深度 3～4 就觸發超時中斷。
  - UI 上顯示的 `(Depth: 10)` 是寫死的狀態提示，在評分口試 (Defense) 時若被 grader 檢查終端或搜尋層數，會被發現未實際達到 10 層要求。

#### 2. AI 模擬非法步未作防護
* **問題位置**：[src/ai/ai.py:L97-L99](file:///home/kyeh/5eyes/src/ai/ai.py#L97-L99)、[src/ai/ai.py:L151-L153](file:///home/kyeh/5eyes/src/ai/ai.py#L151-L153)
* **原因**：
  ```python
  sim = game.clone()
  sim.place_stone(row, col, current)
  val = self._minimax(sim, depth - 1, alpha, beta, ...)
  ```
  `place_stone` 在走法非法（例如踩到禁手、撞到隕石坑等）時會回傳 `False` 且不改動棋盤。AI 程式未檢查回傳值，直接將原封不動的盤面送入下一層遞迴，導致評估值錯亂，甚至可能選出違法走法。

#### 3. 走法排序啟發式 (`quick_score_move`) 誤導剪枝
* **問題位置**：[src/ai/heuristic.py:L104-L123](file:///home/kyeh/5eyes/src/ai/heuristic.py#L104-L123)
* **原因**：
  - `_scan_line_score` 僅計算單純的連子數量，**未檢查兩端是否已被封堵**。
  - 這導致即使兩端都被堵死的「死四」（無法成五），也會被評為價值 100,000 的 `OPEN_FOUR`，嚴重破壞走法排序的最佳度，大幅降低 Alpha-Beta 剪枝效率。
  - 候選步快速評估未計入「吃子」的戰術價值，使 AI 容易忽視吃子攻防。

---

### D. 特殊模式狀態同步與邊界問題 (Modifiers & Bonus Modes)

#### 1. 能力石清除邊界硬編碼與隕石坑狀態脫節
* **問題位置**：[src/core/modifiers.py:L120, L125, L130](file:///home/kyeh/5eyes/src/core/modifiers.py#L120)
* **原因**：
  - 邊界檢查直接硬編碼 `0 <= r < 19` 而非參照 `BOARD_SIZE`。
  - 當炸彈能力石炸到隕石洞 (`HOLE`) 時，將 `board[r][c]` 設為 `EMPTY`，但並未從 `state.holes` 中移除該座標，造成盤面顯示為空格但判定邏輯仍將其視為洞的狀態不一致。

---

## 詳細修復建議與優先級

| 優先級 | 模組 | 問題項目 | 建議方案 |
| :--- | :--- | :--- | :--- |
| **P0 (緊急)** | `main.py` | Aide 戰況輔助閃退 | 改為 `from ai import heuristic` 或直接調用正確的函式路徑。 |
| **P0 (關鍵)** | `rules.py` / `core/game.py` | 雙活三禁手漏洞 | 1. 支援長度為 6 的跳活三模式 (`_X_XX_` / `_XX_X_`)。<br/>2. 在 `is_valid_move` 中判斷若該步伴隨吃子，豁免雙活三限制。 |
| **P0 (關鍵)** | `core/game.py` | 終局吃子破五連 | 連五形成時檢查對手是否有一步合法棋可吃掉該五連中任意子（或湊滿 5 對勝出）。若有，進入終局防守狀態而非立即結算。 |
| **P1 (核心)** | `ai/ai.py` | Minimax 違法步防護 | 在模擬時加入 `if not sim.place_stone(...) : continue`，防止將無效狀態計入博弈樹。 |
| **P1 (效能)** | `ai/heuristic.py` | 走法排序與棋型辨識修正 | 1. 修正 `_scan_line_score`，加入端點開放性判斷（區分活四與死四）。<br/>2. 走法排序加入吃子得分加權。 |
| **P1 (效能)** | `ai/ai.py` | 搜尋效能與真實深度優化 | 減少 `game.clone()` 開銷（例如採用下子/復原的 make_move/undo_move 機制），配合更銳利的候選點縮減，確保在時限內探測更深層數。 |
| **P2 (加分)** | `modifiers.py` | 特殊模式邊界與狀態修正 | 消除硬編碼 `19`，並在炸毀隕石洞時同步清除 `state.holes`。 |

