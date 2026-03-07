import turtle
import random

screen = turtle.Screen()
screen.setup(900, 600)
screen.bgcolor("skyblue")
t = turtle.Turtle()
t.speed(0)
t.width(2)

# Soare
t.penup()
t.goto(320, 200)
t.pendown()
t.color("yellow")
t.begin_fill()
t.circle(50)
t.end_fill()

# Raze soare
for i in range(12):
    t.penup()
    t.goto(320, 250)
    t.setheading(i * 30)
    t.forward(60)
    t.pendown()
    t.forward(40)

# Nori
def nor(x, y):
    t.penup()
    t.goto(x, y)
    t.color("white")
    t.begin_fill()
    for i in range(5):
        t.circle(25)
        t.forward(25)
    t.end_fill()

nor(-250, 200)
nor(-100, 220)
nor(50, 200)

# Munți
t.penup()
t.goto(-450, -50)
t.pendown()
t.color("gray")
t.begin_fill()

for i in range(6):
    t.goto(-350 + i*150, random.randint(50,150))
    t.goto(-250 + i*150, -50)

t.goto(-450, -50)
t.end_fill()

# Iarbă
t.penup()
t.goto(-450, -50)
t.pendown()
t.color("green")
t.begin_fill()
for i in range(2):
    t.forward(900)
    t.right(90)
    t.forward(250)
    t.right(90)
t.end_fill()

# Copac
def copac(x, y):
    t.penup()
    t.goto(x, y)
    t.pendown()

    # trunchi
    t.color("saddlebrown")
    t.begin_fill()
    for i in range(2):
        t.forward(30)
        t.left(90)
        t.forward(80)
        t.left(90)
    t.end_fill()

    # frunze
    t.penup()
    t.goto(x+15, y+80)
    t.pendown()
    t.color("forestgreen")
    t.begin_fill()
    t.circle(40)
    t.end_fill()

# Mai mulți copaci
for i in range(-300, 300, 150):
    copac(i, -50)

# Flori
def floare(x, y):
    culori = ["red","pink","purple","yellow","orange"]
    t.penup()
    t.goto(x, y)
    t.pendown()
    t.color(random.choice(culori))
    t.begin_fill()
    t.circle(8)
    t.end_fill()

for i in range(40):
    floare(random.randint(-430,430), random.randint(-250,-70))

t.hideturtle()
turtle.done()