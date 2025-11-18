import random

color_list = [
    0xA4C400,
    0x60A917,
    0x008A00,
    0x00ABA9,
    0x1BA1E2,
    0x0050EF,
    0x6A00FF,
    0xAA00FF,
    0xF472D0,
    0xD80073,
    0xA20025,
    0xE51400,
    0xFA6800,
    0xF0A30A,
    0xE3C800
    ]

def pick_random_color(output_choice: str) -> str:

    if output_choice == "hex":
        return(random.choice(color_list))
    
    elif output_choice == "decimal":
        return(int(random.choice(color_list)))
