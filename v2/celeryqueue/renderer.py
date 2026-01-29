
from math import ceil,floor, atan2, degrees
from pathlib import Path
from io import BytesIO
import json
import random

from fpdf import Template, FPDF
from pypdf import PdfWriter, PdfReader


IMAGE_PATH = Path("renderResources/logopng.png")
TEMPLATE_PATH = Path("renderResources/segnaposto_template.json")
PLANIMETRIA_PATH = Path("renderResources/Planimetria_FDI2026.pdf")
TAVOLI_JSON_PATH = Path("renderResources/tavoli_rotated_2.json")


class Table_spot():
    def __init__(self,x,y,h,w):
        self.x =x
        self.y = y
        self.h = h
        self.w = w

def table_segmentation(table:dict)->list:
    posti  = table["capacity"]
    h = table['gui']['height']
    w = table['gui']['width']
    x = table['gui']['x']
    y = table['gui']['y']
    segmenti = []

    if table["head_seats"] > 0:  #at most one head, at the bottom
        
        segmenti.append(Table_spot(x,y,w,8))
        segmenti.append(Table_spot(x+8,y,w/2,24))
        segmenti.append(Table_spot(x+8,y+w/2,w/2,24))

        posti -=3
        h = h-32
        x=x+32

    if posti >0:
        square_h = h / ceil(posti/2)
        square_w = w /2
        
        for i in range(posti):
            segmenti.append(Table_spot(x+square_h*floor(i/2),
                                       y+square_w*(i%2),
                                       square_w,
                                       square_h))
        
    return segmenti


class EventInfo:
    def __init__(self, eventln1: str, eventln2: str, eventln3: str, date: str) -> None:
        self.eventln1 = eventln1
        self.eventln2 = eventln2
        self.eventln3 = eventln3
        self.date = date


def generaSegnaposti(
    prenotazioni: list[tuple[str, int]],
    info_evento: EventInfo,
) -> bytes:
    if not IMAGE_PATH.exists():
        raise FileNotFoundError(f"Image not found: {IMAGE_PATH}")
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template not found: {TEMPLATE_PATH}")

    template = Template(format="A4", orientation="portrait", title="Segnaposti")
    template.parse_json(TEMPLATE_PATH)

    for nome, posti in prenotazioni:
        template.add_page()
        template["logo"] = str(IMAGE_PATH)
        template["guest_name"] = str(nome)
        template["places"] = str(posti)
        template["event_line1"] = info_evento.eventln1
        template["event_line2"] = info_evento.eventln2
        template["event_line3"] = info_evento.eventln3
        template["event_date"] = info_evento.date

    template.render()
    return bytes(template.pdf.output())


def generaMappa(
    result:dict,
    title: str = "FESTA DELLO SPORT"
) -> bytes:
    if not PLANIMETRIA_PATH.exists():
        raise FileNotFoundError(f"Planimetria not found: {PLANIMETRIA_PATH}")
    if not TAVOLI_JSON_PATH.exists():
        raise FileNotFoundError(f"Tavoli JSON not found: {TAVOLI_JSON_PATH}")
    
    # Read table definitions
    with open(TAVOLI_JSON_PATH, 'r', encoding='utf-8') as f:
        tavoli_def = json.load(f)

    # Read the planimetry first to get dimensions
    reader = PdfReader(PLANIMETRIA_PATH)
    first_page = reader.pages[0]
    mb = first_page.mediabox
    width= float(mb.width)
    height = float(mb.height)

    # Create the overlay with the rectangle with matching dimensions
    pdf = FPDF(unit="pt", format=(width, height))
    pdf.add_font("verdana", style="", fname="renderResources/Verdana.ttf", uni=True)
    pdf.add_page()
    
## START DRAW LOGIC
    
    
    # change header title
    # pdf.set_fill_color(255, 255, 255)
    # pdf.rect(x=width-75, y=270, w=40, h=607, style='F') 
    # with pdf.rotation(270, width-35, 500):
    #     pdf.set_x(x=width-75)
    #     pdf.set_y(y=500)

    # pdf.set_font("verdana", size=50)
    # pdf.set_text_color(0, 0, 255)
    # text = title
    # w_text = pdf.get_string_width(text)
    # with pdf.rotation(270, width-72, 350):
    #     pdf.text(x=width+150- w_text/2, y=351 , text=text) 
    
    #end header

    labls = [] # Elenco di etichette per i tavoli (testo + coordinate + sfondo) vanno stampate alla fine per non essere coperte dai tavoli
    
    color = getNewColor()
    split_colors = {} # pregeneriamo i colori per i gruppi splittati
    split_tot_size = {}
    for gruppo in result["groups"]:
        if "_part" in gruppo["name"]:
            idgp = gruppo["name"].split("_part")[0]
            if idgp not in split_colors:
                color = getNewColor(color)
                split_colors[idgp] = color
            if idgp not in split_tot_size:
                split_tot_size[idgp] = 0
            split_tot_size[idgp] += gruppo["size"]
            
    

    

    for table in tavoli_def:

        #reference in pdf coordinates 
        #   ^ x
        #   |
        #   |
        #   |--------> y  , x,y from json are bottom-left corners
        x = table['gui']['x']
        y = table['gui']['y']
        width_t = table['gui']['width']
        height_t = table['gui']['height']
        posti = table["capacity"]

        """
        # sanity check
        pdf.set_fill_color(255, 0, 0)  # Red
        pdf.circle(x=x, y=y, radius=1, style='F')
        
        pdf.set_fill_color(0, 255, 0)  # Green
        pdf.circle(x=x+height_t, y=y+width_t, radius=1, style='F')
        """
        
        pdf.set_fill_color(200, 200, 200)
        
        SEAT_W = 12
        SEAT_H = 3
        EDGE_GAP = 1.2
        SEAT_STRIDE = 15.28  #distanza tra i centri dei 
        
        if table["head_seats"] == 0:  
            for vp in range(ceil(posti/2)):
                # Left side
                pdf.rect(x=x+EDGE_GAP+SEAT_STRIDE*vp, y=y-SEAT_H, w=SEAT_W, h=SEAT_H, style='FD')
                # Right side
                if(table["capacity"] % 2 == 0 or vp >  0):
                    pdf.rect(x=x+EDGE_GAP+SEAT_STRIDE*vp, y=y+width_t, w=SEAT_W, h=SEAT_H, style='FD')
        else:
            pdf.rect(x=x-SEAT_H, y=y+((width_t-SEAT_W)/2), w=SEAT_H, h=SEAT_W, style='FD') #horizontal seat
            pdf.rect(x=x+SEAT_W-SEAT_H, y=y-SEAT_H, w=SEAT_W, h=SEAT_H, style='FD')
            pdf.rect(x=x+SEAT_W-SEAT_H, y=y+width_t, w=SEAT_W, h=SEAT_H, style='FD')
            
            for vp in range(ceil((posti-3)/2)):
                # Left side
                pdf.rect(x=x+32+SEAT_STRIDE*vp, y=y-SEAT_H, w=SEAT_W, h=SEAT_H, style='FD')
                # Right side
                if((posti-3) % 2 == 0 or vp >  0):
                    pdf.rect(x=x+32+SEAT_STRIDE*vp, y=y+width_t, w=SEAT_W, h=SEAT_H, style='FD')
        
        gruppi = result["groups"]
        associazioni = result["pairings"]
        gruppiTavolo = [gruppo for gruppo in gruppi if gruppo["name"] in associazioni[str(table["table_id"])]]
        gruppi_testa = [gruppo for gruppo in gruppiTavolo if gruppo.get('required_head',0)]
        gruppi_normali = [gruppo for gruppo in gruppiTavolo if not gruppo.get('required_head',0)]
        #gruppi_normali.sort(key=lambda g: g['size']%2==1)
       
        if sum([gr["required_head"] for gr in gruppi_testa]) > table["head_seats"] or len(gruppi_testa) > 1:  #per ora max 1 testa
            print("Tavolo", table["table_id"], " - In testa:", gruppi_testa)
            raise ValueError("Troppi posti in testa richiesti")
        
        #if table["head_seats"] >0 :
        #    continue 
        pdf.set_font("Arial", size=12)
        pdf.set_text_color(0, 0, 0)
        pdf.set_fill_color(255, 255, 255)
        labLen = pdf.get_string_width(str(table['table_id']))
        with pdf.rotation(270, x + height_t + 5, y + width_t - labLen ):
         #pdf.rect(x=x + height_t + 5, y=y + width_t - labLen +2, w=labLen, h=-14, style='F')
         pdf.circle(x=x + height_t + 5 + labLen/2, y=y + width_t - labLen -5, radius=labLen/2 +4, style='F')
         pdf.text(x=x + height_t + 5, y=y + width_t - labLen, text=str(table['table_id']))

        seg = table_segmentation(table)

        
        
        pdf.set_font("Arial", size=12)
        pdf.set_text_color(0, 0, 0)
        
        for gruppo_testa in gruppi_testa:
            if("_part" in gruppo_testa["name"]):
                color = split_colors[gruppo_testa["name"].split("_part")[0]]
            else:
                color = getNewColor(color)
            pdf.set_fill_color(*color)
            for i in range(gruppo_testa["size"]):
                spot = seg.pop(0)
                pdf.rect(x=spot.x,y=spot.y,w=spot.w,h=spot.h,style="F")
            if("_part" not in gruppo_testa["name"]):
                labls.append( (f"{gruppo_testa['show_name']}({gruppo_testa['size']})", x + 10 , y + width_t/2, color, 262) )
            else:
                idgp = gruppo_testa["name"].split("_part")[0]
                tot_size = split_tot_size.get(idgp, gruppo_testa["size"])
                labls.append( (f"{gruppo_testa['show_name']}({gruppo_testa['size']}/{tot_size})", x + 10 , y + width_t/2, color, 262) )
                

        while len(gruppi_normali) >0 and len(seg) >0:
            candidates = [g for g in gruppi_normali if g['size'] <= len(seg)]
            if not candidates:
                break
            gruppo = next((g for g in candidates if (g['size'] % 2) == (len(seg) % 2)), candidates[0])
            gruppi_normali.remove(gruppo)
            if("_part" in gruppo["name"]):
                color = split_colors[gruppo["name"].split("_part")[0]]
            else:
                color = getNewColor(color)
            pdf.set_fill_color(*color)
            lowest, highest = 999999, 0
            for i in range(gruppo["size"]):
                spot = seg.pop(0)
                pdf.rect(x=spot.x,y=spot.y,w=spot.w,h=spot.h,style="F")
                if spot.x < lowest:
                    lowest = spot.x
                if spot.x+spot.h > highest:
                    highest = spot.x + spot.h
            if "_part" not in gruppo["name"]:
                labls.append( (f"{gruppo['show_name']}({gruppo['size']})", (lowest + highest)/2 , y + width_t/2, color, degrees(atan2(-width_t, lowest-highest))) )
            else:
                idgp = gruppo["name"].split("_part")[0]
                tot_size = split_tot_size.get(idgp, gruppo["size"])
                labls.append( (f"{gruppo['show_name']}({gruppo['size']}/{tot_size})", (lowest + highest)/2 , y + width_t/2, color, degrees(atan2(-width_t, lowest-highest))) )
                

        
        # with pdf.rotation(270, x + height_t/2, y + width_t/2):
        #     pdf.text(x=x + height_t/2 - 10, y=y + width_t/2, text=str(table['table_id']))

        pdf.rect(x=x, y=y, w=height_t, h=width_t, style='D') #table border

    
    pdf.set_font("Arial", size=8)
    pdf.set_text_color(0, 0, 0) 
    for lbl, lx, ly, color, angle in labls:
        pdf.set_fill_color(*color)
        text_w = pdf.get_string_width(lbl) + 6
        text_h = 8+2
        with pdf.rotation(angle, lx, ly):
            with pdf.local_context(fill_opacity=0.7):
                pdf.rect(x=lx - text_w/2, y=ly - text_h/2, w=text_w, h=text_h, style='F')
            pdf.set_text_color(0, 0, 0)
            pdf.text(x=lx - text_w/2 + 3, y=ly + 3, text=lbl)
        
    
    ## END DRAW LOGIC
    overlay_bytes = pdf.output()
    overlay_reader = PdfReader(BytesIO(overlay_bytes))
    overlay_page = overlay_reader.pages[0]

    writer = PdfWriter()

    for page in reader.pages:
        page.merge_page(overlay_page)
        writer.add_page(page)

    # START ELENCO DRAWING
    elenco_pdf = FPDF(unit="pt", format="A4", orientation="portrait")
    elenco_pdf.add_font("verdana", style="", fname="renderResources/Verdana.ttf", uni=True)
    elenco_pdf.add_page()
    elenco_pdf.set_font("verdana", size=24)
    elenco_pdf.set_text_color(0, 0, 0)
    title_text = "ELENCO ALFABETICO"
    page_width = elenco_pdf.w
    text_w = elenco_pdf.get_string_width(title_text)
    elenco_pdf.text(x=(page_width - text_w) / 2, y=50, text=title_text)

    # Draw table: 2 page columns, each with 2 columns (large + small), 50 rows
    left_margin = 40
    top_margin = 80
    gutter = 20
    usable_width = page_width - (left_margin * 2)
    block_width = (usable_width - gutter) / 2
    small_col_w = block_width * 0.1
    large_col_w = block_width - small_col_w
    row_h = 14
    rows = 50

    elenco_pdf.set_draw_color(0, 0, 0)

    # Build alphabetical list: reservation name -> table number
    groups_by_name = {g["name"]: g for g in result.get("groups", [])}
    entries = []
    for table_id, group_names in result.get("pairings", {}).items():
        for gname in group_names:
            group = groups_by_name.get(gname)
            if not group:
                continue
            if "_part" not in group["name"]:
                display_name = group.get("show_name", gname)
                display_name = f"{display_name} ({group.get('size', '')})".rstrip()
                entries.append((display_name, str(table_id)))
            else:
                idgp = group["name"].split("_part")[0]
                tot_size = sum([gr["size"] for gr in result.get("groups", []) if gr["name"].startswith(idgp+"_part")])
                display_name = group.get("show_name", gname)
                display_name = f"{display_name} ({group.get('size', '')}/{tot_size})".rstrip()
                entries.append((display_name, str(table_id)))
    entries.sort(key=lambda x: x[0].lower())

    elenco_pdf.set_font("verdana", size=9)
    for col_idx in range(2):
        x0 = left_margin + col_idx * (block_width + gutter)

        # Header
        header_y = top_margin - 6
        elenco_pdf.text(x=x0 + 2, y=header_y, text="Nome")
        tav_w = elenco_pdf.get_string_width("Tav.")
        tav_x = x0 + large_col_w + (small_col_w - tav_w) / 2
        elenco_pdf.text(x=tav_x, y=header_y, text="Tav.")

        # Outer border and vertical divider (solid)
        elenco_pdf.rect(x=x0, y=top_margin, w=block_width, h=rows * row_h, style='D')
        elenco_pdf.line(x0 + large_col_w, top_margin, x0 + large_col_w, top_margin + rows * row_h)

        # Horizontal lines: solid
        for r in range(rows + 1):
            y_line = top_margin + r * row_h
            elenco_pdf.line(x0, y_line, x0 + block_width, y_line)

        # Row text
        for r in range(rows):
            y = top_margin + r * row_h
            entry_idx = col_idx * rows + r
            if entry_idx < len(entries):
                name, table_no = entries[entry_idx]
                text_y = y + row_h - 4
                # Reservation name
                elenco_pdf.text(x=x0 + 2, y=text_y, text=name)
                # Table number (right column, centered)
                tn_w = elenco_pdf.get_string_width(table_no)
                tn_x = x0 + large_col_w + (small_col_w - tn_w) / 2
                elenco_pdf.text(x=tn_x, y=text_y, text=table_no)
    
    
    # END ELENCO DRAWING

    title_bytes = elenco_pdf.output()
    title_reader = PdfReader(BytesIO(title_bytes))
    writer.add_page(title_reader.pages[0])

    output = BytesIO()
    writer.write(output)
    return output.getvalue()
    



def getNewColor(old_color:tuple = (random.randint(150, 230), random.randint(130, 230), random.randint(120, 230)))->tuple:
    color = (random.randint(150, 230), random.randint(130, 230), random.randint(120, 230))
    while deltaE(color, old_color) < 50:
        color = (random.randint(150, 230), random.randint(130, 230), random.randint(120, 230))
    return color

def rgbToLab(r: int, g: int, b: int) -> dict:
    # Convert RGB [0,255] to XYZ (D65)
    r_lin = r / 255
    g_lin = g / 255
    b_lin = b / 255

    r_lin = ((r_lin + 0.055) / 1.055) ** 2.4 if r_lin > 0.04045 else (r_lin / 12.92)
    g_lin = ((g_lin + 0.055) / 1.055) ** 2.4 if g_lin > 0.04045 else (g_lin / 12.92)
    b_lin = ((b_lin + 0.055) / 1.055) ** 2.4 if b_lin > 0.04045 else (b_lin / 12.92)

    x = (r_lin * 0.4124564 + g_lin * 0.3575761 + b_lin * 0.1804375) * 100
    y = (r_lin * 0.2126729 + g_lin * 0.7151522 + b_lin * 0.0721750) * 100
    z = (r_lin * 0.0193339 + g_lin * 0.1191920 + b_lin * 0.9503041) * 100

    # Convert XYZ to Lab
    x_ref, y_ref, z_ref = 95.047, 100.0, 108.883
    x = x / x_ref
    y = y / y_ref
    z = z / z_ref

    x = x ** (1 / 3) if x > 0.008856 else (7.787 * x + 16 / 116)
    y = y ** (1 / 3) if y > 0.008856 else (7.787 * y + 16 / 116)
    z = z ** (1 / 3) if z > 0.008856 else (7.787 * z + 16 / 116)

    return {
        "L": 116 * y - 16,
        "a": 500 * (x - y),
        "b": 200 * (y - z),
    }


def deltaE(rgb1: tuple, rgb2: tuple) -> float:
    lab1 = rgbToLab(rgb1[0], rgb1[1], rgb1[2])
    lab2 = rgbToLab(rgb2[0], rgb2[1], rgb2[2])
    return (
        (lab1["L"] - lab2["L"]) ** 2
        + (lab1["a"] - lab2["a"]) ** 2
        + (lab1["b"] - lab2["b"]) ** 2
    ) ** 0.5
