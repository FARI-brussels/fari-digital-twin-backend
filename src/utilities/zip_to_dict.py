from io import BytesIO
from typing import Generator, Tuple, Union
from zipfile import ZipFile


def extract_zip_content(zip_file: bytes) -> Generator[Tuple[str, Union[str, bytes]], None, None]:
    """
    Extracts the content of a zip file.
    :param zip_file: The content of the zip file.
    :return: A generator yielding tuples containing the name and content of each file in the zip file.
    """
    with ZipFile(BytesIO(zip_file)) as zip_ref:
        for name in zip_ref.namelist():
            content = zip_ref.read(name)
            try:
                # Try to decode as UTF-8
                text_content = content.decode("utf-8")
                yield name, text_content
            except UnicodeDecodeError:
                # If decoding fails, return the binary content (usefull for tilesets)
                yield name, content


def zip_to_dict(zip_file: bytes) -> dict:
    """
    Converts a zip file to a dictionary.
    zip_file: The content of the zip file.
    return: A dictionary containing the content of the zip file.
    """
    output = {}

    for name, content in extract_zip_content(zip_file):
        output[name] = content

    return output
