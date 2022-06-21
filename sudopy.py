import argparse
import pandas as pd

from collections import OrderedDict
from itertools import chain, combinations, groupby


# provide all possible combinations with a minimum length of <min>
def all_subsets(collection, min):
    result = []
    if len(collection) >= min:
        result = chain(
            *map(
                lambda x: combinations(collection, x),
                range(min, len(collection)+1)
            )
        )
    return result

# checks if every element is identical in iterable
def all_equal(iterable):
    g = groupby(iterable)
    return next(g, True) and not next(g, False)

    

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
        self.clean()


    def print_raw(self, what='all', col=None, row=None):
        if what == 'all':
            for cell in self.puzzle.keys():
                print(cell, self.puzzle[cell]['value'])
        elif what == 'overview':
            result = ''
            for row in range(0, 9):
                if row % 3 == 0 and row > 0:
                    result += '-----------------------\n'
                for col in range(0, 9):
                    value = list(self.puzzle[(col, row)]['value'])
                    if len(value) == 1:
                        result += f' { value[0] }'
                    else:
                        result += f' {value}'
                    if (col + 1) % 3 == 0 and col < 8:
                        result += ' |'
                    if col == 8:
                        result += '\n'
            print(result + '\n')
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


    def dump_in_list(self):
        result = []
        for (c, r), value in self.puzzle.items():
            values = list(value['value'])
            if len(values) == 1:
                result.append((c + 1, r + 1, values[0]))

        return result


    def state(self):
        solved = [
            len(v['value']) == 1 for _k, v in self.puzzle.items()
        ]
        score = solved.count(True) / 81.0
        return score, all(solved)


    def solve(self):
        solved = False
        score = 0.0
        counter = 0
        # initial cleaning
        while not(solved):
            self.clean()
            self.infer()
            self.isolate()
            self.x_wing()
            counter += 1
            (new_score, solved) = s.state()
            if new_score > score:
                score = new_score
            else:
                break
        return solved, counter


    def clean(self):
        """remove potential value pv if in row/col/square 
        we have pv isolated"""
        score, _ = self.state()
        while(True):
            # clean all cells by propagating isolated value
            for (col, row), _ in self.puzzle.items():
                self.__propagate_cell(col, row)
            # assessment
            new_score, _ = self.state()
            if new_score > score:
                score = new_score
            else:
                break



    def __propagate_cell(self, col, row):
        value = self.puzzle[(col, row)]
        if len(value['value']) == 1 and not value['processed']:
            isolated = value['value']
            self.__propagate_row(col, row, isolated) # row
            self.__propagate_column(col, row, isolated) # column
            self.__propagate_square(col, row, isolated) # square
            self.puzzle[(col, row)]['processed'] = True

    def __propagate_row(self, col, row, values):
        if type(col) != set:
            col = set([col])
        for c in set(range(9)) - col:
            self.puzzle[(c, row)]['value'] = \
                self.puzzle[(c, row)]['value'] - values

    def __propagate_column(self, col, row, values):
        # column
        if type(row) != set:
            row = set([row])
        for r in set(list(range(9))) - row:
            self.puzzle[(col, r)]['value'] = \
                self.puzzle[(col, r)]['value'] - values


    def __propagate_square(self, col, row, values):
        # square
        square = self.puzzle[(col, row)]['square'] 
        for c in range(3 * square[0], 3 * square[0] + 3):
            for r in range(3 * square[1], 3 * square[1] + 3):
                if c != col and r != row:
                    self.puzzle[(c, r)]['value'] = \
                        self.puzzle[(c, r)]['value'] - values
            



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

    
    def infer(self, counter=None):
        self.__infer_column_wise()
        self.__infer_row_wise()


    def __infer_column_wise(self):
        # this is about mini columns
        for s_row in range(3):
            for s_col in range(3):
                # per square
                segs = []
                col_range = range(3 * s_col, 3 * s_col + 3)
                row_range = range(3 * s_row, 3 * s_row + 3)
                for c in col_range:
                    mini_col = []
                    for r in row_range:
                        cell_value = self.puzzle[(c, r)]['value']
                        if len(cell_value) > 1:
                            mini_col.append(cell_value)
                    # mini col is ready
                    segs.append(set().union(*mini_col))
                # I have my 3 segments (columns) of the square
                # now we start comparing
                [seg_0, seg_1, seg_2] = segs
                col_0 = seg_0 - seg_1 - seg_2
                col_1 = seg_1 - seg_0 - seg_2
                col_2 = seg_2 - seg_0 - seg_1

                if len(col_0) > 0 and len(col_0) <= 3:
                    self.__propagate_column(col_range[0], set(row_range), col_0)
                    self.clean()
                if len(col_1) > 0 and len(col_1) <= 3:
                    self.__propagate_column(col_range[1], set(row_range), col_1)
                    self.clean()
                if len(col_2) > 0 and len(col_2) <= 3:
                    self.__propagate_column(col_range[2], set(row_range), col_2)
                    self.clean()

    def __infer_row_wise(self):
        # this is about mini rows
        for s_row in range(3):
            for s_col in range(3):
                # per square
                segs = []
                col_range = range(3 * s_col, 3 * s_col + 3)
                row_range = range(3 * s_row, 3 * s_row + 3)
                for r in row_range:
                    mini_row = []
                    for c in col_range:
                        cell_value = self.puzzle[(c, r)]['value']
                        if len(cell_value) > 1:
                            mini_row.append(cell_value)
                    # mini row is ready
                    segs.append(set().union(*mini_row))
                # I have my 3 segments (columns) of the square
                # now we start comparing
                
                [seg_0, seg_1, seg_2] = segs
                row_0 = seg_0 - seg_1 - seg_2
                row_1 = seg_1 - seg_0 - seg_2
                row_2 = seg_2 - seg_0 - seg_1

                if len(row_0) > 0 and len(row_0) <= 3:
                    self.__propagate_row(set(col_range), row_range[0], row_0)
                    self.clean()
                if len(row_1) > 0 and len(row_1) <= 3:
                    self.__propagate_row(set(col_range), row_range[1], row_1)
                    self.clean()
                if len(row_2) > 0 and len(row_2) <= 3:
                    self.__propagate_row(set(col_range), row_range[2], row_2)
                    self.clean()


    def x_wing(self):
        numbers = { i:[] for i in range(1, 10) }
        for coords, value in self.puzzle.items():
            values = value['value']
            if len(values) > 1:
                for v in values:
                    numbers[v].append(coords)
        # at this point I have per possible value a list
        # of coordinates where the value can be found. I have an "x-wing"
        # if the value can be found in different rows in the same columns
        for num in numbers.keys():
            # give me an overview in which rows this value can be found
            rows = sorted(list(set([ r for (_, r) in numbers[num] ])))

            # and I need to know per row in which columns I can find this value
            cols = { r: [] for r in rows }
            for c, r in numbers[num]:
                cols[r].append(c)
            # and convert the collection of columns into sets to facilitate 
            # an equality check, like [3, 4] is the same as [4, 3]
            cols = { r:set(c) for r, c in cols.items() }

            # now I want all possible permutations of these row-numbers, only 
            # take 2 or more rows (zero and 1 is not relevant), sort these 
            # combinations based on length to ensure I get the biggest 
            # combinations first
            row_combinations = sorted(
                list(all_subsets(rows, 2)), 
                reverse=True, 
                key=lambda x:len(x) 
            )
            # now I want the biggest possible X wing, that means as many rows 
            # as I can get in which this number can be found in the same 
            # columns
            for row_numbers in row_combinations:
                # for every row number in comb I want to know if <num> can 
                # be found in the same columns (per different row). If that's
                # the case, and the amount of columns is identical to the 
                # amount of rows, then we have an x-wing of order
                # len(row_numbers)
                column_positions = [ cols[r] for r in row_numbers]
                if all_equal(column_positions) and \
                    len(row_numbers) == len(column_positions[0]):
                    # we found an x-wing, we have to remove the occurrence of 
                    # <num> from all other rows in the columns we have in 
                    # column-positions
                    for c in column_positions[0]:
                        self.__propagate_column(c, set(row_numbers), {num})
                        self.clean()

                    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('puzzle', help='csv filename of puzzle')
    args = parser.parse_args()

    s = Sudoku()
    s.read_data(args.puzzle)
    print(s)
    solved, iterations = s.solve()
    print(s)
    state = 'Not solved' if not(solved) else 'Solved'
    print(f'{state} in {iterations} iterations')


