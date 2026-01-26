
from math import ceil,floor
from pathlib import Path
from io import BytesIO
import json
import random

from fpdf import Template, FPDF
from pypdf import PdfWriter, PdfReader


IMAGE_PATH = Path("renderResources/logopng.png")
TEMPLATE_PATH = Path("renderResources/segnaposto_template.json")
PLANIMETRIA_PATH = Path("renderResources/planimetria_FDI.pdf")
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
    print(width,height)
    # Create the overlay with the rectangle with matching dimensions
    pdf = FPDF(unit="pt", format=(width, height))
    pdf.add_font("verdana", style="", fname="renderResources/Verdana.ttf", uni=True)
    pdf.add_page()
    
## START DRAW LOGIC
    
    
    #change header title
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(x=width-75, y=270, w=40, h=607, style='F') 
    with pdf.rotation(270, width-35, 500):
        pdf.set_x(x=width-75)
        pdf.set_y(y=500)

    pdf.set_font("verdana", size=50)
    pdf.set_text_color(0, 0, 255)
    text = title
    w_text = pdf.get_string_width(text)
    with pdf.rotation(270, width-72, 350):
        pdf.text(x=width+150- w_text/2, y=351 , text=text) 
    
    #end header
    
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

        
        # sanity check
        pdf.set_fill_color(255, 0, 0)  # Red
        pdf.circle(x=x, y=y, radius=1, style='F')
        
        pdf.set_fill_color(0, 255, 0)  # Green
        pdf.circle(x=x+height_t, y=y+width_t, radius=1, style='F')
        
        
        pdf.set_fill_color(200, 200, 200)
        
        SEAT_W = 12
        SEAT_H = 3
        EDGE_GAP = 1.2
        SEAT_STRIDE = 15.23  #distanza tra i centri dei 
        
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
       
        if sum([gr["required_head"] for gr in gruppi_testa]) > table["head_seats"] or len(gruppi_testa) > 1:  #per ora max 1 testa
            raise ValueError("Troppi posti in testa richiesti")
        
        #if table["head_seats"] >0 :
        #    continue 

        seg = table_segmentation(table)
        
        for gruppo_testa in gruppi_testa:
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            pdf.set_fill_color(*color)
            for i in range(gruppo_testa["size"]):
                spot = seg.pop(0)
                pdf.rect(x=spot.x,y=spot.y,w=spot.w,h=spot.h,style="F")

        for gruppo in gruppi_normali:
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            pdf.set_fill_color(*color)
            for i in range(gruppo["size"]):
                spot = seg.pop(0)
                pdf.rect(x=spot.x,y=spot.y,w=spot.w,h=spot.h,style="F")
                

        pdf.set_font("Arial", size=12)
        pdf.set_text_color(0, 0, 0) 
        
        with pdf.rotation(270, x + height_t/2, y + width_t/2):
            pdf.text(x=x + height_t/2 - 10, y=y + width_t/2, text=str(table['table_id']))

        pdf.rect(x=x, y=y, w=height_t, h=width_t, style='D') #table border
        
    
    ## END DRAW LOGIC
    overlay_bytes = pdf.output()
    overlay_reader = PdfReader(BytesIO(overlay_bytes))
    overlay_page = overlay_reader.pages[0]

    writer = PdfWriter()

    for page in reader.pages:
        page.merge_page(overlay_page)
        writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    return output.getvalue()
    