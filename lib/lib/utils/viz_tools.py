import cv2
import numpy as np

def display_images(images, titles):
    import matplotlib.pyplot as plt
    for i in range(len(images)):
        plt.subplot(1, len(images), i+1)
        
        # Handle different image types
        img = images[i]
        
        if len(img.shape) == 3:
            # Color image (BGR to RGB conversion)
            if img.shape[2] == 3:
                img_display = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            else:
                img_display = img
            plt.imshow(img_display)
        elif len(img.shape) == 2:
            # Grayscale image
            plt.imshow(img, cmap='gray')
        else:
            # Skip non-image data (like contours)
            print(f"Skipping non-image data: {img.shape}")
            continue
            
        plt.title(titles[i])
        plt.axis('off')
    
    plt.tight_layout()
    plt.show()

def canny_interactive_dials(img):
    """Interactive Canny edge detection with proper window sizing and aperture size."""
    winname = 'canny_interactive'
    
    # Create resizable window
    cv2.namedWindow(winname, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(winname, 800, 600)
    
    # Get image dimensions
    h, w = img.shape[:2]
    print(f"Image size: {w}x{h}")
    
    cv2.createTrackbar('low_thresh', winname, 0, 255, lambda x: None)
    cv2.createTrackbar('high_thresh', winname, 0, 255, lambda x: None)
    cv2.createTrackbar('aperture_size', winname, 3, 7, lambda x: None)
    
    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        try:
            if cv2.getWindowProperty(winname, cv2.WND_PROP_VISIBLE) < 1:
                break
            
            # Get current window size
            window_width = cv2.getWindowImageRect(winname)[2]
            window_height = cv2.getWindowImageRect(winname)[3]
            
            # Leave room for text overlay (subtract 100 pixels for text area)
            available_height = window_height - 100
            
            # Get trackbar values
            low_thresh = cv2.getTrackbarPos('low_thresh', winname)
            high_thresh = cv2.getTrackbarPos('high_thresh', winname)
            aperture_size = cv2.getTrackbarPos('aperture_size', winname)
            
            # Ensure aperture is odd
            if aperture_size % 2 == 0:
                aperture_size += 1
            if aperture_size < 3:
                aperture_size = 3
            if aperture_size > 7:
                aperture_size = 7
                
            # Apply Canny edge detection
            canny_edge = cv2.Canny(img, low_thresh, high_thresh, apertureSize=aperture_size)
            
            # Create display image with extra space for text (using original dimensions)
            display_h = h + 100  # Add 100 pixels for text
            display_w = w
            result = np.zeros((display_h, display_w, 3), dtype=np.uint8)
            
            # Handle both grayscale and color images
            if len(canny_edge.shape) == 2:
                # Convert grayscale to BGR for display
                edge_display = cv2.cvtColor(canny_edge, cv2.COLOR_GRAY2BGR)
            else:
                edge_display = canny_edge
            
            result[:h, :w] = edge_display
            
            # Add parameter info in the extra space
            cv2.putText(result, f"Low Threshold: {low_thresh}", (10, h + 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(result, f"High Threshold: {high_thresh}", (10, h + 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(result, f"Aperture Size: {aperture_size}", (10, h + 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Resize the final result for display
            result_resized = image_resize(result, width=window_width, height=window_height)
            cv2.imshow(winname, result_resized)
            
        except cv2.error:
            break

    cv2.destroyAllWindows()
    return canny_edge

def image_resize(image, width = None, height = None, inter = cv2.INTER_AREA):
    # initialize the dimensions of the image to be resized and
    # grab the image size
    (h, w) = image.shape[:2]

    # if both the width and height are None, then return the
    # original image
    if width is None and height is None:
        return image

    # calculate scale factors for both dimensions
    if width is None:
        scale = height / float(h)
        new_width = int(w * scale)
        new_height = height
    elif height is None:
        scale = width / float(w)
        new_width = width
        new_height = int(h * scale)
    else:
        # Both width and height specified - maintain aspect ratio and add padding
        scale_w = width / float(w)
        scale_h = height / float(h)
        scale = min(scale_w, scale_h)  # Use smaller scale to fit within bounds
        
        new_width = int(w * scale)
        new_height = int(h * scale)

    # resize the image maintaining aspect ratio
    resized = cv2.resize(image, (new_width, new_height), interpolation = inter)

    # if both width and height were specified, add black padding to center the image
    if width is not None and height is not None:
        # Create black canvas with target dimensions
        if len(image.shape) == 3:
            # Color image
            canvas = np.zeros((height, width, image.shape[2]), dtype=image.dtype)
        else:
            # Grayscale image
            canvas = np.zeros((height, width), dtype=image.dtype)
        
        # Calculate position to center the resized image
        y_offset = (height - new_height) // 2
        x_offset = (width - new_width) // 2
        
        # Place resized image on black canvas
        canvas[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized
        resized = canvas

    # return the resized image
    return resized

def hough_lines_interactive_dials(img):
    """Interactive HoughLines with proper window sizing and diagonal-based rho limit."""
    winname = 'hough_interactive'
    
    # Create resizable window
    cv2.namedWindow(winname, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(winname, 800, 600)
    
    # Calculate image diagonal for rho upper limit
    h, w = img.shape[:2]
    max_rho = int(np.sqrt(h**2 + w**2))
    max_threshold = int(np.sqrt(h**2 + w**2))
    print(f"Image size: {w}x{h}, Max rho: {max_rho}")
    
    # Create trackbars with diagonal-based rho limit
    cv2.createTrackbar('rho', winname, 1, max_rho, lambda x: None)  # Distance resolution
    cv2.createTrackbar('theta_deg', winname, 1, 10, lambda x: None)  # Angle resolution
    cv2.createTrackbar('threshold', winname, 30, max_threshold, lambda x: None)  # Minimum votes
    cv2.createTrackbar('max_lines', winname, 20, 100, lambda x: None)  # Max lines to display
    
    gray = img
    
    # Create edges for HoughLines from original image
    edges = cv2.Canny(gray, 50, 150)
    
    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        try:
            if cv2.getWindowProperty(winname, cv2.WND_PROP_VISIBLE) < 1:
                break
            
            # Get current window size
            window_width = cv2.getWindowImageRect(winname)[2]
            window_height = cv2.getWindowImageRect(winname)[3]
            
            # Get trackbar values
            rho = max(1, cv2.getTrackbarPos('rho', winname))
            theta_deg = max(1, cv2.getTrackbarPos('theta_deg', winname))
            threshold = max(1, cv2.getTrackbarPos('threshold', winname))
            max_lines = max(1, cv2.getTrackbarPos('max_lines', winname))
            
            # Apply HoughLines to original edges
            theta = theta_deg * np.pi / 180
            lines = cv2.HoughLines(edges, rho, theta, threshold=threshold)
            
            # Create display image with extra space for text (using original dimensions)
            display_h = h + 150  # Add 150 pixels for text
            display_w = w
            result = np.zeros((display_h, display_w, 3), dtype=np.uint8)
            
            # Handle both grayscale and color images
            if len(img.shape) == 2:
                # Convert grayscale to BGR for display
                img_display = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            else:
                img_display = img
            
            result[:h, :w] = img_display
            
            if lines is not None:
                # Draw lines on the original image area
                for i, line in enumerate(lines[:max_lines]):
                    rho_val, theta_val = line[0]
                    a = np.cos(theta_val)
                    b = np.sin(theta_val)
                    x0 = a * rho_val
                    y0 = b * rho_val
                    x1 = int(x0 + 1000 * (-b))
                    y1 = int(y0 + 1000 * (a))
                    x2 = int(x0 - 1000 * (-b))
                    y2 = int(y0 - 1000 * (a))
                    
                    cv2.line(result, (x1, y1), (x2, y2), (0, 0, 255), 2)
                
                # Add text overlay in the extra space
                cv2.putText(result, f"Lines: {len(lines)}", (10, h + 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                cv2.putText(result, "No lines detected", (10, h + 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Add parameter info in the extra space
            cv2.putText(result, f"Rho: {rho}/{max_rho}", (10, h + 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(result, f"Theta: {theta_deg} degree(s)", (10, h + 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(result, f"Threshold: {threshold}", (10, h + 130), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Resize the final result for display
            result_resized = image_resize(result, width=window_width, height=window_height)
            cv2.imshow(winname, result_resized)
            
        except cv2.error:
            break
    
    cv2.destroyAllWindows()
    return lines