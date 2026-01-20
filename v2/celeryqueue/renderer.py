from math import ceil
from pathlib import Path
from io import BytesIO
import json

from fpdf import Template, FPDF
from pypdf import PdfWriter, PdfReader


IMAGE_PATH = Path("renderResources/logopng.png")
TEMPLATE_PATH = Path("renderResources/segnaposto_template.json")
PLANIMETRIA_PATH = Path("renderResources/planimetria_FDI.pdf")
TAVOLI_JSON_PATH = Path("renderResources/tavoli.json")


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
    assegnazioni: list[tuple[int, int]],
    gruppi: list[dict],
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
    width = float(mb.width)
    height = float(mb.height)

    # Create the overlay with the rectangle with matching dimensions
    pdf = FPDF(unit="pt", format=(width, height))
    pdf.add_font("verdana", style="", fname="renderResources/Verdana.ttf", uni=True)
    pdf.add_page()
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
    
## START DRAW LOGIC
    for table in tavoli_def:
        y = table['gui']['x']
        x = width - table['gui']['y']
        height_t = table['gui']['width']
        width_t = -table['gui']['height']
        pdf.rect(x=x, y=y, w=width_t, h=height_t, style='D')

        vpl = ceil((table["capacity"] - table["head_seats"])/2)
        pdf.set_fill_color(200, 200, 200)
        for vp in range(vpl):
            if table["head_seats"] <= 0 or vp < vpl - 1:
                # Left side
                pdf.rect(x=x-13.5-15.23*vp, y=y-3, w=12, h=3, style='FD')
                # Right side
                if(table["capacity"] % 2 == 0 or vp < vpl - 1):
                    pdf.rect(x=x-13.5-15.23*vp, y=y+height_t, w=12, h=3, style='FD')
            else:
                # draw head seat and prehead with gap
                pdf.rect(x=x-21-15.23*vp, y=y-3, w=12, h=3, style='FD')
                pdf.rect(x=x-21-15.23*vp, y=y+height_t, w=12, h=3, style='FD')

                pdf.rect(x=x+width_t-3, y=y+((height_t-12)/2), w=3, h=12, style='FD')


        pdf.set_font("Arial", size=12)
        pdf.set_text_color(0, 0, 0)
        
        with pdf.rotation(270, x + width_t/2, y + height_t/2):
            pdf.text(x=x + width_t/2 - 10, y=y + height_t/2, text=str(table['table_id']))


    
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
    