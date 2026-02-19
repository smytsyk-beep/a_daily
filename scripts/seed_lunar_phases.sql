-- =============================================================================
-- Add lunar phase atoms for all locales
-- =============================================================================
--
-- This script adds content atoms for the major lunar phases.
-- The Moon's cycle offers natural timing guidance:
-- - New Moon: New beginnings, intention setting, planting seeds
-- - Waxing Moon: Building, growing, taking action
-- - Full Moon: Culmination, completion, release, celebration
-- - Waning Moon: Letting go, rest, reflection, clearing
--
-- =============================================================================

BEGIN;

-- =============================================================================
-- EN locale: Lunar phase atoms
-- =============================================================================

-- New Moon - new beginnings
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_new_moon', 'new_moon', '["general", "selfcare"]',
 'New Moon: the perfect time to set intentions and plant seeds. Start something new.',
 'The New Moon marks a fresh start—a cosmic reset when the Moon is invisible and everything feels quiet and possible. This is the best time of the month to set intentions, start new projects, or commit to something you want to grow.

Use this window (the day of the New Moon plus 2-3 days after) to plant seeds, literal or metaphorical.',
 'The New Moon marks a fresh start—a cosmic reset when the Moon is invisible and everything feels quiet and possible. This is the best time of the month to set intentions, start new projects, or commit to something you want to grow.

Use this window (the day of the New Moon plus 2-3 days after) to plant seeds, literal or metaphorical.

Whatever you begin now has the full lunar cycle ahead to grow.',
 'Write down one intention or project you want to start this lunar cycle, and take the first step today.');

-- Full Moon - culmination and release
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_full_moon', 'full_moon', '["general", "selfcare"]',
 'Full Moon: time for culmination, completion, and letting go. Celebrate what''s done, release what''s not working.',
 'The Full Moon is the peak of the lunar cycle—when everything comes to light, emotions intensify, and things reach completion. This is the time to celebrate achievements, finish projects, and let go of what no longer serves you.

Use this window (the day of the Full Moon plus 2-3 days after) to acknowledge what''s complete and release what you''re ready to leave behind.',
 'The Full Moon is the peak of the lunar cycle—when everything comes to light, emotions intensify, and things reach completion. This is the time to celebrate achievements, finish projects, and let go of what no longer serves you.

Use this window (the day of the Full Moon plus 2-3 days after) to acknowledge what''s complete and release what you''re ready to leave behind.

Full Moons can be intense—honor your feelings, but don''t make big decisions in the heat of the moment.',
 'Write down one thing you''re ready to let go of, and perform a simple release ritual (burn the paper, delete the file, etc.).');

-- Waxing Moon - building momentum
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_waxing_moon', 'waxing_moon', '["general", "work"]',
 'Waxing Moon: momentum builds, energy rises. Time to take action on what you started.',
 'The Waxing Moon (from New to Full) is the growth phase—when energy builds, momentum increases, and action feels easier. This is the best time to work on projects, push forward on goals, and make things happen.

Use this two-week window to move, build, and grow. Save rest for the Waning phase.',
 'The Waxing Moon (from New to Full) is the growth phase—when energy builds, momentum increases, and action feels easier. This is the best time to work on projects, push forward on goals, and make things happen.

Use this two-week window to move, build, and grow. Save rest for the Waning phase.

The closer you get to the Full Moon, the more energy you''ll have—use it wisely.',
 'Take one concrete action today on a project or goal that you set at the New Moon.');

-- Waning Moon - rest and release
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_waning_moon', 'waning_moon', '["general", "selfcare"]',
 'Waning Moon: energy fades, rest deepens. Time to let go, reflect, and restore.',
 'The Waning Moon (from Full to New) is the release phase—when energy naturally dips, reflection deepens, and it''s easier to let things go. This is the time to rest, clear out what''s not working, and prepare for the next cycle.

Use this two-week window to slow down, clean up, and release. Save launching for the Waxing phase.',
 'The Waning Moon (from Full to New) is the release phase—when energy naturally dips, reflection deepens, and it''s easier to let things go. This is the time to rest, clear out what''s not working, and prepare for the next cycle.

Use this two-week window to slow down, clean up, and release. Save launching for the Waxing phase.

The closer you get to the New Moon, the quieter things feel—honor that.',
 'Identify one thing in your life that''s ready to end or change, and take one step to release it.');

-- =============================================================================
-- RU locale: Лунные фазы
-- =============================================================================

-- Новолуние - новые начинания
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_new_moon', 'new_moon', '["general", "selfcare"]',
 'Новолуние: идеальное время, чтобы ставить намерения и сажать семена. Начни что-то новое.',
 'Новолуние отмечает свежий старт—космический сброс, когда Луна невидима и всё кажется тихим и возможным. Это лучшее время месяца, чтобы ставить намерения, начинать новые проекты или взять на себя обязательство к тому, что хочешь вырастить.

Используй это окно (день Новолуния плюс 2-3 дня после), чтобы посадить семена, буквальные или метафорические.',
 'Новолуние отмечает свежий старт—космический сброс, когда Луна невидима и всё кажется тихим и возможным. Это лучшее время месяца, чтобы ставить намерения, начинать новые проекты или взять на себя обязательство к тому, что хочешь вырастить.

Используй это окно (день Новолуния плюс 2-3 дня после), чтобы посадить семена, буквальные или метафорические.

Что бы ты ни начал сейчас, у этого есть полный лунный цикл впереди, чтобы вырасти.',
 'Запиши одно намерение или проект, который хочешь начать в этом лунном цикле, и сделай первый шаг сегодня.');

-- Полнолуние - кульминация и освобождение
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_full_moon', 'full_moon', '["general", "selfcare"]',
 'Полнолуние: время для кульминации, завершения и отпускания. Отпразднуй то, что сделано, отпусти то, что не работает.',
 'Полнолуние — пик лунного цикла—когда всё выходит на свет, эмоции усиливаются, и вещи достигают завершения. Это время, чтобы отмечать достижения, завершать проекты и отпускать то, что больше не служит тебе.

Используй это окно (день Полнолуния плюс 2-3 дня после), чтобы признать то, что завершено, и отпустить то, что готов оставить позади.',
 'Полнолуние — пик лунного цикла—когда всё выходит на свет, эмоции усиливаются, и вещи достигают завершения. Это время, чтобы отмечать достижения, завершать проекты и отпускать то, что больше не служит тебе.

Используй это окно (день Полнолуния плюс 2-3 дня после), чтобы признать то, что завершено, и отпустить то, что готов оставить позади.

Полнолуния могут быть интенсивными—уважай свои чувства, но не принимай больших решений в жару момента.',
 'Запиши одну вещь, которую готов отпустить, и проведи простой ритуал освобождения (сожги бумагу, удали файл и т.д.).');

-- Растущая Луна - нарастание импульса
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_waxing_moon', 'waxing_moon', '["general", "work"]',
 'Растущая Луна: импульс нарастает, энергия растёт. Время действовать на том, что начал.',
 'Растущая Луна (от Новолуния до Полнолуния) — это фаза роста—когда энергия нарастает, импульс увеличивается, и действие кажется легче. Это лучшее время, чтобы работать над проектами, двигаться вперёд по целям и воплощать вещи.

Используй это двухнедельное окно, чтобы двигаться, строить и расти. Оставь отдых для фазы Убывания.',
 'Растущая Луна (от Новолуния до Полнолуния) — это фаза роста—когда энергия нарастает, импульс увеличивается, и действие кажется легче. Это лучшее время, чтобы работать над проектами, двигаться вперёд по целям и воплощать вещи.

Используй это двухнедельное окно, чтобы двигаться, строить и расти. Оставь отдых для фазы Убывания.

Чем ближе к Полнолунию, тем больше энергии у тебя будет—используй её разумно.',
 'Сделай одно конкретное действие сегодня по проекту или цели, которую поставил в Новолуние.');

-- Убывающая Луна - отдых и освобождение
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_waning_moon', 'waning_moon', '["general", "selfcare"]',
 'Убывающая Луна: энергия угасает, отдых углубляется. Время отпускать, размышлять и восстанавливаться.',
 'Убывающая Луна (от Полнолуния до Новолуния) — это фаза освобождения—когда энергия естественно падает, размышление углубляется, и легче отпускать вещи. Это время, чтобы отдыхать, расчищать то, что не работает, и готовиться к следующему циклу.

Используй это двухнедельное окно, чтобы замедлиться, прибрать и отпустить. Оставь запуски для фазы Роста.',
 'Убывающая Луна (от Полнолуния до Новолуния) — это фаза освобождения—когда энергия естественно падает, размышление углубляется, и легче отпускать вещи. Это время, чтобы отдыхать, расчищать то, что не работает, и готовиться к следующему циклу.

Используй это двухнедельное окно, чтобы замедлиться, прибрать и отпустить. Оставь запуски для фазы Роста.

Чем ближе к Новолунию, тем тише всё становится—уважай это.',
 'Определи одну вещь в своей жизни, которая готова закончиться или измениться, и сделай один шаг, чтобы отпустить её.');

-- =============================================================================
-- ES locale: Fases lunares
-- =============================================================================

-- Luna Nueva - nuevos comienzos
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_new_moon', 'new_moon', '["general", "selfcare"]',
 'Luna Nueva: el momento perfecto para establecer intenciones y plantar semillas. Comienza algo nuevo.',
 'La Luna Nueva marca un nuevo comienzo—un reinicio cósmico cuando la Luna es invisible y todo se siente tranquilo y posible. Este es el mejor momento del mes para establecer intenciones, comenzar nuevos proyectos o comprometerse con algo que quieres que crezca.

Usa esta ventana (el día de la Luna Nueva más 2-3 días después) para plantar semillas, literales o metafóricas.',
 'La Luna Nueva marca un nuevo comienzo—un reinicio cósmico cuando la Luna es invisible y todo se siente tranquilo y posible. Este es el mejor momento del mes para establecer intenciones, comenzar nuevos proyectos o comprometerse con algo que quieres que crezca.

Usa esta ventana (el día de la Luna Nueva más 2-3 días después) para plantar semillas, literales o metafóricas.

Lo que comiences ahora tiene el ciclo lunar completo por delante para crecer.',
 'Escribe una intención o proyecto que quieras comenzar en este ciclo lunar, y da el primer paso hoy.');

-- Luna Llena - culminación y liberación
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_full_moon', 'full_moon', '["general", "selfcare"]',
 'Luna Llena: tiempo de culminación, finalización y dejar ir. Celebra lo hecho, suelta lo que no funciona.',
 'La Luna Llena es el pico del ciclo lunar—cuando todo sale a la luz, las emociones se intensifican y las cosas alcanzan su culminación. Este es el momento para celebrar logros, terminar proyectos y soltar lo que ya no te sirve.

Usa esta ventana (el día de la Luna Llena más 2-3 días después) para reconocer lo que está completo y soltar lo que estás listo para dejar atrás.',
 'La Luna Llena es el pico del ciclo lunar—cuando todo sale a la luz, las emociones se intensifican y las cosas alcanzan su culminación. Este es el momento para celebrar logros, terminar proyectos y soltar lo que ya no te sirve.

Usa esta ventana (el día de la Luna Llena más 2-3 días después) para reconocer lo que está completo y soltar lo que estás listo para dejar atrás.

Las Lunas Llenas pueden ser intensas—honra tus sentimientos, pero no tomes grandes decisiones en el calor del momento.',
 'Escribe una cosa que estés listo para soltar, y realiza un ritual simple de liberación (quema el papel, borra el archivo, etc.).');

-- Luna Creciente - construyendo impulso
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_waxing_moon', 'waxing_moon', '["general", "work"]',
 'Luna Creciente: el impulso crece, la energía sube. Tiempo de tomar acción en lo que comenzaste.',
 'La Luna Creciente (de Nueva a Llena) es la fase de crecimiento—cuando la energía se construye, el impulso aumenta y la acción se siente más fácil. Este es el mejor momento para trabajar en proyectos, avanzar en metas y hacer que las cosas sucedan.

Usa esta ventana de dos semanas para moverte, construir y crecer. Guarda el descanso para la fase Menguante.',
 'La Luna Creciente (de Nueva a Llena) es la fase de crecimiento—cuando la energía se construye, el impulso aumenta y la acción se siente más fácil. Este es el mejor momento para trabajar en proyectos, avanzar en metas y hacer que las cosas sucedan.

Usa esta ventana de dos semanas para moverte, construir y crecer. Guarda el descanso para la fase Menguante.

Cuanto más te acerques a la Luna Llena, más energía tendrás—úsala sabiamente.',
 'Toma una acción concreta hoy en un proyecto o meta que estableciste en la Luna Nueva.');

-- Luna Menguante - descanso y liberación
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_waning_moon', 'waning_moon', '["general", "selfcare"]',
 'Luna Menguante: la energía se desvanece, el descanso profundiza. Tiempo de soltar, reflexionar y restaurar.',
 'La Luna Menguante (de Llena a Nueva) es la fase de liberación—cuando la energía naturalmente disminuye, la reflexión profundiza y es más fácil dejar ir las cosas. Este es el momento para descansar, limpiar lo que no funciona y prepararse para el próximo ciclo.

Usa esta ventana de dos semanas para ir más despacio, limpiar y soltar. Guarda los lanzamientos para la fase Creciente.',
 'La Luna Menguante (de Llena a Nueva) es la fase de liberación—cuando la energía naturalmente disminuye, la reflexión profundiza y es más fácil dejar ir las cosas. Este es el momento para descansar, limpiar lo que no funciona y prepararse para el próximo ciclo.

Usa esta ventana de dos semanas para ir más despacio, limpiar y soltar. Guarda los lanzamientos para la fase Creciente.

Cuanto más te acerques a la Luna Nueva, más tranquilo se siente todo—honra eso.',
 'Identifica una cosa en tu vida que esté lista para terminar o cambiar, y da un paso para soltarla.');

COMMIT;
