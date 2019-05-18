from PIL import Image, ImageOps, ImageSequence
from colorsys import hsv_to_rgb
from io import BytesIO

DEFAULT_CYCLE = 7


def prepare_frames(source_image):
    prepared_frames = []
    for raw_frame in ImageSequence.Iterator(source_image):
        frame = raw_frame.convert('RGBA')
        resized = frame.resize((64, 64))

        # Use alpha channel to set a white background
        _, _, _, alpha = resized.split()
        mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
        resized.paste((255, 255, 255), mask=mask)

        grayscale = ImageOps.grayscale(resized)

        prepared_frames.append(grayscale)

    base_frames = prepared_frames.copy()
    while len(prepared_frames) < DEFAULT_CYCLE:
        prepared_frames.extend(base_frames)

    return prepared_frames


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

    prepared_frames = prepare_frames(source_image)
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
                duration=120
            )
            return gif_bytes.getvalue()
