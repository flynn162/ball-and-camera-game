import pygame
import time

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

class Camera:
    BORDER = 10
    CAM_WIDTH = 640
    CAM_HEIGHT = 360
    COLOR = pygame.Color(100, 100, 100)
    NO_COLOR = pygame.Color(0, 0, 0, 0)

    def __init__(self, screen, x, y):
        self.x = x
        self.y = y
        self.screen = screen
        self.dx = 10
        self.dy = 10

    def draw(self, color):
        dx = self.CAM_WIDTH // 2
        dy = self.CAM_HEIGHT // 2
        rect = pygame.Rect(self.x - dx, self.y - dy,
                           self.CAM_WIDTH, self.CAM_HEIGHT)
        pygame.draw.rect(self.screen, color, rect)

    @staticmethod
    def compute_input_for_ai(ball_x, self_x, length):
        if ball_x <= self_x - length // 2:
            return -256
        elif ball_x >= self_x + length // 2:
            return 256
        else:
            temp = (ball_x - self_x) / (length // 2)
            return int(temp * 256)

    def update(self, ball):
        self.draw(NO_COLOR)

        # compute input value for the "fancy AI"
        value_x = self.compute_input_for_ai(ball.x, self.x, self.CAM_WIDTH)
        value_y = self.compute_input_for_ai(ball.y, self.y, self.CAM_HEIGHT)

        dx, dy = fancy_ai(value_x, value_y)
        self.x += dx
        self.y += dy

        self.draw(self.COLOR)

def fancy_ai(x, y):
    return x // 4, y // 4

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

        screen.fill(BG_COLOR)
        screen.blit(camera_layer, (0, 0))
        screen.blit(ball_layer, (0, 0))

        pygame.display.flip()

        ball.update()
        camera.update(ball)

        pygame.time.wait(30)

if __name__ == '__main__':
    main()
