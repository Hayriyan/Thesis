
import cv2
import mediapipe as mp
import pyautogui
import math
import time

# ========= USER CONFIGURATION =======================================
FLIP_FRAME = True        # Set False if your webcam feed already looks mirrored
INVERT_X   = False       # True  → swap left/right (use if cursor still reversed)
SCREEN_W, SCREEN_H = pyautogui.size()

# Gesture thresholds (all values are pixel distances measured *inside the frame*)
PINCH_CLICK      = (40,  70)   # [min, max] → single click
PINCH_DOUBLE     =  40         # ≤ this      → double click
PINCH_RIGHT      =  60         # thumb-pinky → right click
PINCH_DRAG       = (70, 120)   # start / stop drag
LAUNCHPAD_TOTAL  = 300         # closed fist
SWIPE_SPEED_PX   = 100         # dx in one frame to count as swipe
SWIPE_COOLDOWN_S =   1.0       # seconds
SMOOTHING_ALPHA  =   0.25      # 0-1 exponential smoothing for cursor
# ====================================================================

pyautogui.FAILSAFE = False
mp_hands = mp.solutions.hands
hands    = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
draw     = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
last_raw_x, last_swipe_time = 0, 0
smoothed_x = smoothed_y = 0
drag_mode  = False
mouse_down = False


def dist(lm1, lm2, w, h) -> float:
    """Euclidean distance between two MediaPipe landmarks in *frame* pixels."""
    return math.hypot(int(lm2.x * w) - int(lm1.x * w),
                      int(lm2.y * h) - int(lm1.y * h))


def fingers_up(hand):
    """Returns the number of fingers that are (roughly) raised."""
    tips = [8, 12, 16, 20]   # index → pinky
    count = 0
    for tip in tips:
        if hand[tip].y < hand[tip - 2].y:   # tip above its lower joint
            count += 1
    # Thumb (simple “sideways” check)
    if hand[4].x < hand[3].x:
        count += 1
    return count


while True:
    ok, frame = cap.read()
    if not ok:
        break

    if FLIP_FRAME:
        frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

    if res.multi_hand_landmarks:
        hand_lms = res.multi_hand_landmarks[0]
        lm = hand_lms.landmark

        # ---------- 1. CURSOR MOVEMENT ----------------------------------
        idx = lm[8]                    # index fingertip
        raw_x = idx.x                  # 0–1
        if INVERT_X:                   # optional extra mirroring
            raw_x = 1 - raw_x
        raw_y = idx.y

        # map to screen
        target_x = raw_x * SCREEN_W
        target_y = raw_y * SCREEN_H

        # exponential smoothing
        smoothed_x = smoothed_x + SMOOTHING_ALPHA * (target_x - smoothed_x)
        smoothed_y = smoothed_y + SMOOTHING_ALPHA * (target_y - smoothed_y)
        pyautogui.moveTo(smoothed_x, smoothed_y)

        # visual cue
        cv2.circle(frame,
                   (int(idx.x * w), int(idx.y * h)),
                   10, (0, 255, 0), -1)

        # ---------- 2. GESTURES ----------------------------------------
        pinch      = dist(lm[8], lm[4],  w, h)          # index ↔ thumb
        right_pin  = dist(lm[4], lm[20], w, h)          # thumb ↔ pinky
        fingers    = fingers_up(lm)
        total_dist = sum(dist(lm[i], lm[0], w, h) for i in [4, 8, 12, 16, 20])

        # ----- Click / double-click / right-click
        if PINCH_CLICK[0] < pinch < PINCH_CLICK[1] and not mouse_down:
            pyautogui.click()
            mouse_down = True
            cv2.putText(frame, "Click", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        elif pinch <= PINCH_DOUBLE and not mouse_down:
            pyautogui.doubleClick()
            mouse_down = True
            cv2.putText(frame, "Double-click", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

        elif right_pin <= PINCH_RIGHT and not mouse_down:
            pyautogui.rightClick()
            mouse_down = True
            cv2.putText(frame, "Right-click", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        # ----- Drag
        elif PINCH_DRAG[0] < pinch < PINCH_DRAG[1]:
            if not drag_mode:
                pyautogui.mouseDown()
                drag_mode = True
                cv2.putText(frame, "Drag start", (10, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        else:
            if drag_mode:
                pyautogui.mouseUp()
                drag_mode = False
                cv2.putText(frame, "Drag end", (10, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            mouse_down = False     # reset after any non-pinch frame

        # ----- Scrolling
        if fingers == 2:
            pyautogui.scroll(-30)
            cv2.putText(frame, "Scroll ↓", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 100, 255), 2)
        elif fingers == 3:
            pyautogui.scroll(30)
            cv2.putText(frame, "Scroll ↑", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 255), 2)

        # ----- Swipe (next / previous workspace or tab)
        dx = (raw_x * w - last_raw_x * w)  # pixels in *frame*, not screen
        now = time.time()
        if abs(dx) > SWIPE_SPEED_PX and (now - last_swipe_time) > SWIPE_COOLDOWN_S:
            if dx < 0:
                pyautogui.hotkey("ctrl", "left")
                cv2.putText(frame, "Swipe ←", (10, 160),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 100, 100), 2)
            else:
                pyautogui.hotkey("ctrl", "right")
                cv2.putText(frame, "Swipe →", (10, 160),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 255, 100), 2)
            last_swipe_time = now
        last_raw_x = raw_x

        # ----- Launchpad (fist closes)
        if total_dist < LAUNCHPAD_TOTAL:
            pyautogui.press("f4")
            cv2.putText(frame, "Launchpad", (10, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Draw hand skeleton
        draw.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS)

    else:
        cv2.putText(frame, "No hand 😢", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    cv2.imshow("AirPointer", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
