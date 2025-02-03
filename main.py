import pygame
import random
import sys

# --------------------------
# 定数の定義
# --------------------------
BOARD_WIDTH = 10  # ボードの横マス数
BOARD_HEIGHT = 20  # ボードの縦マス数
BLOCK_SIZE = 30  # 1マスあたりのピクセルサイズ
FPS = 60
DROP_EVENT = pygame.USEREVENT + 1
DROP_INTERVAL = 500  # 落下速度（ミリ秒間隔）

# 色の定義
BACKGROUND_COLOR = (0, 0, 0)  # 背景は黒
GRID_COLOR = (40, 40, 40)  # グリッド線の色

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
    "O": (255, 0, 255),  # マゼンタ（変更後）
    "T": (128, 0, 128),  # パープル
    "S": (0, 255, 0),  # グリーン
    "Z": (255, 0, 0),  # レッド
    "J": (0, 0, 255),  # ブルー
    "L": (255, 165, 0),  # オレンジ
}


# --------------------------
# テトリミノクラス
# --------------------------
class Tetromino:
    def __init__(self, shape_key, shape_matrix):
        """
        shape_matrix は 0,1 の2次元リストです。
        1の部分に対してランダムな数字（0～9）を割り当て、
        shape_key に対応する色も設定します。
        """
        self.shape_key = shape_key
        self.color = SHAPE_COLORS[shape_key]
        self.matrix = []
        for row in shape_matrix:
            new_row = []
            for cell in row:
                if cell:
                    new_row.append(random.randint(0, 9))
                else:
                    new_row.append(None)
            self.matrix.append(new_row)
        self.height = len(self.matrix)
        self.width = len(self.matrix[0])
        # 初期位置はボード上部中央付近に配置
        self.x = BOARD_WIDTH // 2 - self.width // 2
        self.y = 0

    def rotate(self):
        """90度時計回りに回転"""
        self.matrix = [list(reversed(col)) for col in zip(*self.matrix)]
        self.height = len(self.matrix)
        self.width = len(self.matrix[0])

    def flip(self):
        """水平反転（左右反転）"""
        self.matrix = [list(reversed(row)) for row in self.matrix]


# --------------------------
# ゲームボード関係の関数
# --------------------------
def create_board():
    """空のボードを作成（各セルは None ）"""
    board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
    return board


def valid_position(tetromino, board, adj_x=0, adj_y=0):
    """
    テトリミノがボード内に収まり、かつ固定ブロックと重ならないかを判定する。
    adj_x, adj_y を加えた位置が有効かチェックします。
    """
    for i, row in enumerate(tetromino.matrix):
        for j, cell in enumerate(row):
            if cell is not None:
                x = tetromino.x + j + adj_x
                y = tetromino.y + i + adj_y
                if x < 0 or x >= BOARD_WIDTH or y < 0 or y >= BOARD_HEIGHT:
                    return False
                if board[y][x] is not None:
                    return False
    return True


def add_to_board(tetromino, board):
    """落下中のテトリミノをボードに固定する"""
    for i, row in enumerate(tetromino.matrix):
        for j, cell in enumerate(row):
            if cell is not None:
                # 数字とテトリミノの色をタプルで保存
                board[tetromino.y + i][tetromino.x + j] = (cell, tetromino.color)


def clear_lines(board):
    """
    ボード上の各行について、すべてのセルが埋まっている（Noneでない）
    かつその行の数字の合計が 50 以上ならその行を消去する。
    消去された行の数だけ、上部に空行を追加します。
    """
    new_board = []
    lines_cleared = 0
    for row in board:
        if all(cell is not None for cell in row) and sum(cell[0] for cell in row) >= 50:
            lines_cleared += 1
        else:
            new_board.append(row)
    for _ in range(lines_cleared):
        new_board.insert(0, [None for _ in range(BOARD_WIDTH)])
    return new_board, lines_cleared


# --------------------------
# 描画関数
# --------------------------
def draw_board(screen, board, current_tetromino, font):
    """ボード上の固定ブロックと、落下中のテトリミノを描画"""
    # 固定ブロックの描画
    for y, row in enumerate(board):
        for x, cell in enumerate(row):
            rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            if cell is not None:
                block_number, block_color = cell
                pygame.draw.rect(screen, block_color, rect)
                text = font.render(str(block_number), True, (255, 255, 255))
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)
            else:
                pygame.draw.rect(screen, GRID_COLOR, rect, 1)
    # 落下中のテトリミノの描画
    if current_tetromino is not None:
        for i, row in enumerate(current_tetromino.matrix):
            for j, cell in enumerate(row):
                if cell is not None:
                    x = current_tetromino.x + j
                    y = current_tetromino.y + i
                    rect = pygame.Rect(
                        x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE
                    )
                    pygame.draw.rect(screen, current_tetromino.color, rect)
                    text = font.render(str(cell), True, (255, 255, 255))
                    text_rect = text.get_rect(center=rect.center)
                    screen.blit(text, text_rect)


# --------------------------
# メインループ
# --------------------------
import asyncio


async def main():
    pygame.init()
    screen = pygame.display.set_mode(
        (BOARD_WIDTH * BLOCK_SIZE, BOARD_HEIGHT * BLOCK_SIZE)
    )
    pygame.display.set_caption("数字テトリス")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 20)

    board = create_board()
    # ランダムにテトリミノ（形状とそのキー）を選択
    shape_key, shape_matrix = random.choice(list(SHAPES.items()))
    current_tetromino = Tetromino(shape_key, shape_matrix)
    pygame.time.set_timer(DROP_EVENT, DROP_INTERVAL)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == DROP_EVENT:
                # 一定間隔でテトリミノを下に移動
                if valid_position(current_tetromino, board, 0, 1):
                    current_tetromino.y += 1
                else:
                    # これ以上下に移動できなければボードに固定
                    add_to_board(current_tetromino, board)
                    board, cleared = clear_lines(board)
                    shape_key, shape_matrix = random.choice(list(SHAPES.items()))
                    current_tetromino = Tetromino(shape_key, shape_matrix)
                    # 新たなテトリミノが配置できなければゲームオーバー
                    if not valid_position(current_tetromino, board):
                        print("Game Over")
                        running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    if valid_position(current_tetromino, board, -1, 0):
                        current_tetromino.x -= 1
                elif event.key == pygame.K_RIGHT:
                    if valid_position(current_tetromino, board, 1, 0):
                        current_tetromino.x += 1
                elif event.key == pygame.K_DOWN:
                    if valid_position(current_tetromino, board, 0, 1):
                        current_tetromino.y += 1
                elif event.key == pygame.K_UP:
                    # 回転操作
                    old_matrix = [
                        row[:] for row in current_tetromino.matrix
                    ]  # deep copy
                    current_tetromino.rotate()
                    if not valid_position(current_tetromino, board):
                        current_tetromino.matrix = old_matrix  # 無効なら元に戻す
                elif event.key == pygame.K_z:
                    # 裏返す操作（水平反転）
                    old_matrix = [row[:] for row in current_tetromino.matrix]
                    current_tetromino.flip()
                    if not valid_position(current_tetromino, board):
                        current_tetromino.matrix = old_matrix

        screen.fill(BACKGROUND_COLOR)
        draw_board(screen, board, current_tetromino, font)
        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(0)  # 引数は0で固定

    pygame.quit()
    sys.exit()


asyncio.run(main())
