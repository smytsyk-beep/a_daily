-- =============================================================================
-- Add seasonal variations for transit atoms
-- =============================================================================
-- 
-- This script adds content atoms that vary based on seasonal context:
-- - Spring (Mar-May): New beginnings, growth, fresh energy
-- - Summer (Jun-Aug): Peak energy, action, fullness
-- - Autumn (Sep-Nov): Harvest, reflection, letting go
-- - Winter (Dec-Feb): Rest, introspection, preparation
--
-- Seasons are based on Northern Hemisphere.
-- For Southern Hemisphere users, system should invert the seasons.
--
-- =============================================================================

BEGIN;

-- =============================================================================
-- EN locale: Seasonal variations
-- =============================================================================

-- Sun conjunct Mercury - Spring (new ideas, fresh start)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_sun_mercury_clarity_spring', 'sun_conjunct_mercury_spring', '["general", "work"]',
 'Spring clarity: new ideas are easier to see and act on. Perfect for fresh starts.',
 'The Sun and Mercury align as spring energy supports new beginnings. Your mind is clear, and the season''s momentum helps you launch what you''ve been planning.

This is the ideal time to start projects, commit to new plans, or simply think fresh thoughts.',
 'The Sun and Mercury align as spring energy supports new beginnings. Your mind is clear, and the season''s momentum helps you launch what you''ve been planning.

This is the ideal time to start projects, commit to new plans, or simply think fresh thoughts.

Let spring''s forward energy carry you—don''t overthink, just begin.',
 'Start one new thing today that you''ve been planning for weeks.');

-- Mars trine Jupiter - Summer (peak action, maximum output)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mars_jupiter_drive_summer', 'mars_trine_jupiter_summer', '["general", "work"]',
 'Summer power: energy and confidence are at their peak. Time to go big.',
 'Mars and Jupiter combine during summer''s peak energy. You have both the drive and the confidence, and the season supports maximum output.

This is the time to push hard on what matters—the conditions won''t get better than this.',
 'Mars and Jupiter combine during summer''s peak energy. You have both the drive and the confidence, and the season supports maximum output.

This is the time to push hard on what matters—the conditions won''t get better than this.

Summer is short—use this window for your biggest moves.',
 'Commit to one ambitious goal today and move on it with full energy.');

-- Venus opposite Saturn - Autumn (relationship reality check)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_venus_saturn_reality_autumn', 'venus_opposite_saturn_autumn', '["general", "love"]',
 'Autumn sobriety: relationships show what''s real. Time to harvest or let go.',
 'Venus opposite Saturn during autumn brings emotional realism. Just as nature lets go of what it doesn''t need, you''re asked to see relationships clearly—what''s worth keeping, what needs work, and what needs to end.

This isn''t cruel, it''s seasonal wisdom.',
 'Venus opposite Saturn during autumn brings emotional realism. Just as nature lets go of what it doesn''t need, you''re asked to see relationships clearly—what''s worth keeping, what needs work, and what needs to end.

This isn''t cruel, it''s seasonal wisdom.

Use autumn''s natural rhythm of release to help you make hard but necessary choices.',
 'Write down one truth about a relationship that you''ve been avoiding, and decide what to do about it.');

-- Sun trine Moon - Winter (inner-outer balance, rest)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_sun_moon_harmony_winter', 'sun_trine_moon_winter', '["general", "selfcare"]',
 'Winter balance: inner needs and outer duties align. Good day for quiet progress or rest.',
 'The Sun and Moon harmonize during winter''s quiet season. This is a day of gentle balance—neither pushing nor resisting, just being.

Use winter''s natural slowness to move at a sustainable pace, or simply rest without guilt.',
 'The Sun and Moon harmonize during winter''s quiet season. This is a day of gentle balance—neither pushing nor resisting, just being.

Use winter''s natural slowness to move at a sustainable pace, or simply rest without guilt.

Let the season teach you that rest is not wasted time—it''s preparation for spring.',
 'Do one small thing today that honors both your goals and your need for rest.');

-- =============================================================================
-- RU locale: Сезонные вариации
-- =============================================================================

-- Солнце соединение Меркурий - Весна (новые идеи, свежий старт)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_sun_mercury_clarity_spring', 'sun_conjunct_mercury_spring', '["general", "work"]',
 'Весенняя ясность: новые идеи легче увидеть и воплотить. Идеально для свежих стартов.',
 'Солнце и Меркурий выравниваются, а весенняя энергия поддерживает новые начинания. Твой ум чист, и импульс сезона помогает запустить то, что планировал.

Это идеальное время, чтобы начать проекты, взять на себя обязательства по новым планам или просто думать свежими мыслями.',
 'Солнце и Меркурий выравниваются, а весенняя энергия поддерживает новые начинания. Твой ум чист, и импульс сезона помогает запустить то, что планировал.

Это идеальное время, чтобы начать проекты, взять на себя обязательства по новым планам или просто думать свежими мыслями.

Позволь весенней энергии движения нести тебя—не думай слишком много, просто начинай.',
 'Начни одну новую вещь сегодня, которую планировал неделями.');

-- Марс трин Юпитер - Лето (пик действия, максимальная отдача)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_mars_jupiter_drive_summer', 'mars_trine_jupiter_summer', '["general", "work"]',
 'Летняя сила: энергия и уверенность на пике. Время для больших дел.',
 'Марс и Юпитер объединяются во время пика летней энергии. У тебя есть и драйв, и уверенность, и сезон поддерживает максимальную отдачу.

Это время, чтобы напрячься на том, что важно—условия не станут лучше.',
 'Марс и Юпитер объединяются во время пика летней энергии. У тебя есть и драйв, и уверенность, и сезон поддерживает максимальную отдачу.

Это время, чтобы напрячься на том, что важно—условия не станут лучше.

Лето короткое—используй это окно для своих самых больших шагов.',
 'Возьми на себя одну амбициозную цель сегодня и двигайся на неё с полной энергией.');

-- Венера оппозиция Сатурн - Осень (проверка реальностью отношений)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_venus_saturn_reality_autumn', 'venus_opposite_saturn_autumn', '["general", "love"]',
 'Осенняя трезвость: отношения показывают, что реально. Время собирать урожай или отпускать.',
 'Венера оппозиция Сатурн осенью приносит эмоциональный реализм. Так же, как природа отпускает то, что ей не нужно, тебе предлагается ясно увидеть отношения—что стоит сохранить, что нуждается в работе, а что нужно закончить.

Это не жестокость, это сезонная мудрость.',
 'Венера оппозиция Сатурн осенью приносит эмоциональный реализм. Так же, как природа отпускает то, что ей не нужно, тебе предлагается ясно увидеть отношения—что стоит сохранить, что нуждается в работе, а что нужно закончить.

Это не жестокость, это сезонная мудрость.

Используй естественный ритм отпускания осени, чтобы помочь себе сделать трудный, но необходимый выбор.',
 'Запиши одну правду об отношениях, которую избегал, и реши, что с этим делать.');

-- Солнце трин Луна - Зима (баланс внутреннего и внешнего, отдых)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_sun_moon_harmony_winter', 'sun_trine_moon_winter', '["general", "selfcare"]',
 'Зимний баланс: внутренние потребности и внешние обязанности выравниваются. Хороший день для тихого прогресса или отдыха.',
 'Солнце и Луна гармонизируются в тихий зимний сезон. Это день мягкого баланса—ни толкать, ни сопротивляться, просто быть.

Используй естественную медлительность зимы, чтобы двигаться в устойчивом темпе, или просто отдыхай без чувства вины.',
 'Солнце и Луна гармонизируются в тихий зимний сезон. Это день мягкого баланса—ни толкать, ни сопротивляться, просто быть.

Используй естественную медлительность зимы, чтобы двигаться в устойчивом темпе, или просто отдыхай без чувства вины.

Позволь сезону научить тебя, что отдых—это не потерянное время, а подготовка к весне.',
 'Сделай одну маленькую вещь сегодня, которая уважает и твои цели, и твою потребность в отдыхе.');

-- =============================================================================
-- ES locale: Variaciones estacionales
-- =============================================================================

-- Sol conjunción Mercurio - Primavera (nuevas ideas, inicio fresco)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_sun_mercury_clarity_spring', 'sun_conjunct_mercury_spring', '["general", "work"]',
 'Claridad primaveral: las nuevas ideas son más fáciles de ver y actuar. Perfecto para inicios frescos.',
 'El Sol y Mercurio se alinean mientras la energía primaveral apoya nuevos comienzos. Tu mente está clara, y el impulso de la temporada te ayuda a lanzar lo que has estado planeando.

Este es el momento ideal para comenzar proyectos, comprometerse con nuevos planes o simplemente pensar pensamientos frescos.',
 'El Sol y Mercurio se alinean mientras la energía primaveral apoya nuevos comienzos. Tu mente está clara, y el impulso de la temporada te ayuda a lanzar lo que has estado planeando.

Este es el momento ideal para comenzar proyectos, comprometerse con nuevos planes o simplemente pensar pensamientos frescos.

Deja que la energía de avance de la primavera te lleve—no pienses demasiado, solo comienza.',
 'Comienza una cosa nueva hoy que has estado planeando durante semanas.');

-- Marte trígono Júpiter - Verano (acción máxima, salida máxima)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_mars_jupiter_drive_summer', 'mars_trine_jupiter_summer', '["general", "work"]',
 'Poder veraniego: energía y confianza en su punto máximo. Tiempo de ir a lo grande.',
 'Marte y Júpiter se combinan durante el pico de energía del verano. Tienes tanto el impulso como la confianza, y la temporada apoya la máxima producción.

Este es el momento para esforzarte en lo que importa—las condiciones no serán mejores que esto.',
 'Marte y Júpiter se combinan durante el pico de energía del verano. Tienes tanto el impulso como la confianza, y la temporada apoya la máxima producción.

Este es el momento para esforzarte en lo que importa—las condiciones no serán mejores que esto.

El verano es corto—usa esta ventana para tus movimientos más grandes.',
 'Comprométete con un objetivo ambicioso hoy y avanza con toda tu energía.');

-- Venus opuesto Saturno - Otoño (verificación de realidad en relaciones)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_venus_saturn_reality_autumn', 'venus_opposite_saturn_autumn', '["general", "love"]',
 'Sobriedad otoñal: las relaciones muestran lo real. Tiempo de cosechar o soltar.',
 'Venus opuesto Saturno durante el otoño trae realismo emocional. Así como la naturaleza suelta lo que no necesita, se te pide ver las relaciones claramente—qué vale la pena mantener, qué necesita trabajo y qué necesita terminar.

Esto no es crueldad, es sabiduría estacional.',
 'Venus opuesto Saturno durante el otoño trae realismo emocional. Así como la naturaleza suelta lo que no necesita, se te pide ver las relaciones claramente—qué vale la pena mantener, qué necesita trabajo y qué necesita terminar.

Esto no es crueldad, es sabiduría estacional.

Usa el ritmo natural de liberación del otoño para ayudarte a tomar decisiones difíciles pero necesarias.',
 'Escribe una verdad sobre una relación que has estado evitando, y decide qué hacer al respecto.');

-- Sol trígono Luna - Invierno (balance interno-externo, descanso)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_sun_moon_harmony_winter', 'sun_trine_moon_winter', '["general", "selfcare"]',
 'Balance invernal: necesidades internas y deberes externos se alinean. Buen día para progreso tranquilo o descanso.',
 'El Sol y la Luna armonizan durante la estación tranquila del invierno. Este es un día de balance suave—ni empujar ni resistir, solo ser.

Usa la lentitud natural del invierno para moverte a un ritmo sostenible, o simplemente descansa sin culpa.',
 'El Sol y la Luna armonizan durante la estación tranquila del invierno. Este es un día de balance suave—ni empujar ni resistir, solo ser.

Usa la lentitud natural del invierno para moverte a un ritmo sostenible, o simplemente descansa sin culpa.

Deja que la estación te enseñe que el descanso no es tiempo perdido—es preparación para la primavera.',
 'Haz una cosa pequeña hoy que honre tanto tus metas como tu necesidad de descanso.');

COMMIT;
