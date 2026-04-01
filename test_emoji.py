import pygame
import sys

pygame.init()
pygame.font.init()

size = (400, 300)
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Emoji Test")

# Try to load emoji fonts
font_names = "segoeuiemoji,notocoloremoji,applecoloremoji,symbola,dejavusans,freesans"
try:
    font = pygame.font.SysFont(font_names, 42)
except Exception as e:
    print(f"Error loading fonts: {e}")
    sys.exit(1)

emojis = ["♾️", "🪫", "🪄", "🌠", "🔥"]

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((255, 255, 255))
    
    y = 50
    for e in emojis:
        text = font.render(f"Emoji {e}: {e}", True, (0, 0, 0))
        screen.blit(text, (50, y))
        y += 50

    pygame.display.flip()

pygame.quit()
