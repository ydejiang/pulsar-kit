#!/usr/bin/env python
# @ Dejiang Yin -- 2025/04/09
import argparse
from PIL import Image

# Function to crop an image by percentage
def crop_image_by_percentage(image, top_percent, bottom_percent, left_percent, right_percent):
    width, height = image.size
    left = int(width * left_percent)
    right = width - int(width * right_percent)
    top = int(height * top_percent)
    bottom = height - int(height * bottom_percent)
    return image.crop((left, top, right, bottom))

def main():
    parser = argparse.ArgumentParser(description='Crop an image by given percentages from each side.')
    parser.add_argument('input_image', help='Path to the input image')
    parser.add_argument('-output', required=True, help='Path to save the cropped image')
    parser.add_argument('-top', type=float, default=0.08, help='Percentage to crop from top (default: 0.08)')
    parser.add_argument('-bottom', type=float, default=0.006, help='Percentage to crop from bottom (default: 0.006)')
    parser.add_argument('-left', type=float, default=0.03, help='Percentage to crop from left (default: 0.03)')
    parser.add_argument('-right', type=float, default=0.12, help='Percentage to crop from right (default: 0.12)')
    args = parser.parse_args()

    # Open the image
    image = Image.open(args.input_image)

    # Crop the image
    cropped = crop_image_by_percentage(image, args.top, args.bottom, args.left, args.right)

    # Save the result
    cropped.save(args.output)

if __name__ == "__main__":
    main()
