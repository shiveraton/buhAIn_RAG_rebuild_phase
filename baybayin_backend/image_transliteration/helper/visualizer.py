import cv2
import matplotlib.pyplot as plt

class DataVisualizer:
    def __init__(self):
        pass

    def visualize_image(self, img, cmap_value="gray"):
        if img is None:
            print("ERROR: image is empty")
            return
        
        plt.imshow(img, cmap=cmap_value)
        plt.show()
        
    def visualize_keypoints(self, img, keypoints, window_title="ORB Keypoints"):
        if img is None:
            print("ERROR: image is empty")
            return

        img_with_kp = cv2.drawKeypoints(
            img, 
            keypoints, 
            None, 
            color=(0, 255, 0),
            flags=cv2.DRAW_MATCHES_FLAGS_DEFAULT
        )

        if len(img_with_kp.shape) == 3:  
            img_with_kp = cv2.cvtColor(img_with_kp, cv2.COLOR_BGR2RGB)

        plt.figure(figsize=(8, 6))
        plt.title(window_title)
        plt.imshow(img_with_kp, cmap="gray")
        plt.show()
