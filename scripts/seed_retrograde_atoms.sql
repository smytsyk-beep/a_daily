-- =============================================================================
-- Add retrograde variations for transit atoms
-- =============================================================================
--
-- This script adds content atoms for retrograde (Rx) periods.
-- Retrograde motion appears when a planet seems to move backward from Earth's perspective.
--
-- Key retrogrades and their themes:
-- - Mercury Rx: Communication, tech, travel issues; review and revise
-- - Venus Rx: Relationship review, values reassessment, past connections resurface
-- - Mars Rx: Energy dips, frustration, rework rather than launch
-- - Jupiter Rx: Internal growth, philosophical review
-- - Saturn Rx: Structure review, facing old responsibilities
--
-- =============================================================================

BEGIN;

-- =============================================================================
-- EN locale: Retrograde variations
-- =============================================================================

-- Mercury Retrograde - general
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mercury_rx', 'mercury_retrograde', '["general", "work"]',
 'Mercury is retrograde: slow down, review, and double-check. Not the best time for new launches.',
 'Mercury retrograde is the classic "review, don''t launch" period. Communication gets messy, tech breaks, travel plans shift, and misunderstandings multiply.

This isn''t a curse—it''s a forced pause to revisit, revise, and rethink. Use it to clean up old projects, fix what''s broken, and reconnect with people you''ve lost touch with.',
 'Mercury retrograde is the classic "review, don''t launch" period. Communication gets messy, tech breaks, travel plans shift, and misunderstandings multiply.

This isn''t a curse—it''s a forced pause to revisit, revise, and rethink. Use it to clean up old projects, fix what''s broken, and reconnect with people you''ve lost touch with.

If you must move forward—triple-check everything, keep backup plans, and stay flexible.',
 'Revisit one unfinished project or conversation from the past, and close it properly.');

-- Venus Retrograde - relationships
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_venus_rx', 'venus_retrograde', '["general", "love"]',
 'Venus is retrograde: relationships and values are up for review. Past people may resurface.',
 'Venus retrograde is a period of emotional reconsideration. Old relationships, past feelings, and questions about what you truly value come back to the surface.

This is not the time to start new relationships or make big financial moves—it''s time to review, reassess, and sometimes revisit what you thought was over.',
 'Venus retrograde is a period of emotional reconsideration. Old relationships, past feelings, and questions about what you truly value come back to the surface.

This is not the time to start new relationships or make big financial moves—it''s time to review, reassess, and sometimes revisit what you thought was over.

If an ex reaches out—don''t rush. If you''re questioning a relationship—sit with it. The retrograde will pass, and you''ll see more clearly.',
 'Reflect on one relationship or value that''s been on your mind, and journal about it.');

-- Mars Retrograde - energy and action
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mars_rx', 'mars_retrograde', '["general", "work", "health"]',
 'Mars is retrograde: energy dips, progress slows. Rework and refine, don''t launch new projects.',
 'Mars retrograde feels like driving with the handbrake on. You have ideas and goals, but momentum is low, obstacles multiply, and pushing harder just creates frustration.

This is a period for reworking, refining, and building strength internally—not for launching, competing, or forcing your way forward.',
 'Mars retrograde feels like driving with the handbrake on. You have ideas and goals, but momentum is low, obstacles multiply, and pushing harder just creates frustration.

This is a period for reworking, refining, and building strength internally—not for launching, competing, or forcing your way forward.

Use this time to fix what''s broken, train your skills, and prepare for when Mars goes direct—then you''ll have the fuel to move.',
 'Identify one area where you''ve been forcing progress, and shift to refining instead.');

-- Jupiter Retrograde - philosophy and beliefs
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_jupiter_rx', 'jupiter_retrograde', '["general", "learning"]',
 'Jupiter is retrograde: external growth pauses, internal wisdom grows. Time to reflect on beliefs.',
 'Jupiter retrograde shifts growth from outward to inward. External opportunities may slow down, but internal understanding deepens.

This is a period to question what you believe, why you believe it, and whether those beliefs still serve you.',
 'Jupiter retrograde shifts growth from outward to inward. External opportunities may slow down, but internal understanding deepens.

This is a period to question what you believe, why you believe it, and whether those beliefs still serve you.

Use this time for learning, reflection, and philosophical inquiry—not for expanding externally.',
 'Ask yourself one big question about your beliefs or direction, and sit with it.');

-- Saturn Retrograde - structure and responsibility
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_saturn_rx', 'saturn_retrograde', '["general", "work"]',
 'Saturn is retrograde: old structures and responsibilities come back for review. Face what you avoided.',
 'Saturn retrograde brings unfinished business back to the surface—old responsibilities, unfaced fears, structures that need rebuilding.

This is not a comfortable period, but it''s necessary. What you fix now will hold when Saturn goes direct.',
 'Saturn retrograde brings unfinished business back to the surface—old responsibilities, unfaced fears, structures that need rebuilding.

This is not a comfortable period, but it''s necessary. What you fix now will hold when Saturn goes direct.

Use this time to address what you''ve been avoiding, rebuild what''s shaky, and face your limitations honestly.',
 'Write down one responsibility or fear you''ve been avoiding, and take one step toward facing it.');

-- =============================================================================
-- RU locale: Ретроградные вариации
-- =============================================================================

-- Меркурий ретроградный - общее
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_mercury_rx', 'mercury_retrograde', '["general", "work"]',
 'Меркурий ретроградный: замедлись, пересмотри, перепроверь. Не лучшее время для новых запусков.',
 'Ретроградный Меркурий — классический период "пересмотри, не запускай". Общение путается, техника ломается, планы путешествий меняются, а недопонимания множатся.

Это не проклятие—это принудительная пауза, чтобы пересмотреть, исправить и переосмыслить. Используй его, чтобы прибрать старые проекты, починить что сломано, и возобновить связь с людьми, с которыми потерял контакт.',
 'Ретроградный Меркурий — классический период "пересмотри, не запускай". Общение путается, техника ломается, планы путешествий меняются, а недопонимания множатся.

Это не проклятие—это принудительная пауза, чтобы пересмотреть, исправить и переосмыслить. Используй его, чтобы прибрать старые проекты, починить что сломано, и возобновить связь с людьми, с которыми потерял контакт.

Если нужно двигаться вперёд—перепроверяй всё трижды, держи запасные планы и оставайся гибким.',
 'Вернись к одному незавершённому проекту или разговору из прошлого и закрой его правильно.');

-- Венера ретроградная - отношения
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_venus_rx', 'venus_retrograde', '["general", "love"]',
 'Венера ретроградная: отношения и ценности на пересмотре. Люди из прошлого могут всплыть.',
 'Ретроградная Венера — период эмоционального пересмотра. Старые отношения, прошлые чувства и вопросы о том, что ты действительно ценишь, возвращаются на поверхность.

Это не время начинать новые отношения или делать большие финансовые шаги—время пересматривать, переоценивать и иногда возвращаться к тому, что считал законченным.',
 'Ретроградная Венера — период эмоционального пересмотра. Старые отношения, прошлые чувства и вопросы о том, что ты действительно ценишь, возвращаются на поверхность.

Это не время начинать новые отношения или делать большие финансовые шаги—время пересматривать, переоценивать и иногда возвращаться к тому, что считал законченным.

Если бывший выходит на связь—не спеши. Если сомневаешься в отношениях—посиди с этим. Ретроград пройдёт, и ты увидишь яснее.',
 'Поразмышляй об одних отношениях или ценности, которые у тебя на уме, и запиши мысли.');

-- Марс ретроградный - энергия и действие
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_mars_rx', 'mars_retrograde', '["general", "work", "health"]',
 'Марс ретроградный: энергия падает, прогресс замедляется. Переделывай и улучшай, не запускай новое.',
 'Ретроградный Марс ощущается как езда с ручным тормозом. У тебя есть идеи и цели, но импульс низкий, препятствия множатся, а толкание сильнее создаёт только фрустрацию.

Это период для переделки, доработки и внутреннего укрепления—не для запусков, соревнований или прорыва вперёд.',
 'Ретроградный Марс ощущается как езда с ручным тормозом. У тебя есть идеи и цели, но импульс низкий, препятствия множатся, а толкание сильнее создаёт только фрустрацию.

Это период для переделки, доработки и внутреннего укрепления—не для запусков, соревнований или прорыва вперёд.

Используй это время, чтобы починить что сломано, тренировать навыки и готовиться к тому, когда Марс пойдёт прямо—тогда у тебя будет топливо для движения.',
 'Определи одну область, где ты толкал прогресс, и перейди к доработке вместо этого.');

-- Юпитер ретроградный - философия и убеждения
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_jupiter_rx', 'jupiter_retrograde', '["general", "learning"]',
 'Юпитер ретроградный: внешний рост останавливается, внутренняя мудрость растёт. Время для размышления о убеждениях.',
 'Ретроградный Юпитер смещает рост с внешнего на внутреннее. Внешние возможности могут замедлиться, но внутреннее понимание углубляется.

Это период, чтобы задать вопросы о том, во что ты веришь, почему веришь и служат ли эти убеждения тебе всё ещё.',
 'Ретроградный Юпитер смещает рост с внешнего на внутреннее. Внешние возможности могут замедлиться, но внутреннее понимание углубляется.

Это период, чтобы задать вопросы о том, во что ты веришь, почему веришь и служат ли эти убеждения тебе всё ещё.

Используй это время для учёбы, размышления и философского исследования—не для внешней экспансии.',
 'Задай себе один большой вопрос о своих убеждениях или направлении, и посиди с ним.');

-- Сатурн ретроградный - структура и ответственность
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_saturn_rx', 'saturn_retrograde', '["general", "work"]',
 'Сатурн ретроградный: старые структуры и ответственности возвращаются на пересмотр. Столкнись с тем, что избегал.',
 'Ретроградный Сатурн возвращает незавершённые дела на поверхность—старые ответственности, неустранённые страхи, структуры, которые нуждаются в перестройке.

Это не комфортный период, но он необходим. То, что ты исправишь сейчас, будет держаться, когда Сатурн пойдёт прямо.',
 'Ретроградный Сатурн возвращает незавершённые дела на поверхность—старые ответственности, неустранённые страхи, структуры, которые нуждаются в перестройке.

Это не комфортный период, но он необходим. То, что ты исправишь сейчас, будет держаться, когда Сатурн пойдёт прямо.

Используй это время, чтобы обратиться к тому, что избегал, перестроить то, что шатается, и честно столкнуться со своими ограничениями.',
 'Запиши одну ответственность или страх, которые избегал, и сделай один шаг навстречу им.');

-- =============================================================================
-- ES locale: Variaciones retrógradas
-- =============================================================================

-- Mercurio Retrógrado - general
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_mercury_rx', 'mercury_retrograde', '["general", "work"]',
 'Mercurio está retrógrado: ve más despacio, revisa y verifica dos veces. No es el mejor momento para nuevos lanzamientos.',
 'Mercurio retrógrado es el clásico período de "revisar, no lanzar". La comunicación se enreda, la tecnología falla, los planes de viaje cambian y los malentendidos se multiplican.

Esto no es una maldición—es una pausa forzada para revisar, corregir y repensar. Úsalo para limpiar proyectos antiguos, arreglar lo que está roto y reconectar con personas con las que perdiste contacto.',
 'Mercurio retrógrado es el clásico período de "revisar, no lanzar". La comunicación se enreda, la tecnología falla, los planes de viaje cambian y los malentendidos se multiplican.

Esto no es una maldición—es una pausa forzada para revisar, corregir y repensar. Úsalo para limpiar proyectos antiguos, arreglar lo que está roto y reconectar con personas con las que perdiste contacto.

Si debes avanzar—verifica todo tres veces, mantén planes de respaldo y mantente flexible.',
 'Revisa un proyecto o conversación inconclusa del pasado y ciérralo correctamente.');

-- Venus Retrógrada - relaciones
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_venus_rx', 'venus_retrograde', '["general", "love"]',
 'Venus está retrógrada: relaciones y valores en revisión. Personas del pasado pueden resurgir.',
 'Venus retrógrada es un período de reconsideración emocional. Viejas relaciones, sentimientos pasados y preguntas sobre lo que realmente valoras vuelven a la superficie.

Este no es el momento para comenzar nuevas relaciones o hacer grandes movimientos financieros—es tiempo de revisar, reevaluar y a veces revisitar lo que pensabas que había terminado.',
 'Venus retrógrada es un período de reconsideración emocional. Viejas relaciones, sentimientos pasados y preguntas sobre lo que realmente valoras vuelven a la superficie.

Este no es el momento para comenzar nuevas relaciones o hacer grandes movimientos financieros—es tiempo de revisar, reevaluar y a veces revisitar lo que pensabas que había terminado.

Si un ex se contacta—no te apresures. Si estás cuestionando una relación—siéntate con eso. El retrógrado pasará y verás más claro.',
 'Reflexiona sobre una relación o valor que ha estado en tu mente, y escribe sobre ello.');

-- Marte Retrógrado - energía y acción
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_mars_rx', 'mars_retrograde', '["general", "work", "health"]',
 'Marte está retrógrado: la energía baja, el progreso se ralentiza. Retrabaja y refina, no lances nuevos proyectos.',
 'Marte retrógrado se siente como conducir con el freno de mano puesto. Tienes ideas y metas, pero el impulso es bajo, los obstáculos se multiplican y empujar más solo crea frustración.

Este es un período para retrabajar, refinar y construir fuerza internamente—no para lanzar, competir o forzar tu camino hacia adelante.',
 'Marte retrógrado se siente como conducir con el freno de mano puesto. Tienes ideas y metas, pero el impulso es bajo, los obstáculos se multiplican y empujar más solo crea frustración.

Este es un período para retrabajar, refinar y construir fuerza internamente—no para lanzar, competir o forzar tu camino hacia adelante.

Usa este tiempo para arreglar lo que está roto, entrenar tus habilidades y prepararte para cuando Marte avance directamente—entonces tendrás el combustible para moverte.',
 'Identifica un área donde has estado forzando el progreso, y cambia a refinar en su lugar.');

-- Júpiter Retrógrado - filosofía y creencias
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_jupiter_rx', 'jupiter_retrograde', '["general", "learning"]',
 'Júpiter está retrógrado: el crecimiento externo pausa, la sabiduría interna crece. Tiempo para reflexionar sobre creencias.',
 'Júpiter retrógrado cambia el crecimiento de externo a interno. Las oportunidades externas pueden ralentizarse, pero la comprensión interna se profundiza.

Este es un período para cuestionar lo que crees, por qué lo crees y si esas creencias aún te sirven.',
 'Júpiter retrógrado cambia el crecimiento de externo a interno. Las oportunidades externas pueden ralentizarse, pero la comprensión interna se profundiza.

Este es un período para cuestionar lo que crees, por qué lo crees y si esas creencias aún te sirven.

Usa este tiempo para aprender, reflexionar e indagar filosóficamente—no para expandir externamente.',
 'Hazte una gran pregunta sobre tus creencias o dirección, y siéntate con ella.');

-- Saturno Retrógrado - estructura y responsabilidad
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_saturn_rx', 'saturn_retrograde', '["general", "work"]',
 'Saturno está retrógrado: viejas estructuras y responsabilidades vuelven para revisión. Enfrenta lo que evitaste.',
 'Saturno retrógrado trae asuntos pendientes de vuelta a la superficie—viejas responsabilidades, miedos no enfrentados, estructuras que necesitan reconstrucción.

Este no es un período cómodo, pero es necesario. Lo que arregles ahora se mantendrá cuando Saturno avance directamente.',
 'Saturno retrógrado trae asuntos pendientes de vuelta a la superficie—viejas responsabilidades, miedos no enfrentados, estructuras que necesitan reconstrucción.

Este no es un período cómodo, pero es necesario. Lo que arregles ahora se mantendrá cuando Saturno avance directamente.

Usa este tiempo para abordar lo que has estado evitando, reconstruir lo que está tambaleante y enfrentar tus limitaciones honestamente.',
 'Escribe una responsabilidad o miedo que has estado evitando, y da un paso para enfrentarlo.');

COMMIT;
