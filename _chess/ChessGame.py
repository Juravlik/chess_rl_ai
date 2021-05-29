from __future__ import print_function
import sys
import time

sys.path.append('')
from Game import Game

import numpy as np
import chess
import chess.svg


def to_np(board):
    a = [0] * (8 * 8 * 6)
    for sq, pc in board.piece_map().items():
        a[sq * 6 + pc.piece_type - 1] = 1 if pc.color else -1
    return np.array(a)


def from_move(move):
    return move.from_square * 64 + move.to_square


def to_move(action):
    to_sq = action % 64
    from_sq = int(action / 64)
    return chess.Move(from_sq, to_sq)


def who(turn):
    return 1 if turn else -1


def mirror_move(move):
    return chess.Move(chess.square_mirror(move.from_square), chess.square_mirror(move.to_square))


CHECKMATE = 1
STALEMATE = 2
INSUFFICIENT_MATERIAL = 3
SEVENTYFIVE_MOVES = 4
FIVEFOLD_REPETITION = 5
FIFTY_MOVES = 6
THREEFOLD_REPETITION = 7


class ChessGame(Game):

    def __init__(self, n=8):
        pass

    def getInitBoard(self):
        # return initial board (numpy board)
        return chess.Board()

    def getBoardSize(self):
        # (a,b) tuple
        # 6 piece type
        return (8, 8, 6)

    def toArray(self, board):
        return to_np(board)

    def getActionSize(self):
        # return number of actions
        return 64 * 64
        # return self.n*self.n*16+1

    def getNextState(self, board, player, action):
        # if player takes action on board, return next (board,player)
        # action must be a valid move
        assert (who(board.turn) == player)
        move = to_move(action)

        if not board.turn:
            # assume the move comes from the canonical board...
            move = mirror_move(move)
        if move not in board.legal_moves:
            # could be a pawn promotion, which has an extra letter in UCI format
            move = chess.Move.from_uci(move.uci() + 'q')  # assume promotion to queen
            if move not in board.legal_moves:
                assert False, "%s not in %s" % (str(move), str(list(board.legal_moves)))
        board = board.copy()
        board.push(move)
        return (board, who(board.turn))

    def getValidMoves(self, board, player):
        # return a fixed size binary vector
        assert (who(board.turn) == player)
        acts = [0] * self.getActionSize()
        for move in board.legal_moves:
            acts[from_move(move)] = 1
        return np.array(acts)

    def getGameEnded(self, board, player):
        # return 0 if not ended, 1 if player 1 won, -1 if player 1 lost
        outcome = board.outcome()
        if outcome is not None:
            if outcome.winner is None:
                # draw return very little value
                return 1e-4
            else:
                return who(outcome.winner)
        return 0

    def getCanonicalForm(self, board, player):
        # return state if player==1, else return -state if player==-1
        assert (who(board.turn) == player)
        if board.turn:
            return board
        else:
            return board.mirror()

    def getSymmetries(self, board, pi):
        # mirror, rotational
        return [(board, pi)]

    def stringRepresentation(self, board):
        return board.fen()

    @staticmethod
    def display(board):
        print(board)


# import chess
# import chess.svg
#
# from PyQt5.QtSvg import QSvgWidget
# from PyQt5.QtWidgets import QApplication, QWidget
#
#
# class MainWindow(QWidget):
#     def __init__(self, board=chess.Board()):
#         super().__init__()
#
#         self.setGeometry(100, 100, 1000, 1000)
#
#         self.widgetSvg = QSvgWidget(parent=self)
#         self.widgetSvg.setGeometry(10, 10, 980, 980)
#
#         self.chessboard = board
#
#         self.chessboardSvg = chess.svg.board(self.chessboard).encode("UTF-8")
#         self.widgetSvg.load(self.chessboardSvg)
#
#     def nextMove(self, event):
#         self.chessboard.push(event)
#         self.chessboardSvg = chess.svg.board(self.chessboard).encode("UTF-8")
#         self.widgetSvg.load(self.chessboardSvg)
#         self.widgetSvg.update()

# def paintEvent(self, event):
#     self.chessboard.push(event)
#     self.chessboardSvg = chess.svg.board(self.chessboard).encode("UTF-8")
#     self.widgetSvg.load(self.chessboardSvg)


import chess
import chess.svg
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QDialog, QWidget, QRadioButton, QPushButton, QButtonGroup, QGroupBox, QHBoxLayout, \
    QVBoxLayout
import sys


class ChessBoard(QWidget, chess.Board):
    """
       BRIEF  An interactive chessboard that only allows legal moves
    """

    ReadyForNextMove = pyqtSignal(str)
    GameOver = pyqtSignal()

    def __init__(self, parent=None):
        """
           BRIEF  Initialize the chessboard
        """
        super().__init__(parent)
        self.setWindowTitle("Chess")

        self.svg_xy = 50  # top left x,y-pos of chessboard
        self.board_size = 600  # size of chessboard
        self.margin = 0.05 * self.board_size
        self.square_size = (self.board_size - 2 * self.margin) / 8.0
        wnd_wh = self.board_size + 2 * self.svg_xy

        self.setMinimumSize(wnd_wh, wnd_wh)
        self.svg_widget = QSvgWidget(parent=self)
        self.svg_widget.setGeometry(self.svg_xy, self.svg_xy, self.board_size, self.board_size)

        self.last_click = None
        self.DrawBoard()

    @pyqtSlot(QWidget)
    def mousePressEvent(self, event):
        """
           BRIEF  Update the board state based on user clicks
                  If the state changes, update the svg widget
        """
        if self.LeftClickedBoard(event):
            this_click = self.GetClicked(event)

            if self.last_click:
                if self.last_click != this_click:
                    uci = self.last_click + this_click
                    self.ApplyMove(uci + self.GetPromotion(uci))
            self.last_click = this_click

    def GetPromotion(self, uci):
        """
           BRIEF  Get the uci piece type the pawn will be promoted to
        """
        if chess.Move.from_uci(uci + 'q') in self.legal_moves:
            dialog = PromotionDialog(self)
            if dialog.exec() == QDialog.Accepted:
                return dialog.SelectedPiece()
        return ''

    @pyqtSlot(str)
    def ApplyMove(self, uci):
        """
           BRIEF  Apply a move to the board
        """
        move = chess.Move.from_uci(uci)
        if move in self.legal_moves:
            self.push(move)
            self.DrawBoard()

            print(self.fen())
            if not self.is_game_over():
                self.ReadyForNextMove.emit(self.fen())
            else:
                print("Game over!")
                self.GameOver.emit()
            sys.stdout.flush()


    def DrawBoard(self):
        """
           BRIEF  Redraw the chessboard based on board state
                  Highlight src and dest squares for last move
                  Highlight king if in check
        """
        self.svg_widget.load(self._repr_svg_().encode("utf-8"))

    def GetClicked(self, event):
        """
           BRIEF  Get the algebraic notation for the clicked square
        """
        top_left = self.svg_xy + self.margin
        file_i = int((event.x() - top_left) / self.square_size)
        rank_i = 7 - int((event.y() - top_left) / self.square_size)
        return chr(file_i + 97) + str(rank_i + 1)

    def LeftClickedBoard(self, event):
        """
           BRIEF  Check to see if they left-clicked on the chess board
        """
        topleft = self.svg_xy + self.margin
        bottomright = self.board_size + self.svg_xy - self.margin
        return all([
            event.buttons() == Qt.LeftButton,
            topleft < event.x() < bottomright,
            topleft < event.y() < bottomright,
        ])


class PromotionDialog(QDialog):
    """
       BRIEF  A dialog used to decide what to promote a pawn to
    """

    def __init__(self, parent=None):
        """
           BRIF  Initialize the dialog with buttons
        """
        super().__init__(parent, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        self.setWindowTitle("Promotion")

        radio_q = QRadioButton("q")
        radio_r = QRadioButton("r")
        radio_b = QRadioButton("b")
        radio_n = QRadioButton("n")

        self.button_group = QButtonGroup()
        self.button_group.addButton(radio_q)
        self.button_group.addButton(radio_r)
        self.button_group.addButton(radio_b)
        self.button_group.addButton(radio_n)

        radio_q.setChecked(True)

        radio_h_layout = QHBoxLayout()
        radio_h_layout.addWidget(radio_q)
        radio_h_layout.addWidget(radio_r)
        radio_h_layout.addWidget(radio_b)
        radio_h_layout.addWidget(radio_n)

        group_box = QGroupBox()
        group_box.setLayout(radio_h_layout)

        ok_button = QPushButton("Ok")
        cancel_button = QPushButton("Cancel")

        ok_button.released.connect(self.accept)
        cancel_button.released.connect(self.reject)

        button_h_layout = QHBoxLayout()
        button_h_layout.addWidget(ok_button)
        button_h_layout.addWidget(cancel_button)

        v_layout = QVBoxLayout()
        v_layout.addWidget(group_box)
        v_layout.addLayout(button_h_layout)
        self.setLayout(v_layout)

    def SelectedPiece(self):
        """
           BRIEF  Get the uci piece type the user selected from the dialog
        """
        return self.button_group.checkedButton().text()



if __name__ == "__main__":
    """
       BRIEF  Test the ChessBoard class
    """
    from PyQt5.QtWidgets import QApplication

    q_app = QApplication([])
    board = ChessBoard()
    board.show()


    q_app.exec()
