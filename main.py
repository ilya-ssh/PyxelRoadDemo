import pyxel
from array_data import pixel_data
from config import *


def rescale(n, nx, ny):
    for y in range(int(16 * n)):
        for x in range(int(16 * n)):
            if pixel_data[int(y / n)][int(x / n)] != 13:
                pyxel.pset(x + nx, y + ny, pixel_data[int(y / n)][int(x / n)])


def rescalem(n, nx, ny):
    n = round(n * 2) / 2
    for y in range(16):
        for x in range(16):
            if pixel_data[int(y)][int(x)] != 13:
                pyxel.rect((x * n) + nx, (y * n) + ny, 1 * n, 1 * n, pixel_data[int(y)][int(x)])

    return n


def drawQuad(
        color: int,
        x1: int,
        y1: int,
        w1: int,
        x2: int,
        y2: int,
        w2: int,
):
    points = [(x1 - w1, y1), (x2 - w2, y2), (x2 + w2, y2), (x1 + w1, y1)]
    color = color
    draw_polygon(points, color)


class Line:
    def __init__(self, i):
        self.i = i
        self.x = self.y = self.z = 0.0  # game position (3D space)
        self.X = self.Y = self.W = 0.0  # game position (2D projection)
        self.scale = 0.0  # scale from camera position
        self.curve = 0.0  # curve radius
        self.spriteX = 0.0  # sprite position X
        self.clip = 0.0  # correct sprite Y position
        self.sprite = None

        self.grass_color = 0
        self.rumble_color = 0
        self.road_color = 0

    def project(self, camX, camY, camZ):
        self.scale = camD / (self.z - camZ)
        self.X = (1 + self.scale * (self.x - camX)) * WINDOW_WIDTH / 2
        self.Y = (1 - self.scale * (self.y - camY)) * WINDOW_HEIGHT / 2
        self.W = self.scale * roadW * WINDOW_WIDTH / 2

    def drawSprite(self):
        if self.sprite is None:
            return

        w = 160
        h = 160
        destX = self.X + self.scale * self.spriteX * WINDOW_WIDTH / 2
        destY = self.Y + 4
        destW = w * self.W / 266
        destH = h * self.W / 266

        destX += destW * self.spriteX
        destY += destH * -1

        clipH = destY + destH - self.clip
        if clipH < 0:
            clipH = 0
        if clipH >= destH:
            return

        # avoid scalling up images which causes lag

        scale = destW / w * 10
        if 0 < destX < WINDOW_WIDTH and destY < WINDOW_HEIGHT and clipH > 0:
            if scale > 1:
                rescalem(scale, destX, destY)
            else:
                rescale(scale, destX, destY)


def draw_polygon(points, color):
    # Triangulate the polygon using the ear clipping algorithm
    triangles = []
    remaining_points = points.copy()
    while len(remaining_points) >= 3:
        # Find an "ear" triangle
        for i in range(len(remaining_points)):
            prev = remaining_points[(i - 1) % len(remaining_points)]
            curr = remaining_points[i]
            next = remaining_points[(i + 1) % len(remaining_points)]
            if is_ear(prev, curr, next, remaining_points):
                triangles.append((prev, curr, next))
                remaining_points.remove(curr)
                break

    # Draw each triangle with the specified color
    for triangle in triangles:
        x1, y1 = triangle[0]
        x2, y2 = triangle[1]
        x3, y3 = triangle[2]
        pyxel.tri(x1, y1, x2, y2, x3, y3, col=color)


def is_ear(p1, p2, p3, polygon):
    # Check if the triangle formed by p1, p2, p3 is an "ear"
    if not is_ccw(p1, p2, p3):
        return False
    for point in polygon:
        if point in (p1, p2, p3):
            continue
        if is_inside_triangle(p1, p2, p3, point):
            return False
    return True


def is_ccw(p1, p2, p3):
    # Check if the points p1, p2, p3 are in counter-clockwise order
    # using the cross product method
    return (p2[0] - p1[0]) * (p3[1] - p1[1]) > (p2[1] - p1[1]) * (p3[0] - p1[0])


def is_inside_triangle(p1, p2, p3, point):
    # Check if the point is inside the triangle formed by p1, p2, p3
    u = ((p2[0] - p1[0]) * (point[1] - p1[1]) - (p2[1] - p1[1]) * (point[0] - p1[0])) / (
                (p2[1] - p1[1]) * (p3[0] - p2[0]) - (p2[0] - p1[0]) * (p3[1] - p2[1]))
    v = ((p3[0] - p2[0]) * (point[1] - p2[1]) - (p3[1] - p2[1]) * (point[0] - p2[0])) / (
                (p2[1] - p1[1]) * (p3[0] - p2[0]) - (p2[0] - p1[0]) * (p3[1] - p2[1]))
    return 0 <= u <= 1 and 0 <= v <= 1 and u + v <= 1


class GameWindow:
    playerY: int

    def __init__(self):

        self.pos = 0
        self.playerX = 0  # player start at the center of the road
        self.playerY = 1000  # camera height offset
        self.inputX = 0

        self.speed = 0
        self.kmh = 0
        self.backgroundx = 0
        self.background2x = 0
        self.linespr = 0

        # set up Pyxel
        pyxel.init(WINDOW_WIDTH, WINDOW_HEIGHT, fps=30)
        pyxel.colors[0] = 0x000000  # black
        pyxel.colors[1] = 0xFFFFFF  # white
        pyxel.colors[2] = 0xD8D8FC  # lightgrey
        pyxel.colors[3] = 0xB4B4D8  # lightgrey
        pyxel.colors[4] = 0x9090B4  # darkergrey
        pyxel.colors[5] = 0xB4D8FC  # sky
        pyxel.colors[6] = 0x90D800  # brightgreen
        pyxel.colors[7] = 0x486C00  # swamp green
        pyxel.colors[8] = 0x004800  # dark green
        pyxel.colors[9] = 0x6C90B4  # blueish grey
        pyxel.colors[10] = 0x486C90  # darker blueish grey
        pyxel.colors[11] = 0x909000  # yellowish swamp green
        pyxel.colors[12] = 0xFF0021  # red
        pyxel.colors[13] = 0x940000  # darker red
        pyxel.colors[14] = 0x4A0000  # dark red
        pyxel.colors[15] = 0xefea7c
        pyxel.image(0).load(0, 0, "assets/test.png")

        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btn(pyxel.KEY_W):
            if 90 > self.kmh > 0 and pyxel.frame_count % 5 == 0:
                self.kmh += 2
            if pyxel.frame_count % 5 == 0:
                self.kmh += 1
        if pyxel.btn(pyxel.KEY_S):
            self.kmh -= 1  # it has to be N integer times the segment length
        if pyxel.btn(pyxel.KEY_D):
            if self.kmh > 0:
                self.playerX += 50
        if pyxel.btn(pyxel.KEY_A):
            if self.kmh > 0:
                self.playerX -= 50
        if pyxel.btn(pyxel.KEY_UP):
            self.playerY += 100
        if pyxel.btn(pyxel.KEY_DOWN):
            self.playerY -= 100
            # avoid camera going below ground
        if self.playerY < 500:
            self.playerY = 500
            # turbo speed
        if pyxel.btn(pyxel.KEY_TAB):
            self.speed *= 2  # it has to be N integer times the segment length
        if self.kmh < 0:
            self.kmh = 0
        if self.kmh == 0:
            self.speed = 0
        if 50 > self.kmh > 0:
            self.speed = 200
        if 100 > self.kmh > 50:
            self.speed = 400
        if 150 > self.kmh > 100:
            self.speed = 600
        if self.kmh > 150 and pyxel.frame_count % 12 == 0:
            self.kmh = 150

        self.playerX = self.playerX - self.linespr * (self.kmh * 0.05)

        self.pos += self.speed

    def draw(self):
        pyxel.cls(5)

        pyxel.blt(self.background2x, 80, 0, 0, 177, 256, 32, 5)
        pyxel.blt(self.background2x + WINDOW_WIDTH, 80, 0, 0, 145, 256, 32, 5)
        pyxel.blt(self.background2x - WINDOW_WIDTH, 80, 0, 0, 145, 256, 32, 5)

        pyxel.blt(self.backgroundx, 95, 0, 0, 233, 256, 23, 5)
        pyxel.blt(self.backgroundx + WINDOW_WIDTH, 95, 0, 0, 209, 256, 24, 5)
        pyxel.blt(self.backgroundx - WINDOW_WIDTH, 95, 0, 0, 209, 256, 24, 5)

        pyxel.blt(self.backgroundx, 115, 0, 0, 233, 256, -23, 5)
        pyxel.blt(self.backgroundx + WINDOW_WIDTH, 116, 0, 0, 209, 256, -24, 5)
        pyxel.blt(self.backgroundx - WINDOW_WIDTH, 116, 0, 0, 209, 256, -24, 5)

        # create road lines for each segment
        lines = []
        MINIMAP_SCALE_FACTOR = 0.1  # adjust this to scale the minimap to the desired size

        minimap_coords = []  # list to store the x, y coordinates for the minimap
        for i in range(1600):
            line = Line(i)
            line.z = (
                    i * segL + 0.00001
            )  # adding a small value avoids Line.project() errors

            # change color at every other 3 lines (int floor division)
            grass_color = light_grass if (i // 40) % 2 else dark_grass
            rumble_color = white_rumble
            road_color = dark_road
            stripe_color = dark_road if (i // 15) % 2 else white_rumble

            line.grass_color = grass_color
            line.rumble_color = rumble_color
            line.road_color = road_color
            line.stripe_color = stripe_color

            # right curve
            if 300 < i < 400:
                line.curve = 2.2

            # uphill and downhill
            if 1600 > i > 750:
                line.y = pyxel.sin((i / 30.0) * 180 / 3.14159265358979323846) * 1500

            # left curve
            if i > 1100:
                line.curve = -0.7

            if i % 80 == 0:
                line.spriteX = -6
                line.sprite = 1

            if i % 125 == 0:
                line.spriteX = -7
                line.sprite = 1

            if i % 65 == 0:
                line.spriteX = 6
                line.sprite = 1

            # Sprites segments
            lines.append(line)

        N = len(lines)

        # loop the circut from start to finish
        while self.pos >= N * segL:
            self.pos -= N * segL
        while self.pos < 0:
            self.pos += N * segL
        startPos = self.pos // segL

        x = dx = 0.0  # curve offset on x axis

        camH = lines[startPos].y + self.playerY
        maxy = WINDOW_HEIGHT

        if self.speed > 0:
            self.backgroundx -= lines[startPos].curve * 0.5

        elif self.speed < 0:
            self.backgroundx += lines[startPos].curve * 0.5

        if self.speed > 0:
            self.background2x -= lines[startPos].curve * 0.05

        elif self.speed < 0:
            self.background2x += lines[startPos].curve * 0.05

        self.linespr = lines[startPos].curve

        # draw road
        for n in range(startPos, startPos + show_N_seg):
            current = lines[n % N]
            # loop the circut from start to finish = pos - (N * segL if n >= N else 0)
            current.project(self.playerX - x, camH, self.pos - (N * segL if n >= N else 0))
            x += dx
            dx += current.curve

            current.clip = maxy

            # don't draw "above ground"
            if current.Y >= maxy:
                continue
            maxy = current.Y

            prev = lines[(n - 1) % N]  # previous line

            drawQuad(
                current.grass_color,
                0,
                prev.Y,
                WINDOW_WIDTH,
                0,
                current.Y,
                WINDOW_WIDTH,
            )
            drawQuad(
                current.rumble_color,
                prev.X,
                prev.Y,
                prev.W * 1.05,
                current.X,
                current.Y,
                current.W * 1.05,
            )
            drawQuad(
                current.road_color,
                prev.X,
                prev.Y,
                prev.W,
                current.X,
                current.Y,
                current.W,
            )

            drawQuad(
                current.stripe_color,
                prev.X,
                prev.Y,
                prev.W * 0.025,
                current.X,
                current.Y,
                current.W * 0.025,
            )
            for n in range(startPos + show_N_seg, startPos + 1, -1):
                lines[n % N].drawSprite()

            pyxel.text(1, 30, f'{self.kmh} km/h debug', 0)
            pyxel.text(1, 37, f'{self.linespr} correct player X debug', 0)
            pyxel.text(1, 44, f'{int(self.pos / 200)} player pos', 0)
            pyxel.text(1, 51, f'{int(self.playerY / 200)} player Y', 0)
            pyxel.text(1, 58, f'{int(self.playerX / 200)} player X', 0)

            for n in range(16):
                pyxel.rect(6 * n, 20, 6, 6, n)


GameWindow()
