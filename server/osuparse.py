import zipfile
import pygame
import time
import math
import sys

# -----------------------------
# 1. CONFIG
# -----------------------------
LANES = 4
NOTE_SPEED = 300  # pixels per second
HIT_Y = 500  # y coordinate for "hit line"
WINDOW_SIZE = (800, 600)
KEYS = [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]  # 4-lane keys
HIT_WINDOW = 0.15  # seconds

# -----------------------------
# 2. HELPER FUNCTIONS
# -----------------------------
def extract_osu(osz_path):
    """Extract .osu and audio from .osz"""
    osu_content = None
    audio_file_path = None

    with zipfile.ZipFile(osz_path, 'r') as z:
        for file in z.namelist():
            if file.endswith('.osu'):
                osu_content = z.read(file).decode('utf-8')
            elif file.endswith('.mp3'):
                audio_file_path = file
                z.extract(file)  # extract to current folder
    return osu_content, audio_file_path

def parse_osu(osu_text):
    """Parse hit circles into a list of {time, lane}"""
    lines = osu_text.splitlines()
    section = ''
    notes = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('['):
            section = line
            continue
        if section == '[HitObjects]':
            parts = line.split(',')
            x = int(parts[0])
            time_ms = int(parts[2])
            type_flag = int(parts[3])
            is_circle = (type_flag & 1) != 0
            if not is_circle:
                continue
            lane = min(LANES - 1, int(x / 512 * LANES))
            notes.append({'time': time_ms / 1000, 'lane': lane})
    return notes

# -----------------------------
# 3. INITIALIZE PYGAME
# -----------------------------
pygame.init()
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption("Python Rhythm Prototype")
clock = pygame.time.Clock()

# -----------------------------
# 4. LOAD BEATMAP
# -----------------------------
osu_file, audio_file = extract_osu(r"C:\\Users\\stringbot\\Downloads\\2466542 TM - Shinseikatsu.osz")
notes = parse_osu(osu_file)

# -----------------------------
# 5. LOAD AUDIO
# -----------------------------
pygame.mixer.init()
pygame.mixer.music.load("output.ogg")

# -----------------------------
# 6. GAME LOOP
# -----------------------------
start_time = None
running = True
score = 0
combo = 0
hit_notes = set()

pygame.mixer.music.play()
start_time = time.time()

while running:
    current_time = time.time() - start_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in KEYS:
                lane = KEYS.index(event.key)
                # find the closest note in this lane that is not hit
                closest_note = None
                closest_delta = HIT_WINDOW + 1
                for i, note in enumerate(notes):
                    if i in hit_notes or note['lane'] != lane:
                        continue
                    delta = current_time - note['time']
                    if abs(delta) < closest_delta:
                        closest_delta = abs(delta)
                        closest_note = i
                if closest_note is not None and closest_delta <= HIT_WINDOW:
                    hit_notes.add(closest_note)
                    # judgement
                    if closest_delta <= HIT_WINDOW/3:
                        print("Perfect!")
                        score += 300
                        combo += 1
                    elif closest_delta <= HIT_WINDOW*2/3:
                        print("Great!")
                        score += 100
                        combo += 1
                    else:
                        print("Good!")
                        score += 50
                        combo += 1
                else:
                    print("Miss!")
                    combo = 0

    # -----------------------------
    # 7. DRAW NOTES
    # -----------------------------
    screen.fill((30, 30, 30))

    lane_width = WINDOW_SIZE[0] / LANES
    for i, note in enumerate(notes):
        if i in hit_notes:
            continue
        # vertical position: notes scroll down towards HIT_Y
        y = HIT_Y - NOTE_SPEED * (note['time'] - current_time)
        x = note['lane'] * lane_width + lane_width / 2
        if 0 <= y <= WINDOW_SIZE[1]:
            pygame.draw.circle(screen, (255, 200, 0), (int(x), int(y)), 20)

    # Draw hit line
    pygame.draw.line(screen, (255,255,255), (0,HIT_Y), (WINDOW_SIZE[0],HIT_Y), 2)

    # Draw score and combo
    font = pygame.font.SysFont(None, 36)
    score_text = font.render(f"Score: {score}  Combo: {combo}", True, (255,255,255))
    screen.blit(score_text, (10,10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
