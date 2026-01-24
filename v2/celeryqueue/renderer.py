from math import ceil
from pathlib import Path
from io import BytesIO
import json
import random

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
    
## START DRAW LOGIC

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
        pdf.text(x=width+150- w_text/2, y=351 , text=text) # Titolo centrato

    for table in tavoli_def:
        y = table['gui']['x']
        x = width - table['gui']['y']
        height_t = table['gui']['width']
        width_t = -table['gui']['height']
        

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

        postiADestra = vpl # posti a destra (non considerando la formazione di 3 posti per la testa (gestito separatamente))
        postiASinistra = table["capacity"] - postiADestra # posti a sinistra (non considerando la formazione di 3 posti per la testa (gestito separatamente))
        testaA3 = False # indica se il tavolo ha la testa con la formazione a 3 posti
        if table["head_seats"] > 0:
            postiASinistra -= 2
            postiADestra -= 1
            testaA3 = True
            testaA3posti = [False, False, False]  # indica se i posti della testa sono stati assegnati (destra, centro, sinistra)
        assegnatiADestra = 0
        assegnatiASinistra = 0
        

        # for gruppo_id in assegnazioni[str(table['table_id']-1)]:
        #     gruppo = gruppi[gruppo_id]
        #     print(" - Group ", gruppo_id, ": ", gruppo['show_name'], " (size ", gruppo['size'], ")")
        #     color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        #     pdf.set_fill_color(*color)

        #     gruppoADestra = ceil(gruppo['size']/2)
        #     gruppoASinistra = gruppo['size'] - gruppoADestra
            
        #     pdf.rect(x=x, y=y, w=-15.23*gruppoADestra, h=height_t/2, style='F')
        #     pdf.rect(x=x, y=y+height_t/2, w=-15.23*gruppoASinistra, h=height_t/2, style='F')

        #     break

        ## render dei gruppi colorati dei gruppi assegnati al tavolo
        gruppiTavolo = assegnazioni[str(table['table_id']-1)] #gruppi assegnati a questo tavolo
        gruppiTavolo = sorted(gruppiTavolo, key=lambda gid: (gruppi[gid].get('require_head', 0) == 0, gruppi[gid]['size'] % 2, gruppi[gid]['size']), reverse=True) # ordino per dimensione decrescente (prima i gruppi dispari, alla fine sempre quelli che richiedono testa)
        postiLiberi = table["capacity"] - sum([gruppi[gid]['size'] for gid in gruppiTavolo])

        lato = 0 # 0 = sinistra, 1 = destra
        for gid in gruppiTavolo:
            gruppo = gruppi[gid]
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            pdf.set_fill_color(*color)
            gruppoADestra = ceil(gruppo['size']/2)
            gruppoASinistra = gruppo['size'] - gruppoADestra
            # Controllo se il gruppo richiede la testa
            # if gruppo.get('require_head', 0) == 1 and testaA3:
            #     # Assegno 2 posti alla testa
            #     pdf.rect(x=x, y=y+((height_t-12)/2), w=-15.23*2, h=12, style='F')
            #     gruppoASinistra -= 2
            #     testaA3 = False # la testa è stata assegnata

            for l in range(gruppo["size"]):
                if lato == 0 and assegnatiASinistra < postiASinistra:
                    pdf.rect(x=x-15.23*assegnatiASinistra, y=y+height_t/2, w=-15.23, h=height_t/2, style='F')
                    assegnatiASinistra += 1
                    lato = 1
                elif lato == 1 and assegnatiADestra < postiADestra:
                    pdf.rect(x=x-15.23*assegnatiADestra, y=y, w=-15.23, h=height_t/2, style='F')
                    assegnatiADestra += 1
                    lato = 0
                else:
                    # non ci sono più posti su questo lato, cambio lato
                    lato = 1 - lato
                    if lato == 0 and assegnatiASinistra < postiASinistra:
                        pdf.rect(x=x-15.23*assegnatiASinistra, y=y+height_t/2, w=-15.23, h=height_t/2, style='F')
                        assegnatiASinistra += 1
                    elif lato == 1 and assegnatiADestra < postiADestra:
                        pdf.rect(x=x-15.23*assegnatiADestra , y=y, w=-15.23, h=height_t/2, style='F')
                        assegnatiADestra += 1


            
        
        




        
        # pdf.set_font("Arial", size=12)
        # pdf.set_text_color(0, 0, 0)
        
        # with pdf.rotation(270, x + width_t/2, y + height_t/2):
        #     pdf.text(x=x + width_t/2 - 10, y=y + height_t/2, text=str(table['table_id']))

        pdf.rect(x=x, y=y, w=width_t, h=height_t, style='D')

    
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
    