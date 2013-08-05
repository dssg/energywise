import matplotlib.pyplot as plt
from math import sqrt
import pylab as p

x = range(100)
y = [sqrt(i) for i in x]
# x[a:b:c]  <- from a to b in steps of c
x = x[::-1]
plt.plot(x,y,color='k',lw=2)
plt.fill_between(x,y,0,color='0.8')
plt.plot(40,2, marker='o', color='b')
plt.plot(20,4, marker='o', color='b')
plt.plot(71,2.6, marker='o', color='b')
plt.plot(30,5, marker='o', color='b')
plt.plot(55,4.5, marker='o', color='b')
plt.plot(67,5.2, marker='o', color='b')
plt.plot(16,7.6, marker='o', color='b')
plt.plot(78,2.9, marker='o', color='b')
plt.plot(42,6.2, marker='o', color='b')
plt.plot(32,5.8, marker='o', color='r')
plt.xlabel('Hours of operation')
plt.ylabel('Energy Consumption ($10,000)')
#p.arrow(32, 5.8, 40, 3, fc="k", ec="k",head_width=0.05, head_length=0.1)
plt.annotate('your building', xy=(32, 5.8),  xycoords='data',
                xytext=(-50, 30), textcoords='offset points',
                arrowprops=dict(arrowstyle="->")
                )
plt.show()


