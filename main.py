"""Text Diffing."""
import difflib
import sys
from pathlib import Path

from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import (QColor,
                         QIcon,
                         QSyntaxHighlighter,
                         QTextCharFormat)
from PyQt5.QtWidgets import (QAction,
                             QApplication,
                             QLabel,
                             QMainWindow,
                             QPlainTextEdit,
                             QPushButton,
                             QTextEdit,
                             qApp)

ORIG_TEXT = '.0000.txt'  # save original file here. Change it whatever you like
DUPL_TEXT = '.0001.txt'  # save duplicate text here.Change to anything you like


def count_texts(text):
    """Return a tuple containing num of words, characters and lines."""
    return len(text.split()), len(text), len(text.splitlines())


def format_text(color):
    """Return a QTextCharFormat with the given attributes."""
    _color = QColor()
    _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setBackground(_color)

    return _format


STYLES = {
    'plusSymbol': format_text('magenta'),
    'minusSymbol': format_text('magenta'),
}


class DiffHighlighter(QSyntaxHighlighter):

    """Syntax highlighter for the diff."""

    pSymbol = ['+', ]
    mSymbol = ['-', ]  # FIXME: this isn't working

    def __init__(self, document):
        """Initialize with few rules to highlight."""
        super().__init__(document)
        rules = []  # empty rules at first

        rules += [(r'%s' % o, 0, STYLES['minusSymbol'])
                  for o in DiffHighlighter.mSymbol]

        self.rules = [(QRegExp(pat + '.*'), index, fmt)
                      for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text."""
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)
            while index >= 0:
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)


class Window(QMainWindow):

    """Abstract window that will be used for all other windows."""

    def __init__(self):
        """Initialize this class window."""
        super().__init__()

        # delegate ui initialization to `initUI`
        self.initUI()

    def initUI(self):
        """Initialize UI thing-y."""
        # exit action button
        exit_action = QAction(QIcon('exit.png'), '&Exit', self)
        exit_action.setStatusTip('Exit Application')
        exit_action.triggered.connect(qApp.quit)

        # save action button
        save_action = QAction(QIcon('save.png'), '&Done?', self)
        save_action.setStatusTip('Save Application')
        save_action.triggered.connect(self.done_pressed)

        # add `save` and `exit` action to the `file` menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        file_menu.addAction(save_action)
        file_menu.addAction(exit_action)

        # done-button
        self.done_button = QPushButton('Done?', self)
        self.done_button.move(250, 10)
        # call `done_pressed` when btn is pressed.
        self.done_button.clicked[bool].connect(self.done_pressed)

        # set statusbar message initially
        self.statusBar().showMessage('Ready')

        # set geometry of the window
        self.setGeometry(400, 300, 350, 350)

    def run(self):
        """Run me."""
        self.show()

    def autosave(self):
        """Autosave the file as the user types."""
        # current working directory/ directory of this file
        file_path = Path(__file__)

        # currently the save_path is same as file_path.
        # But you can change it here if you'd like.
        # eg. `python
        # >>> save_path = file_path.with_name(self.SAVE_LOC) /'..' / 'texts'
        # O: 'texts'
        save_path = file_path.with_name(self.SAVE_LOC)

        # save the textbox contents to file.
        # Also aggregate few details about the text-input
        with save_path.open('w', encoding='utf8') as file:
            _text = str(self.text_edit.toPlainText())
            file.write(_text)
            num_words, num_chars, num_lines = count_texts(_text)

        # give few details in the status bar
        self.statusBar().showMessage('Text changed. Autosaving...  '
                                     f'{num_words} w   '
                                     f'{num_chars} c   '
                                     '&  '
                                     f'{num_lines} l.  ')

    def done_pressed(self):
        """When pressed `Done`, i am called."""
        pass  # do nothing unless overridden


class MainWindow(Window):

    """I am the chosen one for showing up for original text input."""

    def __init__(self):
        """Initialize main window."""
        super().__init__()
        self.SAVE_LOC = ORIG_TEXT  # save text to ORIG_TEXT

        self.initUI()

        self.original_text_edit_lbl = QLabel('Original text', self)
        self.original_text_edit_lbl.move(80, 70)

        self.original_text_edit = QPlainTextEdit(self)
        self.original_text_edit.setPlaceholderText("Enter original text here.")
        self.original_text_edit.setMinimumWidth(285)
        self.original_text_edit.move(50, 100)
        self.original_text_edit.setMinimumSize(100, 200)

        # when text changes, call `self.autosave` and saves automatically
        self.original_text_edit.textChanged.connect(self.autosave)

        self.text_edit = self.original_text_edit

        self.setWindowTitle('Original Text | CodeDiff')

        self.run()

    def done_pressed(self):
        """Pressed done? Disable btn and text editor."""
        self.original_text_edit.setDisabled(True)  # make text box uneditable
        self.done_button.setDisabled(True)  # disable this button
        self.statusBar().showMessage('Done. '
                                     "Now, you won't be able to edit anything "
                                     'in the input box.')

        # show other window  for duplicate text
        self.duplicate_window = DuplicateWindow()
        self.duplicate_window.show()


class DuplicateWindow(Window):

    """Show duplicate window for input."""

    def __init__(self):
        """Initialize duplicate window."""
        super().__init__()
        self.SAVE_LOC = DUPL_TEXT  # save text to DUPL_TEXT

        self.initUI()

        self.duplicate_text_edit_lbl = QLabel('Duplicate text', self)
        self.duplicate_text_edit_lbl.move(80, 70)

        self.duplicate_text_edit = QPlainTextEdit(self)
        self.duplicate_text_edit.setPlaceholderText(
            "Enter copy of original text here."
        )
        self.duplicate_text_edit.setMinimumWidth(285)
        self.duplicate_text_edit.move(50, 100)
        self.duplicate_text_edit.setMinimumSize(100, 200)

        self.duplicate_text_edit.textChanged.connect(self.autosave)

        self.text_edit = self.duplicate_text_edit

        self.setWindowTitle('Duplicate Text | CodeDiff')

        self.setGeometry(30, 300, 350, 350)

        self.run()

    def done_pressed(self):
        """Done pressed? Show diff."""
        self.diff_window = DiffWindow()
        self.diff_window.show()

    def autosave(self):
        """Override `autosave` and change diff as the user types."""
        super().autosave()
        try:
            self.diff_window.diff_text.setText('\n'.join(get_diffed_text()))
        except AttributeError:
            # This happens when the done isn't pressed at all.
            # So there's no any `diff_window`. I got this
            pass


class DiffWindow(Window):

    """Diff window."""

    def __init__(self):
        """Initialize diff window."""
        super().__init__()
        super().initUI()

        self.diff_text_lbl = QLabel('Diff', self)
        self.diff_text_lbl.move(80, 70)

        self.diff_text = QTextEdit(self)
        highlight = DiffHighlighter(self.diff_text.document())

        self.diff_text.append('\n'.join(get_diffed_text()))
        self.diff_text.setMinimumWidth(285)
        self.diff_text.setMinimumSize(100, 200)
        self.diff_text.move(50, 100)
        self.diff_text.setReadOnly(True)

        self.setGeometry(300, 300, 350, 350)

        self.done_button.setDisabled(True)

        self.setWindowTitle('Diff Text | CodeDiff')

        self.setGeometry(800, 300, 350, 350)

        self.run()


def get_diffed_text():
    """Diff the text from two files."""
    # original file
    original_file = (
        Path(__file__)
        .with_name(ORIG_TEXT)
        .open('r', encoding='utf8')
    )

    duplicate_file = (
        Path(__file__)
        .with_name(DUPL_TEXT)
        .open('r', encoding='utf8')
    )

    # compare and diff line by line
    diff = difflib.Differ()
    diff = diff.compare(
        original_file.read().splitlines(),
        duplicate_file.read().splitlines(),
    )

    return diff


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # initialize the window for original textinput window
    main_window = MainWindow()
    main_window.run()

    sys.exit(app.exec_())
