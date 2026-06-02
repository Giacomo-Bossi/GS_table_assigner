
from math import ceil,floor, atan2, degrees
from pathlib import Path
from io import BytesIO
from contextlib import contextmanager
import json
import random

from fpdf import Template, FPDF
from pypdf import PdfWriter, PdfReader
from requests import head


IMAGE_PATH = Path("renderResources/logopng.png")
TEMPLATE_PATH = Path("renderResources/segnaposto_template.json")
PLANIMETRIA_PATH = Path("renderResources/PLANIMETRIA FDS.pdf")
TAVOLI_JSON_PATH = Path("renderResources/tavoli_FDS.json")


class Table_spot():
    def __init__(self,x,y,h,w):
        self.x =x
        self.y = y
        self.h = h
        self.w = w

@contextmanager
def nullcontext():
    """A context manager that does nothing."""
    yield

def table_segmentation(table:dict, head_lateral_seats_offset:int=9, head_other_seats_offset:int=32, seats_stride:int=18 )->list:
    """Return list of Table_spot for the given table.

    Optional drawing parameters (defaults match `tavoli` draw_params):
    - head_lateral_seats_offset: offset for lateral head seats
    - head_other_seats_offset: offset for other head seats
    - seats_stride: stride between seat centers
    """
    posti  = table["capacity"]
    h = table['gui']['height']
    w = table['gui']['width']
    x = table['gui']['x']
    y = table['gui']['y']
    segmenti = []

    if table["head_seats"] > 0:  #at most one head, at the bottom
        segmenti.append(Table_spot(x, y, w, head_lateral_seats_offset)) #head seat
        segmenti.append(Table_spot(x + head_lateral_seats_offset, y, w/2,  head_other_seats_offset - head_lateral_seats_offset)) #left head lateral seats
        segmenti.append(Table_spot(x + head_lateral_seats_offset, y + w/2, w/2, head_other_seats_offset - head_lateral_seats_offset)) #rigth head lateral seats

        posti -= 3
        h = h - head_other_seats_offset
        x = x + head_other_seats_offset

    if posti >0:
        square_h = h / ceil(posti/2)
        square_w = w / 2
        
        for i in range(posti):
            segmenti.append(Table_spot(x+square_h*floor(i/2),
                                       y+square_w*(i%2),
                                       square_w,
                                       square_h))
        
    return segmenti


def expand_aggregated_group(group: dict) -> list[dict]:
    aggregated = group.get("aggregated_reservations")
    if not isinstance(aggregated, list) or len(aggregated) == 0:
        return [{
            **group,
            "show_name": str(group.get("show_name", group.get("name", ""))),
            "_agg_parent": group.get("name"),
        }]

    expanded = []
    for sub in aggregated:
        if not isinstance(sub, dict):
            continue
        name = str(sub.get("name", group.get("name", "")))
        show_name = str(sub.get("show_name", name))
        expanded.append({
            "name": name,
            "show_name": show_name,
            "size": sub.get("size", 0),
            "real_size": sub.get("real_size", sub.get("size", 0)),
            "required_head": sub.get("required_head", 0),
            "near_field": sub.get("near_field", False),
            "_agg_parent": group.get("name"),
        })

    if not expanded:
        return [{
            **group,
            "show_name": str(group.get("show_name", group.get("name", ""))),
            "_agg_parent": group.get("name"),
        }]

    head_idx = next((i for i, g in enumerate(expanded) if g.get("required_head")), None)
    if head_idx is not None:
        for i, g in enumerate(expanded):
            if i != head_idx and g.get("required_head"):
                g["required_head"] = 0

    return expanded


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
        table_definitions = json.load(f)

    head_lateral_seats_offset = table_definitions.get("draw_params", {}).get("head_lateral_seats_offset", 9)
    head_other_seats_offset = table_definitions.get("draw_params", {}).get("head_other_seats_offset", 32)
    seats_stride = table_definitions.get("draw_params", {}).get("seats_stride", 18)
    tavoli_def = table_definitions.get("tables", [])
    # Read the planimetry first to get dimensions
    reader = PdfReader(PLANIMETRIA_PATH)
    first_page = reader.pages[0]
    mb = first_page.mediabox
    width= float(mb.width)
    height = float(mb.height)

    # Create the overlay with the rectangle with matching dimensions
    
    squared = max(width, height) # quadrato serve perchè altrimenti ruotando la pagina (nel merge) gli elementi possono uscire fuori dalla pagina ed esere tagliati
    pdf = FPDF(unit="pt", format=(squared, squared)) 
    pdf.add_font("verdana", style="", fname="renderResources/Verdana.ttf", uni=True)
    pdf.add_page()
    
## START DRAW LOGIC ##################################
    
    
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

    groups = result.get("groups", [])
    groups_by_name = {g.get("name"): g for g in groups if g.get("name") is not None}
    render_groups = []
    for group in groups:
        render_groups.extend(expand_aggregated_group(group))

    color = getNewColor()
    split_colors = {} # pregeneriamo i colori per i gruppi splittati
    split_tot_size = {}
    for gruppo in render_groups:
        name = gruppo.get("name", "")
        if "-part" in name:
            idgp = name.split("-part")[0]
            if idgp not in split_colors:
                color = getNewColor(color)
                split_colors[idgp] = color
            if idgp not in split_tot_size:
                split_tot_size[idgp] = 0
            split_tot_size[idgp] += gruppo.get("real_size", gruppo.get("size", 0))
            
    

    

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

        
        horizontal = table.get("horizontal", False)
        ##print(f"Drawing table {table['table_id']} at ({x},{y}) w={width_t} h={height_t} posti={posti} head={table['head_seats']} horizontal={horizontal}")

        # Determine rotation context
        label_ctx = pdf.rotation(90, x, y) if horizontal else nullcontext()
        
        with label_ctx:
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
            HEAD_LATERAL_SEATS_OFFSET = head_lateral_seats_offset
            HEAD_OTHER_SEATS_OFFSET = head_other_seats_offset
            EDGE_GAP = 1.2
            SEAT_STRIDE = seats_stride  #distanza tra i centri dei posti
            
            if table["head_seats"] == 0:  
                for vp in range(ceil(posti/2)):
                    # Left side
                    pdf.rect(x=x+EDGE_GAP+SEAT_STRIDE*vp, y=y-SEAT_H, w=SEAT_W, h=SEAT_H, style='FD')
                    # Right side
                    if(table["capacity"] % 2 == 0 or vp >  0):
                        pdf.rect(x=x+EDGE_GAP+SEAT_STRIDE*vp, y=y+width_t, w=SEAT_W, h=SEAT_H, style='FD')
            else:
                pdf.rect(x=x-SEAT_H, y=y+((width_t-SEAT_W)/2), w=SEAT_H, h=SEAT_W, style='FD') #horizontal seat
                pdf.rect(x=x+HEAD_LATERAL_SEATS_OFFSET, y=y-SEAT_H, w=SEAT_W, h=SEAT_H, style='FD')
                pdf.rect(x=x+HEAD_LATERAL_SEATS_OFFSET, y=y+width_t, w=SEAT_W, h=SEAT_H, style='FD')
                
                for vp in range(ceil((posti-3)/2)):
                    # Left side
                    pdf.rect(x=x+HEAD_OTHER_SEATS_OFFSET+SEAT_STRIDE*vp, y=y-SEAT_H, w=SEAT_W, h=SEAT_H, style='FD')
                    # Right side
                    if((posti-3) % 2 == 0 or vp >  0):
                        pdf.rect(x=x+HEAD_OTHER_SEATS_OFFSET+SEAT_STRIDE*vp, y=y+width_t, w=SEAT_W, h=SEAT_H, style='FD')
            
            pdf.rect(x=x, y=y, w=height_t, h=width_t, style='D') #table border
            
            # Draw table ID label inside rotation context (position rotates with table, text stays upright)
            pdf.set_font("Arial", size=12)
            pdf.set_text_color(0, 0, 0)
            pdf.set_fill_color(255, 255, 255)
            labLen = pdf.get_string_width(str(table['table_id']))
            with pdf.rotation(270, x + height_t + 5, y + width_t - labLen):
                pdf.circle(x=x + height_t + 5 + labLen/2, y=y + width_t - labLen -5, radius=labLen/2 - 1 +4, style='F')
                pdf.text(x=x + height_t + 5, y=y + width_t - labLen, text=str(table['table_id']))


            associazioni = result.get("pairings", {})
            assigned_names = associazioni.get(str(table["table_id"]), [])
            gruppiTavolo = []
            for gname in assigned_names:
                group = groups_by_name.get(gname)
                if not group:
                    continue
                expanded = expand_aggregated_group(group)
                for sub in expanded:
                    sub["_agg_order"] = len(gruppiTavolo)
                gruppiTavolo.extend(expanded)
            gruppi_testa = [gruppo for gruppo in gruppiTavolo if gruppo.get('required_head',0)]
            for gt in gruppi_testa:
                if gt.get('size', 0) % 2 == 0:
                    gt['size'] += 1
                    
            gruppi_normali = [gruppo for gruppo in gruppiTavolo if not gruppo.get('required_head',0)]
            #gruppi_normali.sort(key=lambda g: g['size']%2==1)
        
            if sum(gr.get("required_head", 0) for gr in gruppi_testa) > table["head_seats"] or len(gruppi_testa) > 1:  #per ora max 1 testa
                print("Tavolo", table["table_id"], " - In testa:", gruppi_testa)
                raise ValueError("Troppi posti in testa richiesti")
            
            #if table["head_seats"] >0 :
            #    continue 

            seg = table_segmentation(table, head_lateral_seats_offset, head_other_seats_offset, seats_stride)

            if not gruppi_testa:
                seg.sort(key=lambda s: -s.x)
            
            
            pdf.set_font("Arial", size=12)
            pdf.set_text_color(0, 0, 0)
            
            for gruppo_testa in gruppi_testa:
                gruppo_name = gruppo_testa.get("name", "")
                gruppo_show = gruppo_testa.get("show_name", gruppo_name)
                gruppo_size = gruppo_testa.get("size", 0)
                gruppo_real_size = gruppo_testa.get("real_size", gruppo_size)
                if("-part" in gruppo_name):
                    color = split_colors[gruppo_name.split("-part")[0]]
                else:
                    color = getNewColor(color)
                pdf.set_fill_color(*color)
                for i in range(gruppo_size):
                    spot = seg.pop(0)
                    if i < gruppo_real_size:
                        pdf.rect(x=spot.x,y=spot.y,w=spot.w,h=spot.h,style="F")
                if("-part" not in gruppo_name):
                    labls.append( (f"{gruppo_show}({gruppo_real_size})", x + 10 , y + width_t/2, color, 262, horizontal, x, y) )
                else:
                    idgp = gruppo_name.split("-part")[0]
                    tot_size = split_tot_size.get(idgp, gruppo_real_size)
                    labls.append( (f"{gruppo_show}({gruppo_real_size}/{tot_size})", x + 10 , y + width_t/2, color, 262, horizontal, x, y) )
                    

            agg_parent_has_head = {g.get("_agg_parent", g.get("name", "")) for g in gruppi_testa}
            parent_order = {gname: idx for idx, gname in enumerate(assigned_names)}

            blocks = []
            for gruppo in gruppi_normali:
                parent = gruppo.get("_agg_parent", gruppo.get("name", ""))
                if not blocks or blocks[-1][0].get("_agg_parent") != parent:
                    blocks.append([gruppo])
                else:
                    blocks[-1].append(gruppo)

            blocks.sort(
                key=lambda block: (
                    0 if block[0].get("_agg_parent", block[0].get("name", "")) in agg_parent_has_head else 1,
                    parent_order.get(block[0].get("_agg_parent", block[0].get("name", "")), 10**9),
                )
            )

            for block in blocks:
                if not seg:
                    break
                block_size = sum(g.get("size", 0) for g in block)
                if block_size > len(seg):
                    continue

                for gruppo in block:
                    if not seg:
                        break
                    gruppo_name = gruppo.get("name", "")
                    gruppo_show = gruppo.get("show_name", gruppo_name)
                    gruppo_size = gruppo.get("size", 0)
                    gruppo_real_size = gruppo.get("real_size", gruppo_size)
                    if("-part" in gruppo_name):
                        color = split_colors[gruppo_name.split("-part")[0]]
                    else:
                        color = getNewColor(color)
                    pdf.set_fill_color(*color)
                    lowest, highest = 999999, 0
                    for i in range(gruppo_size):
                        spot = seg.pop(0)
                        if i < gruppo_real_size:
                            pdf.rect(x=spot.x,y=spot.y,w=spot.w,h=spot.h,style="F")
                            if spot.x < lowest:
                                lowest = spot.x
                            if spot.x+spot.h > highest:
                                highest = spot.x + spot.h
                    # # Fallback if no seats were drawn (e.g. real_size was 0)
                    # if lowest == 999999:
                    #     lowest = highest = spot.x if 'spot' in locals() else x
                    if "-part" not in gruppo_name:
                        labls.append( (f"{gruppo_show}({gruppo_real_size})", (lowest + highest)/2 , y + width_t/2, color, degrees(atan2(-width_t, lowest-highest)), horizontal, x, y) )
                    else:
                        idgp = gruppo_name.split("-part")[0]
                        tot_size = split_tot_size.get(idgp, gruppo_real_size)
                        labls.append( (f"{gruppo_show}({gruppo_real_size}/{tot_size})", (lowest + highest)/2 , y + width_t/2, color, degrees(atan2(-width_t, lowest-highest)), horizontal, x, y) )
                
            pdf.rect(x=x, y=y, w=height_t, h=width_t, style='D') #table border

    
    pdf.set_font("Arial", size=8)
    pdf.set_text_color(0, 0, 0) 
    for lbl, lx, ly, color, angle, is_horizontal, rot_x, rot_y in labls:
        pdf.set_fill_color(*color)
        text_w = pdf.get_string_width(lbl) + 6
        text_h = 8+2
        rotation_ctx = pdf.rotation(90, rot_x, rot_y) if is_horizontal else nullcontext()
        with rotation_ctx:
            with pdf.rotation(angle, lx, ly):
                with pdf.local_context(fill_opacity=0.7):
                    pdf.rect(x=lx - text_w/2, y=ly - text_h/2, w=text_w, h=text_h, style='F')
                pdf.set_text_color(0, 0, 0)
                pdf.text(x=lx - text_w/2 + 3, y=ly + 3, text=lbl)
        
    
## END DRAW LOGIC ##################################
    overlay_bytes = pdf.output()
    overlay_reader = PdfReader(BytesIO(overlay_bytes))
    overlay_page = overlay_reader.pages[0]
    #overlay_page.rotate(270)  # Ruota l'overlay per allinearlo alla planimetria

    writer = PdfWriter()

    for page in reader.pages:
        overlay_page.transfer_rotation_to_content()
        page.rotate(270)  # Ruota la pagina della planimetria per allinearla all'overlay
        #page.transfer_rotation_to_content()
        page.merge_page(overlay_page)
        writer.add_page(page)





## START ELENCO DRAWING ###########################
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
    entries = []
    for table_id, group_names in result.get("pairings", {}).items():
        for gname in group_names:
            group = groups_by_name.get(gname)
            if not group:
                continue
            for display_group in expand_aggregated_group(group):
                display_name = display_group.get("show_name", display_group.get("name", gname))
                display_size = display_group.get("real_size", display_group.get("size", ""))
                display_group_name = display_group.get("name", gname)
                if "-part" not in display_group_name:
                    display_name = f"{display_name} ({display_size})".rstrip()
                    entries.append((display_name, str(table_id)))
                else:
                    idgp = display_group_name.split("-part")[0]
                    tot_size = sum(
                        gr.get("real_size", gr.get("size", 0))
                        for gr in render_groups
                        if gr.get("name", "").startswith(idgp + "-part")
                    )
                    display_name = f"{display_name} ({display_size}/{tot_size})".rstrip()
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
    
    
# END ELENCO DRAWING ###########################

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
