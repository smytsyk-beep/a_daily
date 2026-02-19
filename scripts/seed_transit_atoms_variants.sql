-- =============================================================================
-- Add more variants for popular transits across all locales
-- =============================================================================
--
-- This script adds 2-3 additional variants for the most popular transits
-- to increase variety and avoid repetition in daily digests.
--
-- Target: 3-4 variants for top 10 most common transits
--
-- =============================================================================

BEGIN;

-- =============================================================================
-- EN locale: Add variants for popular transits
-- =============================================================================

-- Venus trine Moon - variant 3 (selfcare + love)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_venus_moon_harmony', 'venus_trine_moon', '["general", "selfcare", "love"]',
 'Your emotional world feels softer today. Good time to connect with yourself and others.',
 'Venus and Moon in harmony soften the emotional landscape. Today is ideal for anything that nourishes your heart: a good conversation, time with loved ones, or simply being gentle with yourself.

If you''ve been running on empty—today is permission to slow down and refill.',
 'Venus and Moon in harmony soften the emotional landscape. Today is ideal for anything that nourishes your heart: a good conversation, time with loved ones, or simply being gentle with yourself.

If you''ve been running on empty—today is permission to slow down and refill.

Small acts of care matter more than usual: a warm bath, a call to a friend, or just sitting quietly with your feelings.',
 'Do one small thing today that feels like emotional self-care.');

-- Mars square Sun - variant 3 (work + health)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mars_sun_push', 'mars_square_sun', '["general", "work", "health"]',
 'Energy is high but so is tension. Channel it into productive action, not conflict.',
 'Mars and Sun create friction today—you have energy, but it comes with impatience and irritability. This is powerful fuel if used well, or exhausting drama if not.

Pick one concrete goal and pour your energy there. Avoid arguments and multitasking—focus wins today.',
 'Mars and Sun create friction today—you have energy, but it comes with impatience and irritability. This is powerful fuel if used well, or exhausting drama if not.

Pick one concrete goal and pour your energy there. Avoid arguments and multitasking—focus wins today.

Physical activity helps: a workout, a walk, or any hands-on task that lets you channel the intensity constructively.',
 'Pick your battle today: one task, one goal, full focus. Close it.');

-- Sun trine Moon - variant 3 (general)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_sun_moon_harmony', 'sun_trine_moon', '["general"]',
 'Today feels balanced—neither pushing nor resisting. Use it for whatever needs gentle attention.',
 'Sun and Moon in harmony create a rare day when you don''t have to choose between what you want and what you feel. Both are aligned, making it easier to move forward without internal conflict.

This is not a day for fireworks—it''s a day for steady, grounded progress.',
 'Sun and Moon in harmony create a rare day when you don''t have to choose between what you want and what you feel. Both are aligned, making it easier to move forward without internal conflict.

This is not a day for fireworks—it''s a day for steady, grounded progress.

Use it for whatever has been waiting: a conversation, a decision, a small step on a big project.',
 'Make one small move today on something that matters to you long-term.');

-- Mercury sextile Venus - variant 3 (love)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mercury_venus_flow', 'mercury_sextile_venus', '["general", "love"]',
 'Communication flows easily today. Perfect for heart-to-heart conversations.',
 'Mercury and Venus align to make words softer and listening easier. If there''s something you''ve been meaning to say—or hear—today is the day.

Misunderstandings clear up faster, and people are more willing to meet you halfway.',
 'Mercury and Venus align to make words softer and listening easier. If there''s something you''ve been meaning to say—or hear—today is the day.

Misunderstandings clear up faster, and people are more willing to meet you halfway.

Use this window for the conversations that matter: with a partner, a friend, or yourself.',
 'Say one thing today you''ve been holding back.');

-- Mars trine Jupiter - variant 3 (general + selfcare)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mars_jupiter_drive', 'mars_trine_jupiter', '["general", "selfcare"]',
 'Energy and optimism combine. Great day to act on something you''ve been planning.',
 'Mars and Jupiter together give you a boost of both energy and confidence. This is one of the most productive transits—when action feels easier and results come faster.

Don''t overthink—just move. Trust that the wind is at your back.',
 'Mars and Jupiter together give you a boost of both energy and confidence. This is one of the most productive transits—when action feels easier and results come faster.

Don''t overthink—just move. Trust that the wind is at your back.

If you''ve been waiting for motivation—this is it. Use it before it passes.',
 'Start one thing today that you''ve been putting off.');

-- Sun conjunct Mercury - variant 3 (work + money)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_sun_mercury_clarity', 'sun_conjunct_mercury', '["general", "work", "money"]',
 'Mental clarity is sharp today. Excellent for decisions, planning, and communication.',
 'Sun and Mercury together sharpen your mind and clarify your priorities. Today is one of the best days for thinking, planning, and making decisions that require precision.

If you''ve been unclear about next steps—today you''ll see them.',
 'Sun and Mercury together sharpen your mind and clarify your priorities. Today is one of the best days for thinking, planning, and making decisions that require precision.

If you''ve been unclear about next steps—today you''ll see them.

Use this clarity for what matters: review your finances, make a plan, or have that strategic conversation.',
 'Write down one decision you''ve been avoiding, and make it today.');

-- Venus conjunct Jupiter - variant 3 (selfcare)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_venus_jupiter_joy', 'venus_conjunct_jupiter', '["general", "selfcare"]',
 'Today feels generous and joyful. Permission to enjoy life without guilt.',
 'Venus and Jupiter together amplify pleasure and ease. This is a rare day when life feels lighter, and you''re allowed to simply enjoy it.

No productivity pressure today—just be present with what feels good.',
 'Venus and Jupiter together amplify pleasure and ease. This is a rare day when life feels lighter, and you''re allowed to simply enjoy it.

No productivity pressure today—just be present with what feels good.

Treat yourself, spend time with people you love, or simply rest without justifying it.',
 'Do one thing today purely for pleasure, with zero guilt.');

-- =============================================================================
-- RU locale: Add variants for popular transits
-- =============================================================================

-- Sun trine Moon - вариант 3 (general)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_sun_moon_harmony', 'sun_trine_moon', '["general"]',
 'Сегодня всё течёт мягко и без сопротивления. Используй это для дел, которые требуют баланса.',
 'Солнце и Луна образуют гармоничный аспект — редкий день, когда твои внутренние потребности и внешние задачи не спорят. Это не день для подвигов, а день для ровного, устойчивого движения.

Если что-то давно ждёт твоего внимания — сегодня хороший момент.',
 'Солнце и Луна образуют гармоничный аспект — редкий день, когда твои внутренние потребности и внешние задачи не спорят. Это не день для подвигов, а день для ровного, устойчивого движения.

Если что-то давно ждёт твоего внимания — сегодня хороший момент.

Используй баланс: сделай один небольшой шаг в сторону важного проекта, или просто отдохни, если это нужнее.',
 'Сделай одну вещь сегодня, которую откладываешь уже давно.');

-- Mercury sextile Venus - вариант 3 (love)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_mercury_venus_flow', 'mercury_sextile_venus', '["general", "love"]',
 'Слова находятся легко, разговоры идут мягко. Хороший день для важных диалогов.',
 'Меркурий и Венера создают лёгкость в общении. Сегодня проще сказать то, что важно, и услышать другого без защитных реакций.

Если есть разговор, который откладывал — сегодня подходящий момент.',
 'Меркурий и Венера создают лёгкость в общении. Сегодня проще сказать то, что важно, и услышать другого без защитных реакций.

Если есть разговор, который откладывал — сегодня подходящий момент.

Люди сегодня более открыты и готовы слушать. Используй это для диалогов, которые имеют значение.',
 'Напиши или позвони одному человеку, с которым хочешь поговорить.');

-- Venus trine Moon - вариант 2 (love)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_venus_moon_harmony', 'venus_trine_moon', '["general", "love"]',
 'Эмоциональный мир сегодня мягче. Хороший день для близости и заботы.',
 'Венера и Луна в гармонии делают эмоциональный фон более мягким и отзывчивым. Сегодня легче быть с собой и с близкими без напряжения.

Если хочется тепла и близости — сегодня хороший день для этого.',
 'Венера и Луна в гармонии делают эмоциональный фон более мягким и отзывчивым. Сегодня легче быть с собой и с близкими без напряжения.

Если хочется тепла и близости — сегодня хороший день для этого.

Позволь себе замедлиться и побыть в контакте с тем, что важно: с собой, с партнёром, с близкими.',
 'Проведи время с тем, кто тебе дорог, без повестки и планов.');

-- Mars square Sun - вариант 3 (health)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_mars_sun_push', 'mars_square_sun', '["general", "health", "selfcare"]',
 'Энергии много, терпения мало. Направь её в физическую активность или конкретную задачу.',
 'Марс и Солнце создают напряжение, которое можно использовать продуктивно — или спустить в конфликты. Выбор за тобой.

Физическая активность помогает: тренировка, прогулка, уборка — что угодно, что позволит телу выпустить накопившееся напряжение.',
 'Марс и Солнце создают напряжение, которое можно использовать продуктивно — или спустить в конфликты. Выбор за тобой.

Физическая активность помогает: тренировка, прогулка, уборка — что угодно, что позволит телу выпустить накопившееся напряжение.

Если чувствуешь раздражение — не действуй сразу. Сначала подвигайся, потом решай.',
 'Сделай что-то физическое сегодня: спорт, прогулка, уборка — на выбор.');

-- =============================================================================
-- ES locale: Add variants for popular transits
-- =============================================================================

-- Sun trine Moon - variante 3 (general)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_sun_moon_harmony', 'sun_trine_moon', '["general"]',
 'Hoy todo fluye suave y sin resistencia. Úsalo para cosas que necesitan equilibrio.',
 'El Sol y la Luna forman un aspecto armonioso—un día raro en que tus necesidades internas y tareas externas no chocan. No es un día para hazañas, sino para avanzar de manera constante y equilibrada.

Si algo ha estado esperando tu atención—hoy es un buen momento.',
 'El Sol y la Luna forman un aspecto armonioso—un día raro en que tus necesidades internas y tareas externas no chocan. No es un día para hazañas, sino para avanzar de manera constante y equilibrada.

Si algo ha estado esperando tu atención—hoy es un buen momento.

Usa el equilibrio: da un paso hacia un proyecto importante, o simplemente descansa si eso es lo que necesitas.',
 'Haz una cosa hoy que has estado posponiendo.');

-- Mercury sextile Venus - variante 2 (love)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_mercury_venus_flow', 'mercury_sextile_venus', '["general", "love"]',
 'Las palabras fluyen fácilmente hoy. Perfecto para conversaciones importantes.',
 'Mercurio y Venus crean facilidad en la comunicación. Hoy es más fácil decir lo importante y escuchar al otro sin defensas.

Si hay una conversación pendiente—hoy es el momento.',
 'Mercurio y Venus crean facilidad en la comunicación. Hoy es más fácil decir lo importante y escuchar al otro sin defensas.

Si hay una conversación pendiente—hoy es el momento.

La gente está más abierta y dispuesta a escuchar hoy. Úsalo para diálogos que importan.',
 'Escribe o llama a alguien con quien quieres hablar.');

-- Venus trine Moon - variante 2 (love)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_venus_moon_harmony', 'venus_trine_moon', '["general", "love"]',
 'El mundo emocional es más suave hoy. Buen día para cercanía y cuidado.',
 'Venus y la Luna en armonía suavizan el tono emocional. Hoy es más fácil estar contigo y con los demás sin tensión.

Si quieres calidez y cercanía—hoy es un buen día para eso.',
 'Venus y la Luna en armonía suavizan el tono emocional. Hoy es más fácil estar contigo y con los demás sin tensión.

Si quieres calidez y cercanía—hoy es un buen día para eso.

Permítete ir más despacio y estar en contacto con lo que importa: contigo, con tu pareja, con gente cercana.',
 'Pasa tiempo con alguien importante para ti, sin agenda ni planes.');

-- Mars square Sun - variante 2 (health)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_mars_sun_push', 'mars_square_sun', '["general", "health", "selfcare"]',
 'Mucha energía, poca paciencia. Canalízala en actividad física o una tarea concreta.',
 'Marte y el Sol crean tensión que puedes usar productivamente—o gastar en conflictos. Tú decides.

La actividad física ayuda: ejercicio, caminar, limpiar—lo que sea que permita a tu cuerpo liberar la tensión acumulada.',
 'Marte y el Sol crean tensión que puedes usar productivamente—o gastar en conflictos. Tú decides.

La actividad física ayuda: ejercicio, caminar, limpiar—lo que sea que permita a tu cuerpo liberar la tensión acumulada.

Si sientes irritación—no actúes de inmediato. Primero muévete, luego decide.',
 'Haz algo físico hoy: deporte, caminar, limpiar—lo que prefieras.');

COMMIT;
