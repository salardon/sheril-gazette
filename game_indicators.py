import numpy as np


def enrichir_donnees_joueurs(joueurs_dict):
    """
    Enrichit les joueurs avec des indicateurs militaires et geopolitiques.
    """
    for jid, data in joueurs_dict.items():
        if jid == "_dons_emis_tour":
            continue

        combats = data.get("combats", {})
        attaques_lancees = combats.get("attaques_lancees", 0)
        attaques_subies = combats.get("attaques_subies", 0)
        cibles = combats.get("cibles_attaquees", [])
        total_engagements = attaques_lancees + attaques_subies
        indice_tension = float(total_engagements) / max(1, data.get("planetes", 1))
        planetes_conquises = combats.get("planetes_perdues_adversaire", 0)
        ratio_offensif = (
            float(planetes_conquises) / max(1, attaques_lancees)
            if attaques_lancees > 0 else 0.0
        )

        data["indicateurs_militaires"] = {
            "balance_projection": int(attaques_lancees - attaques_subies),
            "attaques_lancees": int(attaques_lancees),
            "attaques_subies": int(attaques_subies),
            "cibles_attaquees": cibles,
            "indice_tension": round(indice_tension, 3),
            "ratio_offensif": round(ratio_offensif, 3)
        }

        alliance = data.get("alliance", "Aucune")
        dons = data.get("dons_recus", {})
        nb_dons = dons.get("total_recu", 0)
        score_isolement = 1.0 if alliance == "Aucune" else 0.2
        facteur_connexions = (
            len(cibles) * 0.15 + nb_dons * 0.2 + total_engagements * 0.05
        )
        score_isolement = max(0.0, min(1.0, score_isolement - facteur_connexions))

        if len(cibles) >= 2 and alliance == "Aucune":
            score_isolement = round(max(0.3, min(0.6, score_isolement)), 2)
        else:
            score_isolement = round(score_isolement, 2)

        data["indicateurs_geopolitiques"] = {
            "alliance": str(alliance),
            "est_isole": score_isolement
        }

    return joueurs_dict
