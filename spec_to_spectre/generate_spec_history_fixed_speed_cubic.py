import argparse


def f(t, v, a):
    return 1.0 + (t**3 * v) / (a**2 + t**2)


def df(t, v, a):
    return (3.0 * a**2 * t**2 + t**4) * v / (a**2 + t**2)**2


def d2f(t, v, a):
    return (2.0 * (3.0 * a**4 * t - a**2 * t**3)) * v / (a**2 + t**2)**3


def d3f(t, v, a):
    return (6.0 * a**2 *
            (a**4 - 6.0 * a**2 * t**2 + t**4)) * v / (a**2 + t**2)**4


def print_history_row(t, v, a, dt):
    result = "t=  " + str(t + dt) + ";TLastUpdate=  " + str(
        t) + ";Nc=1;DerivOrder=2;Version=1;a=  " + str(f(t + dt, v, a))
    result += ";da= " + str(df(t + dt, v, a)) + ";d2a= " + str(
        d2f(t + dt, v, a)) + ";"
    print(result)


p = argparse.ArgumentParser()
p.add_argument('--velocity',
               type=float,
               help='Asymptotic velocity',
               default=-1.0e-6)
p.add_argument('--timescale', type=float, help='Timescale', default=50.0)
p.add_argument('--dt', type=float, help="Step between lines in output")
p.add_argument('--tfinal', type=float, help="Final time in output")
args = p.parse_args()

time = 0.0
while (time < args.tfinal):
    print_history_row(time, args.velocity, args.timescale, args.dt)
    time += args.dt

# Checks that the functions are coded correctly
# print(args.velocity, args.timescale)
# print(f(1.1, 2.2, 3.3))
# print(df(4.4, 5.5, 6.6))
# print(d2f(7.7, 8.8, 9.9))
# print(d3f(1.1, 2.2, 3.3))
