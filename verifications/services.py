import hashlib
from math import atan2, cos, pi, radians, sin, sqrt
from PIL import Image

def calculate_sha256(uploaded_file):
    sha256 = hashlib.sha256()

    for chunk in uploaded_file.chunks():
        sha256.update(chunk)

    uploaded_file.seek(0)

    return sha256.hexdigest()


def calculate_phash(uploaded_file):
    uploaded_file.seek(0)

    with Image.open(uploaded_file) as image:
        pixels = list(
            image.convert('L')
            .resize((32, 32), Image.Resampling.LANCZOS)
            .getdata()
        )

    coefficients = []
    for vertical_frequency in range(8):
        for horizontal_frequency in range(8):
            coefficient = 0.0
            for row in range(32):
                for column in range(32):
                    coefficient += (
                        pixels[(row * 32) + column]
                        * cos(((2 * row + 1) * vertical_frequency * pi) / 64)
                        * cos(((2 * column + 1) * horizontal_frequency * pi) / 64)
                    )
            vertical_scale = sqrt(1 / 32) if vertical_frequency == 0 else sqrt(2 / 32)
            horizontal_scale = sqrt(1 / 32) if horizontal_frequency == 0 else sqrt(2 / 32)
            coefficient *= vertical_scale * horizontal_scale
            coefficients.append(coefficient)

    comparison_values = sorted(coefficients[1:])
    median = comparison_values[len(comparison_values) // 2]
    bits = ''.join('1' if value > median else '0' for value in coefficients)
    result = f'{int(bits, 2):016x}'

    uploaded_file.seek(0)

    return result

def calculate_distance_meters(lat1, lon1, lat2, lon2):
    earth_radius = 6_371_000

    latitude_difference = radians(float(lat2) - float(lat1))
    longitude_difference = radians(float(lon2) - float(lon1))

    first_latitude = radians(float(lat1))
    second_latitude = radians(float(lat2))

    value = (
        sin(latitude_difference / 2) ** 2
        + cos(first_latitude)
        * cos(second_latitude)
        * sin(longitude_difference / 2) ** 2
    )

    value = min(1.0, max(0.0, value))
    angle = 2 * atan2(sqrt(value), sqrt(1 - value))

    return earth_radius * angle
