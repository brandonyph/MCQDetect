#!/usr/bin/env python3
"""
MCQ Answer Sheet Generator
Creates a printable answer sheet with corner markers for automatic processing.
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import argparse

class MCQSheetGenerator:
    def __init__(self, width=2480, height=3508):  # A4 at 300 DPI
        self.width = width
        self.height = height
        self.margin = 200
        self.corner_size = 80
        self.circle_radius = 38  # 150% bigger (25 * 1.5 = 37.5, rounded to 38)
        self.question_spacing = 90  # Increased from 60 to 90 for better spacing
        self.option_spacing = 120
        
    def create_corner_markers(self, draw):
        """Create L-shaped corner markers for sheet detection"""
        marker_thickness = 15
        marker_length = self.corner_size
        
        # Top-left corner
        draw.rectangle([50, 50, 50 + marker_length, 50 + marker_thickness], fill='black')
        draw.rectangle([50, 50, 50 + marker_thickness, 50 + marker_length], fill='black')
        
        # Top-right corner
        draw.rectangle([self.width - 50 - marker_length, 50, self.width - 50, 50 + marker_thickness], fill='black')
        draw.rectangle([self.width - 50 - marker_thickness, 50, self.width - 50, 50 + marker_length], fill='black')
        
        # Bottom-left corner
        draw.rectangle([50, self.height - 50 - marker_thickness, 50 + marker_length, self.height - 50], fill='black')
        draw.rectangle([50, self.height - 50 - marker_length, 50 + marker_thickness, self.height - 50], fill='black')
        
        # Bottom-right corner
        draw.rectangle([self.width - 50 - marker_length, self.height - 50 - marker_thickness, self.width - 50, self.height - 50], fill='black')
        draw.rectangle([self.width - 50 - marker_thickness, self.height - 50 - marker_length, self.width - 50, self.height - 50], fill='black')
    
    def create_header(self, draw, font_large, font_medium):
        """Create the header section with title and student info"""
        # Title
        title = "MULTIPLE CHOICE ANSWER SHEET"
        title_bbox = draw.textbbox((0, 0), title, font=font_large)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((self.width - title_width) // 2, 150), title, fill='black', font=font_large)
        
        # Student information fields
        y_start = 250
        fields = ["Name: " + "_" * 50, "Student ID: " + "_" * 30, "Date: " + "_" * 20]
        
        for i, field in enumerate(fields):
            draw.text((self.margin, y_start + i * 50), field, fill='black', font=font_medium)
    
    def create_mcq_grid(self, draw, font_medium, num_questions=50, options_per_question=4):
        """Create the MCQ answer grid"""
        start_y = 450
        questions_per_column = 25
        column_width = (self.width - 2 * self.margin) // 2
        
        option_letters = ['A', 'B', 'C', 'D', 'E'][:options_per_question]
        
        for q in range(num_questions):
            # Determine column and position
            column = q // questions_per_column
            row_in_column = q % questions_per_column
            
            x_base = self.margin + column * column_width
            y_pos = start_y + row_in_column * self.question_spacing
            
            # Question number - aligned with circle centers
            q_num = str(q + 1).zfill(2)
            # Calculate text height to center it with the circles
            text_bbox = draw.textbbox((0, 0), f"{q_num}.", font=font_medium)
            text_height = text_bbox[3] - text_bbox[1]
            question_y = y_pos + self.circle_radius - text_height // 2
            draw.text((x_base, question_y), f"{q_num}.", fill='black', font=font_medium)
            
            # Answer options
            for i, letter in enumerate(option_letters):
                option_x = x_base + 60 + i * self.option_spacing
                
                # Draw circle for answer - centered at option_x
                circle_center_x = option_x + self.circle_radius
                circle_center_y = y_pos + self.circle_radius
                
                draw.ellipse([
                    circle_center_x - self.circle_radius,
                    circle_center_y - self.circle_radius,
                    circle_center_x + self.circle_radius,
                    circle_center_y + self.circle_radius
                ], outline='black', width=3)
                
                # Draw letter centered inside the circle
                letter_bbox = draw.textbbox((0, 0), letter, font=font_medium)
                letter_width = letter_bbox[2] - letter_bbox[0]
                letter_height = letter_bbox[3] - letter_bbox[1]
                
                # Center the letter inside the circle
                letter_x = circle_center_x - letter_width // 2
                letter_y = circle_center_y - letter_height // 2
                
                draw.text((letter_x, letter_y), letter, fill='black', font=font_medium)
    
    def create_instructions(self, draw, font_small):
        """Add instructions at the bottom"""
        instructions = [
            "INSTRUCTIONS:",
            "• Use a No. 2 pencil or black pen only",
            "• Fill in circles completely",
            "• Erase completely to change answers",
            "• Make no stray marks on this sheet"
        ]
        
        start_y = self.height - 200
        for i, instruction in enumerate(instructions):
            draw.text((self.margin, start_y + i * 25), instruction, fill='black', font=font_small)
    
    def generate_sheet(self, num_questions=50, options_per_question=4, output_path="mcq_answer_sheet.png"):
        """Generate the complete MCQ answer sheet"""
        # Create image
        img = Image.new('RGB', (self.width, self.height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts, fall back to default if not available
        try:
            font_large = ImageFont.truetype("arial.ttf", 48)
            font_medium = ImageFont.truetype("arial.ttf", 32)
            font_small = ImageFont.truetype("arial.ttf", 24)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Create sheet components
        self.create_corner_markers(draw)
        self.create_header(draw, font_large, font_medium)
        self.create_mcq_grid(draw, font_medium, num_questions, options_per_question)
        self.create_instructions(draw, font_small)
        
        # Save the image
        img.save(output_path, dpi=(300, 300))
        print(f"MCQ answer sheet saved as: {output_path}")
        return img

def main():
    parser = argparse.ArgumentParser(description='Generate MCQ Answer Sheet')
    parser.add_argument('--questions', type=int, default=50, help='Number of questions (default: 50)')
    parser.add_argument('--options', type=int, default=4, help='Options per question (default: 4)')
    parser.add_argument('--output', type=str, default='mcq_answer_sheet.png', help='Output filename')
    
    args = parser.parse_args()
    
    generator = MCQSheetGenerator()
    generator.generate_sheet(args.questions, args.options, args.output)

if __name__ == "__main__":
    main()