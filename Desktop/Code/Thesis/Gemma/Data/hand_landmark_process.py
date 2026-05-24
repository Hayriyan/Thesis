# hand_landmark_process.py
import cv2
import mediapipe as mp
import pyautogui
import math
import time

def run_hand_landmark():
    """
    Runs the hand-tracking code in a separate process:
      - Opens the webcam,
      - Uses MediaPipe to track hand landmarks,
      - Performs mouse actions (click, drag, etc.) via pyautogui.
    """
    cap = cv2.VideoCapture(0)
    hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
    draw = mp.solutions.drawing_utils
    screen_w, screen_h = pyautogui.size()

    prev_x, prev_y = 0, 0
    smooth_factor = 5
    click_down = False
    drag_mode = False
    last_swipe_time = 0

    def get_distance(p1, p2, frame_w, frame_h):
        x1, y1 = int(p1.x * frame_w), int(p1.y * frame_h)
        x2, y2 = int(p2.x * frame_w), int(p2.y * frame_h)
        return math.hypot(x2 - x1, y2 - y1)

    while True:
        success, frame = cap.read()
        if not success:
            time.sleep(0.01)
            continue

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            for hand in result.multi_hand_landmarks:
                draw.draw_landmarks(frame, hand, mp.solutions.hands.HAND_CONNECTIONS)
                lm = hand.landmark

                # Follow the index finger with the mouse
                index_tip = lm[8]
                index_x = int(index_tip.x * screen_w)
                index_y = int(index_tip.y * screen_h)
                curr_x = prev_x + (index_x - prev_x) / smooth_factor
                curr_y = prev_y + (index_y - prev_y) / smooth_factor
                pyautogui.moveTo(curr_x, curr_y)
                prev_x, prev_y = curr_x, curr_y

                cx, cy = int(index_tip.x * w), int(index_tip.y * h)
                cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)

                thumb_tip = lm[4]
                pinky_tip = lm[20]
                middle_tip = lm[12]

                pinch_distance = get_distance(index_tip, thumb_tip, w, h)
                right_click_distance = get_distance(thumb_tip, pinky_tip, w, h)

                # Click logic
                if 40 < pinch_distance < 70:
                    if not click_down:
                        click_down = True
                        pyautogui.click()
                        cv2.putText(frame, "Click", (cx, cy - 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                elif pinch_distance <= 40:
                    if not click_down:
                        click_down = True
                        pyautogui.doubleClick()
                        cv2.putText(frame, "Double Click", (cx, cy - 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
                elif right_click_distance < 60:
                    if not click_down:
                        click_down = True
                        pyautogui.rightClick()
                        cv2.putText(frame, "Right Click", (cx, cy - 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                elif 70 < pinch_distance < 120:
                    if not drag_mode:
                        drag_mode = True
                        pyautogui.mouseDown()
                        cv2.putText(frame, "Drag Start", (cx, cy - 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                else:
                    if drag_mode:
                        drag_mode = False
                        pyautogui.mouseUp()
                        cv2.putText(frame, "Drag End", (cx, cy - 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

                # Scrolling using the middle finger
                if middle_tip.y < 0.4:
                    pyautogui.scroll(20)
                    cv2.putText(frame, "Scroll Up", (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                                1, (0, 200, 255), 2)
                elif middle_tip.y > 0.7:
                    pyautogui.scroll(-20)
                    cv2.putText(frame, "Scroll Down", (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                                1, (0, 100, 255), 2)

                # Swipe detection (example using horizontal speed)
                now = time.time()
                speed_x = abs(index_x - prev_x)
                if speed_x > 100 and (now - last_swipe_time) > 1:
                    if index_x < prev_x:
                        pyautogui.hotkey("ctrl", "left")
                        cv2.putText(frame, "Swipe Left", (10, 90), cv2.FONT_HERSHEY_SIMPLEX,
                                    1, (255, 100, 100), 2)
                    else:
                        pyautogui.hotkey("ctrl", "right")
                        cv2.putText(frame, "Swipe Right", (10, 90), cv2.FONT_HERSHEY_SIMPLEX,
                                    1, (100, 255, 100), 2)
                    last_swipe_time = now

                click_down = False
        else:
            cv2.putText(frame, "No Hand Detected", (10, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow("AirPointer – Full Gesture System", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_hand_landmark()
