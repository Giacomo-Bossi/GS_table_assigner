from pathlib import Path
from fpdf import FPDF

IMAGE_PATH = Path("logopng.png")

class EventInfo:
    def __init__(self, eventln1: str, eventln2:str, eventln3: str, date: str) -> None:
        self.eventln1 = eventln1
        self.eventln2 = eventln2
        self.eventln3 = eventln3
        self.date = date



def generaSegnaposti(prenotazioni: list[tuple[str, int]], info_evento: EventInfo) -> bytes:
    if not IMAGE_PATH.exists():
        raise FileNotFoundError(f"Image not found: {IMAGE_PATH}")
    pdf = FPDF()
    for pren in prenotazioni:
        name = pren[0]
        places = str(pren[1])

        pdf.add_page()

        pdf.image(str(IMAGE_PATH), x=15, y=152, w=18, h=21)

        pdf.set_line_width(0.7)
        pdf.line(11.3, 181, 194.817, 181)

        pdf.set_line_width(0.08)
        pdf.rect(x=159.977, y=184, w=34.84, h=24.96)

        pdf.set_font("helvetica", style="IB", size=34)
        pdf.set_xy(98, 154)
        pdf.cell(w=34.84, h=10, text=name, align="C")

        pdf.set_font("helvetica", style="IB", size=36)
        pdf.set_xy(80.5, 187.5)
        pdf.cell(w=35, h=10, text="RISERVATO", align="C")

        pdf.set_font("helvetica", style="IB", size=16)
        pdf.set_xy(10, 185.5)
        pdf.cell(w=35, h=10, text=info_evento.eventln1, align="C")

        pdf.set_font("helvetica", style="IB", size=16)
        pdf.set_xy(10, 192)
        pdf.cell(w=35, h=10, text=info_evento.eventln2, align="C")
        pdf.set_font("helvetica", style="IB", size=16)
        pdf.set_xy(10, 198.5)
        pdf.cell(w=35, h=10, text=info_evento.eventln3, align="C")

        pdf.set_font("helvetica", style="I", size=11)
        pdf.set_xy(159.977, 183)
        pdf.cell(w=34.84, h=10, text="P O S T I", align="C")

        pdf.set_font("helvetica", style="IB", size=50)
        pdf.set_xy(159.5, 196.6)
        pdf.cell(w=34.84, h=10, text=places, align="C")

        pdf.set_font("helvetica", style="IB", size=12)
        pdf.set_xy(82.9, 200.2)
        pdf.cell(w=35, h=10, text=info_evento.date, align="C")

    return bytes(pdf.output())

event = EventInfo("Festa", "d'inverno", "2026", "Sabato 31 Gennaio 2026")
# event = EventInfo("Festa dello", "Sport 2026", "", "Mercoledì 12 Giugno 2024")
generaSegnaposti(prenotazioni=[["Mario Rossi", 17],["Luca Bianchi", 5],["Alessandro Verdi", 3]], info_evento=event)
