#!/usr/bin/env python3
"""
MCQ Answer Sheet Auto Filler
Automatically fills in a blank MCQ answer sheet with random answers for testing purposes.
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw
import argparse
import random
import json

class MCQAutoFiller:
    def __init__(self):
        self.circle_radius = 38
        self.question_spacing = 90
        self.option_spacing = 120
        self.margin = 200
        
    def create_answer_template(self, num_questions=50, options_per_question=4):
        """Create a template with circle positions matching the generator"""
        template = {}
        start_y = 450
        questions_per_column = 25
        column_width = (2480 - 2 * self.margin) // 2
        
        option_letters = ['A', 'B', 'C', 'D', 'E'][:options_per_question]
        
        for q in range(num_questions):
            # Determine column and position
            column = q // questions_per_column
            row_in_column = q % questions_per_column
            
            x_base = self.margin + column * column_width
            y_pos = start_y + row_in_column * self.question_spacing
            
            question_num = q + 1
            template[question_num] = {}
            
            # Calculate circle positions for each option
            for i, letter in enumerate(option_letters):
                option_x = x_base + 60 + i * self.option_spacing
                
                circle_center_x = option_x + self.circle_radius
                circle_center_y = y_pos + self.circle_radius
                
                template[question_num][letter] = {
                    'center': (circle_center_x, circle_center_y),
                    'radius': self.circle_radius
                }
        
        return template
    
    def generate_random_answers(self, num_questions=50, options_per_question=4, 
                              skip_probability=0.1, answer_key=None):
        """Generate random answers for the MCQ sheet"""
        option_letters = ['A', 'B', 'C', 'D', 'E'][:options_per_question]
        answers = {}
        
        for q in range(1, num_questions + 1):
            # Sometimes skip questions (simulate incomplete answers)
            if random.random() < skip_probability:
                answers[q] = None
            elif answer_key and str(q) in answer_key:
                # Use provided answer key if available
                answers[q] = answer_key[str(q)]
            else:
                # Random answer
                answers[q] = random.choice(option_letters)
        
        return answers
    
    def fill_answers_on_sheet(self, blank_sheet_path, answers, output_path, 
                             fill_intensity=0.3, add_noise=True):
        """Fill in the answers on a blank MCQ sheet"""
        # Load the blank sheet
        image = cv2.imread(blank_sheet_path)
        if image is None:
            print(f"Error: Could not load image from {blank_sheet_path}")
            return None
        
        # Convert to PIL for easier drawing
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)
        
        # Create template
        template = self.create_answer_template()
        
        # Fill in answers
        for question_num, selected_answer in answers.items():
            if selected_answer and question_num in template:
                if selected_answer in template[question_num]:
                    center_x, center_y = template[question_num][selected_answer]['center']
                    radius = template[question_num][selected_answer]['radius']
                    
                    # Calculate fill color based on intensity
                    fill_value = int(255 * (1 - fill_intensity))
                    fill_color = (fill_value, fill_value, fill_value)
                    
                    # Add some randomness to simulate pencil marks
                    if add_noise:
                        noise = random.randint(-20, 20)
                        fill_value = max(0, min(255, fill_value + noise))
                        fill_color = (fill_value, fill_value, fill_value)
                    
                    # Fill the circle
                    draw.ellipse([
                        center_x - radius + 5,  # Slightly smaller than the outline
                        center_y - radius + 5,
                        center_x + radius - 5,
                        center_y + radius - 5
                    ], fill=fill_color)
                    
                    # Add some imperfection to simulate hand-filled circles
                    if add_noise:
                        # Add some random dots for texture
                        for _ in range(random.randint(5, 15)):
                            dot_x = center_x + random.randint(-radius//2, radius//2)
                            dot_y = center_y + random.randint(-radius//2, radius//2)
                            dot_size = random.randint(1, 3)
                            darker_fill = max(0, fill_value - random.randint(10, 30))
                            dot_color = (darker_fill, darker_fill, darker_fill)
                            draw.ellipse([
                                dot_x - dot_size, dot_y - dot_size,
                                dot_x + dot_size, dot_y + dot_size
                            ], fill=dot_color)
        
        # Convert back to OpenCV format and save
        filled_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        cv2.imwrite(output_path, filled_image)
        
        print(f"Filled answer sheet saved to: {output_path}")
        return filled_image
    
    def create_test_scenarios(self, blank_sheet_path, num_scenarios=5):
        """Create multiple test scenarios with different answer patterns"""
        scenarios = [
            {
                'name': 'random_complete',
                'description': 'Completely random answers',
                'skip_prob': 0.0,
                'intensity': 0.4
            },
            {
                'name': 'random_with_skips',
                'description': 'Random answers with some skipped questions',
                'skip_prob': 0.15,
                'intensity': 0.3
            },
            {
                'name': 'light_filling',
                'description': 'Lightly filled answers (harder to detect)',
                'skip_prob': 0.05,
                'intensity': 0.2
            },
            {
                'name': 'heavy_filling',
                'description': 'Heavily filled answers',
                'skip_prob': 0.0,
                'intensity': 0.6
            },
            {
                'name': 'pattern_answers',
                'description': 'Following A-B-C-D pattern',
                'skip_prob': 0.0,
                'intensity': 0.4,
                'pattern': True
            }
        ]
        
        results = {}
        
        for scenario in scenarios:
            print(f"\nCreating scenario: {scenario['name']}")
            print(f"Description: {scenario['description']}")
            
            if scenario.get('pattern'):
                # Create patterned answers (A-B-C-D repeating)
                answers = {}
                options = ['A', 'B', 'C', 'D']
                for q in range(1, 51):
                    answers[q] = options[(q-1) % 4]
            else:
                # Generate random answers
                answers = self.generate_random_answers(
                    skip_probability=scenario['skip_prob']
                )
            
            # Fill the sheet
            output_path = f"filled_sheet_{scenario['name']}.png"
            self.fill_answers_on_sheet(
                blank_sheet_path, 
                answers, 
                output_path,
                fill_intensity=scenario['intensity'],
                add_noise=True
            )
            
            # Save answer key
            answer_key_path = f"answer_key_{scenario['name']}.json"
            with open(answer_key_path, 'w') as f:
                json.dump(answers, f, indent=2)
            
            results[scenario['name']] = {
                'filled_sheet': output_path,
                'answer_key': answer_key_path,
                'answers': answers,
                'description': scenario['description']
            }
            
            # Print summary
            filled_count = sum(1 for ans in answers.values() if ans is not None)
            print(f"  - Questions answered: {filled_count}/50")
            print(f"  - Answer distribution: {self.analyze_answers(answers)}")
        
        return results
    
    def analyze_answers(self, answers):
        """Analyze answer distribution"""
        distribution = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'None': 0}
        
        for answer in answers.values():
            if answer is None:
                distribution['None'] += 1
            else:
                distribution[answer] += 1
        
        return {k: v for k, v in distribution.items() if v > 0}
    
    def fill_from_answer_key(self, blank_sheet_path, answer_key_path, output_path):
        """Fill sheet using a provided answer key JSON file"""
        try:
            with open(answer_key_path, 'r') as f:
                answer_key = json.load(f)
            
            # Convert string keys to integers for consistency
            answers = {}
            for q_str, answer in answer_key.items():
                answers[int(q_str)] = answer
            
            self.fill_answers_on_sheet(blank_sheet_path, answers, output_path)
            print(f"Sheet filled using answer key: {answer_key_path}")
            
        except Exception as e:
            print(f"Error loading answer key: {e}")

def main():
    parser = argparse.ArgumentParser(description='Auto-fill MCQ Answer Sheet')
    parser.add_argument('blank_sheet', help='Path to blank MCQ answer sheet')
    parser.add_argument('--output', default='filled_answer_sheet.png', 
                       help='Output filled sheet path')
    parser.add_argument('--answer-key', help='JSON file with specific answers to fill')
    parser.add_argument('--save-answers', help='Save generated answers to JSON file')
    parser.add_argument('--intensity', type=float, default=0.8, 
                       help='Fill intensity (0.0-1.0, default: 0.4)')
    parser.add_argument('--skip-prob', type=float, default=0.1, 
                       help='Probability of skipping questions (default: 0.1)')
    parser.add_argument('--no-noise', action='store_true', 
                       help='Disable noise/texture in filled circles')
    parser.add_argument('--test-scenarios', action='store_true',
                       help='Create multiple test scenarios')
    
    args = parser.parse_args()
    
    filler = MCQAutoFiller()
    
    if args.test_scenarios:
        # Create multiple test scenarios
        print("Creating test scenarios...")
        results = filler.create_test_scenarios(args.blank_sheet)
        
        print(f"\nCreated {len(results)} test scenarios:")
        for name, info in results.items():
            print(f"  - {name}: {info['description']}")
            print(f"    Files: {info['filled_sheet']}, {info['answer_key']}")
    
    elif args.answer_key:
        # Fill using provided answer key
        filler.fill_from_answer_key(args.blank_sheet, args.answer_key, args.output)
    
    else:
        # Generate random answers and fill
        print("Generating random answers...")
        answers = filler.generate_random_answers(skip_probability=args.skip_prob)
        
        print("Filling answer sheet...")
        filler.fill_answers_on_sheet(
            args.blank_sheet, 
            answers, 
            args.output,
            fill_intensity=args.intensity,
            add_noise=not args.no_noise
        )
        
        # Save answer key if requested
        if args.save_answers:
            with open(args.save_answers, 'w') as f:
                json.dump(answers, f, indent=2)
            print(f"Answer key saved to: {args.save_answers}")
        
        # Print summary
        filled_count = sum(1 for ans in answers.values() if ans is not None)
        print(f"\nSummary:")
        print(f"  - Questions answered: {filled_count}/50")
        print(f"  - Answer distribution: {filler.analyze_answers(answers)}")

if __name__ == "__main__":
    main()