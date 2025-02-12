import cv2
import numpy as np
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt

def resize_image(image, max_width=800, max_height=600):
    height, width = image.shape[:2]
    scaling_factor = min(max_width / width, max_height / height, 1)  # Ensure scaling factor <= 1

    if scaling_factor < 1:
        new_size = (int(width * scaling_factor), int(height * scaling_factor))
        resized_image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
        return resized_image
    return image

def calculate_contour_centers(contours):
    centers = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        center = (x + w / 2, y + h / 2)
        centers.append(center)
    return np.array(centers)

def print_contour_distances(centers):
    if len(centers) < 2:
        print("Not enough contours to calculate distances.")
        return
    
    distances = []
    
    # Calculate pairwise distances
    for i in range(len(centers)):
        for j in range(i + 1, len(centers)):
            dist = np.linalg.norm(centers[i] - centers[j])
            distances.append(dist)
    
    # Compute statistics
    min_distance = np.min(distances)
    max_distance = np.max(distances)
    mean_distance = np.mean(distances)
    
    print(f"Minimum distance between contours: {min_distance}")
    print(f"Maximum distance between contours: {max_distance}")
    print(f"Mean distance between contours: {mean_distance}")
    
    return distances

def visualize_contour_centers(centers, labels):
    plt.figure(figsize=(10, 8))
    unique_labels = set(labels)
    colors = [plt.cm.Spectral(each) for each in np.linspace(0, 1, len(unique_labels))]
    
    for k, col in zip(unique_labels, colors):
        if k == -1:
            # Black used for noise.
            col = [0, 0, 0, 1]

        class_member_mask = (labels == k)

        xy = centers[class_member_mask]
        plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=tuple(col),
                 markeredgecolor='k', markersize=6)

    plt.title('DBSCAN Clustering of Card Contours')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.show()

def group_contours_by_proximity(contours, eps=5000, min_samples=1, debug=False):
    centers = calculate_contour_centers(contours)
    
    # Print centers for debugging
    print("Contour centers:")
    print(centers)
    
    # Print distance statistics
    distances = print_contour_distances(centers)
    
    # Apply DBSCAN clustering
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(centers)
    
    labels = clustering.labels_
    unique_labels = set(labels)
    
    # Print cluster labels
    print(f"DBSCAN Cluster Labels: {labels}")
    
    # Remove noise label (-1) if exists
    if -1 in unique_labels:
        unique_labels.remove(-1)
    num_players = len(unique_labels)
    print(f"Number of players (clusters) found: {num_players}")
    
    # Group contours by label using index mapping
    grouped_contours = {label: [] for label in unique_labels}
    for idx, label in enumerate(labels):
        if label != -1:
            grouped_contours[label].append(contours[idx])
    
    if debug:
        visualize_contour_centers(centers, labels)
    
    return grouped_contours, num_players, labels

def get_player_bounding_boxes(grouped_contours):
    players = []
    
    for label, contour_group in grouped_contours.items():
        x_min, y_min, x_max, y_max = float('inf'), float('inf'), 0, 0
        
        for cnt in contour_group:
            x, y, w, h = cv2.boundingRect(cnt)
            x_min = min(x_min, x)
            y_min = min(y_min, y)
            x_max = max(x_max, x + w)
            y_max = max(y_max, y + h)
        
        # Bounding box
        bounding_box = (int(x_min), int(y_min), int(x_max - x_min), int(y_max - y_min))
        
        # Center point
        center = (int(x_min + (x_max - x_min) / 2), int(y_min + (y_max - y_min) / 2))
        
        players.append({"center": center, "bounding_box": bounding_box})
    
    return players

def visualize_clusters_on_image(image, centers, labels):
    unique_labels = set(labels)
    colors = [tuple(np.random.randint(0, 255, size=3).tolist()) for _ in unique_labels]
    
    for center, label in zip(centers, labels):
        if label == -1:
            color = (0, 0, 0)  # Black for noise
        else:
            color = colors[label]
        cv2.circle(image, (int(center[0]), int(center[1])), 10, color, -1)
        if label != -1:
            cv2.putText(image, f"Cluster {label}", (int(center[0]), int(center[1])), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    cv2.imshow("Clusters Visualization", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def detect_cards(image_path, eps=5000, min_samples=1, debug=False, max_width=800, max_height=600):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not read the image file at {image_path}.")
        return []
    
    orig_image = image.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 100, 200)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if debug:
        cv2.drawContours(orig_image, contours, -1, (0, 255, 0), 2)
        resized_image_with_contours = resize_image(orig_image, max_width, max_height)
        cv2.imshow("Detected Contours", resized_image_with_contours)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    # Group contours using DBSCAN
    grouped_contours, num_players, labels = group_contours_by_proximity(contours, eps=eps, min_samples=min_samples, debug=debug)
    players = get_player_bounding_boxes(grouped_contours)
    
    for idx, player in enumerate(players, 1):
        x, y, w, h = player["bounding_box"]
        center_x, center_y = player["center"]
    
        # Draw bounding box and center for each player
        cv2.rectangle(orig_image, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.circle(orig_image, (int(center_x), int(center_y)), 5, (0, 0, 255), -1)
        cv2.putText(orig_image, f"Player {idx}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    if debug:
        # Visualize cluster assignments
        centers = calculate_contour_centers(contours)
        visualize_clusters_on_image(orig_image, centers, labels)
        
        resized_image_with_players = resize_image(orig_image, max_width, max_height)
        cv2.imshow("Players Grouped", resized_image_with_players)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    print(f"Number of players (clusters) found: {num_players}")
    for idx, player in enumerate(players, 1):
        x, y, w, h = player["bounding_box"]
        center_x, center_y = player["center"]
        print(f"Player {idx}: Center=({center_x}, {center_y}), Bounding Box=({x}, {y}, {w}, {h})")
    
    return players

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Detect and group playing cards by proximity into players.")
    parser.add_argument("image_path", help="Path to the input image containing playing cards.")
    parser.add_argument("--debug", action="store_true", help="Display intermediate processing steps and visualizations.")
    parser.add_argument("--max_width", type=int, default=800, help="Maximum width for resized images.")
    parser.add_argument("--max_height", type=int, default=600, help="Maximum height for resized images.")
    parser.add_argument("--eps", type=float, default=500, help="DBSCAN epsilon parameter for clustering.")
    parser.add_argument("--min_samples", type=int, default=10, help="DBSCAN min_samples parameter for clustering.")
    
    args = parser.parse_args()
    
    detect_cards(
        args.image_path, 
        eps=args.eps, 
        min_samples=args.min_samples, 
        debug=args.debug, 
        max_width=args.max_width, 
        max_height=args.max_height
    )
