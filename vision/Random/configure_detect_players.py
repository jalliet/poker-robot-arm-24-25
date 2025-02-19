import cv2
import numpy as np

def resize_image(image, max_width=800, max_height=600):
    """
    Resizes an image to fit within the specified maximum width and height while maintaining aspect ratio.

    Parameters:
        image (numpy.ndarray): The input image to resize.
        max_width (int): The maximum width of the resized image.
        max_height (int): The maximum height of the resized image.

    Returns:
        numpy.ndarray: The resized image.
    """
    height, width = image.shape[:2]
    scaling_factor = min(max_width / width, max_height / height, 1)

    if scaling_factor < 1:
        new_size = (int(width * scaling_factor), int(height * scaling_factor))
        resized_image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
        return resized_image
    return image

def update_canny(val, blurred, orig_image, max_width, max_height):
    """
    Updates the Canny edge detection and displays the results based on trackbar values.
    """
    low_threshold = cv2.getTrackbarPos('Low Threshold', 'Canny Edges')
    high_threshold = cv2.getTrackbarPos('High Threshold', 'Canny Edges')
    
    # Perform Canny edge detection with the current trackbar thresholds
    edges = cv2.Canny(blurred, low_threshold, high_threshold)
    
    # Resize and show edges in the Canny window
    resized_edges = resize_image(edges, max_width, max_height)
    cv2.imshow('Canny Edges', resized_edges)
    
    # Find contours based on the edges
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    output_image = orig_image.copy()
    cv2.drawContours(output_image, contours, -1, (0, 255, 0), 3)

    # Resize and display the image with detected contours
    resized_with_contours = resize_image(output_image, max_width, max_height)
    cv2.imshow('Detected Contours', resized_with_contours)

def detect_cards(image_path, debug=False, max_width=800, max_height=600):
    """
    Detects playing cards in an image using edge detection and contour analysis.

    Parameters:
        image_path (str): Path to the input image.
        debug (bool): If True, displays intermediate steps and enables Canny trackbars.
        max_width (int): Maximum width for resized images.
        max_height (int): Maximum height for resized images.

    Returns:
        List of detected card contours and their bounding rectangles.
    """
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not read the image file at {image_path}.")
        return []

    orig_image = image.copy()
    height, width = image.shape[:2]

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if debug:
        resized_gray = resize_image(gray, max_width, max_height)
        cv2.namedWindow("Grayscale Image", cv2.WINDOW_NORMAL)
        cv2.imshow("Grayscale Image", resized_gray)
        cv2.moveWindow("Grayscale Image", 100, 100)  # Position window
        cv2.waitKey(0)

    # Apply Gaussian Blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    if debug:
        resized_blurred = resize_image(blurred, max_width, max_height)
        cv2.namedWindow("Blurred Image", cv2.WINDOW_NORMAL)
        cv2.imshow("Blurred Image", resized_blurred)
        cv2.moveWindow("Blurred Image", 150, 150)  # Position window
        cv2.waitKey(0)

        # Create Canny edge detection window with trackbars
        cv2.namedWindow('Canny Edges', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Detected Contours', cv2.WINDOW_NORMAL)

        # Create trackbars for lower and upper Canny thresholds
        cv2.createTrackbar('Low Threshold', 'Canny Edges', 50, 100, lambda val: update_canny(val, blurred, orig_image, max_width, max_height))
        cv2.createTrackbar('High Threshold', 'Canny Edges', 150, 300, lambda val: update_canny(val, blurred, orig_image, max_width, max_height))

        # Display initial Canny edge detection results
        update_canny(0, blurred, orig_image, max_width, max_height)

        # Wait until the user presses a key
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # Perform Canny edge detection (default values)
    edges = cv2.Canny(blurred, 15, 25)

    if debug:
        resized_edges = resize_image(edges, max_width, max_height)
        cv2.namedWindow("Canny Edges", cv2.WINDOW_NORMAL)
        cv2.imshow("Canny Edges", resized_edges)
        cv2.moveWindow("Canny Edges", 200, 200)  # Position window
        cv2.waitKey(0)

    # Find contours in the edge-detected image
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Draw the contours on the original image
    cv2.drawContours(orig_image, contours, -1, (0, 255, 0), 3)  # Green color for contours

    # Resize the original image with contours for display if necessary
    resized_image_with_contours = resize_image(orig_image, max_width, max_height)

    if debug:
        cv2.namedWindow("Detected Contours", cv2.WINDOW_NORMAL)
        cv2.imshow("Detected Contours", resized_image_with_contours)
        cv2.moveWindow("Detected Contours", 250, 250)  # Position window
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    detected_cards = []
    bounding_rects = []

    for cnt in contours:
        hull = cv2.convexHull(cnt)
        
        # Approximate the contour to a polygon
        epsilon = 0.03 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(hull, epsilon, True)

        # Continue if the approximated convex hull has 4 sides (quadrilateral)
        if len(approx) == 4:
            # Compute the bounding rectangle
            x, y, w, h = cv2.boundingRect(approx)

            # Calculate aspect ratio to filter out non-card shapes
            aspect_ratio = w / float(h)
            # Standard playing cards have an aspect ratio close to 0.7 (width / height)
            if 0.6 < aspect_ratio < 0.8:
                # Filter based on size (adjust thresholds as needed)
                if 1000 < cv2.contourArea(cnt) < 15000:
                    detected_cards.append(approx)
                    bounding_rects.append((x, y, w, h))

                    # Draw the contour and bounding box on the original image
                    cv2.drawContours(orig_image, [approx], -1, (0, 255, 0), 2)
                    cv2.rectangle(orig_image, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    cv2.putText(orig_image, f"Card {len(detected_cards)}", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    print(f"Total Cards Detected: {len(detected_cards)}")
    for idx, rect in enumerate(bounding_rects, 1):
        x, y, w, h = rect
        print(f"Card {idx}: Position=({x}, {y}), Width={w}, Height={h}")

    return detected_cards, bounding_rects

if __name__ == "__main__":
    import argparse

    # Argument parser for command-line options
    parser = argparse.ArgumentParser(description="Detect playing cards in an image using OpenCV.")
    parser.add_argument("image_path", help="Path to the input image containing playing cards.")
    parser.add_argument("--debug", action="store_true", help="Display intermediate processing steps and enable Canny trackbars.")
    parser.add_argument("--max_width", type=int, default=800, help="Maximum width for resized images.")
    parser.add_argument("--max_height", type=int, default=600, help="Maximum height for resized images.")

    args = parser.parse_args()

    detect_cards(args.image_path, debug=args.debug, max_width=args.max_width, max_height=args.max_height)
