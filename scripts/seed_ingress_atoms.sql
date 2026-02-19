-- =============================================================================
-- Add ingress (sign change) atoms for all locales
-- =============================================================================
--
-- This script adds content atoms for ingresses—when planets change zodiac signs.
-- Each sign brings a different flavor to planetary energy.
--
-- Key ingresses and their meanings:
-- - Sun ingress: Season/month change, new focus
-- - Mars ingress: Action style shifts
-- - Venus ingress: Relationship/pleasure style shifts
-- - Mercury ingress: Communication style shifts
--
-- We'll focus on a few key ingresses for each locale.
--
-- =============================================================================

BEGIN;

-- =============================================================================
-- EN locale: Ingress variations
-- =============================================================================

-- Sun enters Aries (Spring Equinox)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_sun_ingress_aries', 'sun_in_aries', '["general", "selfcare"]',
 'The Sun enters Aries: new beginnings, fresh energy, spring awakening. Your personal new year starts now.',
 'The Sun''s ingress into Aries marks the astrological new year—the spring equinox, when day and night balance before light takes over.

This is the cosmic reset: a time to plant seeds, set intentions, and move forward with fresh energy. The next few weeks are ideal for starting what you''ve been planning.',
 'The Sun''s ingress into Aries marks the astrological new year—the spring equinox, when day and night balance before light takes over.

This is the cosmic reset: a time to plant seeds, set intentions, and move forward with fresh energy. The next few weeks are ideal for starting what you''ve been planning.

Whatever you launch now has the wind of spring at its back.',
 'Write down one intention or project you want to start this season, and take the first step today.');

-- Mars enters Scorpio (intense action)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mars_ingress_scorpio', 'mars_in_scorpio', '["general", "work"]',
 'Mars enters Scorpio: action becomes intense, focused, and relentless. Go deep, not wide.',
 'Mars in Scorpio is one of the most powerful placements—action becomes strategic, focused, and emotionally charged. This is not the time for surface-level work; it''s time to dig deep and commit fully.

Use the next few weeks for work that requires intensity, focus, and the willingness to face uncomfortable truths.',
 'Mars in Scorpio is one of the most powerful placements—action becomes strategic, focused, and emotionally charged. This is not the time for surface-level work; it''s time to dig deep and commit fully.

Use the next few weeks for work that requires intensity, focus, and the willingness to face uncomfortable truths.

Pick your battles carefully—Scorpio Mars doesn''t do half-measures.',
 'Choose one deep, meaningful project and commit to it fully for the next few weeks.');

-- Venus enters Taurus (pleasure and stability)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_venus_ingress_taurus', 'venus_in_taurus', '["general", "love", "money"]',
 'Venus enters Taurus: pleasure, sensuality, and stability. Time to enjoy what you have and build what lasts.',
 'Venus in Taurus is Venus at home—pleasure becomes simple, sensual, and grounded. This is a time to slow down and enjoy: good food, physical comfort, nature, and steady affection.

Use the next few weeks to appreciate what you have, invest in long-term security, and reconnect with your senses.',
 'Venus in Taurus is Venus at home—pleasure becomes simple, sensual, and grounded. This is a time to slow down and enjoy: good food, physical comfort, nature, and steady affection.

Use the next few weeks to appreciate what you have, invest in long-term security, and reconnect with your senses.

Luxury doesn''t have to be expensive—it just has to feel good.',
 'Do one thing today that feels indulgent and grounding: good food, a massage, time in nature.');

-- Mercury enters Gemini (fast thinking)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mercury_ingress_gemini', 'mercury_in_gemini', '["general", "work"]',
 'Mercury enters Gemini: thinking speeds up, curiosity peaks, connections multiply. Time for learning and networking.',
 'Mercury in Gemini is Mercury at full speed—thoughts move fast, conversations flow easily, and curiosity is high. This is an excellent time for learning, networking, writing, and exploring new ideas.

Use the next few weeks to connect, communicate, and absorb new information.',
 'Mercury in Gemini is Mercury at full speed—thoughts move fast, conversations flow easily, and curiosity is high. This is an excellent time for learning, networking, writing, and exploring new ideas.

Use the next few weeks to connect, communicate, and absorb new information.

Just watch for scattered energy—Gemini wants to do everything at once.',
 'Start learning one new skill or reach out to one person you want to connect with.');

-- =============================================================================
-- RU locale: Ингрессии (смена знака)
-- =============================================================================

-- Солнце входит в Овен (Весеннее равноденствие)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_sun_ingress_aries', 'sun_in_aries', '["general", "selfcare"]',
 'Солнце входит в Овен: новые начинания, свежая энергия, весеннее пробуждение. Твой личный новый год начинается сейчас.',
 'Вход Солнца в Овен отмечает астрологический новый год—весеннее равноденствие, когда день и ночь балансируют, прежде чем свет возьмёт верх.

Это космическая перезагрузка: время сажать семена, ставить намерения и двигаться вперёд со свежей энергией. Следующие несколько недель идеальны для начала того, что планировал.',
 'Вход Солнца в Овен отмечает астрологический новый год—весеннее равноденствие, когда день и ночь балансируют, прежде чем свет возьмёт верх.

Это космическая перезагрузка: время сажать семена, ставить намерения и двигаться вперёд со свежей энергией. Следующие несколько недель идеальны для начала того, что планировал.

Что бы ты ни запустил сейчас, у него будет ветер весны за спиной.',
 'Запиши одно намерение или проект, который хочешь начать в этом сезоне, и сделай первый шаг сегодня.');

-- Марс входит в Скорпион (интенсивное действие)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_mars_ingress_scorpio', 'mars_in_scorpio', '["general", "work"]',
 'Марс входит в Скорпион: действие становится интенсивным, сфокусированным и неумолимым. Иди вглубь, не вширь.',
 'Марс в Скорпионе — одно из самых мощных положений—действие становится стратегическим, сфокусированным и эмоционально заряженным. Это не время для поверхностной работы; пора копать глубоко и вкладываться полностью.

Используй следующие несколько недель для работы, которая требует интенсивности, фокуса и готовности столкнуться с неудобными истинами.',
 'Марс в Скорпионе — одно из самых мощных положений—действие становится стратегическим, сфокусированным и эмоционально заряженным. Это не время для поверхностной работы; пора копать глубоко и вкладываться полностью.

Используй следующие несколько недель для работы, которая требует интенсивности, фокуса и готовности столкнуться с неудобными истинами.

Выбирай битвы тщательно—Марс в Скорпионе не делает половинчатых мер.',
 'Выбери один глубокий, значимый проект и вложись в него полностью на следующие недели.');

-- Венера входит в Телец (удовольствие и стабильность)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_venus_ingress_taurus', 'venus_in_taurus', '["general", "love", "money"]',
 'Венера входит в Телец: удовольствие, чувственность и стабильность. Время наслаждаться тем, что есть, и строить то, что продлится.',
 'Венера в Тельце — Венера дома—удовольствие становится простым, чувственным и заземлённым. Это время замедлиться и наслаждаться: хорошая еда, физический комфорт, природа и устойчивая привязанность.

Используй следующие несколько недель, чтобы ценить то, что имеешь, инвестировать в долгосрочную безопасность и переподключиться к своим чувствам.',
 'Венера в Тельце — Венера дома—удовольствие становится простым, чувственным и заземлённым. Это время замедлиться и наслаждаться: хорошая еда, физический комфорт, природа и устойчивая привязанность.

Используй следующие несколько недель, чтобы ценить то, что имеешь, инвестировать в долгосрочную безопасность и переподключиться к своим чувствам.

Роскошь не обязательно дорогая—она просто должна чувствоваться хорошо.',
 'Сделай одну вещь сегодня, которая кажется баловством и заземлением: хорошая еда, массаж, время на природе.');

-- Меркурий входит в Близнецы (быстрое мышление)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_mercury_ingress_gemini', 'mercury_in_gemini', '["general", "work"]',
 'Меркурий входит в Близнецы: мышление ускоряется, любопытство на пике, связи множатся. Время для обучения и нетворкинга.',
 'Меркурий в Близнецах — Меркурий на полной скорости—мысли движутся быстро, разговоры текут легко, и любопытство высоко. Это отличное время для обучения, нетворкинга, письма и исследования новых идей.

Используй следующие несколько недель, чтобы соединяться, общаться и впитывать новую информацию.',
 'Меркурий в Близнецах — Меркурий на полной скорости—мысли движутся быстро, разговоры текут легко, и любопытство высоко. Это отличное время для обучения, нетворкинга, письма и исследования новых идей.

Используй следующие несколько недель, чтобы соединяться, общаться и впитывать новую информацию.

Просто следи за рассеянной энергией—Близнецы хотят делать всё сразу.',
 'Начни изучать один новый навык или выйди на связь с одним человеком, с которым хочешь соединиться.');

-- =============================================================================
-- ES locale: Ingresos (cambio de signo)
-- =============================================================================

-- Sol entra en Aries (Equinoccio de primavera)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_sun_ingress_aries', 'sun_in_aries', '["general", "selfcare"]',
 'El Sol entra en Aries: nuevos comienzos, energía fresca, despertar primaveral. Tu año personal comienza ahora.',
 'El ingreso del Sol en Aries marca el año nuevo astrológico—el equinoccio de primavera, cuando el día y la noche se equilibran antes de que la luz tome el control.

Este es el reinicio cósmico: tiempo para plantar semillas, establecer intenciones y avanzar con energía fresca. Las próximas semanas son ideales para comenzar lo que has estado planeando.',
 'El ingreso del Sol en Aries marca el año nuevo astrológico—el equinoccio de primavera, cuando el día y la noche se equilibran antes de que la luz tome el control.

Este es el reinicio cósmico: tiempo para plantar semillas, establecer intenciones y avanzar con energía fresca. Las próximas semanas son ideales para comenzar lo que has estado planeando.

Lo que lances ahora tiene el viento de la primavera a su favor.',
 'Escribe una intención o proyecto que quieras comenzar esta temporada, y da el primer paso hoy.');

-- Marte entra en Escorpio (acción intensa)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_mars_ingress_scorpio', 'mars_in_scorpio', '["general", "work"]',
 'Marte entra en Escorpio: la acción se vuelve intensa, enfocada e implacable. Ve profundo, no amplio.',
 'Marte en Escorpio es uno de los emplazamientos más poderosos—la acción se vuelve estratégica, enfocada y emocionalmente cargada. Este no es el momento para trabajo superficial; es momento de profundizar y comprometerse completamente.

Usa las próximas semanas para trabajo que requiera intensidad, enfoque y disposición para enfrentar verdades incómodas.',
 'Marte en Escorpio es uno de los emplazamientos más poderosos—la acción se vuelve estratégica, enfocada y emocionalmente cargada. Este no es el momento para trabajo superficial; es momento de profundizar y comprometerse completamente.

Usa las próximas semanas para trabajo que requiera intensidad, enfoque y disposición para enfrentar verdades incómodas.

Elige tus batallas con cuidado—Marte en Escorpio no hace medias tintas.',
 'Elige un proyecto profundo y significativo y comprométete completamente con él durante las próximas semanas.');

-- Venus entra en Tauro (placer y estabilidad)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_venus_ingress_taurus', 'venus_in_taurus', '["general", "love", "money"]',
 'Venus entra en Tauro: placer, sensualidad y estabilidad. Tiempo de disfrutar lo que tienes y construir lo que dura.',
 'Venus en Tauro es Venus en casa—el placer se vuelve simple, sensual y fundamentado. Este es un tiempo para ir más despacio y disfrutar: buena comida, comodidad física, naturaleza y afecto constante.

Usa las próximas semanas para apreciar lo que tienes, invertir en seguridad a largo plazo y reconectar con tus sentidos.',
 'Venus en Tauro es Venus en casa—el placer se vuelve simple, sensual y fundamentado. Este es un tiempo para ir más despacio y disfrutar: buena comida, comodidad física, naturaleza y afecto constante.

Usa las próximas semanas para apreciar lo que tienes, invertir en seguridad a largo plazo y reconectar con tus sentidos.

El lujo no tiene que ser caro—solo tiene que sentirse bien.',
 'Haz una cosa hoy que se sienta indulgente y fundamentada: buena comida, un masaje, tiempo en la naturaleza.');

-- Mercurio entra en Géminis (pensamiento rápido)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_mercury_ingress_gemini', 'mercury_in_gemini', '["general", "work"]',
 'Mercurio entra en Géminis: el pensamiento se acelera, la curiosidad alcanza su pico, las conexiones se multiplican. Tiempo para aprender y hacer networking.',
 'Mercurio en Géminis es Mercurio a toda velocidad—los pensamientos se mueven rápido, las conversaciones fluyen fácilmente y la curiosidad es alta. Este es un excelente momento para aprender, hacer networking, escribir y explorar nuevas ideas.

Usa las próximas semanas para conectar, comunicar y absorber nueva información.',
 'Mercurio en Géminis es Mercurio a toda velocidad—los pensamientos se mueven rápido, las conversaciones fluyen fácilmente y la curiosidad es alta. Este es un excelente momento para aprender, hacer networking, escribir y explorar nuevas ideas.

Usa las próximas semanas para conectar, comunicar y absorber nueva información.

Solo cuida la energía dispersa—Géminis quiere hacer todo a la vez.',
 'Comienza a aprender una nueva habilidad o contacta a una persona con la que quieras conectar.');

COMMIT;
