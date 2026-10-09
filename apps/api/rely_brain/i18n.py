"""Locale strings (EN/TR/ES). Language changes wording only; every number comes from facts.

Turkish and Spanish templates use arrow notation ("%8 → %65") to stay grammatical without
suffix rules; all placeholders are filled from the same locale-invariant facts.
"""
from __future__ import annotations

CHANNEL = {
    "en": {"L": "left", "C": "centre", "R": "right"},
    "tr": {"L": "sol", "C": "merkez", "R": "sağ"},
    "es": {"L": "izquierdo", "C": "central", "R": "derecho"},
}

RULE_NAME = {
    "en": {"sub_shift": "substitution shift", "red_card": "red card", "shot_surge": "shot surge", "momentum_swing": "momentum swing",
           "channel_dominance": "channel dominance", "possession_swing": "pass-share swing",
           "dangerous_sequences": "repeated dangerous sequences", "goal": "goal"},
    "tr": {"sub_shift": "oyuncu değişikliği etkisi", "red_card": "kırmızı kart", "shot_surge": "şut patlaması",
           "momentum_swing": "momentum değişimi", "channel_dominance": "kanal hakimiyeti", "possession_swing": "pas payı değişimi",
           "dangerous_sequences": "tekrarlanan tehlikeli ataklar", "goal": "gol"},
    "es": {"sub_shift": "cambio con efecto", "red_card": "tarjeta roja", "shot_surge": "aluvión de tiros",
           "momentum_swing": "cambio de inercia", "channel_dominance": "dominio de carril", "possession_swing": "cambio en la cuota de pases",
           "dangerous_sequences": "llegadas peligrosas repetidas", "goal": "gol"},
}

TITLE = {
    "sub_shift": {"en": "{team}'s {minute}' change moves the attack to the {ch}",
                  "tr": "{team}, {minute}' değişikliğiyle hücumu {ch} kanala taşıdı",
                  "es": "El cambio del {minute}' de {team} lleva el ataque al carril {ch}"},
    "red_card": {"en": "Red card reshapes the game: {team} down to ten",
                 "tr": "Kırmızı kart oyunu değiştirdi: {team} 10 kişi",
                 "es": "La roja cambia el partido: {team} con diez"},
    "shot_surge": {"en": "{team} shot surge", "tr": "{team} şut yağdırıyor", "es": "Aluvión de tiros de {team}"},
    "momentum_swing": {"en": "Momentum swings to {team}", "tr": "Momentum {team} tarafına geçti", "es": "La inercia cambia hacia {team}"},
    "channel_dominance": {"en": "{team} dominate the {ch} channel", "tr": "{team} {ch} kanalda üstün",
                          "es": "{team} domina el carril {ch}"},
    "possession_swing": {"en": "{team} take control of the ball", "tr": "{team} oyunun kontrolünü aldı",
                         "es": "{team} se adueña del balón"},
    "dangerous_sequences": {"en": "{team} keep arriving in the box", "tr": "{team} ceza sahasına sürekli geliyor",
                            "es": "{team} no deja de pisar el área"},
    "goal": {"en": "Goal: {player} ({team})", "tr": "Gol: {player} ({team})", "es": "Gol: {player} ({team})"},
}

BODY = {
    "sub_shift": {
        "en": ["Before the change, {share_before}% of {team}'s progressive actions went through the {ch} channel. Since {player_in} came on for {player_out}, it is {share_after}% ({prog_after} actions).",
               "Shots: {shots_before} in the {window_minutes} minutes before, {shots_after} since. Box entries since the change: {box_after}.",
               "{key_player} is the most involved player in that channel ({key_player_actions} progressive actions)."],
        "tr": ["Değişiklikten önce {team} ileri taşıyan aksiyonlarında {ch} kanal payı: %{share_before}. {player_in}, {player_out} yerine girdiğinden beri: %{share_after} ({prog_after} aksiyon).",
               "Şutlar: önceki {window_minutes} dakikada {shots_before}, değişiklikten beri {shots_after}. O andan beri ceza sahası girişleri: {box_after}.",
               "Bu kanalda en etkili oyuncu {key_player} ({key_player_actions} ileri aksiyon)."],
        "es": ["Antes del cambio, el {share_before}% de las acciones progresivas de {team} iban por el carril {ch}. Desde la entrada de {player_in} por {player_out}: {share_after}% ({prog_after} acciones).",
               "Tiros: {shots_before} en los {window_minutes} minutos previos, {shots_after} desde entonces. Llegadas al área desde el cambio: {box_after}.",
               "{key_player} es el jugador más implicado en ese carril ({key_player_actions} acciones progresivas)."],
    },
    "red_card": {
        "en": ["{player} was sent off in minute {minute}.",
               "{opponent}'s share of completed passes: {share_before}% before, {share_after}% after; share of final-third actions: {territory_before}% before, {territory_after}% after.",
               "{opponent} final-third entries: {entries_before} before, {entries_after} after. {team} high pressures: {press_before} before, {press_after} after, a deeper block."],
        "tr": ["{player}, {minute}. dakikada kırmızı kart gördü.",
               "{opponent} tamamlanan pas payı: %{share_before} → %{share_after}; son üçte birdeki aksiyon payı: %{territory_before} → %{territory_after}.",
               "{opponent} son üçte bir girişleri: {entries_before} → {entries_after}. {team} önde baskı: {press_before} → {press_after}; blok daha geride."],
        "es": ["{player} fue expulsado en el minuto {minute}.",
               "Pases completados de {opponent}: {share_before}% → {share_after}%; acciones en el último tercio: {territory_before}% → {territory_after}%.",
               "Entradas al último tercio de {opponent}: {entries_before} → {entries_after}. Presión alta de {team}: {press_before} → {press_after}; bloque más bajo."],
    },
    "shot_surge": {
        "en": ["{team} have taken {shots_after} shots in the last {window_minutes} minutes, after {shots_before} in the {window_minutes} before (xG in the window: {xg_after})."],
        "tr": ["{team} son {window_minutes} dakikada {shots_after} şut çekti; önceki {window_minutes} dakikada {shots_before} (penceredeki xG: {xg_after})."],
        "es": ["{team} suma {shots_after} tiros en los últimos {window_minutes} minutos, tras {shots_before} en los {window_minutes} anteriores (xG en la ventana: {xg_after})."],
    },
    "momentum_swing": {
        "en": ["Rely momentum for {team} moved from {momentum_before} to {momentum_after} ({short_window}-minute averages).",
               "Last {short_window} minutes: {entries_after} final-third entries, {shots_after} shots, {high_press_after} high pressures, {recoveries_after} recoveries."],
        "tr": ["{team} için Rely momentumu {momentum_before} → {momentum_after} ({short_window} dakikalık ortalamalar).",
               "Son {short_window} dakika: {entries_after} son üçte bir girişi, {shots_after} şut, {high_press_after} önde baskı, {recoveries_after} top kazanımı."],
        "es": ["La inercia Rely de {team} pasó de {momentum_before} a {momentum_after} (medias de {short_window} minutos).",
               "Últimos {short_window} minutos: {entries_after} entradas al último tercio, {shots_after} tiros, {high_press_after} presiones altas, {recoveries_after} recuperaciones."],
    },
    "channel_dominance": {
        "en": ["{channel_entries} of {team}'s {entries_after} final-third entries in the last {window_minutes} minutes came down the {ch} ({share_after}%, up from {share_before}%)."],
        "tr": ["{team} son {window_minutes} dakikadaki {entries_after} son üçte bir girişinin {channel_entries} tanesini {ch} kanaldan yaptı (%{share_before} → %{share_after})."],
        "es": ["{channel_entries} de las {entries_after} entradas al último tercio de {team} en los últimos {window_minutes} minutos fueron por el carril {ch} ({share_before}% → {share_after}%)."],
    },
    "possession_swing": {
        "en": ["{team}'s share of completed passes rose from {share_before}% to {share_after}% between consecutive {window_minutes}-minute windows."],
        "tr": ["{team} tamamlanan pas payı art arda iki {window_minutes} dakikalık pencerede %{share_before} → %{share_after}."],
        "es": ["La cuota de pases completados de {team} subió del {share_before}% al {share_after}% entre dos ventanas de {window_minutes} minutos."],
    },
    "dangerous_sequences": {
        "en": ["{seq_after} {team} sequences reached the box or ended in a shot in the last {danger_window} minutes, after {seq_before} in the {danger_window} before. Box entries: {box_after}."],
        "tr": ["{team} son {danger_window} dakikada {seq_after} atakta ceza sahasına ulaştı ya da şutla bitirdi; önceki {danger_window} dakikada {seq_before}. Ceza sahası girişleri: {box_after}."],
        "es": ["{seq_after} secuencias de {team} llegaron al área o acabaron en tiro en los últimos {danger_window} minutos, tras {seq_before} en los {danger_window} anteriores. Llegadas al área: {box_after}."],
    },
    "goal": {
        "en": ["{player} scores for {team} in minute {minute}."],
        "tr": ["{player}, {minute}. dakikada {team} adına golü attı."],
        "es": ["{player} marca para {team} en el minuto {minute}."],
    },
}

FAN = {
    "sub_shift": {"en": "Since {player_in} came on, {team} keep attacking down the {ch}.",
                  "tr": "{player_in} oyuna girdiğinden beri {team} sürekli {ch} kanaldan geliyor.",
                  "es": "Desde que entró {player_in}, {team} ataca una y otra vez por el carril {ch}."},
    "red_card": {"en": "{team} are down to ten and {opponent} are camped in their half.",
                 "tr": "{team} 10 kişi kaldı, {opponent} rakip yarı sahaya yerleşti.",
                 "es": "{team} se queda con diez y {opponent} vive en su campo."},
    "shot_surge": {"en": "{team} are peppering the goal right now.", "tr": "{team} şu an kaleyi bombalıyor.", "es": "{team} está bombardeando la portería."},
    "momentum_swing": {"en": "The game has tilted towards {team}.", "tr": "Oyun {team} lehine döndü.", "es": "El partido se inclina hacia {team}."},
    "channel_dominance": {"en": "{team} keep finding joy down the {ch}.", "tr": "{team} {ch} kanalda rahat geçiyor.", "es": "{team} encuentra premio una y otra vez por el carril {ch}."},
    "possession_swing": {"en": "{team} have taken the ball off their opponents.", "tr": "{team} topu rakibinden aldı.", "es": "{team} le ha quitado el balón al rival."},
    "dangerous_sequences": {"en": "{team} are knocking on the door again and again.", "tr": "{team} kapıyı tekrar tekrar çalıyor.", "es": "{team} llama a la puerta una y otra vez."},
    "goal": {"en": "{player} scores for {team}!", "tr": "{player} {team} adına sahneye çıktı, gol!", "es": "¡Gol de {player} para {team}!"},
}

REC = {  # (for the moment team, for the opponent)
    "sub_shift": {"en": ("Keep loading the {ch} side and add a runner from midfield; protect the space behind the advanced full-back.",
                         "Shift the block towards the {ch} side and double up on {key_player}."),
                  "tr": ("{ch} kanalı beslemeye devam edin, orta sahadan koşu ekleyin; öne çıkan bekin arkasını koruyun.",
                         "Bloğu {ch} tarafa kaydırın ve {key_player} için ikili kapsama yapın."),
                  "es": ("Seguid cargando el carril {ch} y sumad una llegada desde el medio; proteged la espalda del lateral adelantado.",
                         "Bascular el bloque hacia el carril {ch} y doblar la marca sobre {key_player}.")},
    "red_card": {"en": ("Settle into a compact 4-4-1, defend the box and use direct balls to relieve pressure.",
                        "Stretch the ten men: switch play quickly and attack the wide channels."),
                 "tr": ("Kompakt 4-4-1'e geçin, ceza sahasını savunun, baskıyı uzun toplarla kırın.",
                        "10 kişiyi genişletin: oyunu hızlı çevirin ve kanatlardan yüklenin."),
                 "es": ("Replegarse en un 4-4-1 compacto, defender el área y salir en largo para aliviar.",
                        "Estirar a los diez: cambios de orientación rápidos y ataque por fuera.")},
    "shot_surge": {"en": ("Sustain the pressure: keep numbers around the box for second balls.", "Slow the game down and win the second balls in front of the box."),
                   "tr": ("Baskıyı sürdürün: ikinci toplar için ceza sahası çevresinde sayı bırakın.", "Oyunu yavaşlatın, ceza sahası önündeki ikinci topları kazanın."),
                   "es": ("Mantener la presión: gente alrededor del área para las segundas jugadas.", "Enfriar el partido y ganar las segundas jugadas frente al área.")},
    "momentum_swing": {"en": ("Press while the momentum is high; keep the line up to win the ball early.", "Break the rhythm with longer possessions and a tactical stoppage."),
                       "tr": ("Momentum yüksekken baskı yapın; topu erken kazanmak için hattı yukarıda tutun.", "Daha uzun top hakimiyeti ve taktik bir duraksama ile ritmi bozun."),
                       "es": ("Presionar mientras dure la inercia; línea alta para robar pronto.", "Romper el ritmo con posesiones largas y una pausa táctica.")},
    "channel_dominance": {"en": ("Keep isolating that side, but vary the final ball.", "Shift the block to the {ch} side and get a midfielder to cover."),
                          "tr": ("O tarafı izole etmeye devam edin ama son pası çeşitlendirin.", "Bloğu {ch} tarafa kaydırın, bir orta saha oyuncusunu desteğe gönderin."),
                          "es": ("Seguir aislando ese costado, pero variar el último pase.", "Bascular hacia el carril {ch} y que un mediocentro ayude.")},
    "possession_swing": {"en": ("Use the ball to pin the opponent back and look for switches.", "Compress the centre and press the first pass."),
                         "tr": ("Topla rakibi geriye yaslayın ve oyunu çevirin.", "Merkezi daraltın ve ilk pası baskılayın."),
                         "es": ("Usar el balón para hundir al rival y buscar cambios de orientación.", "Cerrar por dentro y presionar el primer pase.")},
    "dangerous_sequences": {"en": ("Keep committing numbers to the box; the chances are coming.", "Defend the box with more bodies and block crosses at source."),
                            "tr": ("Ceza sahasına sayı göndermeye devam edin; pozisyonlar geliyor.", "Ceza sahasını daha kalabalık savunun, ortaları kaynağında engelleyin."),
                            "es": ("Seguir llegando con gente al área; las ocasiones llegan.", "Defender el área con más hombres y bloquear los centros en origen.")},
    "goal": {"en": ("Manage the next five minutes and keep the shape.", "Respond calmly: rebuild from the back and regain control."),
             "tr": ("Sonraki beş dakikayı yönetin ve düzeni koruyun.", "Sakin tepki verin: geriden yeniden kurun ve kontrolü geri alın."),
             "es": ("Gestionar los próximos cinco minutos y mantener la estructura.", "Responder con calma: salir desde atrás y recuperar el control.")},
}

UI = {
    "en": {"for_team": "For {team}", "talking_point": "Talking point", "stat_to_show": "Stat to show", "what_happened": "What happened",
           "confidence": "Confidence {confidence_pct}%", "also": "Also supported by: {rules}", "window_open": "The after window is still open; numbers will grow.",
           "faded": "The effect has since faded.", "sub": "{player_in} on for {player_out} ({team})", "yellow": "Yellow card: {player} ({team})",
           "red": "Red card: {player} ({team})", "goal_feed": "GOAL {team}: {player}", "unavailable": "AI explanation unavailable; structured intelligence shown.",
           "recap_until": "Recap to {clock}"},
    "tr": {"for_team": "{team} için", "talking_point": "Yayın notu", "stat_to_show": "Gösterilecek istatistik", "what_happened": "Ne oldu",
           "confidence": "Güven %{confidence_pct}", "also": "Destekleyen kurallar: {rules}", "window_open": "Sonrası penceresi hâlâ açık; sayılar artabilir.",
           "faded": "Etki daha sonra azaldı.", "sub": "{player_in}, {player_out} yerine ({team})", "yellow": "Sarı kart: {player} ({team})",
           "red": "Kırmızı kart: {player} ({team})", "goal_feed": "GOL {team}: {player}", "unavailable": "Yapay zekâ açıklaması yok; yapılandırılmış analiz gösteriliyor.",
           "recap_until": "{clock} itibarıyla özet"},
    "es": {"for_team": "Para {team}", "talking_point": "Tema para antena", "stat_to_show": "Dato para mostrar", "what_happened": "Qué pasó",
           "confidence": "Confianza {confidence_pct}%", "also": "También lo respaldan: {rules}", "window_open": "La ventana posterior sigue abierta; las cifras crecerán.",
           "faded": "El efecto se ha diluido después.", "sub": "{player_in} entra por {player_out} ({team})", "yellow": "Amarilla: {player} ({team})",
           "red": "Roja: {player} ({team})", "goal_feed": "GOL {team}: {player}", "unavailable": "Explicación IA no disponible; se muestra la inteligencia estructurada.",
           "recap_until": "Resumen hasta {clock}"},
}

RECAP = {
    "en": {"result": "{home} {home_goals}-{away_goals} {away}", "goals": "Goals: {list}", "no_goals": "No goals.",
           "decisive": "The decisive shift: {title}.", "stats": "Shots {home_shots}-{away_shots}, on target {home_sot}-{away_sot}, pass share {home_poss}%-{away_poss}%, final-third entries {home_entries}-{away_entries}.",
           "key_moments": "Key moments", "coach_intro": "What decided it, and what to take into the next match:",
           "broadcast_intro": "Full time at a synthetic {home} vs {away}.", "fan_win": "{winner} take it!", "fan_draw": "Honours even.",
           "social": "{home} {home_goals}-{away_goals} {away}. {title} #RelyMatchBrain #SyntheticData",
           "ft": "Full time", "partial": "Recap to {clock} (match in progress)"},
    "tr": {"result": "{home} {home_goals}-{away_goals} {away}", "goals": "Goller: {list}", "no_goals": "Gol yok.",
           "decisive": "Belirleyici değişim: {title}.", "stats": "Şut {home_shots}-{away_shots}, isabetli {home_sot}-{away_sot}, pas payı %{home_poss}-%{away_poss}, son üçte bir girişi {home_entries}-{away_entries}.",
           "key_moments": "Kritik anlar", "coach_intro": "Maçı ne belirledi, bir sonraki maça ne taşınmalı:",
           "broadcast_intro": "Sentetik {home} - {away} maçında son düdük.", "fan_win": "{winner} kazandı!", "fan_draw": "Puanlar paylaşıldı.",
           "social": "{home} {home_goals}-{away_goals} {away}. {title} #RelyMatchBrain #SentetikVeri",
           "ft": "Maç sonu", "partial": "{clock} itibarıyla özet (maç sürüyor)"},
    "es": {"result": "{home} {home_goals}-{away_goals} {away}", "goals": "Goles: {list}", "no_goals": "Sin goles.",
           "decisive": "El giro decisivo: {title}.", "stats": "Tiros {home_shots}-{away_shots}, a puerta {home_sot}-{away_sot}, cuota de pases {home_poss}%-{away_poss}%, entradas al último tercio {home_entries}-{away_entries}.",
           "key_moments": "Momentos clave", "coach_intro": "Qué decidió el partido y qué llevarse al siguiente:",
           "broadcast_intro": "Final en el sintético {home} - {away}.", "fan_win": "¡Gana {winner}!", "fan_draw": "Reparto de puntos.",
           "social": "{home} {home_goals}-{away_goals} {away}. {title} #RelyMatchBrain #DatosSintéticos",
           "ft": "Final", "partial": "Resumen hasta {clock} (partido en juego)"},
}

TACTIC = {
    "amplify_3_2_5": {
        "name": {"en": "Amplify: 4-3-3 to 3-2-5 in possession", "tr": "Büyüt: topla oyunda 4-3-3'ten 3-2-5'e", "es": "Potenciar: de 4-3-3 a 3-2-5 con balón"},
        "instruction": {"en": "Right-back steps inside next to the holding midfielder, left-back pushes high, right-sided midfielder attacks the half-space, right winger stays wide.",
                        "tr": "Sağ bek ön liberonun yanına içeri girer, sol bek yükselir, sağ iç orta saha yarı alana koşar, sağ kanat genişlikte kalır.",
                        "es": "El lateral derecho se mete por dentro junto al pivote, el lateral izquierdo sube, el interior derecho ataca el medio espacio y el extremo derecho da amplitud."},
        "risk": {"en": "Rest defence becomes three centre-backs plus two midfielders; a turnover on the left leaves space behind the advanced left-back.",
                 "tr": "Arka güvenlik üç stoper ve iki orta sahaya iner; solda top kaybı öne çıkan sol bekin arkasında boşluk bırakır.",
                 "es": "La defensa de seguridad queda en tres centrales y dos mediocentros; una pérdida por la izquierda deja espacio a la espalda del lateral izquierdo."},
    },
    "hold_4_3_3": {
        "name": {"en": "Hold: keep the 4-3-3", "tr": "Koru: 4-3-3'te kal", "es": "Mantener: seguir en 4-3-3"},
        "instruction": {"en": "Keep the current shape and rely on the wide players for progression.", "tr": "Mevcut yapıyı koruyun, ilerlemeyi kanat oyuncularıyla sağlayın.",
                        "es": "Mantener la estructura actual y progresar a través de los hombres de banda."},
        "risk": {"en": "Less overload on the strong side; the channel advantage may fade as the opponent adjusts.", "tr": "Güçlü tarafta daha az sayısal üstünlük; rakip ayar yaptıkça avantaj azalabilir.",
                 "es": "Menos superioridad en el lado fuerte; la ventaja puede diluirse cuando el rival se ajuste."},
    },
    "counter_5_4_1": {
        "name": {"en": "Counter: opponent drops into 5-4-1", "tr": "Karşı hamle: rakip 5-4-1'e çekilir", "es": "Respuesta: el rival se repliega en 5-4-1"},
        "instruction": {"en": "Opponent's left winger tracks back into a back five to match the overload; one striker stays high.",
                        "tr": "Rakibin sol kanadı beşli savunmaya geri döner; bir forvet önde kalır.",
                        "es": "El extremo izquierdo rival baja a una línea de cinco para igualar la superioridad; un delantero se queda arriba."},
        "risk": {"en": "Fewer outlets for the opponent's counter-attacks; their pressure on the ball drops.", "tr": "Rakibin kontra atak çıkışı azalır; topa baskısı düşer.",
                 "es": "Menos salidas para la contra rival; baja su presión sobre el balón."},
    },
}

WHATIF = {
    "amplify_3_2_5": {"effect": {"en": "Adds a fifth attacker across the front line and a second player in the right half-space.",
                                 "tr": "Ön hatta beşinci bir hücumcu ve sağ yarı alanda ikinci bir oyuncu ekler.",
                                 "es": "Añade un quinto atacante en primera línea y un segundo jugador en el medio espacio derecho."},
                      "advantage": {"en": "Builds on the measured {ch}-channel shift ({share_before}% → {share_after}% of progressive actions).",
                                    "tr": "Ölçülen {ch} kanal kaymasının üzerine kurar (ileri aksiyon payı %{share_before} → %{share_after}).",
                                    "es": "Aprovecha el giro medido hacia el carril {ch} ({share_before}% → {share_after}% de las acciones progresivas)."}},
    "hold_4_3_3": {"effect": {"en": "No structural change; the current pattern continues.", "tr": "Yapısal değişiklik yok; mevcut desen sürer.",
                              "es": "Sin cambio estructural; el patrón actual continúa."},
                   "advantage": {"en": "Keeps rest defence at four plus a holding midfielder.", "tr": "Arka güvenliği dört savunmacı ve bir ön liberoda tutar.",
                                 "es": "Mantiene la defensa de seguridad con cuatro más el pivote."}},
    "counter_5_4_1": {"effect": {"en": "Matches the overload on that side with an extra defender.", "tr": "O taraftaki sayısal üstünlüğü ekstra bir savunmacıyla dengeler.",
                                 "es": "Iguala la superioridad en ese costado con un defensor extra."},
                      "advantage": {"en": "Reduces space for the {ch}-channel progressive actions ({prog_after} since the change).",
                                    "tr": "{ch} kanaldaki ileri aksiyonlar için alanı azaltır (değişiklikten beri {prog_after}).",
                                    "es": "Reduce el espacio para las acciones progresivas por el carril {ch} ({prog_after} desde el cambio)."}},
    "_limitations": {"en": "Event data has no off-ball tracking: positional effects are inferred from on-ball events. No score prediction is made.",
                     "tr": "Olay verisinde topsuz takip yok: pozisyonel etkiler top üzerindeki olaylardan çıkarılır. Skor tahmini yapılmaz.",
                     "es": "Los datos de eventos no incluyen seguimiento sin balón: los efectos posicionales se infieren de acciones con balón. No se predice el marcador."},
}


def fmt(template: str, params: dict) -> str | None:
    """Format a template; returns None if a placeholder is missing or None (the sentence is skipped)."""
    try:
        out = template.format(**params)
    except (KeyError, IndexError, ValueError):
        return None
    return None if "None" in out else out
