#!/usr/bin/env python3

import cv2
import numpy as np
import sys

# Constants
BIT_DEPTH = 8

class StegoMotion:
    """
    A class for performing steganography on video files.
    """

    def __init__(self, video_path):
        """
        Constructor for the StegoMotion class.

        Args:
            video_path (str): The path to the video file.
        """
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.num_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

    def embed_character(self, frame, char):
        """
        Embeds a character into a video frame.

        Args:
            frame (numpy.ndarray): The input video frame.
            char (int): The character to embed.

        Returns:
            numpy.ndarray: The modified video frame.
        """
        char_bin = format(char, f'0{BIT_DEPTH}b')
        for i in range(frame.shape[0]):
            for j in range(frame.shape[1]):
                for k in range(frame.shape[2]):
                    if len(char_bin) > 0:
                        frame[i][j][k] = (frame[i][j][k] & 0xFE) | int(char_bin[0])
                        char_bin = char_bin[1:]
                    else:
                        return frame
        return frame

    def embed_message(self, output_path, message):
        """
        Embeds a message into a video and saves the output video.

        Args:
            output_path (str): The path to save the output video.
            message (str): The message to embed.
        """
        # For AVI and MOV video files:
        out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc('F', 'F', 'V', '1'), self.fps, (self.frame_width, self.frame_height))

        idx = 0
        message = message.encode('utf-8')

        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                assert frame.dtype == np.uint8
                if idx == 0:  # First embed the length of the message.
                    frame = self.embed_character(frame, len(message))
                elif idx <= len(message):  # Then embed the message.
                    frame = self.embed_character(frame, message[idx - 1])
                out.write(frame)
                idx += 1
            else:
                break

        # Release resources:
        self.cap.release()
        out.release()

    def extract_bits(self, frame):
        """
        Extracts the least significant bit of each pixel in a frame.

        Args:
            frame (numpy.ndarray): The input video frame.

        Yields:
            int: The extracted bit.
        """
        for i in range(frame.shape[0]):
            for j in range(frame.shape[1]):
                for k in range(frame.shape[2]):
                    yield frame[i][j][k] & 1

    def extract_length(self):
        """
        Extracts the length of the hidden message from the video.

        Returns:
            int: The length of the hidden message.
        """
        ret, frame = self.cap.read()
        bits = self.extract_bits(frame)
        length = 0
        for _ in range(BIT_DEPTH):
            length = (length << 1) | next(bits)
        return length

    def extract_character(self, frame):
        """
        Extracts a character from a video frame.

        Args:
            frame (numpy.ndarray): The input video frame.

        Returns:
            int: The extracted character.
        """
        bits = self.extract_bits(frame)
        char = 0
        for _ in range(BIT_DEPTH):
            char = (char << 1) | next(bits)
        return char

    def extract_message(self):
        """
        Extracts the hidden message from the video.

        Returns:
            str: The extracted message.
        """
        length = self.extract_length()

        # Do NOT skip the first frame after length.
        # The frame was already read in extract_length().

        message = []
        for _ in range(length):
            ret, frame = self.cap.read()
            if ret:
                assert frame.dtype == np.uint8
                char = self.extract_character(frame)
                message.append(char)
            else:  # No more frames to read.
                break

        # Release resource:
        self.cap.release()

        message = bytes(message)
        return message.decode('utf-8')  # Convert bytes to string.

    def get_max_chars(self):
        """
        Returns the maximum number of characters that can be embedded in the video.

        Returns:
            int: The maximum number of characters.
        """
        return self.num_frames - 1  # -1 to account for the length frame.

def main():
    if len(sys.argv) < 2:
        print("Usage: python stego_script.py <video_file>")
        return

    video_file = sys.argv[1]

    # Check if the file extension is valid:
    valid_extensions = ['.avi', '.mov']
    if not any(video_file.lower().endswith(ext) for ext in valid_extensions):
        print("Error: Only .avi and .mov files are supported.")
        return

    # ANSI escape codes for text colors:
    cyan = '\033[96m'
    magenta = '\033[95m'
    white = '\033[97m'
    red = '\033[91m'

    print(cyan + "Select the mode of operation:")
    print(magenta + "D." + white + " Detect Message")
    print(magenta + "H." + white + " Hide Message")

    mode = input(cyan + "Enter the mode (D/H): " + white)
    stego = StegoMotion(video_file)

    if mode == 'H':
        max_chars = stego.get_max_chars()
        print(f"You can enter a message up to {max_chars} characters.")
        message = input("Enter the message to hide: ")
        if len(message) > max_chars:
            print("Message is too long for the video!")
            return
        output_file = input("Enter the output video path (e.g., output.avi): ")
        stego.embed_message(output_file, message)
        print(f'Message successfully hidden in {output_file}.')

    elif mode == 'D':
        message = stego.extract_message()
        if message:
            print(white + f'Detected message: {red}{message}{white}')
        else:
            print("No message detected.")

    else:
        print('Invalid mode!')
        return

if __name__ == "__main__":
    main()
