import cv2
import numpy as np
import os
from typing import List, Tuple

class ImageStraightener:
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.image = cv2.imread(image_path)
        if self.image is None:
            raise ValueError(f"Could not load image from {image_path}")
        self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.straightened_image = None
        
    def detect_corner_markers(self) -> List[Tuple[int, int]]:
        """Detect the corner markers (black squares) in the image"""
        # Create a binary image
        _, binary = cv2.threshold(self.gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        corners = []
        for contour in contours:
            # Filter contours by area and aspect ratio
            area = cv2.contourArea(contour)
            if 100 < area < 2000:  # Adjust based on marker size
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                
                # Corner markers should be roughly square and near the corners
                if 0.7 < aspect_ratio < 1.3:  # Roughly square
                    # Check if it's near a corner
                    height, width = self.gray.shape
                    center_x, center_y = x + w//2, y + h//2
                    
                    # Define corner regions (adjust margins as needed)
                    margin = 100
                    if ((center_x < margin or center_x > width - margin) and 
                        (center_y < margin or center_y > height - margin)):
                        corners.append((center_x, center_y))
        
        # Sort corners: top-left, top-right, bottom-right, bottom-left
        if len(corners) >= 4:
            corners = sorted(corners)
            # Sort by y-coordinate to separate top and bottom pairs
            top_corners = sorted([c for c in corners if c[1] < self.gray.shape[0]//2])
            bottom_corners = sorted([c for c in corners if c[1] >= self.gray.shape[0]//2])
            
            # Sort each pair by x-coordinate
            if len(top_corners) >= 2 and len(bottom_corners) >= 2:
                return [top_corners[0], top_corners[-1], bottom_corners[-1], bottom_corners[0]]
        
        # Fallback: use image corners if markers not detected properly
        h, w = self.gray.shape
        margin = 50
        return [(margin, margin), (w-margin, margin), (w-margin, h-margin), (margin, h-margin)]
    
    def crop_and_straighten(self, corners: List[Tuple[int, int]], output_width: int = 800, output_height: int = 1000) -> np.ndarray:
        """Crop and straighten the image based on corner points"""
        # Define the destination points for perspective correction
        dst_points = np.float32([[0, 0], [output_width, 0], [output_width, output_height], [0, output_height]])
        
        # Convert corners to numpy array
        src_points = np.float32(corners)
        
        # Get perspective transform matrix
        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        
        # Apply perspective correction
        self.straightened_image = cv2.warpPerspective(self.image, matrix, (output_width, output_height))
        return self.straightened_image
    
    def save_straightened_image(self, output_path: str):
        """Save the straightened image to specified path"""
        if self.straightened_image is None:
            raise ValueError("No straightened image to save. Run crop_and_straighten() first.")
        
        success = cv2.imwrite(output_path, self.straightened_image)
        if not success:
            raise ValueError(f"Failed to save image to {output_path}")
        
        print(f"Straightened image saved to: {output_path}")
    
    def process_image(self, output_path: str, output_width: int = 800, output_height: int = 1000):
        """Complete processing pipeline: detect corners, straighten, and save"""
        print(f"Processing image: {self.image_path}")
        
        print("Detecting corner markers...")
        corners = self.detect_corner_markers()
        print(f"Found corners at: {corners}")
        
        print("Cropping and straightening image...")
        self.crop_and_straighten(corners, output_width, output_height)
        
        print("Saving straightened image...")
        self.save_straightened_image(output_path)
        
        print("Processing complete!")

def main():
    # Define input and output paths here
    input_image_path = ".\\Output\\filled_answer_sheet.png"      # Change this to your input image path
    output_image_path = ".\\Output\\croppedstraighten_answer_sheet.png"  # Change this to your desired output path
    
    # Optional: define output dimensions (width, height)
    output_width = 800
    output_height = 1000
    
    # Check if input file exists
    if not os.path.exists(input_image_path):
        print(f"Error: Input image file '{input_image_path}' not found.")
        print("Please update the input_image_path variable in main() with the correct path.")
        return
    
    try:
        # Create straightener instance and process the image
        straightener = ImageStraightener(input_image_path)
        straightener.process_image(output_image_path, output_width, output_height)
        
    except Exception as e:
        print(f"Error processing image: {e}")
        print("Make sure OpenCV is installed: pip install opencv-python")

if __name__ == "__main__":
    main()
