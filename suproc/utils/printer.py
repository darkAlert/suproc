"""
AVA Single Unique Process
© AVA, 2025
"""


class TablePrinter:
    def __init__(self, header: str, alignment=None, logger=None):
        self.logger = logger
        self._header = header

        # Calculate maximum column widths:
        columns = header.split('|')[1:-1]
        self.col_widths = []
        for col in columns:
            self.col_widths.append(len(col)-2)

        if alignment:
            assert len(alignment) == len(self.col_widths)
        else:
            alignment = ['^']*len(self.col_widths)

        # Create a format string for printing:
        self.output = " | ".join([f"{{:{align}{width}.{width}}}" for width, align in zip(self.col_widths, alignment)])
        self.output = f"| {self.output} |"

        # Create separators:
        self._outer = f"# {'==='.join(['=' * width for width in self.col_widths])} #"
        self._inner = f"| {'-+-'.join(['-' * width for width in self.col_widths])} |"

    def print_special(self, item: str=None):
        if item is None:
            item = self._outer

        if item == 'outer':
            item = self._outer
        elif item == 'inner':
            item = self._inner
        elif item == 'header':
            item = self._header
        else:
            raise NotImplementedError

        if self.logger:
            self.logger.debug(item)
        else:
            print(item)

    def print_row(self, row: list or tuple):
        output = self.output.format(*row)
        if self.logger:
            self.logger.debug(output)
        else:
            print(output)
