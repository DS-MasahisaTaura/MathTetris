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
SHAPES = {
    "I": [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
    "S": [[0, 1, 1], [1, 1, 0], [0, 0, 0]],
    "Z": [[1, 1, 0], [0, 1, 1], [0, 0, 0]],
    "J": [[1, 0, 0], [1, 1, 1], [0, 0, 0]],
    "L": [[0, 0, 1], [1, 1, 1], [0, 0, 0]],
}

# 各形状ごとの色の定義
SHAPE_COLORS = {
    "I": (0, 255, 255),  # シアン
    "O": (255, 0, 255),  # マゼンタ
    "T": (128, 0, 128),  # パープル
    "S": (0, 255, 0),  # グリーン
    "Z": (255, 0, 0),  # レッド
    "J": (0, 0, 255),  # ブルー
    "L": (255, 165, 0),  # オレンジ
}


def rotate_matrix(matrix):
    return [list(row) for row in zip(*matrix[::-1])]


def flip_matrix(matrix):
    return [row[::-1] for row in matrix]


class Piece:
    def __init__(self, shape_key):
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
        self.x = BOARD_WIDTH // 2 - self.width // 2
        self.y = 0

    def rotate(self):
        self.matrix = [list(reversed(col)) for col in zip(*self.matrix)]
        self.height = len(self.matrix)
        self.width = len(self.matrix[0])

    def flip(self):
        self.matrix = flip_matrix(self.matrix)

    def get_cells(self):
        cells = []
        for dy, row in enumerate(self.matrix):
            for dx, val in enumerate(row):
                if val is not None:
                    cells.append((self.x + dx, self.y + dy, val))
        return cells


class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(width)] for _ in range(height)]

    def is_valid_position(self, piece, dx=0, dy=0):
        for x, y, _ in piece.get_cells():
            new_x = x + dx
            new_y = y + dy
            if new_x < 0 or new_x >= self.width or new_y >= self.height:
                return False
            if new_y >= 0 and self.grid[new_y][new_x] is not None:
                return False
        return True

    def add_piece(self, piece):
        for x, y, val in piece.get_cells():
            if y >= 0:
                self.grid[y][x] = (val, piece.color)

    def clear_lines(self):
        new_grid = []
        lines_cleared = 0
        for row in self.grid:
            if None not in row:
                row_sum = sum(cell[0] for cell in row if cell is not None)
                if row_sum >= 30:
                    lines_cleared += 1
                    continue
            new_grid.append(row)
        for _ in range(lines_cleared):
            new_grid.insert(0, [None for _ in range(self.width)])
        self.grid = new_grid
        return lines_cleared


def draw_board(surface, board, font):
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
    for x, y, val in piece.get_cells():
        if y >= 0:
            rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(surface, piece.color, rect)
            pygame.draw.rect(surface, DARKGRAY, rect, 1)
            text = font.render(str(val), True, WHITE)
            text_rect = text.get_rect(center=rect.center)
            surface.blit(text, text_rect)


class Button:
    def __init__(self, rect, label, action):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action

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
    pygame.display.set_caption("タップ操作テトリス")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 20)

    board = Board(BOARD_WIDTH, BOARD_HEIGHT)
    current_piece = Piece(random.choice(list(SHAPES.keys())))
    pygame.time.set_timer(DROP_EVENT, 500)

    btn_width = WINDOW_WIDTH // 5
    btn_height = CONTROL_HEIGHT
    btn_y = BOARD_HEIGHT * BLOCK_SIZE
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

            # MOUSEBUTTONDOWN によるタップ処理
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                if mouse_y >= BOARD_HEIGHT * BLOCK_SIZE:
                    for btn in buttons:
                        if btn.rect.collidepoint(mouse_x, mouse_y):
                            btn.action()

            # FINGERDOWN (タッチ) にも対応する
            elif event.type == pygame.FINGERDOWN:
                # FINGERDOWN の座標は正規化されているので、ピクセルに変換する
                finger_x = event.x * WINDOW_WIDTH
                finger_y = event.y * WINDOW_HEIGHT
                if finger_y >= BOARD_HEIGHT * BLOCK_SIZE:
                    for btn in buttons:
                        if btn.rect.collidepoint(finger_x, finger_y):
                            btn.action()

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

        screen.fill(BLACK)
        draw_board(screen, board, font)
        draw_piece(screen, current_piece, font)
        control_rect = pygame.Rect(
            0, BOARD_HEIGHT * BLOCK_SIZE, WINDOW_WIDTH, CONTROL_HEIGHT
        )
        pygame.draw.rect(screen, GRAY, control_rect)
        for btn in buttons:
            btn.draw(screen, font)

        pygame.display.flip()
        await asyncio.sleep(0)  # 引数は0で固定

    pygame.quit()
    sys.exit()


asyncio.run(main())
