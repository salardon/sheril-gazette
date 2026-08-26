import re
from bs4 import BeautifulSoup


def parse_evt(soup, tour_id):
    dons_emis = []
    messages = soup.find_all(class_="message")
    if not messages:
        lignes = soup.get_text().split("\n")
    else:
        lignes = [m.get_text() for m in messages]

    regex_argent = re.compile(r"Le commandant\s+(.+?)\s*\((\d+)\)\s+as?\s+transmis\s+([\d\s\.,\xA0]+)\s+au commandant\s+(.+?)\s*\((\d+)\)", re.IGNORECASE)
    regex_centaures = re.compile(r"Le commandant\s+(.+?)\s*\((\d+)\)\s+as?\s+transmis\s+([\d\s\.,\xA0]+)\s+centaures?\s+au commandant\s+(.+?)\s*\((\d+)\)", re.IGNORECASE)
    regex_tech = re.compile(r"Le commandant\s+(.+?)\s*\((\d+)\)\s+as?\s+transmis\s+la technologie\s+(.+?)\s+au commandant\s+(.+?)\s*\((\d+)\)", re.IGNORECASE)

    for ligne in lignes:
        match_tech = regex_tech.search(ligne)
        if match_tech:
            nom_emetteur, id_emetteur, nom_tech, nom_receveur, id_receveur = match_tech.groups()
            dons_emis.append({
                "emetteur": str(id_emetteur), "emetteur_nom": nom_emetteur.strip(),
                "receveur": str(id_receveur), "receveur_nom": nom_receveur.strip(),
                "montant": 1.0, "type_don": f"Technologie: {nom_tech.strip()}"
            })
            continue

        match_centaures = regex_centaures.search(ligne)
        if match_centaures:
            nom_emetteur, id_emetteur, montant_str, nom_receveur, id_receveur = match_centaures.groups()
            montant_propre = montant_str.replace("\xa0", "").replace(" ", "").replace("\u202f", "").replace(",", ".")
            try:
                montant = float(montant_propre)
            except ValueError:
                montant = 0.0

            dons_emis.append({
                "emetteur": str(id_emetteur), "emetteur_nom": nom_emetteur.strip(),
                "receveur": str(id_receveur), "receveur_nom": nom_receveur.strip(),
                "montant": montant, "type_don": "Centaures"
            })
            continue

        match_argent = regex_argent.search(ligne)
        if match_argent:
            nom_emetteur, id_emetteur, montant_str, nom_receveur, id_receveur = match_argent.groups()
            montant_propre = montant_str.replace("\xa0", "").replace(" ", "").replace("\u202f", "").replace(",", ".")
            try:
                montant = float(montant_propre)
            except ValueError:
                montant = 0.0

            dons_emis.append({
                "emetteur": str(id_emetteur), "emetteur_nom": nom_emetteur.strip(),
                "receveur": str(id_receveur), "receveur_nom": nom_receveur.strip(),
                "montant": montant, "type_don": "Argent"
            })
    return {"dons_emis": dons_emis}


def parse_classement_generique(soup, tour_id):
    resultats = {}
    if not soup:
        return resultats

    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for tr in rows[1:]:
            cols = tr.find_all(["td", "th"])
            if len(cols) < 3:
                continue

            jid = None
            nom_brut = ""
            race = "-"
            valeur = 0.0

            for i, col in enumerate(cols):
                txt = col.get_text(strip=True)
                if txt.isdigit() and len(txt) <= 3 and i >= 2:
                    jid = txt
                if txt in ["Atalantes", "Fergok", "Yoksor", "Zwaias", "Fremens", "Humain", "Cyborg"]:
                    race = txt

            if not jid:
                for col in cols:
                    span_num = col.find("span", class_="c6")
                    if span_num and span_num.get_text(strip=True).isdigit():
                        jid = span_num.get_text(strip=True)
                        break

            if not jid:
                continue

            for col in cols[:2]:
                t = col.get_text(strip=True)
                if not t.isdigit() and len(t) > 1 and "---" not in t:
                    nom_brut = re.sub(r'\s*\(\d+\)', '', t).strip()
                    break

            for col in reversed(cols):
                txt = col.get_text(strip=True)
                if any(char.isdigit() for char in txt) and "%" not in txt:
                    partie_principale = txt.split('(')[0]
                    clean_t = re.sub(r'[^\d,\.-]', '', partie_principale.replace('\xa0', '').replace(' ', '').replace('\u202f', '').replace(',', '.'))
                    if clean_t and clean_t not in ['.', '-', '+']:
                        try:
                            valeur = float(clean_t)
                            break
                        except ValueError:
                            pass

            resultats[jid] = {
                "joueur_id": str(jid), "nom": nom_brut if nom_brut else f"ID:{jid}",
                "race": race, "valeur": float(valeur), "rang": 0, "variation": 0.0
            }
    return resultats


def parse_planetes(soup, tour_id):
    resultats = {}
    if not soup:
        return resultats

    for table in soup.find_all("table"):
        for tr in table.find_all("tr")[1:]:
            cols = tr.find_all(["td", "th"])
            if len(cols) < 5:
                continue

            nom_txt = cols[1].get_text(strip=True)
            numero_txt = cols[2].get_text(strip=True)
            if "---" in nom_txt or not numero_txt.isdigit():
                continue

            planetes_txt = cols[4].get_text(strip=True)
            clean_planetes = re.sub(r'[^\d]', '', planetes_txt.split('(')[0])
            resultats[numero_txt] = {
                "joueur_id": numero_txt,
                "nom": nom_txt,
                "race": cols[3].get_text(strip=True) or "-",
                "planetes": int(clean_planetes) if clean_planetes.isdigit() else 0
            }
    return resultats


def parse_combats(soup, tour_id):
    resultats = {}
    if not soup:
        return resultats

    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cols = tr.find_all(["td", "th"])
            if len(cols) < 5:
                continue

            match_att = re.search(r'\((\d+)\)', cols[0].get_text())
            match_def = re.search(r'\((\d+)\)', cols[1].get_text())
            if not match_att or not match_def:
                continue

            id_attaquant = match_att.group(1)
            id_defenseur = match_def.group(1)
            texte_cible = cols[4].get_text(strip=True)
            planete_prise = 0
            if "aucune plan" not in texte_cible.lower() and "(" in texte_cible:
                match_planet_count = re.findall(r'\b[A-Za-zÀ-ÿ0-9]+\s+\d+\b', texte_cible)
                planete_prise = len(match_planet_count) if match_planet_count else 1

            for jid in [id_attaquant, id_defenseur]:
                resultats.setdefault(jid, {"combats": {
                    "attaques_lancees": 0, "attaques_subies": 0,
                    "cibles_attaquees": [], "planetes_perdues_adversaire": 0,
                    "planetes_prises": 0, "planetes_perdues": 0
                }})

            attaquant = resultats[id_attaquant]["combats"]
            defenseur = resultats[id_defenseur]["combats"]
            attaquant["attaques_lancees"] += 1
            attaquant["planetes_perdues_adversaire"] += planete_prise
            attaquant["planetes_prises"] += planete_prise
            if id_defenseur not in attaquant["cibles_attaquees"]:
                attaquant["cibles_attaquees"].append(id_defenseur)
            defenseur["attaques_subies"] += 1
            defenseur["planetes_perdues"] += planete_prise
    return resultats


def parse_alliances(soup, tour_id):
    resultats = {}
    if not soup:
        return resultats

    for table in soup.find_all("table"):
        for tr in table.find_all("tr")[1:]:
            cols = tr.find_all(["td", "th"])
            if len(cols) < 5:
                continue

            nom_alliance = cols[1].get_text(strip=True)
            if not nom_alliance:
                continue

            for span in tr.find_all("span", class_=re.compile(r'^race\d+$')):
                match = re.search(r'\((\d+)\)', span.get_text())
                if match:
                    resultats[match.group(1)] = {"alliance": nom_alliance}
    return resultats


PARSERS_REGISTRY = {
    "evt.htm": parse_evt,
    "technologie.htm": parse_classement_generique,
    "rayonnement.htm": parse_classement_generique,
    "pop_vs.htm": parse_classement_generique,
    "offensive.htm": parse_classement_generique,
    "centaures.htm": parse_classement_generique,
    "pop.htm": parse_classement_generique,
    "puissance.htm": parse_classement_generique,
    "reputation.htm": parse_classement_generique,
    "planetes.htm": parse_planetes,
    "combats.htm": parse_combats,
    "alliances.htm": parse_alliances,
    "alliance.htm": parse_alliances
}
