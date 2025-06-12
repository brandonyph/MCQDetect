import cv2
import numpy as np
from typing import List, Dict, Tuple
import json
import argparse
import os

class MCQAnswerSheetScanner:
    def __init__(self):
        self.answers = {}
        self.bubble_threshold = 0.6  # Threshold for determining if a bubble is filled
        
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Load and preprocess the image for better bubble detection"""
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY_INV, 11, 2)
        
        return thresh, gray, img
    
    def detect_bubbles(self, thresh_img: np.ndarray, original_img: np.ndarray) -> List[Dict]:
        """Detect circular bubbles in the image"""
        # Find contours
        contours, _ = cv2.findContours(thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        bubbles = []
        
        for contour in contours:
            # Calculate area and perimeter
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            
            # Filter by area (adjust these values based on your image size)
            if area < 100 or area > 2000:
                continue
            
            # Calculate circularity
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            
            # Filter by circularity (circles should have circularity close to 1)
            if circularity < 0.6:
                continue
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Check aspect ratio (circles should be roughly square)
            aspect_ratio = float(w) / h
            if aspect_ratio < 0.7 or aspect_ratio > 1.3:
                continue
            
            # Calculate center
            center_x = x + w // 2
            center_y = y + h // 2
            
            # Extract the bubble region for fill detection
            bubble_region = thresh_img[y:y+h, x:x+w]
            fill_ratio = np.sum(bubble_region) / (255 * w * h)
            
            bubbles.append({
                'center': (center_x, center_y),
                'bbox': (x, y, w, h),
                'area': area,
                'fill_ratio': fill_ratio,
                'contour': contour
            })
        
        return bubbles
    
    def organize_bubbles_by_rows(self, bubbles: List[Dict]) -> Dict[int, List[Dict]]:
        """Organize bubbles into rows based on their y-coordinates"""
        if not bubbles:
            return {}
        
        # Sort bubbles by y-coordinate
        bubbles.sort(key=lambda b: b['center'][1])
        
        rows = {}
        current_row = 0
        last_y = bubbles[0]['center'][1]
        tolerance = 20  # Pixels tolerance for same row
        
        for bubble in bubbles:
            y = bubble['center'][1]
            
            # If y-coordinate is significantly different, start new row
            if abs(y - last_y) > tolerance:
                current_row += 1
                last_y = y
            
            if current_row not in rows:
                rows[current_row] = []
            
            rows[current_row].append(bubble)
        
        # Sort bubbles in each row by x-coordinate
        for row in rows.values():
            row.sort(key=lambda b: b['center'][0])
        
        return rows
    
    def map_bubbles_to_questions(self, organized_bubbles: Dict[int, List[Dict]]) -> Dict[int, str]:
        """Map detected bubbles to question numbers and answer choices"""
        answers = {}
        
        # Expected pattern: 50 questions, 4 choices each (A, B, C, D)
        # Questions 1-25 on left side, 26-50 on right side
        choices = ['A', 'B', 'C', 'D']
        
        # Sort rows by average y-coordinate
        sorted_rows = sorted(organized_bubbles.items(), key=lambda x: np.mean([b['center'][1] for b in x[1]]))
        
        for row_idx, (_, row_bubbles) in enumerate(sorted_rows):
            if len(row_bubbles) < 4:  # Skip rows with insufficient bubbles
                continue
            
            # Determine if this is left side (questions 1-25) or right side (questions 26-50)
            avg_x = np.mean([b['center'][0] for b in row_bubbles])
            
            # Split bubbles into left and right groups
            left_bubbles = [b for b in row_bubbles if b['center'][0] < avg_x]
            right_bubbles = [b for b in row_bubbles if b['center'][0] >= avg_x]
            
            # Process left side (questions 1-25)
            if len(left_bubbles) >= 4:
                left_bubbles.sort(key=lambda b: b['center'][0])
                question_num = row_idx + 1
                if question_num <= 25:
                    for i, bubble in enumerate(left_bubbles[:4]):
                        if bubble['fill_ratio'] > self.bubble_threshold:
                            answers[question_num] = choices[i]
                            break
            
            # Process right side (questions 26-50)
            if len(right_bubbles) >= 4:
                right_bubbles.sort(key=lambda b: b['center'][0])
                question_num = row_idx + 26
                if question_num <= 50:
                    for i, bubble in enumerate(right_bubbles[:4]):
                        if bubble['fill_ratio'] > self.bubble_threshold:
                            answers[question_num] = choices[i]
                            break
        
        return answers
    
    def scan_answer_sheet(self, image_path: str, debug: bool = False, output_dir: str = ".") -> Dict[int, str]:
        """Main function to scan the answer sheet and extract answers"""
        try:
            # Preprocess image
            thresh_img, gray_img, original_img = self.preprocess_image(image_path)
            
            # Detect bubbles
            bubbles = self.detect_bubbles(thresh_img, original_img)
            
            if debug:
                print(f"Detected {len(bubbles)} potential bubbles")
            
            # Organize bubbles by rows
            organized_bubbles = self.organize_bubbles_by_rows(bubbles)
            
            if debug:
                print(f"Organized into {len(organized_bubbles)} rows")
                for row_idx, row_bubbles in organized_bubbles.items():
                    print(f"Row {row_idx}: {len(row_bubbles)} bubbles")
            
            # Map bubbles to questions and answers
            answers = self.map_bubbles_to_questions(organized_bubbles)
            
            if debug:
                # Create debug image showing detected bubbles
                debug_img = original_img.copy()
                for bubble in bubbles:
                    x, y, w, h = bubble['bbox']
                    color = (0, 255, 0) if bubble['fill_ratio'] > self.bubble_threshold else (0, 0, 255)
                    cv2.rectangle(debug_img, (x, y), (x+w, y+h), color, 2)
                    cv2.putText(debug_img, f"{bubble['fill_ratio']:.2f}", 
                              (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                
                # Save debug image to output directory
                debug_output_path = os.path.join(output_dir, 'debug_bubbles.jpg')
                cv2.imwrite(debug_output_path, debug_img)
                print(f"Debug image saved as '{debug_output_path}'")
            
            return answers
            
        except Exception as e:
            print(f"Error scanning answer sheet: {str(e)}")
            return {}
    
    def save_results(self, answers: Dict[int, str], output_dir: str = ".", output_filename: str = "scanned_answers.json"):
        """Save the scanned answers to a JSON file in the specified directory"""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create full output path
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'w') as f:
            json.dump(answers, f, indent=2)
        print(f"Results saved to {output_path}")
    
    def print_results(self, answers: Dict[int, str]):
        """Print the scanned answers in a readable format"""
        print("\n=== SCANNED ANSWERS ===")
        for question in range(1, 51):
            answer = answers.get(question, "No answer detected")
            print(f"Question {question:2d}: {answer}")
        
        print(f"\nTotal answered questions: {len(answers)}/50")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='MCQ Answer Sheet Scanner')
    parser.add_argument('image_path', help='Path to the answer sheet image')
    parser.add_argument('-o', '--output-dir', default='.', 
                       help='Output directory for results (default: current directory)')
    parser.add_argument('-f', '--output-file', default='scanned_answers.json',
                       help='Output filename for JSON results (default: scanned_answers.json)')
    parser.add_argument('-d', '--debug', action='store_true',
                       help='Enable debug mode (saves debug image)')
    parser.add_argument('-t', '--threshold', type=float, default=0.6,
                       help='Bubble fill threshold (0.0-1.0, default: 0.6)')
    
    return parser.parse_args()

# Usage example
if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    # Create scanner instance
    scanner = MCQAnswerSheetScanner()
    
    # Set bubble threshold if provided
    scanner.bubble_threshold = args.threshold
    
    try:
        # Scan the answer sheet
        answers = scanner.scan_answer_sheet(args.image_path, debug=args.debug, output_dir=args.output_dir)
        
        # Print results
        scanner.print_results(answers)
        
        # Save results to JSON file in specified directory
        scanner.save_results(answers, args.output_dir, args.output_file)
        
    except FileNotFoundError:
        print(f"Error: Could not find image file '{args.image_path}'")
        print("Please make sure the image file exists and provide the correct path")
    except Exception as e:
        print(f"Error: {str(e)}")
