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
        pygame.draw.circle(self.screen, color,
                           (self.x, HEIGHT - self.y), self.RADIUS)

    def update(self):
        # Hide the ball!
        self.draw(NO_COLOR)

        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0
        if keys[pygame.K_UP]:
            dy = 10
        if keys[pygame.K_DOWN]:
            dy = -10
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

def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]

def mag_squared(v):
    return v[0] * v[0] + v[1] * v[1]

def project_onto(a, b, out):
    d = dot(a, b)
    ms = mag_squared(b)
    out[0] = d * b[0] // ms
    out[1] = d * b[1] // ms


class Camera:
    CAM_WIDTH = 640
    CAM_HEIGHT = 360
    COLOR = pygame.Color(100, 100, 100)
    NO_COLOR = pygame.Color(0, 0, 0, 0)

    I = [0, 1]
    ROT_CCW = square([16, 1])
    ROT_CW = square([16, -1])
    MAG_SQUARED = 16*16 + 1*1
    VECTOR_LENGTH = 300

    def __init__(self, screen, x, y):
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.screen = screen

        self.temp = [0, 0]
        self.vec1 = [self.VECTOR_LENGTH, 0]
        self.vec2 = multiply(self.vec1, self.I)
        self.ai_input = self.Input(self)

    def draw(self, color):
        # Convert coordinate from Cartesian system to column-row system
        p1 = (self.x, HEIGHT - self.y)
        p2 = (self.x + self.vec1[0], HEIGHT - self.y - self.vec1[1])
        p3 = (self.x + self.vec2[0], HEIGHT - self.y - self.vec2[1])
        pygame.draw.polygon(self.screen, color, (p1, p2, p3))

    @staticmethod
    def compute_input_for_ai(ball_x, self_x, length):
        if ball_x <= self_x - length // 2:
            return -1024
        elif ball_x >= self_x + length // 2:
            return 1024
        else:
            temp = (ball_x - self_x) / (length // 2)
            return int(temp * 1024)

    def swap_temp_with_vec1(self):
        keep = self.vec1
        self.vec1 = self.temp
        self.temp = keep

    def update(self, ball):
        self.draw(NO_COLOR)

        dx, dy, rot = self.fancy_ai(ball)

        self.x += dx
        self.y += dy
        if rot:
            multiply_into(self.vec1, rot, self.temp)
            self.swap_temp_with_vec1()
            self.vec1[0] = self.vec1[0] // self.MAG_SQUARED
            self.vec1[1] = self.vec1[1] // self.MAG_SQUARED
            multiply_into(self.vec1, self.I, self.vec2)

        self.draw(self.COLOR)

    class Input:
        def __init__(self, camera):
            self.parent = camera
            self.d_max = self.parent.VECTOR_LENGTH * 1000 // 1414
            self.temp = [0, 0]
            self.how_far_from_object = 0
            self.direction_vector = [0, 0]

        @staticmethod
        def normalize(value, max_value):
            if value >= max_value:
                return 1024
            elif value <= -max_value:  # min value is implied
                return -1024
            else:
                return value * 1024 // max_value

        def compute(self, ball):
            vd = (ball.x - self.parent.x, ball.y - self.parent.y)

            # draw a diamond (we will use the L1 norm here)
            l1_distance = abs(vd[0]) + abs(vd[1])
            self.how_far_from_object = self.normalize(l1_distance, self.d_max)

            # direction
            if l1_distance == 0:
                self.direction_vector[0] = 0
                self.direction_vector[1] = 0
            else:
                # 1. Let vec1 = a + bi, compute the complex number (c+di) st.
                # (a+bi)(c+di) = |v|
                # Sol: c + di = |v| (a - bi) / (a^2 + b^2) = (a - bi) / |v|
                self.temp[0] = self.parent.vec1[0]
                self.temp[1] = -self.parent.vec1[1]
                # 2. rotate the vd vector
                multiply_into(vd, self.temp, self.direction_vector)
                # divide by |v|
                self.direction_vector[0] //= self.parent.VECTOR_LENGTH
                self.direction_vector[1] //= self.parent.VECTOR_LENGTH
                # normalize
                self.direction_vector[0] = self.normalize(
                    self.direction_vector[0],
                    self.parent.VECTOR_LENGTH * 6 // 5
                )
                self.direction_vector[1] = self.normalize(
                    self.direction_vector[1],
                    self.parent.VECTOR_LENGTH * 6 // 5
                )

            # distance from wall (to be implemented)

    def fancy_ai(self, ball):
        value_x = self.compute_input_for_ai(ball.x, self.x, self.CAM_WIDTH)
        value_y = self.compute_input_for_ai(ball.y, self.y, self.CAM_HEIGHT)
        self.ai_input.compute(ball)

        return 0, 0, self.ROT_CW

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags=pygame.DOUBLEBUF)

    flags = pygame.SRCALPHA | pygame.HWSURFACE
    ball_layer = pygame.surface.Surface((WIDTH, HEIGHT), flags=flags)
    camera_layer = pygame.surface.Surface((WIDTH, HEIGHT), flags=flags)

    # prepare game world
    ball = Ball(ball_layer, WIDTH // 2, HEIGHT // 2)
    camera = Camera(camera_layer, WIDTH // 2, HEIGHT // 2)

    ticks = 0
    while True:
        ticks = pygame.time.get_ticks()

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

        new_ticks = pygame.time.get_ticks()
        wait_time = 33 - (new_ticks - ticks)
        ticks = new_ticks
        if wait_time > 1:
            pygame.time.wait(wait_time)
        else:
            pygame.time.wait(1)

if __name__ == '__main__':
    main()
