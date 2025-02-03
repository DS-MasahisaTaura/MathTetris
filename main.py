import pygame
import random
import sys

# 定数の定義
BLOCK_SIZE = 30  # 1マスのピクセルサイズ
BOARD_WIDTH = 10  # 横のマス数
BOARD_HEIGHT = 20  # 縦のマス数
CONTROL_HEIGHT = 60  # 画面下部のコントロール領域の高さ
WINDOW_WIDTH = BOARD_WIDTH * BLOCK_SIZE
WINDOW_HEIGHT = BOARD_HEIGHT * BLOCK_SIZE + CONTROL_HEIGHT
FPS = 60
DROP_EVENT = pygame.USEREVENT + 1  # 自動落下用のイベント

# カラー定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARKGRAY = (50, 50, 50)

# テトリスの各ブロック（テトリミノ）の形定義
# 1がブロック部分、0が空白
SHAPES = {
    "I": [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
    "S": [[0, 1, 1], [1, 1, 0], [0, 0, 0]],
    "Z": [[1, 1, 0], [0, 1, 1], [0, 0, 0]],
    "J": [[1, 0, 0], [1, 1, 1], [0, 0, 0]],
    "L": [[0, 0, 1], [1, 1, 1], [0, 0, 0]],
}

# 各形状ごとの色の定義（Oテトリミノの色は黄色ではなくマゼンタに変更）
SHAPE_COLORS = {
    "I": (0, 255, 255),  # シアン
    "O": (255, 0, 255),  # マゼンタ
    "T": (128, 0, 128),  # パープル
    "S": (0, 255, 0),  # グリーン
    "Z": (255, 0, 0),  # レッド
    "J": (0, 0, 255),  # ブルー
    "L": (255, 165, 0),  # オレンジ
}


# 回転（時計回り）: 行列を回転する
def rotate_matrix(matrix):
    return [list(row) for row in zip(*matrix[::-1])]


# 裏返し（左右反転）: 各行を反転する
def flip_matrix(matrix):
    return [row[::-1] for row in matrix]


# Piece クラス：各テトリミノを表す
class Piece:
    def __init__(self, shape_key):
        """
        shape_key は "I", "O" などの文字列です。
        SHAPES[shape_key] の行列の 1 の部分に対してランダムな数字（0～9）を割り当て、
        空白は None として保持します。色も設定します。
        """
        self.shape_key = shape_key
        self.color = SHAPE_COLORS[shape_key]
        self.matrix = []
        for row in SHAPES[shape_key]:
            new_row = []
            for cell in row:
                if cell:
                    new_row.append(random.randint(0, 9))
                else:
                    new_row.append(None)
            self.matrix.append(new_row)
        self.height = len(self.matrix)
        self.width = len(self.matrix[0])
        # 初期位置は盤面上部中央付近に配置
        self.x = BOARD_WIDTH // 2 - self.width // 2
        self.y = 0

    def rotate(self):
        """90度時計回りに回転"""
        self.matrix = [list(reversed(col)) for col in zip(*self.matrix)]
        self.height = len(self.matrix)
        self.width = len(self.matrix[0])

    def flip(self):
        """水平反転（左右反転）"""
        self.matrix = flip_matrix(self.matrix)

    def get_cells(self):
        """
        ブロックの現在のセルの位置と数字を返す。
        返り値のリストは [(x, y, digit), ...] となる。
        """
        cells = []
        for dy, row in enumerate(self.matrix):
            for dx, val in enumerate(row):
                if val is not None:  # None なら空セル
                    cells.append((self.x + dx, self.y + dy, val))
        return cells


# Board クラス：盤面状態を管理
class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # 盤面は2次元リスト。各セルは None（空）または (digit, color)
        self.grid = [[None for _ in range(width)] for _ in range(height)]

    def is_valid_position(self, piece, dx=0, dy=0):
        """piece を現在位置から dx, dy 移動させた場合に衝突しないか判定する"""
        for x, y, _ in piece.get_cells():
            new_x = x + dx
            new_y = y + dy
            if new_x < 0 or new_x >= self.width or new_y >= self.height:
                return False
            if new_y >= 0 and self.grid[new_y][new_x] is not None:
                return False
        return True

    def add_piece(self, piece):
        """piece のセルを盤面に固定する（セルには (digit, color) を保存）"""
        for x, y, val in piece.get_cells():
            if y >= 0:
                self.grid[y][x] = (val, piece.color)

    def clear_lines(self):
        """数字の合計が30以上の、完全に埋まった行を削除する"""
        new_grid = []
        lines_cleared = 0
        for row in self.grid:
            # 行が完全に埋まっているか判定（None が含まれていない）
            if None not in row:
                # 行の合計を計算（各セルは (digit, color) なので digit 部分を用いる）
                row_sum = sum(cell[0] for cell in row if cell is not None)
                if row_sum >= 30:
                    lines_cleared += 1
                    continue  # この行は削除する
            new_grid.append(row)
        # 上部に空行を追加して盤面サイズを維持
        for _ in range(lines_cleared):
            new_grid.insert(0, [None for _ in range(self.width)])
        self.grid = new_grid
        return lines_cleared


def draw_board(surface, board, font):
    """盤面（固定ブロック）の描画"""
    for y, row in enumerate(board.grid):
        for x, cell in enumerate(row):
            rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(surface, DARKGRAY, rect, 1)
            if cell is not None:
                digit, color = cell
                pygame.draw.rect(surface, color, rect)
                text = font.render(str(digit), True, WHITE)
                text_rect = text.get_rect(center=rect.center)
                surface.blit(text, text_rect)


def draw_piece(surface, piece, font):
    """現在操作中のピースの描画"""
    for x, y, val in piece.get_cells():
        if y >= 0:
            rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(surface, piece.color, rect)
            pygame.draw.rect(surface, DARKGRAY, rect, 1)
            text = font.render(str(val), True, WHITE)
            text_rect = text.get_rect(center=rect.center)
            surface.blit(text, text_rect)


# ボタン情報
class Button:
    def __init__(self, rect, label, action):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action  # ボタンが押されたときに呼ぶ関数

    def draw(self, surface, font):
        pygame.draw.rect(surface, DARKGRAY, self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 2)
        text = font.render(self.label, True, WHITE)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)


import asyncio


async def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("MathTetris")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 20)

    board = Board(BOARD_WIDTH, BOARD_HEIGHT)
    current_piece = Piece(random.choice(list(SHAPES.keys())))

    # 自動落下タイマー（500msごと）
    pygame.time.set_timer(DROP_EVENT, 500)

    # コントロール用のボタンを作成（画面下部に配置）
    # 今回は5つのボタン（←, →, ↓, rotate, flip）を配置
    btn_width = WINDOW_WIDTH // 5
    btn_height = CONTROL_HEIGHT
    btn_y = BOARD_HEIGHT * BLOCK_SIZE  # 盤面下部から開始
    buttons = []

    def move_left():
        nonlocal current_piece
        if board.is_valid_position(current_piece, dx=-1):
            current_piece.x -= 1

    def move_right():
        nonlocal current_piece
        if board.is_valid_position(current_piece, dx=1):
            current_piece.x += 1

    def move_down():
        nonlocal current_piece
        if board.is_valid_position(current_piece, dy=1):
            current_piece.y += 1

    def rotate_piece():
        nonlocal current_piece
        original = [row[:] for row in current_piece.matrix]
        current_piece.rotate()
        if not board.is_valid_position(current_piece):
            # 衝突した場合は元に戻す（時計回り4回で元に戻るので、単純に3回回転）
            for _ in range(3):
                current_piece.rotate()

    def flip_piece():
        nonlocal current_piece
        original = [row[:] for row in current_piece.matrix]
        current_piece.flip()
        if not board.is_valid_position(current_piece):
            current_piece.matrix = original

    buttons.append(
        Button((0 * btn_width, btn_y, btn_width, btn_height), "←", move_left)
    )
    buttons.append(
        Button((1 * btn_width, btn_y, btn_width, btn_height), "→", move_right)
    )
    buttons.append(
        Button((2 * btn_width, btn_y, btn_width, btn_height), "↓", move_down)
    )
    buttons.append(
        Button((3 * btn_width, btn_y, btn_width, btn_height), "rotate", rotate_piece)
    )
    buttons.append(
        Button((4 * btn_width, btn_y, btn_width, btn_height), "flip", flip_piece)
    )

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == DROP_EVENT:
                if board.is_valid_position(current_piece, dy=1):
                    current_piece.y += 1
                else:
                    board.add_piece(current_piece)
                    board.clear_lines()
                    current_piece = Piece(random.choice(list(SHAPES.keys())))
                    if not board.is_valid_position(current_piece):
                        print("Game Over!")
                        running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # タッチ（クリック）位置がコントロール領域内なら各ボタンのアクションを実行
                mouse_x, mouse_y = event.pos
                if mouse_y >= BOARD_HEIGHT * BLOCK_SIZE:
                    for btn in buttons:
                        if btn.rect.collidepoint(mouse_x, mouse_y):
                            btn.action()

            # キーボード操作も併用可能（任意）
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    move_left()
                elif event.key == pygame.K_RIGHT:
                    move_right()
                elif event.key == pygame.K_DOWN:
                    move_down()
                elif event.key == pygame.K_UP:
                    rotate_piece()
                elif event.key == pygame.K_z:
                    flip_piece()

        # 描画
        screen.fill(BLACK)
        # 盤面描画（上部）
        draw_board(screen, board, font)
        draw_piece(screen, current_piece, font)

        # コントロール領域の背景
        control_rect = pygame.Rect(
            0, BOARD_HEIGHT * BLOCK_SIZE, WINDOW_WIDTH, CONTROL_HEIGHT
        )
        pygame.draw.rect(screen, GRAY, control_rect)

        # 各ボタンの描画
        for btn in buttons:
            btn.draw(screen, font)

        pygame.display.flip()

        await asyncio.sleep(0)  # 引数は0で固定
    pygame.quit()
    sys.exit()


asyncio.run(main())
