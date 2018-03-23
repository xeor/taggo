import piexif


def run(filepath):

    try:
        exifdata = piexif.load(filepath)
    except piexif.InvalidImageDataError:
        return {}

    # How to present?
    # exifdata['GPS'][piexif.GPSIFD.GPSLatitudeRef],  # N
    # exifdata['GPS'][piexif.GPSIFD.GPSLatitude],     # ((59, 1), (50, 1), (1111, 100))
    # exifdata['GPS'][piexif.GPSIFD.GPSLongitudeRef], # E
    # exifdata['GPS'][piexif.GPSIFD.GPSLongitude],    # (10, 1), (50, 1), (3000, 100))
    gpslatlon = None

    return {
        'ImageLength': exifdata['0th'].get(piexif.ImageIFD.ImageLength, b''),
        'ImageWidth': exifdata['0th'].get(piexif.ImageIFD.ImageWidth, b''),
        'Make': exifdata['0th'].get(piexif.ImageIFD.Make, b'').decode('utf-8'),
        'Model': exifdata['0th'].get(piexif.ImageIFD.Model, b'').decode('utf-8'),
        'Orientation': exifdata['0th'].get(piexif.ImageIFD.Orientation, b''),

        'Flash': exifdata['Exif'].get(piexif.ExifIFD.Flash, b''),

        'GPSAltitudeRef': exifdata['GPS'].get(piexif.GPSIFD.GPSAltitudeRef, b''),
        'GPSLatLon': gpslatlon,
    }
