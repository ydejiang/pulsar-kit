#!/usr/bin/env python
# @ Dejiang Yin -- 2025/04/09
import argparse
from PIL import Image

# Function to crop an image by percentage
def crop_image_by_percentage(image, top_percent, bottom_percent, left_percent, right_percent):
    """
    Crop an image according to the specified percentage for the top, bottom, left, and right sides.
    Args:
        image (Image): The input PIL Image object.
        top_percent (float): The percentage of cropping for the top side (ranging from 0 to 1).
        bottom_percent (float): The percentage of cropping for the bottom side (ranging from 0 to 1).
        left_percent (float): The percentage of cropping for the left side (ranging from 0 to 1).
        right_percent (float): The percentage of cropping for the right side (ranging from 0 to 1).
    Returns:
        Image: The cropped PIL Image object.
    """
    width, height = image.size
    left = int(width * left_percent)
    right = width - int(width * right_percent)
    top = int(height * top_percent)
    bottom = height - int(height * bottom_percent)
    cropped_image = image.crop((left, top, right, bottom))
    return cropped_image

# Function to vertically merge two images
def vertical_merge_images(image1, image2):
    """
    Calculate the total height and width of the merged image,
    create a new blank image, and then paste the two input images onto it.
    Args:
        image1 (Image): The first PIL Image object.
        image2 (Image): The second PIL Image object.
    Returns:
        Image: The vertically merged PIL Image object.
    """
    # Get the heights of the two images
    height1, height2 = image1.height, image2.height
    # Calculate the total height and width of the merged image
    total_height = height1 + height2
    width = image1.width
    # Create a new blank image for merging
    new_image = Image.new('RGB', (width, total_height))
    # Paste the images onto the new image
    new_image.paste(image1, (0, 0))
    new_image.paste(image2, (0, height1))
    return new_image

def main():
    parser = argparse.ArgumentParser(description='Vertically merge two images and crop the first image if needed')
    parser.add_argument('input_images', nargs=2, help='Paths of the two input images, in the order of [image1, image2]')
    parser.add_argument('-output', required=True, help='Path of the output merged image')
    parser.add_argument('-top', type=float, default=0.08, help='Percentage of cropping for the top side of the first image (default value: 0.08)')
    parser.add_argument('-bottom', type=float, default=0.006, help='Percentage of cropping for the bottom side of the first image (default value: 0.006)')
    parser.add_argument('-left', type=float, default=0.03, help='Percentage of cropping for the left side of the first image (default value: 0.03)')
    parser.add_argument('-right', type=float, default=0.12, help='Percentage of cropping for the right side of the first image (default value: 0.12)')
    args = parser.parse_args()
    image_path1, image_path2 = args.input_images
    output_path = args.output
    top_percent_1 = args.top
    bottom_percent_1 = args.bottom
    left_percent_1 = args.left
    right_percent_1 = args.right
    # Open the images
    image1 = Image.open(image_path1)
    image2 = Image.open(image_path2)
    # Crop the first image according to the percentage
    image1 = crop_image_by_percentage(image1, top_percent_1, bottom_percent_1, left_percent_1, right_percent_1)
    # Get the width of the cropped first image
    target_width = image1.width
    # Resize the second image to have the same width as the first image and scale the height proportionally
    width_ratio = target_width / image2.width
    new_height = int(image2.height * width_ratio)
    image2 = image2.resize((target_width, new_height), Image.BILINEAR)
    # Vertically merge the two images
    merged_image = vertical_merge_images(image1, image2)
    # Save the merged image
    merged_image.save(output_path)
    # print(f"Image has been saved to {output_path}")
if __name__ == "__main__":
    main()
