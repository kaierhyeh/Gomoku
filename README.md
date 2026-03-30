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
  - **Human vs AI**: Challenge the AI.
  - **Human vs Human (Hotseat)**: Local two-player with move-suggestion feature.

## 🚀 Installation & Compilation

```bash
cd 5eyes
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

一款由 **Python** 與 **Pygame** 打造、搭載 AI 對手的五子棋遊戲。AI 核心採用 **Minimax 演算法 + Alpha-Beta 剪枝**，並搭配基於棋型辨識的啟發式評估函數，在完整的 19×19 棋盤上提供具挑戰性的對局體驗。

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
  - **人類 vs AI**：挑戰 AI。
  - **人類 vs 人類 (Hotseat)**：本機雙人對戰，附建議走法功能。

## 🚀 安裝與編譯

```bash
cd 5eyes
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