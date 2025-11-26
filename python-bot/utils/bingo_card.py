from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import random
import requests
import os

BINGO_RANGES = {
    "B": range(1, 16),
    "I": range(16, 31),
    "N": range(31, 46),
    "G": range(46, 61),
    "O": range(61, 76),
}

def generate_bingo_card():
    """Generates a 5x5 bingo card matrix."""
    card = []
    for letter in "BINGO":
        numbers = random.sample(BINGO_RANGES[letter], 5)
        card.append(numbers)
    card[2][2] = "FREE"  # Replaced by logo
    return card

def rounded_rectangle(draw, xy, radius, fill, outline=None, width=1):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)

def add_glow(draw, xy, radius, glow_color):
    """Creates a glow effect behind the rectangle."""
    x0, y0, x1, y1 = xy
    glow_img = Image.new("RGBA", (x1-x0+radius*4, y1-y0+radius*4), (0,0,0,0))
    glow_draw = ImageDraw.Draw(glow_img)
    for i in range(4,0,-1):
        glow_draw.rounded_rectangle(
            [radius*2-i, radius*2-i, x1-x0+radius*2+i, y1-y0+radius*2+i],
            radius=radius,
            fill=glow_color+(20*i,)
        )
    return glow_img, (x0-radius*2, y0-radius*2)

def fetch_logo_image(url, size):
    """Downloads image from URL and resizes it."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        logo = Image.open(BytesIO(response.content)).convert("RGBA")
        logo = logo.resize((size, size), Image.Resampling.LANCZOS)
        print("✅ Logo fetched successfully from:", url)
        return logo

    except Exception as e:
        print("❌ Failed to fetch logo:", e)
        return None


def generate_card_image(card, logo_url=None):
    cell_size = 100
    grid_size = 5
    margin = 40
    width = grid_size*cell_size + margin*2
    height = grid_size*cell_size + margin*2 + 120  # extra space for header

    img = Image.new("RGBA", (width, height), "#00257f")
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        header_font = ImageFont.truetype("arial.ttf", 100)  # bigger BINGO
        num_font = ImageFont.truetype("arial.ttf", 50)    # bigger numbers
    except:
        header_font = ImageFont.load_default()
        num_font = ImageFont.load_default()

    # Cyan header row
    for col in range(5):
        x = margin + col*cell_size
        y = margin
        rounded_rectangle(draw, [x,y,x+cell_size,y+cell_size], radius=15, fill="#00ffff", outline="white", width=2)

    # Draw BINGO letters
    letters = list("BINGO")
    for i, letter in enumerate(letters):
        bbox = draw.textbbox((0,0), letter, font=header_font)
        w,h = bbox[2]-bbox[0], bbox[3]-bbox[1]
        x = margin + i*cell_size + (cell_size-w)/2
        y = margin + (cell_size-h)/2
        draw.text((x,y), letter, fill="black", font=header_font)

    # Top y for numbers
    top_y = margin + cell_size

    for col in range(5):
        for row in range(5):
            x = margin + col*cell_size
            y = top_y + row*cell_size

            # Center logo for middle cell
            if col==2 and row==2 and logo_url:
                logo = fetch_logo_image(logo_url, cell_size)
                if logo:
                    # Glow behind logo
                    glow_img, glow_pos = add_glow(draw, [x,y,x+cell_size,y+cell_size], radius=15, glow_color=(0,255,255))
                    img.paste(glow_img, glow_pos, glow_img)

                    # Preserve aspect ratio
                    logo_ratio = logo.width / logo.height
                    max_size = cell_size
                    if logo.width > logo.height:
                        logo_w = max_size
                        logo_h = int(max_size / logo_ratio)
                    else:
                        logo_h = max_size
                        logo_w = int(max_size * logo_ratio)

                    logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
                    logo_x = x + (cell_size - logo_w)//2
                    logo_y = y + (cell_size - logo_h)//2
                    img.paste(logo, (logo_x, logo_y), logo)
                continue

            # Normal cell
            rounded_rectangle(draw, [x,y,x+cell_size,y+cell_size], radius=15, fill="#00257f", outline="white", width=2)

            txt = str(card[col][row])
            # Glow behind number
            glow_img, glow_pos = add_glow(draw, [x,y,x+cell_size,y+cell_size], radius=15, glow_color=(0,255,255))
            img.paste(glow_img, glow_pos, glow_img)

            # Text with shadow
            bbox = draw.textbbox((0,0), txt, font=num_font)
            w,h = bbox[2]-bbox[0], bbox[3]-bbox[1]
            draw.text((x+(cell_size-w)/2 +2, y+(cell_size-h)/2 +2), txt, fill="black", font=num_font)
            draw.text((x+(cell_size-w)/2, y+(cell_size-h)/2), txt, fill="white", font=num_font)

    # Output as bytes
    output = BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output
