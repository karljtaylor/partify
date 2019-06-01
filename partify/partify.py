from PIL import Image, ImageOps, ImageSequence
from colorsys import hsv_to_rgb
from io import BytesIO
from analytics-python import analytics 

DEFAULT_CYCLE = 7


def prepare_frames(source_image):
    width, height = source_image.size
    max_size = max(width, height)

    prepared_frames = []
    frame_times = []
    for raw_frame in ImageSequence.Iterator(source_image):
        # Make sure the image is a square
        if width == height:
            frame = raw_frame.convert('RGBA')
        else:
            frame = Image.new('RGBA', (max_size, max_size), (255, 255, 255, 0))
            frame.paste(raw_frame, (int((max_size - width) / 2), int((max_size - height) / 2)))

        if max_size > 128:
            frame = frame.resize((128, 128), Image.ANTIALIAS)

        # Use alpha channel to set a white background
        _, _, _, alpha = frame.split()
        mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
        frame.paste((255, 255, 255), mask=mask)

        grayscale = ImageOps.grayscale(frame)

        prepared_frames.append(grayscale)
        frame_times.append(raw_frame.info.get('duration', 120))

    base_frames = prepared_frames.copy()
    base_times = frame_times.copy()
    while len(prepared_frames) < DEFAULT_CYCLE:
        prepared_frames.extend(base_frames)
        frame_times.extend(base_times)

    return prepared_frames, frame_times


def generate_spectrum(frame_count):
    num_loops = 1
    num_frames_per_loop = DEFAULT_CYCLE
    remainder = 0

    # If there are more frames than the default cycle length, divide frames into multiple cycles
    if frame_count > DEFAULT_CYCLE:
        num_loops = frame_count // DEFAULT_CYCLE
        remainder = frame_count % DEFAULT_CYCLE
    while remainder >= num_loops:
        # Distribute extra frames into loops
        num_frames_per_loop += 1
        remainder -= 1

    remainder_count = remainder
    for _ in range(num_loops):
        num_frames_this_loop = num_frames_per_loop
        if remainder_count > 0:
            # Add one remainder frame into each loop until there are none left
            num_frames_this_loop += 1
            remainder_count -= 1
        for frame in range(num_frames_this_loop):
            rgb = hsv_to_rgb(frame / num_frames_this_loop, 1.0, 1.0)
            yield (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))


def colorize_frame(frame, spectrum):
    result = ImageOps.colorize(frame, next(spectrum), (255, 255, 255))

    return result


def partify(image_bytes):
    source_image = Image.open(BytesIO(image_bytes))

    prepared_frames, frame_times = prepare_frames(source_image)
    spectrum = generate_spectrum(len(prepared_frames))

    output = []
    for frame in prepared_frames:
        output.append(colorize_frame(frame, spectrum))

    if output:
        with BytesIO() as gif_bytes:
            output[0].save(
                gif_bytes,
                format='GIF',
                save_all=True,
                append_images=output[1:],
                loop=0,
                dispose=2,
                duration=frame_times,
                quality=90
            )
            return gif_bytes.getvalue()
