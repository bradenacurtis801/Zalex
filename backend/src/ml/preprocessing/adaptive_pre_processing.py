import cv2
import numpy as np
import src.utils.viz_tools as viz_tools


def prepare_text_for_processing(gray: np.ndarray) -> np.ndarray:
    """
    Prepare a grayscale image for text processing by ensuring text is white.
    Automatically detects text color and inverts if necessary.
    
    Args:
        gray_image (np.ndarray): Input grayscale image
        
    Returns:
        np.ndarray: Image with text as white pixels, ready for processing
    """
    if len(gray.shape) != 2:
        raise ValueError("Image must be grayscale")
    
    # Use Otsu's method to automatically determine text vs background
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    # Determine if text is dark or light by checking the histogram
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    dark_pixels = np.sum(hist[:128])  # Pixels with intensity 0-127
    light_pixels = np.sum(hist[128:])  # Pixels with intensity 128-255

    viz_tools.display_images([gray, binary], ['Gray', 'Binary'])
    
    # If more dark pixels, text is dark; otherwise text is light
    if dark_pixels > light_pixels:
        # Text is dark, so we need to invert to make text white
        return cv2.bitwise_not(binary)
    else:
        # Text is light, binary already has text as white
        return binary

def detect_skew_hough_lines(processed_image: np.ndarray) -> float:
    """
    Detect skew using Hough lines and display a single image with lines overlayed.
    
    Args:
        processed_image (np.ndarray): Pre-processed binary image should have as little noise as possible
    """
    if len(processed_image.shape) != 2:
        raise ValueError("Image must be grayscale")

    # calculate the edge pixels -- this will result in text edges in white.
    # NOTE: Adjusting the threshold1 and threshold2 (2nd and 3rd arg) does not seem to affect the results. 
            # Adjusting the apertureSize (4th arg) has a minor effect on generating accurate text edges.
    edges = cv2.Canny(processed_image, 0, 1, apertureSize=3)

    # Detect line
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=30)

    if lines is None:
        print("No lines detected.")
        return None

    # Draw lines overlay on original image
    line_angles = []
    for line in lines[:30]:  # optionally limit number of lines displayed
        _, theta = line[0]
        line_angles.append(np.degrees(theta) - 90)

    line_angles = np.array(line_angles)

    # filter out outliers
    median = np.median(line_angles)
    threshold = 20  # degrees
    filtered_angles = line_angles[np.abs(line_angles - median) < threshold]

    # Take the mean of filtered angles
    if len(filtered_angles) > 0:
        skew_angle = np.mean(filtered_angles)
    else:
        skew_angle = np.mean(line_angles)  # fallback if all considered outliers

    return skew_angle


def deskew(image):
    """
    Corrects the skew of a document image.

    This function takes a grayscale image, finds the text block,
    calculates its rotation angle, and rotates the image to make the text
    horizontal. This is critical for improving OCR accuracy as misaligned
    text can lead to character merging or splitting errors.[2, 3]

    Args:
        image: A grayscale OpenCV image (numpy array).

    Returns:
        The deskewed image.
    """

    angle = detect_skew_hough_lines(image)

    # Rotate the image to correct for the skew.
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, rotation_matrix, (w, h),
                             flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return rotated


def remove_noise(image):
    """
    Removes noise from an image while preserving edges.

    Uses Non-Local Means Denoising, an advanced technique that is more effective
    at removing scanner artifacts and "salt-and-pepper" noise than simple
    blurring filters, leading to clearer characters for the OCR engine.[4, 5]

    Args:
        image: An OpenCV image (can be color or grayscale).

    Returns:
        The denoised image.
    """
    if len(image.shape) == 2:
        # The parameters (h, templateWindowSize, searchWindowSize) are tuned for effectiveness.
        # h: Filter strength. A higher value removes more noise but may blur details.
        return cv2.fastNlMeansDenoising(image, None, h=10, templateWindowSize=7, searchWindowSize=21)
    else:
        return cv2.fastNlMeansDenoisingColored(image, None, h=10, templateWindowSize=7, searchWindowSize=21)


def adaptive_thresholding(image):
    """
    Applies adaptive thresholding to binarize the image.

    This method is superior to global thresholding for documents with uneven
    lighting, shadows, or stains, as it calculates a unique threshold for
    different regions of the image.[6, 7] This ensures that text is clearly
    separated from the background across the entire page.

    Args:
        image: A grayscale OpenCV image.

    Returns:
        The binarized (black and white) image.
    """
    # cv2.ADAPTIVE_THRESH_GAUSSIAN_C: Threshold value is the weighted sum of neighborhood values.
    # cv2.THRESH_BINARY: Pixels above the threshold are set to 255 (white).
    # blockSize: The size of the neighborhood area.
    # C: A constant subtracted from the mean.
    return cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 11, 2)


def adaptive_preprocessing_module(image_path):
    """
    Orchestrates the full adaptive pre-processing pipeline for OCR.

    Args:
        image_path (str): The file path to the input image.

    Returns:
        An OpenCV image object that has been optimized for OCR.
    """
    # Load the image from the specified path
    orig_gray_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if orig_gray_image is None:
        print(f"Error: Unable to load image at {image_path}")
        return None
    
    thresh = prepare_text_for_processing(orig_gray_image)

    viz_tools.display_images([orig_gray_image, thresh], ['Orig Gray Image', 'Thresh'])
    
    # 1. Denoising: Remove noise while preserving text clarity.
    denoised_image = remove_noise(thresh)

    # 2. Skew Correction: Correct the rotational skew of the document.
    deskewed_image = deskew(denoised_image)

    viz_tools.display_images([deskewed_image], ['Deskewed Image'])

    # 3. Binarization: Apply adaptive thresholding to create a clean black & white image.
    final_image = adaptive_thresholding(deskewed_image)

    return final_image, orig_gray_image


if __name__ == '__main__':
    # --- Replace this with the path to your document image ---
    # INPUT_IMAGE_PATH = './documents/179e55030d77f06414bc4229c767d6e4.jpg'
    # INPUT_IMAGE_PATH = 'C:/Users/brade/Downloads/ScanPro/ScanPro/test_data/rotated/rotated_115_page_11.png'
    # INPUT_IMAGE_PATH = './page_11_white_text_black_background_rotated_140.png'
    # INPUT_IMAGE_PATH = './page_11_black_text_white_background_rotated_140.png'
    INPUT_IMAGE_PATH = './page_2_black_text_white_background_rotated_140.png'

    processed_image, original_image = adaptive_preprocessing_module(INPUT_IMAGE_PATH)

    if processed_image is not None:
        # Display the original and processed images for comparison
        # Note: You may need to resize the images to fit your screen.
        viz_tools.display_images([original_image, processed_image], ['Original Image', 'Processed Image for OCR'])
