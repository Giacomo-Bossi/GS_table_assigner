from pathlib import Path

from fpdf import Template


IMAGE_PATH = Path("logopng.png")
TEMPLATE_PATH = Path("segnaposto_template.json")


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
    template.parse_json(str(TEMPLATE_PATH))

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


if __name__ == "__main__": # test
    event = EventInfo("Festa", "d'inverno", "2026", "Sabato 31 Gennaio 2026")
    prenotazioni = [
        ("Mario Rossi", 17),
        ("Luca Bianchi", 5),
        ("Alessandra Verdi", 4),
    ]
    pdf_bytes = generaSegnaposti(prenotazioni=prenotazioni, info_evento=event)
