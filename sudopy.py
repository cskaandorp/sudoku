from collections import OrderedDict
from optparse import Values
from turtle import pos
import pandas as pd
from sqlalchemy import over

class Sudoku:
    def __init__(self):
        self.puzzle = OrderedDict()
        for row in range(9):
            for col in range(9):
                self.puzzle[(col, row)] = {
                    'value': set(list(range(1, 10))),
                    'processed': False,
                    'square': (int(col / 3.0), int(row / 3.0))
                }


    def read_data(self, path):
        df = pd.read_csv(path)
        for _i, row in df.iterrows():
            self.set_cell(row['col']-1, row['row']-1, row['value'])


    def set_cell(self, col, row, value):
        if not type(value) == set:
            value = set([value])
        # set    
        self.puzzle[(col, row)]['value'] = value
        # and propagate
        self.__propagate_cell(col, row)


    def print_raw(self, what='all', col=None, row=None):
        if what == 'all':
            for cell in self.puzzle.keys():
                print(cell, self.puzzle[cell]['value'])
        elif what == 'cell':
            cell = (col, row)
            print(cell, self.puzzle[cell]['value'])
        elif what == 'col':
            for r in range(0, 9):
                cell = (col, r)
                print(cell, self.puzzle[cell]['value'])
        elif what == 'row':
            for c in range(0, 9):
                cell = (c, row)
                print(cell, self.puzzle[cell]['value'])
        else:
            square = self.puzzle[(col, row)]['square'] 
            for r in range(3 * square[1], 3 * square[1] + 3):
                for c in range(3 * square[0], 3 * square[0] + 3):
                    print((c, r), self.puzzle[(c, r)]['value'])
        print('----------------')



    def __repr__(self) -> str:
        result = ''
        for row in range(0, 9):
            if row % 3 == 0 and row > 0:
                result += '-----------------------\n'
            for col in range(0, 9):
                value = list(self.puzzle[(col, row)]['value'])
                if len(value) == 1:
                    result += f' { value[0] }'
                else:
                    result += ' X'
                if (col + 1) % 3 == 0 and col < 8:
                    result += ' |'
                if col == 8:
                    result += '\n'
        return result + '\n'


    def state(self):
        solved = [len(v['value']) == 1 for _k, v in self.puzzle.items()]
        score = solved.count(True) / 81.0
        return score, all(solved)


    def solve(self):
        solved = False
        score = 0.0
        # initial cleaning
        while not(solved):

            self.clean()
            self.infer()
            self.isolate()

            (new_score, solved) = s.state()

            if new_score > score:
                score = new_score
            else:
                break


    def clean(self):
        """remove potential value pv if in row/col/square 
        we have pv isolated"""
        for (col, row), _ in self.puzzle.items():
            self.__propagate_cell(col, row)


    def __propagate_cell(self, col, row):
        value = self.puzzle[(col, row)]
        if len(value['value']) == 1 and not value['processed']:
            isolated = value['value']
            # remove this value from row/col/square, row:
            for c in set(range(9)) - set([col]):
                self.puzzle[(c, row)]['value'] = self.puzzle[(c, row)]['value'] - isolated
            # column
            for r in set(range(9)) - set([row]):
                self.puzzle[(col, r)]['value'] = self.puzzle[(col, r)]['value'] - isolated
            # square
            # what are the square cells around isolated value
            square = value['square'] 
            for c in range(3 * square[0], 3 * square[0] + 3):
                for r in range(3 * square[1], 3 * square[1] + 3):
                    if c != col and r != row:
                        self.puzzle[(c, r)]['value'] = self.puzzle[(c, r)]['value'] - isolated
            self.puzzle[(col, row)]['processed'] = True


    def isolate(self):
        self.__isolate_column_wise()
        self.__isolate_row_wise()
        self.__isolate_square_wise()


    def __isolate_column_wise(self):
        """Go through every row per column, if one cell has a 
        unique value in its potential values for that row then 
        it must be the correct value"""
        for col in range(9):
            overview = { i: [] for i in range(1, 10) }
            for row in range(9):
                value = self.puzzle[(col, row)]['value']
                for v in value:
                    overview[v].append(row)
            # browse through the overview
            for value, rows in overview.items():
                # if there is only one row for this value
                if len(rows) == 1:
                    self.set_cell(col, rows[0], value)


    def __isolate_row_wise(self):
        """Go through every column per row, if one cell has a 
        unique value in its potential values for that column 
        then it must be the correct value"""
        for row in range(9):
            overview = { i: [] for i in range(1, 10) }
            for col in range(9):
                # create overview
                value = self.puzzle[(col, row)]['value']
                for v in value:
                    overview[v].append(col)
            # browse through the overview
            for value, cols in overview.items():
                # if there is only one row for this value
                if len(cols) == 1:
                    self.set_cell(cols[0], row, value)


    def __isolate_square_wise(self):
        """Go through every square, find all cells with their
        possible values, if one of them contains a unique value
        then that must be the correct value"""
        for s_row in range(0, 3):
            for s_col in range(0, 3):
                # collect all cells for this square
                cells = [pos for pos, value in self.puzzle.items() 
                    if value['square'] == (s_col, s_row)]
                # create an overview for this square
                overview = { i: [] for i in range(1, 10) }
                # iterate over cells and fill overview
                for col, row in cells:
                    value = self.puzzle[(col, row)]['value']
                    for v in value:
                        overview[v].append((col, row))
                # browse through the overview
                for value, positions in overview.items():
                    # if there is only one row for this value
                    if len(positions) == 1:
                        (col, row) = positions[0]
                        self.set_cell(col, row, value)

    
    def infer(self):
        self.__infer_column_wise()
        print('-------')


    def __infer_column_wise(self):
        for s_row in range(3):
            for s_col in range(3):
                square = (s_col, s_row)
                # I have my square, collect cells
                cells = { key:c for key, c in self.puzzle.items() 
                    if c['square'] == square }
                # process these cells column-wise within the square
                

                print(cells)
        # for col in range(9):
        #     # divide column into square segments
        #     indexes = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
        #     divisions = [
        #         [self.puzzle[(col, r)]['value'] for r in sub 
        #             if len(self.puzzle[(col, r)]['value']) > 1] 
        #         for sub in indexes
        #     ]
        #     unions = [set().union(*d) for d in divisions]
        #     inters = [unions[s].intersection(*d) for s, d in enumerate(divisions)]

                
                

            #print(divisions, unions, inters)
            # seg_1 = [self.puzzle[(col, r)]['values'] for r in [0, 1, 2]]
            # seg_2 = [self.puzzle[(col, r)]['values'] for r in [3, 4, 5]]
            # seg_3 = [self.puzzle[(col, r)]['values'] for r in [6, 7, 8]]
            # # remove known values
            # clean_1 = [v for v in seg_1 if len(v) > 1]
            # clean_2 = [v for v in seg_2 if len(v) > 1]
            # clean_3 = [v for v in seg_3 if len(v) > 1]





if __name__ == '__main__':
    s = Sudoku()
    s.read_data('puzzle3.csv')
    print(s)
    s.solve()
    print(s)


