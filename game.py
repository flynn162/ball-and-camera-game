import pygame

WIDTH, HEIGHT = 1920, 1080
BG_COLOR = pygame.Color('black')
FG_COLOR = pygame.Color('white')
NO_COLOR = pygame.Color(0, 0, 0, 0)

class Ball:
    RADIUS = 30

    def __init__(self, screen, x, y):
        self.x = x
        self.y = y
        self.screen = screen

    def draw(self, color):
        pygame.draw.circle(self.screen, color, (self.x, self.y), self.RADIUS)

    def update(self):
        # Hide the ball!
        self.draw(NO_COLOR)

        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0
        if keys[pygame.K_UP]:
            dy = -10
        if keys[pygame.K_DOWN]:
            dy = 10
        if keys[pygame.K_LEFT]:
            dx = -10
        if keys[pygame.K_RIGHT]:
            dx = 10
        if keys[pygame.K_x]:
            dx *= 2
            dy *= 2

        self.x = max(0, min(self.x + dx, WIDTH))
        self.y = max(0, min(self.y + dy, HEIGHT))
        self.draw(FG_COLOR)


def multiply_into(z, w, out):
    out[0] = z[0] * w[0] - z[1] * w[1]
    out[1] = z[0] * w[1] + z[1] * w[0]

def multiply(z, w):
    result = [0, 0]
    multiply_into(z, w, result)
    return result

def square(z):
    result = [0, 0]
    multiply_into(z, z, result)
    return result


class Camera:
    CAM_WIDTH = 640
    CAM_HEIGHT = 360
    COLOR = pygame.Color(100, 100, 100)
    NO_COLOR = pygame.Color(0, 0, 0, 0)

    I = [0, 1]
    ROT_CCW = square([16, 1])
    ROT_CW = square([16, -1])
    MAG_SQUARED = 16*16 + 1*1
    VECTOR_LENGTH = 250

    def __init__(self, screen, x, y):
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.screen = screen

        self.temp = [0, 0]
        self.vec1 = [0, self.VECTOR_LENGTH]
        self.vec2 = multiply(self.vec1, self.I)

    def draw(self, color):

        # Convert coordinate from Cartesian system to column-row system
        p1 = (self.x, self.y)
        p2 = (self.x + self.vec1[0], self.y - self.vec1[1])
        p3 = (self.x + self.vec2[0], self.y - self.vec2[1])
        pygame.draw.polygon(self.screen, color, (p1, p2, p3))

    @staticmethod
    def compute_input_for_ai(ball_x, self_x, length):
        if ball_x <= self_x - length // 2:
            return -256
        elif ball_x >= self_x + length // 2:
            return 256
        else:
            temp = (ball_x - self_x) / (length // 2)
            return int(temp * 256)

    def swap_temp_with_vec1(self):
        keep = self.vec1
        self.vec1 = self.temp
        self.temp = keep

    def update(self, ball):
        self.draw(NO_COLOR)

        # compute input value for the "fancy AI"
        value_x = self.compute_input_for_ai(ball.x, self.x, self.CAM_WIDTH)
        value_y = self.compute_input_for_ai(ball.y, self.y, self.CAM_HEIGHT)

        dx, dy, rot = self.fancy_ai(value_x, value_y)

        self.x += dx
        self.y += dy
        if rot:
            multiply_into(self.vec1, self.ROT_CCW, self.temp)
            self.swap_temp_with_vec1()
            self.vec1[0] = self.vec1[0] // self.MAG_SQUARED
            self.vec1[1] = self.vec1[1] // self.MAG_SQUARED
            multiply_into(self.vec1, self.I, self.vec2)

        self.draw(self.COLOR)

    def fancy_ai(self, x, y):
        return x // 4, y // 4, self.ROT_CCW

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags=pygame.DOUBLEBUF)

    flags = pygame.SRCALPHA | pygame.HWSURFACE
    ball_layer = pygame.surface.Surface((WIDTH, HEIGHT), flags=flags)
    camera_layer = pygame.surface.Surface((WIDTH, HEIGHT), flags=flags)

    # prepare game world
    ball = Ball(ball_layer, WIDTH // 2, HEIGHT // 2)
    camera = Camera(camera_layer, WIDTH // 2, HEIGHT // 2)

    while True:
        e = pygame.event.poll()
        if e.type == pygame.QUIT:
            pygame.quit()
            break

        screen.fill(BG_COLOR)
        screen.blit(camera_layer, (0, 0))
        screen.blit(ball_layer, (0, 0))

        pygame.display.flip()

        ball.update()
        camera.update(ball)

        pygame.time.wait(30)

if __name__ == '__main__':
    main()
