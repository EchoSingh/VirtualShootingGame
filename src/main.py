import cv2
import mediapipe as mp
import pygame
import random
import time
import math

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

try:
    crosshair_img = pygame.image.load('assets/crosshair.png')
    target_img = pygame.image.load('assets/target.png')
    shoot_sound = pygame.mixer.Sound('assets/sounds/shoot.wav')
except pygame.error as e:
    print(f"Error loading assets: {e}")
    pygame.quit()
    exit()

target_img = pygame.transform.scale(target_img, (50, 50))

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Error: Could not open video device.")

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

targets = []
score = 0
font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()

camera_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
camera_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

def spawn_target():
    max_x = SCREEN_WIDTH - target_img.get_width()
    max_y = SCREEN_HEIGHT - target_img.get_height()
    if max_x <= 0 or max_y <= 0:
        raise ValueError("Target image size is too large for the screen.")
    x = random.randint(0, max_x)
    y = random.randint(0, max_y)
    return pygame.Rect(x, y, target_img.get_width(), target_img.get_height())

def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

def detect_shooting_gesture(hand_landmarks):
    index_tip = hand_landmarks.landmark[8]
    thumb_tip = hand_landmarks.landmark[4]
    distance = math.sqrt((index_tip.x - thumb_tip.x) ** 2 + (index_tip.y - thumb_tip.y) ** 2)
    return distance < 0.05

def main():
    global score
    targets.append(spawn_target())
    shooting_gesture_detected = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)

        crosshair_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                for id, lm in enumerate(hand_landmarks.landmark):
                    h, w, c = frame.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    if id == 8:
                        crosshair_x = int(cx * SCREEN_WIDTH / camera_width)
                        crosshair_y = int(cy * SCREEN_HEIGHT / camera_height)
                        crosshair_pos = (crosshair_x, crosshair_y)

                if detect_shooting_gesture(hand_landmarks):
                    shooting_gesture_detected = True
                else:
                    shooting_gesture_detected = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                cap.release()
                cv2.destroyAllWindows()
                return

        if shooting_gesture_detected:
            for target in targets[:]:
                if target.collidepoint(crosshair_pos):
                    targets.remove(target)
                    score += 1
                    targets.append(spawn_target())
                    shoot_sound.play()

        screen.fill((0, 0, 0))
        for target in targets:
            screen.blit(target_img, target.topleft)
            draw_text(f'({target.x}, {target.y})', font, (255, 255, 255), screen, target.x, target.y - 20)
        screen.blit(crosshair_img, (crosshair_pos[0] - crosshair_img.get_width() // 2,
                                    crosshair_pos[1] - crosshair_img.get_height() // 2))
        draw_text(f'Score: {score}', font, (255, 255, 255), screen, 10, 10)
        draw_text(f'Crosshair: ({crosshair_pos[0]}, {crosshair_pos[1]})', font, (255, 255, 255), screen, crosshair_pos[0] + 10, crosshair_pos[1] - 20)
        pygame.display.flip()

        clock.tick(30)

        cv2.imshow('Virtual Shooting Game', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

if __name__ == "__main__":
    main()
