<p align="right">
  <a href="#gomoku-五目">
    <img src="https://img.shields.io/badge/中文-sienna?style=for-the-badge" />
  </a>
</p>

# Gomoku

An AI-powered Gomoku (五目, Five in a Row) game built with **Python** and **Pygame**. The AI uses the **Minimax algorithm with Alpha-Beta pruning** and a pattern-based heuristic evaluation to deliver a challenging opponent on a full 19×19 Go board.

This project explores adversarial search, heuristic design, and the balance between search depth and computation time.

### Sample Board State
<table>
  <tr><td>·</td><td>·</td><td>·</td><td>·</td><td>·</td></tr>
  <tr><td>·</td><td>●</td><td>●</td><td>●</td><td>·</td></tr>
  <tr><td>·</td><td>·</td><td>○</td><td>·</td><td>·</td></tr>
  <tr><td>·</td><td>·</td><td>○</td><td>·</td><td>·</td></tr>
  <tr><td>·</td><td>·</td><td>·</td><td>·</td><td>·</td></tr>
</table>

*Black (●) has an Open Three — the AI identifies and scores this pattern.*

## ✨ Features

- **Full 19×19 Board**: Standard Go board, no stone limit.
- **Minimax + Alpha-Beta Pruning**: Adversarial search with efficient branch cutting.
- **Pattern-based Heuristic**: Recognizes Open Four, Closed Four, Open Three, and more.
- **Capture Rule (Ninuki-renju)**: Flank a pair of opponent stones to remove them. Capture 10 stones to win.
- **Double Free-Three Ban**: Moves that simultaneously create two free-three alignments are forbidden.
- **Endgame Capture**: A five-in-a-row win can be overturned if the opponent can break it by capturing.
- **AI Move Timer**: Displays AI thinking time per move *(average < 0.5s — required by Subject)*.
- **Two Game Modes**:
  - **AI**: Challenge the AI.
  - **PvP**: Local two-player with move-suggestion feature.

## 🎁 Bonus Features / Extra Scope

To provide an exceptional user experience and stretch beyond the mandatory subject requirements, several bonus mechanics have been implemented:

- **Undo System**: Press `[R]` to safely revert the last turn. In PvE, it seamlessly rewinds both the AI's and the human's moves to maintain game flow.
- **Aide System**: A dynamic, toggleable side-panel assistant. It analyzes the board in real-time and warns you with **'Threat'** or **'UNO!'** alerts if the opponent is dangerously close to winning.
- **Four Custom Game Modes**:
  - **Decay**: Stones have a finite lifespan of 10 turns before they crack and vanish from the board.
  - **Power Stones**: Accumulate points via capturing opponent stones to unleash area-of-effect spells (Bomb, Cross, Diagonal).
  - **Shooting Star**: Random meteor strikes that might land stones that change colors, or destroy squares on the board.
  - **Everything**: Surviving all the above mechanics at the same time!
- **Multi-language Support**: Real-time localization switching between English, French, and Traditional Chinese.
- **Premium UI/UX**: Hand-drawn vector icons, lively animations, hover states, percentage loading bars, and a modern side-panel.

## 🚀 Installation & Compilation

```bash
cd Gomoku
make
```

## 🛠️ Usage

```bash
./Gomoku
```

## 📊 AI Performance
- **Search depth**: ≥ 10 levels
- **Average move time**: < 0.5 seconds
- **Optimizations**: Move ordering, candidate filtering, iterative deepening, transposition table (Zobrist hashing)

<br/>

---

<br/>

<p align="right">
  <a href="#gomoku">
    <img src="https://img.shields.io/badge/-TOP-sienna?style=for-the-badge" />
  </a>
</p>

# Gomoku (五目)

一款由 **Python** 與 **Pygame** 打造、搭載 AI 的五子棋。AI 核心採用 **Minimax 演算法 + Alpha-Beta 剪枝**，並搭配基於棋型辨識的啟發式評估函數，在 19×19 棋盤上提供具挑戰性的對局體驗。

本專案旨在探索博弈樹搜尋 (Adversarial Search)、啟發式設計，以及搜尋深度與運算時間之間的平衡。

## ✨ 核心特點

- **完整 19×19 棋盤**：在標準圍棋盤上進行，無落子數量限制。
- **Minimax + Alpha-Beta 剪枝**：博弈搜尋演算法，高效裁剪無效分支。
- **棋型辨識啟發式**：自動辨識關鍵棋型（活四、死四、活三等），精準評估盤面價值。
- **吃子規則 (Ninuki-renju)**：以夾擊方式吃掉對手的一對棋子。吃滿 10 子即獲勝。
- **禁手：雙活三**：禁止同時製造兩個活三的走法。
- **終局吃子**：五連時若對手能透過吃子破壞連線，則不算勝利。
- **AI 思考計時器**：即時顯示 AI 每手的思考時間（平均 < 0.5 秒，**Subject 強制要求**）。
- **雙模式對局**：
  - **AI**：挑戰 AI。
  - **PvP**：本機雙人對戰，附建議走法功能。

## 🎁 額外加分項目 (Bonus Features)

為了提供滿分的體驗並超越基本的評分要求，本專案額外實作了以下高級機制：

- **悔棋系統 (Undo System)**：按下 `[R]` 鍵即可安全退回上一步。在對戰 AI 模式中，系統會自動退回「雙方」的步數以保證公平性。
- **即時戰況輔助 (Aide System)**：可自由開關的即時盤面分析。當對手即將獲勝或產生重大威脅時，系統會在畫面下方彈出 **'Threat'** 或是 **'UNO!'** 來給予玩家警告。
- **四種全新自訂遊戲模式**：
  - **風化模式 (Decay)**：每顆落下的棋子僅有 10 回合的壽命，隨後會風化消失。
  - **超能石模式 (Power Stones)**：透過一般吃子累積能量，施放十字、對角或大範圍炸彈等清盤技能。
  - **流星模式 (Shooting Star)**：天外隕石會隨機墜落，被砸中的網格將產生黑白間變色的子，或產生地陷無法落子。
  - **大亂鬥模式 (Everything)**：同時挑戰上述所有混沌機制！
- **多國語言支援**：即時切換英文 (EN)、法文 (FR) 與繁體中文 (ZH)。
- **現代化 UI/UX**：拋棄傳統呆板介面，擁有自定義純手工繪製的向量圖標、現代化側邊欄、動畫以及動態讀取條。

## 🚀 安裝與編譯

```bash
cd Gomoku
make
```

## 🛠️ 使用方式

```bash
./Gomoku
```

## 📊 AI 效能指標
- **搜尋深度**：≥ 10 層
- **平均每手時間**：< 0.5 秒
- **效能優化策略**：走法排序、候選過濾（僅搜尋棋子附近空位）、漸進式深化、Transposition Table (Zobrist Hash)
