"""
Schach Pro – Kivy Android App (Überarbeitet)
=============================================
Vollständig Android-kompatibel:
  - Brett als GridLayout mit echten Buttons (kein Canvas-Absturz)
  - Figuren als Buchstaben (immer sichtbar, kein Font-Problem)
  - KI vs KI, Mensch vs KI, Mensch vs Mensch
  - Suchtiefe 1–3 einstellbar (Handy-Performance)
  - Sauberes Threading mit Stop-Event
  - Undo-Funktion für menschliche Züge
  - Piece-Square-Tables für verbesserte KI-Bewertung
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import get_color_from_hex

import threading
import time


# ═══════════════════════════════════════════════════════════════════════
#  KONSTANTEN
# ═══════════════════════════════════════════════════════════════════════

# -- Farben --
COLOR_BACKGROUND    = get_color_from_hex('#1a1a1a')
COLOR_ACCENT        = get_color_from_hex('#c9a227')
COLOR_DARK          = get_color_from_hex('#232120')
COLOR_SQUARE_LIGHT  = get_color_from_hex('#F0E9C5')
COLOR_SQUARE_DARK   = get_color_from_hex('#4A7C59')
COLOR_HIGHLIGHT_L   = get_color_from_hex('#F6F669')
COLOR_HIGHLIGHT_D   = get_color_from_hex('#BACA2B')
COLOR_SELECTED      = get_color_from_hex('#aadd66')
COLOR_CHECK         = get_color_from_hex('#cc2222')
COLOR_DOT           = get_color_from_hex('#88dd44')
COLOR_BTN_ACTIVE    = (0.79, 0.64, 0.15, 1)
COLOR_BTN_INACTIVE  = (0.22, 0.20, 0.18, 1)
COLOR_TEXT_DARK     = (0.1, 0.1, 0.1, 1)
COLOR_TEXT_LIGHT    = (0.9, 0.85, 0.75, 1)

# -- Figurendarstellung (Buchstaben, Android-sicher) --
PIECE_DISPLAY = {
    'K': 'Kg', 'Q': 'D', 'R': 'T', 'B': 'L', 'N': 'S', 'P': 'B',
    'k': 'Ks', 'q': 'd', 'r': 't', 'b': 'l', 'n': 's', 'p': 'b',
}

FILE_NAMES = 'abcdefgh'

# -- Startstellung --
INITIAL_BOARD = [
    ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
    ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
    [None] * 8,
    [None] * 8,
    [None] * 8,
    [None] * 8,
    ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
    ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R'],
]

# -- Figurenwerte --
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 950, 'K': 0,
}

# -- Piece-Square-Tables (aus Weiß-Perspektive, Rang 0 = oberer Rand) --
#    Positiver Wert = gute Position für die Figur
PST_PAWN = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

PST_KNIGHT = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

PST_BISHOP = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

PST_ROOK = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
]

PST_QUEEN = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

PST_KING_MIDGAME = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
]

PIECE_SQUARE_TABLES = {
    'P': PST_PAWN, 'N': PST_KNIGHT, 'B': PST_BISHOP,
    'R': PST_ROOK, 'Q': PST_QUEEN, 'K': PST_KING_MIDGAME,
}

# Bestrafung für Wiederholungsstellungen
CONTEMPT_VALUE = 70


# ═══════════════════════════════════════════════════════════════════════
#  SCHACH-ENGINE
# ═══════════════════════════════════════════════════════════════════════

def is_white_piece(piece: str) -> bool:
    """Prüft ob eine Figur weiß ist (Großbuchstabe)."""
    return piece is not None and piece == piece.upper()


def is_valid_square(row: int, col: int) -> bool:
    """Prüft ob die Koordinaten auf dem Brett liegen."""
    return 0 <= row < 8 and 0 <= col < 8


def generate_pseudo_moves(
    board: list, row: int, col: int,
    is_white: bool, castling: frozenset, en_passant: tuple
) -> list:
    """
    Erzeugt alle Pseudo-Züge einer Figur (ohne Schach-Prüfung).

    Returns:
        Liste von Zügen als (start_row, start_col, end_row, end_col)
    """
    piece = board[row][col]
    piece_type = piece.upper()
    moves = []

    def try_add(target_row: int, target_col: int):
        """Fügt einen Zug hinzu, wenn das Zielfeld gültig und nicht von eigener Figur besetzt ist."""
        if is_valid_square(target_row, target_col):
            target = board[target_row][target_col]
            if not target or is_white_piece(target) != is_white:
                moves.append((row, col, target_row, target_col))

    def slide(directions: list):
        """Erzeugt Züge für Gleitfiguren (Läufer, Turm, Dame)."""
        for d_row, d_col in directions:
            next_row, next_col = row + d_row, col + d_col
            while is_valid_square(next_row, next_col):
                target = board[next_row][next_col]
                if target:
                    if is_white_piece(target) != is_white:
                        moves.append((row, col, next_row, next_col))
                    break
                moves.append((row, col, next_row, next_col))
                next_row += d_row
                next_col += d_col

    if piece_type == 'P':
        direction = -1 if is_white else 1
        start_rank = 6 if is_white else 1

        # Einzelschritt vorwärts
        ahead_row = row + direction
        if is_valid_square(ahead_row, col) and not board[ahead_row][col]:
            moves.append((row, col, ahead_row, col))
            # Doppelschritt vom Startrang
            double_row = row + 2 * direction
            if row == start_rank and not board[double_row][col]:
                moves.append((row, col, double_row, col))

        # Schlagen (diagonal)
        for d_col in [-1, 1]:
            target_row, target_col = row + direction, col + d_col
            if is_valid_square(target_row, target_col):
                target = board[target_row][target_col]
                if target and is_white_piece(target) != is_white:
                    moves.append((row, col, target_row, target_col))
                elif en_passant == (target_row, target_col):
                    moves.append((row, col, target_row, target_col))

    elif piece_type == 'N':
        for d_row, d_col in [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1),
        ]:
            try_add(row + d_row, col + d_col)

    elif piece_type == 'B':
        slide([(-1, -1), (-1, 1), (1, -1), (1, 1)])

    elif piece_type == 'R':
        slide([(-1, 0), (1, 0), (0, -1), (0, 1)])

    elif piece_type == 'Q':
        slide([(-1, -1), (-1, 1), (1, -1), (1, 1),
               (-1, 0), (1, 0), (0, -1), (0, 1)])

    elif piece_type == 'K':
        # Normale Königszüge
        for d_row in [-1, 0, 1]:
            for d_col in [-1, 0, 1]:
                if d_row or d_col:
                    try_add(row + d_row, col + d_col)

        # Rochade
        king_rank = 7 if is_white else 0
        rook_char = 'R' if is_white else 'r'
        if row == king_rank and col == 4:
            kingside = 'K' if is_white else 'k'
            queenside = 'Q' if is_white else 'q'

            # Kurze Rochade (Königsseite)
            if (kingside in castling
                    and not board[king_rank][5]
                    and not board[king_rank][6]
                    and board[king_rank][7] == rook_char):
                moves.append((row, col, king_rank, 6))

            # Lange Rochade (Damenseite)
            if (queenside in castling
                    and not board[king_rank][3]
                    and not board[king_rank][2]
                    and not board[king_rank][1]
                    and board[king_rank][0] == rook_char):
                moves.append((row, col, king_rank, 2))

    return moves


def execute_move(
    board: list, move: tuple,
    castling: frozenset, en_passant: tuple
) -> tuple:
    """
    Führt einen Zug auf einer Kopie des Bretts aus.

    Returns:
        (neues_brett, neue_rochade, neues_en_passant, geschlagene_figur)
    """
    new_board = [list(rank) for rank in board]
    start_row, start_col, end_row, end_col = move
    piece = new_board[start_row][start_col]
    piece_type = piece.upper()
    captured = new_board[end_row][end_col]
    new_en_passant = None

    # Figur bewegen
    new_board[end_row][end_col] = piece
    new_board[start_row][start_col] = None

    # Bauern-Sonderregeln
    if piece_type == 'P':
        # Umwandlung (automatisch zur Dame)
        if end_row == 0:
            new_board[end_row][end_col] = 'Q'
        elif end_row == 7:
            new_board[end_row][end_col] = 'q'

        # En-Passant-Schlagen
        elif en_passant == (end_row, end_col):
            capture_row = end_row + (1 if is_white_piece(piece) else -1)
            captured = new_board[capture_row][end_col]
            new_board[capture_row][end_col] = None

        # En-Passant-Feld setzen bei Doppelschritt
        if abs(end_row - start_row) == 2:
            new_en_passant = ((start_row + end_row) // 2, end_col)

    # Rochade: Turm umsetzen
    if piece_type == 'K':
        if start_col == 4 and end_col == 6:  # Kurze Rochade
            new_board[start_row][5] = new_board[start_row][7]
            new_board[start_row][7] = None
        elif start_col == 4 and end_col == 2:  # Lange Rochade
            new_board[start_row][3] = new_board[start_row][0]
            new_board[start_row][0] = None

    # Rochade-Rechte aktualisieren
    new_castling = set(castling)
    if piece_type == 'K':
        if is_white_piece(piece):
            new_castling -= {'K', 'Q'}
        else:
            new_castling -= {'k', 'q'}

    # Turm bewegt oder geschlagen → Rochade-Recht verlieren
    rook_positions = {
        'K': (7, 7), 'Q': (7, 0),
        'k': (0, 7), 'q': (0, 0),
    }
    for right, position in rook_positions.items():
        if (start_row, start_col) == position or (end_row, end_col) == position:
            new_castling.discard(right)

    return new_board, frozenset(new_castling), new_en_passant, captured


def is_square_attacked(board: list, row: int, col: int, by_white: bool) -> bool:
    """Prüft ob ein Feld von einer bestimmten Farbe angegriffen wird."""

    # Springerangriffe
    for d_row, d_col in [
        (-2, -1), (-2, 1), (-1, -2), (-1, 2),
        (1, -2), (1, 2), (2, -1), (2, 1),
    ]:
        nr, nc = row + d_row, col + d_col
        if is_valid_square(nr, nc):
            piece = board[nr][nc]
            if piece and piece.upper() == 'N' and is_white_piece(piece) == by_white:
                return True

    # Diagonale Angriffe (Läufer, Dame, König nah, Bauer nah)
    for d_row, d_col in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nr, nc = row + d_row, col + d_col
        distance = 0
        while is_valid_square(nr, nc):
            piece = board[nr][nc]
            if piece:
                if is_white_piece(piece) == by_white:
                    ptype = piece.upper()
                    if ptype in ('B', 'Q'):
                        return True
                    if distance == 0 and ptype == 'K':
                        return True
                    if distance == 0 and ptype == 'P':
                        # Weiße Bauern greifen nach oben an (d_row < 0 aus ihrer Sicht)
                        if by_white and d_row == -1:
                            return True
                        if not by_white and d_row == 1:
                            return True
                break
            nr += d_row
            nc += d_col
            distance += 1

    # Gerade Angriffe (Turm, Dame, König nah)
    for d_row, d_col in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = row + d_row, col + d_col
        distance = 0
        while is_valid_square(nr, nc):
            piece = board[nr][nc]
            if piece:
                if is_white_piece(piece) == by_white:
                    ptype = piece.upper()
                    if ptype in ('R', 'Q'):
                        return True
                    if distance == 0 and ptype == 'K':
                        return True
                break
            nr += d_row
            nc += d_col
            distance += 1

    return False


def find_king(board: list, is_white: bool) -> tuple:
    """Findet die Position des Königs einer Farbe."""
    king = 'K' if is_white else 'k'
    for row in range(8):
        for col in range(8):
            if board[row][col] == king:
                return row, col
    return None


def is_in_check(board: list, is_white: bool) -> bool:
    """Prüft ob der König einer Farbe im Schach steht."""
    king_square = find_king(board, is_white)
    return bool(king_square and is_square_attacked(board, king_square[0], king_square[1], not is_white))


def get_legal_moves(
    board: list, is_white: bool,
    castling: frozenset, en_passant: tuple
) -> list:
    """
    Erzeugt alle legalen Züge für eine Farbe.
    Filtert Pseudo-Züge, die den eigenen König im Schach lassen.
    """
    legal = []
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if not piece or is_white_piece(piece) != is_white:
                continue

            for move in generate_pseudo_moves(board, row, col, is_white, castling, en_passant):
                _, _, end_row, end_col = move
                piece_type = piece.upper()

                # Rochade: König darf nicht über angegriffenes Feld ziehen
                if piece_type == 'K' and abs(end_col - col) == 2:
                    if is_in_check(board, is_white):
                        continue
                    step = 1 if end_col > col else -1
                    path_attacked = any(
                        is_square_attacked(board, row, c, not is_white)
                        for c in range(col, end_col + step, step)
                    )
                    if path_attacked:
                        continue

                # Zug ausführen und prüfen ob eigener König im Schach steht
                new_board, _, _, _ = execute_move(board, move, castling, en_passant)
                if not is_in_check(new_board, is_white):
                    legal.append(move)

    return legal


# ── Bewertungsfunktion ────────────────────────────────────────────────

def evaluate_position(board: list, perspective_white: bool) -> int:
    """
    Bewertet eine Stellung aus Sicht einer Farbe.
    Nutzt Materialwerte und Piece-Square-Tables.
    """
    score = 0
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if not piece:
                continue

            piece_type = piece.upper()
            material = PIECE_VALUES.get(piece_type, 0)

            # PST-Index: für Weiß direkt, für Schwarz gespiegelt
            pst = PIECE_SQUARE_TABLES.get(piece_type)
            positional = 0
            if pst:
                if is_white_piece(piece):
                    positional = pst[row * 8 + col]
                else:
                    # Schwarz: Brett vertikal spiegeln
                    positional = pst[(7 - row) * 8 + col]

            total = material + positional
            if is_white_piece(piece):
                score += total
            else:
                score -= total

    return score if perspective_white else -score


# ── Alpha-Beta-Suche ──────────────────────────────────────────────────

def alpha_beta_search(
    board: list, depth: int, alpha: int, beta: int,
    is_white: bool, castling: frozenset, en_passant: tuple,
    stop_event: threading.Event, position_history: dict
) -> tuple:
    """
    Alpha-Beta-Suche mit Zugsortierung.

    Returns:
        (bewertung, bester_zug)
    """
    if stop_event.is_set():
        return 0, None

    moves = get_legal_moves(board, is_white, castling, en_passant)

    # Kein legaler Zug → Matt oder Patt
    if not moves:
        if is_in_check(board, is_white):
            return -29000, None  # Matt
        return -CONTEMPT_VALUE, None  # Patt (leichte Bestrafung)

    # Blattknoten → statische Bewertung
    if depth == 0:
        return evaluate_position(board, is_white), None

    # Zugsortierung: Schlagzüge zuerst (nach Wert der geschlagenen Figur)
    moves.sort(
        key=lambda m: -(PIECE_VALUES.get((board[m[2]][m[3]] or '').upper(), 0)),
    )

    best_score = -999999
    best_move = moves[0]

    for move in moves:
        if stop_event.is_set():
            break

        new_board, new_castling, new_ep, _ = execute_move(board, move, castling, en_passant)

        # Stellungswiederholung erkennen
        position_key = _board_to_key(new_board)
        new_history = dict(position_history)
        new_history[position_key] = new_history.get(position_key, 0) + 1

        if new_history[position_key] >= 2:
            score = -CONTEMPT_VALUE  # Wiederholung vermeiden
        else:
            score = -alpha_beta_search(
                new_board, depth - 1, -beta, -alpha,
                not is_white, new_castling, new_ep,
                stop_event, new_history,
            )[0]

        if score > best_score:
            best_score = score
            best_move = move
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break  # Beta-Cutoff

    return best_score, best_move


def find_best_move(
    board: list, is_white: bool,
    castling: frozenset, en_passant: tuple,
    max_depth: int, stop_event: threading.Event,
    position_history: dict,
) -> tuple:
    """
    Findet den besten Zug mittels iterativer Tiefensuche.
    Gibt None zurück, wenn kein legaler Zug existiert.
    """
    legal = get_legal_moves(board, is_white, castling, en_passant)
    if not legal:
        return None

    best = legal[0]
    for depth in range(1, max_depth + 1):
        if stop_event.is_set():
            break
        _, move = alpha_beta_search(
            board, depth, -999999, 999999,
            is_white, castling, en_passant,
            stop_event, dict(position_history),
        )
        if move and move in legal and not stop_event.is_set():
            best = move

    return best if best in legal else legal[0]


def _board_to_key(board: list) -> str:
    """Erzeugt einen kompakten String-Schlüssel für eine Stellung."""
    return ''.join(piece or '.' for rank in board for piece in rank)


# ═══════════════════════════════════════════════════════════════════════
#  SPIELZUSTAND (für Undo)
# ═══════════════════════════════════════════════════════════════════════

class GameState:
    """Speichert den vollständigen Spielzustand für Undo."""

    __slots__ = [
        'board', 'white_to_move', 'castling', 'en_passant',
        'position_history', 'halfmove_clock', 'move_number',
        'last_move', 'check_side',
    ]

    def __init__(
        self, board, white_to_move, castling, en_passant,
        position_history, halfmove_clock, move_number,
        last_move, check_side,
    ):
        self.board = [list(rank) for rank in board]
        self.white_to_move = white_to_move
        self.castling = castling
        self.en_passant = en_passant
        self.position_history = dict(position_history)
        self.halfmove_clock = halfmove_clock
        self.move_number = move_number
        self.last_move = last_move
        self.check_side = check_side


# ═══════════════════════════════════════════════════════════════════════
#  BRETT-WIDGET
# ═══════════════════════════════════════════════════════════════════════

class SquareButton(Button):
    """Ein einzelnes Schachfeld als Kivy-Button."""

    def __init__(self, row: int, col: int, **kwargs):
        super().__init__(**kwargs)
        self.row = row
        self.col = col
        self.piece = None
        self.is_light = (row + col) % 2 == 0
        self.is_selected = False
        self.is_highlighted = False
        self.is_move_dot = False
        self.is_in_check = False
        self.font_size = dp(20)
        self.bold = True
        self.border = (0, 0, 0, 0)
        self._apply_background()

    def update(
        self, piece: str, selected: bool,
        highlighted: bool, move_dot: bool, in_check: bool,
    ):
        """Aktualisiert Zustand und Darstellung des Felds."""
        self.piece = piece
        self.is_selected = selected
        self.is_highlighted = highlighted
        self.is_move_dot = move_dot
        self.is_in_check = in_check
        self._apply_background()

        if piece:
            self.text = PIECE_DISPLAY.get(piece, piece)
            # Weiße Figuren: dunkler Text auf hellem Grund
            # Schwarze Figuren: heller Text
            self.color = COLOR_TEXT_DARK if is_white_piece(piece) else (1, 1, 1, 1)
        elif move_dot:
            self.text = '•'
            self.color = (0.4, 0.85, 0.2, 1)
        else:
            self.text = ''

    def _apply_background(self):
        """Setzt die Hintergrundfarbe basierend auf dem Zustand."""
        if self.is_in_check:
            bg = (0.8, 0.13, 0.13, 1)
        elif self.is_selected:
            bg = (0.67, 0.87, 0.4, 1)
        elif self.is_highlighted:
            bg = (0.96, 0.96, 0.41, 1) if self.is_light else (0.73, 0.79, 0.17, 1)
        else:
            bg = (0.94, 0.91, 0.77, 1) if self.is_light else (0.29, 0.49, 0.35, 1)

        self.background_normal = ''
        self.background_color = bg


class BoardWidget(GridLayout):
    """8×8-Schachbrett aus SquareButtons."""

    def __init__(self, on_square_tap, **kwargs):
        super().__init__(cols=8, rows=8, spacing=1, **kwargs)
        self._on_tap = on_square_tap
        self.squares: dict = {}

        # Felder erzeugen (Rang 7 oben, Rang 0 unten)
        for rank in range(7, -1, -1):
            for file in range(8):
                square = SquareButton(rank, file)
                square.bind(
                    on_press=lambda btn, r=rank, c=file: self._on_tap(r, c)
                )
                self.squares[(rank, file)] = square
                self.add_widget(square)

    def refresh(
        self, board: list, selected: tuple,
        legal_targets: list, last_move: tuple,
        check_side: bool,
    ):
        """Aktualisiert alle Felder des Bretts."""
        for (row, col), square in self.squares.items():
            piece = board[row][col]
            is_selected = selected == (row, col)
            is_highlighted = bool(
                last_move and (
                    (last_move[0] == row and last_move[1] == col)
                    or (last_move[2] == row and last_move[3] == col)
                )
            )
            is_dot = (row, col) in legal_targets
            is_check = (
                (piece == 'K' and check_side is True)
                or (piece == 'k' and check_side is False)
            )
            square.update(piece, is_selected, is_highlighted, is_dot, is_check)


# ═══════════════════════════════════════════════════════════════════════
#  HAUPT-APP
# ═══════════════════════════════════════════════════════════════════════

class ChessApp(App):
    """Schach Pro – Kivy-App mit KI, Undo und konfigurierbaren Spielmodi."""

    MODE_LABELS = ['KI vs KI', 'Mensch vs KI', 'Mensch vs Mensch']
    MODE_KEYS = ['ai_vs_ai', 'human_vs_ai', 'human_vs_human']

    def __init__(self):
        super().__init__()
        # Spieleinstellungen
        self.mode: str = 'ai_vs_ai'
        self.human_plays_white: bool = True
        self.depth_white: int = 2
        self.depth_black: int = 2

        # Spielzustand
        self._init_game_state()

        # UI-Referenzen
        self.board_widget: BoardWidget = None
        self.status_label: Label = None
        self.log_label: Label = None
        self.clock_white_label: Label = None
        self.clock_black_label: Label = None

        # Threading
        self._stop_event = threading.Event()
        self._ai_busy = False

        # Undo-Verlauf
        self._history: list = []
        self._log_lines: list = []

    def _init_game_state(self):
        """Setzt den Spielzustand auf Anfangsstellung zurück."""
        self.board = [list(rank) for rank in INITIAL_BOARD]
        self.white_to_move = True
        self.castling = frozenset('KQkq')
        self.en_passant = None
        self.position_history: dict = {}
        self.halfmove_clock = 0
        self.move_number = 0
        self.last_move = None
        self.check_side = None
        self.selected_square = None
        self.legal_targets: list = []
        self.is_running = False
        self._ai_busy = False

    # ── UI aufbauen ───────────────────────────────────────────────────

    def build(self):
        Window.clearcolor = (0.1, 0.1, 0.1, 1)
        root = BoxLayout(orientation='vertical', spacing=dp(3), padding=dp(4))

        # Titel
        title = Label(
            text='♟  Schach Pro',
            size_hint_y=None, height=dp(32),
            font_size=dp(18), bold=True,
            color=list(COLOR_ACCENT) + [1],
        )
        root.add_widget(title)

        # Statuszeile
        self.status_label = Label(
            text='Bereit – drücke Start',
            size_hint_y=None, height=dp(22),
            font_size=dp(11), color=(0.7, 0.65, 0.5, 1),
        )
        root.add_widget(self.status_label)

        # Uhr Schwarz (oben)
        self.clock_black_label = Label(
            text='♚ Schwarz',
            size_hint_y=None, height=dp(26),
            font_size=dp(13), bold=True,
            color=(0.9, 0.4, 0.4, 1),
        )
        root.add_widget(self.clock_black_label)

        # Schachbrett
        self.board_widget = BoardWidget(on_square_tap=self.on_square_tap)
        root.add_widget(self.board_widget)
        self.board_widget.refresh(self.board, None, [], None, None)

        # Uhr Weiß (unten)
        self.clock_white_label = Label(
            text='♔ Weiß',
            size_hint_y=None, height=dp(26),
            font_size=dp(13), bold=True,
            color=(0.4, 0.9, 0.4, 1),
        )
        root.add_widget(self.clock_white_label)

        # Buttons
        button_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(4))
        buttons = [
            ('▶ Start', self.start_game, True),
            ('■ Stopp', self.stop_game, False),
            ('↺ Neu', self.new_game, False),
            ('↶ Undo', self.undo_move, False),
            ('⚙', self.open_settings, False),
        ]
        for label, callback, is_primary in buttons:
            btn = Button(
                text=label, font_size=dp(13),
                background_normal='',
                background_color=COLOR_BTN_ACTIVE if is_primary else COLOR_BTN_INACTIVE,
                color=COLOR_TEXT_DARK if is_primary else COLOR_TEXT_LIGHT,
            )
            btn.bind(on_press=lambda x, fn=callback: fn())
            button_row.add_widget(btn)
        root.add_widget(button_row)

        # Zugprotokoll
        scroll_view = ScrollView(size_hint_y=None, height=dp(80))
        self.log_label = Label(
            text='', font_size=dp(10),
            size_hint_y=None,
            color=(0.85, 0.8, 0.65, 1),
            halign='left', valign='top',
            text_size=(Window.width - dp(16), None),
        )
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        scroll_view.add_widget(self.log_label)
        root.add_widget(scroll_view)

        # Legende
        legend = Label(
            text=(
                'Weiß: Kg=König D=Dame T=Turm L=Läufer S=Springer B=Bauer\n'
                'Schwarz: Ks=König d=Dame t=Turm l=Läufer s=Springer b=Bauer'
            ),
            size_hint_y=None, height=dp(30),
            font_size=dp(8), color=(0.5, 0.5, 0.5, 1),
        )
        root.add_widget(legend)

        return root

    # ── Spielsteuerung ────────────────────────────────────────────────

    def start_game(self):
        """Startet ein neues Spiel im gewählten Modus."""
        if self.is_running:
            return

        self._init_game_state()
        self._history.clear()
        self._log_lines.clear()
        self.is_running = True
        self._stop_event.clear()
        self._update_status('Spiel läuft…')
        Clock.schedule_once(self._refresh_board, 0)

        if self.mode == 'ai_vs_ai':
            threading.Thread(target=self._ai_vs_ai_loop, daemon=True).start()
        elif self.mode == 'human_vs_ai':
            if self.human_plays_white:
                self._update_status('Dein Zug! (Weiß)')
            else:
                self._update_status('KI denkt…')
                threading.Thread(target=self._ai_single_turn, daemon=True).start()
        else:
            self._update_status('♙ Weiß am Zug')

    def stop_game(self):
        """Stoppt das laufende Spiel."""
        self._stop_event.set()
        self.is_running = False
        self._ai_busy = False
        self._update_status('Gestoppt.')

    def new_game(self):
        """Setzt das Spiel komplett zurück."""
        self.stop_game()
        Clock.schedule_once(lambda dt: self._do_new_game(), 0.2)

    def _do_new_game(self):
        self._init_game_state()
        self._history.clear()
        self._log_lines.clear()
        Clock.schedule_once(self._refresh_board, 0)
        self._update_status('Bereit – drücke Start')

    def undo_move(self):
        """Macht den letzten Zug rückgängig (nur im Mensch-Modus)."""
        if self.mode == 'ai_vs_ai' or self._ai_busy or not self._history:
            return

        # Bei Mensch vs KI: zwei Züge zurück (Mensch + KI)
        if self.mode == 'human_vs_ai' and len(self._history) >= 2:
            self._history.pop()  # KI-Zug rückgängig
            self._log_lines.pop()

        state = self._history.pop()
        if self._log_lines:
            self._log_lines.pop()

        self.board = state.board
        self.white_to_move = state.white_to_move
        self.castling = state.castling
        self.en_passant = state.en_passant
        self.position_history = state.position_history
        self.halfmove_clock = state.halfmove_clock
        self.move_number = state.move_number
        self.last_move = state.last_move
        self.check_side = state.check_side
        self.selected_square = None
        self.legal_targets = []

        Clock.schedule_once(self._refresh_board, 0)
        self._update_status('Zug zurückgenommen')

    # ── KI-Schleifen ──────────────────────────────────────────────────

    def _ai_vs_ai_loop(self):
        """KI gegen KI: Abwechselnd Züge berechnen."""
        while self.is_running and not self._stop_event.is_set():
            if self._check_game_end():
                return

            is_white = self.white_to_move
            color_name = 'Weiß' if is_white else 'Schwarz'
            self._update_status(f'{color_name} denkt…')
            self._ai_busy = True

            depth = self.depth_white if is_white else self.depth_black
            move = find_best_move(
                self.board, is_white, self.castling, self.en_passant,
                depth, self._stop_event, self.position_history,
            )

            self._ai_busy = False
            if self._stop_event.is_set():
                return

            if move:
                self._apply_move(move, is_white)
                Clock.schedule_once(self._refresh_board, 0)

            time.sleep(0.4)

    def _ai_single_turn(self):
        """Ein einzelner KI-Zug (für Mensch vs KI)."""
        if self._stop_event.is_set() or not self.is_running:
            return

        is_white = self.white_to_move
        color_name = 'Weiß' if is_white else 'Schwarz'
        self._update_status(f'{color_name} (KI) denkt…')
        self._ai_busy = True

        depth = self.depth_white if is_white else self.depth_black
        move = find_best_move(
            self.board, is_white, self.castling, self.en_passant,
            depth, self._stop_event, self.position_history,
        )

        self._ai_busy = False
        if self._stop_event.is_set() or not self.is_running:
            return

        if move:
            self._apply_move(move, is_white)
            Clock.schedule_once(self._refresh_board, 0)
            self._check_game_end()

    # ── Spielende prüfen ──────────────────────────────────────────────

    def _check_game_end(self) -> bool:
        """Prüft auf Matt, Patt, 50-Züge-Regel und Stellungswiederholung."""
        legal = get_legal_moves(self.board, self.white_to_move, self.castling, self.en_passant)

        if not legal:
            if is_in_check(self.board, self.white_to_move):
                winner = 'Schwarz' if self.white_to_move else 'Weiß'
                message = f'Schachmatt! {winner} gewinnt!'
            else:
                message = 'Remis – Patt!'
            self._end_game(message)
            return True

        if self.halfmove_clock >= 100:
            self._end_game('Remis – 50-Züge-Regel')
            return True

        position_key = _board_to_key(self.board)
        if self.position_history.get(position_key, 0) >= 3:
            self._end_game('Remis – 3× Wiederholung')
            return True

        return False

    def _end_game(self, message: str):
        """Beendet das Spiel mit einer Nachricht."""
        self._stop_event.set()
        self.is_running = False
        self._update_status(message)
        Clock.schedule_once(lambda dt: self._show_popup(message), 0.2)

    # ── Zug ausführen ─────────────────────────────────────────────────

    def _apply_move(self, move: tuple, is_white: bool):
        """Führt einen Zug aus und aktualisiert den gesamten Spielzustand."""
        # Zustand für Undo speichern
        self._history.append(GameState(
            self.board, self.white_to_move, self.castling, self.en_passant,
            self.position_history, self.halfmove_clock, self.move_number,
            self.last_move, self.check_side,
        ))

        piece = self.board[move[0]][move[1]]
        new_board, new_castling, new_ep, captured = execute_move(
            self.board, move, self.castling, self.en_passant,
        )

        self.board = new_board
        self.castling = new_castling
        self.en_passant = new_ep
        self.last_move = move
        self.white_to_move = not is_white
        self.move_number += 1

        # Halbzug-Uhr (für 50-Züge-Regel)
        if captured or (piece and piece.upper() == 'P'):
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # Schach-Status des Gegners
        opponent_in_check = is_in_check(self.board, not is_white)
        self.check_side = (not is_white) if opponent_in_check else None

        # Stellungswiederholung tracken
        position_key = _board_to_key(self.board)
        self.position_history[position_key] = self.position_history.get(position_key, 0) + 1

        # Zugnotation im Protokoll
        piece_name = PIECE_DISPLAY.get(piece, '?')
        capture_str = f'×{PIECE_DISPLAY.get(captured, captured)}' if captured else ''
        check_str = '+' if opponent_in_check else ''
        start_str = f'{FILE_NAMES[move[1]]}{8 - move[0]}'
        end_str = f'{FILE_NAMES[move[3]]}{8 - move[2]}'
        entry = f'{self.move_number}. {piece_name}{start_str}{capture_str}{end_str}{check_str}'
        self._log_lines.append(entry)

    # ── Feld-Tap-Handler ──────────────────────────────────────────────

    def on_square_tap(self, row: int, col: int):
        """Verarbeitet einen Tap auf ein Schachfeld."""
        if not self.is_running or self._ai_busy:
            return

        # KI vs KI: kein menschlicher Eingriff
        if self.mode == 'ai_vs_ai':
            return

        # Wer darf klicken?
        if self.mode == 'human_vs_ai':
            if self.white_to_move != self.human_plays_white:
                return  # KI ist am Zug
            human_is_white = self.human_plays_white
        else:
            human_is_white = self.white_to_move

        # Erste Auswahl: Figur wählen
        if self.selected_square is None:
            piece = self.board[row][col]
            if piece and is_white_piece(piece) == human_is_white:
                self.selected_square = (row, col)
                all_legal = get_legal_moves(self.board, human_is_white, self.castling, self.en_passant)
                self.legal_targets = [
                    (m[2], m[3]) for m in all_legal
                    if m[0] == row and m[1] == col
                ]
        else:
            # Zweite Auswahl: Zug ausführen oder andere Figur wählen
            all_legal = get_legal_moves(self.board, human_is_white, self.castling, self.en_passant)
            attempted_move = (self.selected_square[0], self.selected_square[1], row, col)

            if attempted_move in all_legal:
                # Legaler Zug → ausführen
                self.selected_square = None
                self.legal_targets = []
                self._apply_move(attempted_move, human_is_white)
                Clock.schedule_once(self._refresh_board, 0)

                if not self._check_game_end():
                    if self.mode == 'human_vs_ai':
                        threading.Thread(target=self._ai_single_turn, daemon=True).start()
                    else:
                        color = '♙ Weiß' if self.white_to_move else '♟ Schwarz'
                        self._update_status(f'{color} am Zug')
                return
            else:
                # Andere eigene Figur auswählen?
                piece = self.board[row][col]
                if piece and is_white_piece(piece) == human_is_white:
                    self.selected_square = (row, col)
                    self.legal_targets = [
                        (m[2], m[3]) for m in all_legal
                        if m[0] == row and m[1] == col
                    ]
                else:
                    self.selected_square = None
                    self.legal_targets = []

        Clock.schedule_once(self._refresh_board, 0)

    # ── UI-Helfer ─────────────────────────────────────────────────────

    def _refresh_board(self, dt=0):
        """Aktualisiert Brett, Uhren und Zugprotokoll."""
        self.board_widget.refresh(
            self.board, self.selected_square, self.legal_targets,
            self.last_move, self.check_side,
        )
        is_white_turn = self.white_to_move
        self.clock_white_label.text = '♔ Weiß' + (' ◀ am Zug' if is_white_turn else '')
        self.clock_black_label.text = '♚ Schwarz' + (' ◀ am Zug' if not is_white_turn else '')
        self.log_label.text = '\n'.join(self._log_lines[-20:])

    def _update_status(self, text: str):
        """Setzt den Statustext (threadsicher)."""
        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', text), 0)

    def _show_popup(self, message: str):
        """Zeigt ein Popup-Fenster mit einer Nachricht."""
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        content.add_widget(Label(
            text=message, font_size=dp(16),
            color=COLOR_TEXT_LIGHT,
        ))
        ok_button = Button(
            text='OK', size_hint_y=None, height=dp(40),
            background_normal='', background_color=COLOR_BTN_ACTIVE,
            color=COLOR_TEXT_DARK,
        )
        content.add_widget(ok_button)

        popup = Popup(
            title='Spiel beendet', content=content,
            size_hint=(0.8, 0.4), auto_dismiss=False,
        )
        ok_button.bind(on_press=popup.dismiss)
        popup.open()

    # ── Einstellungen ─────────────────────────────────────────────────

    def open_settings(self):
        """Öffnet das Einstellungs-Popup."""
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # -- Spielmodus --
        content.add_widget(self._section_label('Spielmodus'))
        mode_row = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(4))
        for label, key in zip(self.MODE_LABELS, self.MODE_KEYS):
            is_active = self.mode == key
            btn = Button(
                text=label, font_size=dp(11),
                background_normal='',
                background_color=COLOR_BTN_ACTIVE if is_active else COLOR_BTN_INACTIVE,
                color=COLOR_TEXT_DARK if is_active else COLOR_TEXT_LIGHT,
            )

            def on_mode_select(instance, mode_key=key):
                self.mode = mode_key
                popup.dismiss()
                self.open_settings()

            btn.bind(on_press=on_mode_select)
            mode_row.add_widget(btn)
        content.add_widget(mode_row)

        # -- Farbwahl (nur bei Mensch vs KI) --
        if self.mode == 'human_vs_ai':
            content.add_widget(self._section_label('Ich spiele'))
            color_row = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(4))
            for label, value in [('Weiß ♙', True), ('Schwarz ♟', False)]:
                is_active = self.human_plays_white == value
                btn = Button(
                    text=label, font_size=dp(12),
                    background_normal='',
                    background_color=COLOR_BTN_ACTIVE if is_active else COLOR_BTN_INACTIVE,
                    color=COLOR_TEXT_DARK if is_active else COLOR_TEXT_LIGHT,
                )

                def on_color_select(instance, val=value):
                    self.human_plays_white = val
                    popup.dismiss()
                    self.open_settings()

                btn.bind(on_press=on_color_select)
                color_row.add_widget(btn)
            content.add_widget(color_row)

        # -- KI-Stärke --
        strength_options = [
            ('♙ Weiß Stärke', 'depth_white'),
            ('♟ Schwarz Stärke', 'depth_black'),
        ]
        for label, attribute in strength_options:
            content.add_widget(self._section_label(label))
            depth_row = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(4))
            for depth, depth_label in [(1, 'Einfach'), (2, 'Mittel'), (3, 'Stark')]:
                current_depth = getattr(self, attribute)
                is_active = current_depth == depth
                btn = Button(
                    text=depth_label, font_size=dp(11),
                    background_normal='',
                    background_color=COLOR_BTN_ACTIVE if is_active else COLOR_BTN_INACTIVE,
                    color=COLOR_TEXT_DARK if is_active else COLOR_TEXT_LIGHT,
                )

                def on_depth_select(instance, attr=attribute, val=depth):
                    setattr(self, attr, val)
                    popup.dismiss()
                    self.open_settings()

                btn.bind(on_press=on_depth_select)
                depth_row.add_widget(btn)
            content.add_widget(depth_row)

        # Schließen-Button
        close_button = Button(
            text='Schließen', size_hint_y=None, height=dp(42),
            background_normal='', background_color=COLOR_BTN_INACTIVE,
            color=COLOR_TEXT_LIGHT, font_size=dp(13),
        )
        content.add_widget(close_button)

        popup = Popup(
            title='⚙ Einstellungen', content=content,
            size_hint=(0.95, 0.85), auto_dismiss=True,
        )
        close_button.bind(on_press=popup.dismiss)
        popup.open()

    @staticmethod
    def _section_label(text: str) -> Label:
        """Erzeugt ein Abschnitts-Label für die Einstellungen."""
        return Label(
            text=text, size_hint_y=None, height=dp(24),
            font_size=dp(13), color=list(COLOR_ACCENT) + [1],
            halign='left',
        )


# ═══════════════════════════════════════════════════════════════════════
#  EINSTIEGSPUNKT
# ═══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    ChessApp().run()
