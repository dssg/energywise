from itertools import izip_longest


def grouper(n, iterable, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)

n = 64

with open('timeStamps.csv') as f:
    for i, g in enumerate(grouper(n, f, fillvalue=''), 1):
        with open('timeStamps_{0}'.format(i * n), 'w') as fout:
            fout.writelines(g)

