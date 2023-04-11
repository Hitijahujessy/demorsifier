MORSE_CODE_DICT = {'A': '.-', 'B': '-...',
                   'C': '-.-.', 'D': '-..', 'E': '.',
                   'F': '..-.', 'G': '--.', 'H': '....',
                   'I': '..', 'J': '.---', 'K': '-.-',
                   'L': '.-..', 'M': '--', 'N': '-.',
                   'O': '---', 'P': '.--.', 'Q': '--.-',
                   'R': '.-.', 'S': '...', 'T': '-',
                   'U': '..-', 'V': '...-', 'W': '.--',
                   'X': '-..-', 'Y': '-.--', 'Z': '--..',
                   '1': '.----', '2': '..---', '3': '...--',
                   '4': '....-', '5': '.....', '6': '-....',
                   '7': '--...', '8': '---..', '9': '----.',
                   '0': '-----', ',': '--..--', '·': '.-.-.-',
                   '?': '..--..', '|': '-..-.', '–': '-....-',
                   '(': '-.--.', ')': '-.--.-', "'": '.----.',
                   '"': '.-..-.', '!': '-·-·--'}

REVERSE_MORSE_CODE_DICT = {v: k for k, v in MORSE_CODE_DICT.items()}


def split_string(string):
    new_string = string.split()
    return new_string


def code_to_char(morse_code: str):
    if morse_code == "/":
        char = " "
    else:
        try:
            char = REVERSE_MORSE_CODE_DICT[morse_code]
        except KeyError:
            char = "[not a real character]"
    return char


def code_list_to_string(code_list: list):
    text_list = ""
    for code in code_list:
        text_list += code_to_char(code)
    return text_list


def translate(morse_string: str):
    morse_list = split_string(morse_string)
    text_list = code_list_to_string(morse_list)
    print(text_list)
    return text_list


string = "... --- ..."
string = " ..-. --- .-. . .. --. -. / - . -..- - / - .-. .- -. ... .-.. .- - .. --- -."
translate(string)
