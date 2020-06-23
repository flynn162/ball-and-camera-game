import pygame
import fuzzy
import vm

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
    ACCELERATION = 3
    DECELERATION = -6

    class Rotation:
        def __init__(self, dx):
            self.reset(dx)

        def reset(self, dx):
            self.ccw = square([dx, 1])
            self.cw = square([dx, -1])
            self.mag_squared = dx*dx + 1

        def _compute(self, vector_length, vec1, rot, output):
            multiply_into(vec1, rot, output)
            ## use symmetric rounding
            x = int(output[0] / self.mag_squared)
            y = int(output[1] / self.mag_squared)
            ## fix the length of the vector
            if x*x + y*y < vector_length ** 2:
                if output[0] != 0:
                    x += output[0] // abs(output[0])
                if output[1] != 0:
                    y += output[1] // abs(output[1])
            output[0] = x
            output[1] = y

        def rotate_ccw(self, vector_length, vec1, output):
            self._compute(vector_length, vec1, self.ccw, output)

        def rotate_cw(self, vector_length, vec1, output):
            self._compute(vector_length, vec1, self.cw, output)

    def __init__(self, screen, x, y):
        self.x = x
        self.y = y
        # targeted velocity
        self.vx = 0
        self.vy = 0
        # real velocity
        self.curr_vx = 0
        self.curr_vy = 0
        self.screen = screen

        self.temp = [0, 0]
        self.vec1 = [self.VECTOR_LENGTH, 0]
        self.vec2 = multiply(self.vec1, self.I)
        self.rot = self.Rotation(16)

        self.ai_input = self.Input(self)
        self.allocate_member_functions()
        self.fuzzy_machine = vm.VM(
            {'dir-x': self.fdirx, 'dir-y': self.fdiry, 'dist': self.fdist},
            {'dx': self.fdx, 'dy': self.fdy, 'rot': self.frot},
            'rule.scm'
        )

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

        # compute (dx * v1/|v1|) + (dy * v2/|v2|)
        self.vx = (dx*self.vec1[0] + dy*self.vec2[0]) // self.VECTOR_LENGTH
        self.vy = (dx*self.vec1[1] + dy*self.vec2[1]) // self.VECTOR_LENGTH

        dvx = 0
        dvy = 0

        if self.curr_vx >= self.vx:
            dvx = max(self.DECELERATION, self.vx - self.curr_vx)
        else:
            dvx = min(self.ACCELERATION, self.vx - self.curr_vx)

        if self.curr_vy >= self.vy:
            dvy = max(self.DECELERATION, self.vy - self.curr_vy)
        else:
            dvy = min(self.ACCELERATION, self.vy - self.curr_vy)

        self.curr_vx += dvx
        self.curr_vy += dvy

        self.curr_vx = min(50, max(-50, self.curr_vx))
        self.curr_vy = min(50, max(-50, self.curr_vy))

        self.x += self.curr_vx
        self.y += self.curr_vy

        if rot != 0:
            self.rot.reset(100 - min(100, abs(rot)))
            if rot < 0:
                self.rot.rotate_cw(self.VECTOR_LENGTH, self.vec1, self.temp)
            else:
                self.rot.rotate_ccw(self.VECTOR_LENGTH, self.vec1, self.temp)
            self.swap_temp_with_vec1()
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

        def put_into(self, virtual_machine):
            virtual_machine.input('dir-x', self.direction_vector[0])
            virtual_machine.input('dir-y', self.direction_vector[1])
            virtual_machine.input('dist', self.how_far_from_object)

    def allocate_member_functions(self):
        # NM, NS, Z, PS, PM
        self.fdirx = fuzzy.FiveLevels(
            (-1500, -500),
            (-600, -10),
            (-100, 100),
            (10, 600),
            (500, 1500)
        )
        self.fdiry = fuzzy.FiveLevels(
            (-1500, -500),
            (-600, -10),
            (-100, 100),
            (10, 600),
            (500, 1500)
        )
        # Z, PS, PM
        self.fdist = fuzzy.ThreeLevelsPositive(
            (-10, 300),
            (250, 700),
            (600, 1500)
        )
        # NM, NS, Z, PS, PM
        self.fdx = fuzzy.FiveLevels(
            (-30, -15),
            (-20, -5),
            (-9, 9),
            (5, 20),
            (15, 30)
        )
        self.fdy = fuzzy.FiveLevels(
            (-30, -15),
            (-20, -5),
            (-9, 9),
            (5, 20),
            (15, 30)
        )
        # NM, Z, PM
        self.frot = fuzzy.ThreeLevels(
            (-100, -50),
            (-50, 50),
            (50, 100)
        )

    def fancy_ai(self, ball):
        self.ai_input.compute(ball)
        self.ai_input.put_into(self.fuzzy_machine)
        self.fuzzy_machine.run()

        return (
            min(50, max(-50, self.fuzzy_machine.get_output('dx'))),
            min(50, max(-50, self.fuzzy_machine.get_output('dy'))),
            self.fuzzy_machine.get_output('rot')
        )


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
