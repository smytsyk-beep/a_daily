-- =============================================================================
-- Add house-based transit atoms for all locales
-- =============================================================================
--
-- This script adds content atoms that combine transits with house positions.
-- Houses represent different life areas:
-- - 1st: Self, identity, appearance
-- - 2nd: Money, values, possessions
-- - 3rd: Communication, siblings, short trips
-- - 4th: Home, family, roots
-- - 5th: Creativity, romance, children
-- - 6th: Work, health, daily routines
-- - 7th: Partnerships, relationships
-- - 8th: Transformation, shared resources
-- - 9th: Travel, education, philosophy
-- - 10th: Career, public image, goals
-- - 11th: Friends, community, future
-- - 12th: Spirituality, subconscious, solitude
--
-- =============================================================================

BEGIN;

-- =============================================================================
-- EN locale: House-based transit atoms
-- =============================================================================

-- Sun in 1st house
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, house_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_sun_1h', 'sun_in_1st', '["general", "selfcare"]', '["house_1"]',
 'Your energy and presence are more visible now. Good time to show up and be seen.',
 'When the Sun moves through your 1st house, you naturally become more visible and energized. This is your season—a time to focus on yourself, your goals, and how you present to the world.

Use this period to refresh your image, start new projects, or simply be more assertive about what you want.',
 'When the Sun moves through your 1st house, you naturally become more visible and energized. This is your season—a time to focus on yourself, your goals, and how you present to the world.

Use this period to refresh your image, start new projects, or simply be more assertive about what you want.

It''s your personal new year—set intentions and move on them.',
 'Write down one thing you want to change about how you show up in the world.');

-- Venus in 2nd house
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, house_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_venus_2h', 'venus_in_2nd', '["general", "money"]', '["house_2"]',
 'Money and pleasure are connected now. Good time to attract resources and enjoy what you have.',
 'Venus in your 2nd house brings focus to money, values, and material comfort. This is one of the best times for earning, attracting opportunities, or simply enjoying what you already have.

Treat yourself, negotiate a raise, or review your finances with a focus on abundance, not scarcity.',
 'Venus in your 2nd house brings focus to money, values, and material comfort. This is one of the best times for earning, attracting opportunities, or simply enjoying what you already have.

Treat yourself, negotiate a raise, or review your finances with a focus on abundance, not scarcity.

Your relationship with money is softer now—use it wisely.',
 'Make one move today that increases your financial well-being or enjoyment.');

-- Mars in 6th house
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, house_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mars_6h', 'mars_in_6th', '["general", "work", "health"]', '["house_6"]',
 'Energy goes into work and health routines now. Good time to tackle tasks and build habits.',
 'Mars in your 6th house supercharges your productivity and discipline. You have more energy for work, daily routines, and health improvements—but also more irritation if things feel inefficient.

Use this period to organize your life, build new habits, or push through tasks you''ve been avoiding.',
 'Mars in your 6th house supercharges your productivity and discipline. You have more energy for work, daily routines, and health improvements—but also more irritation if things feel inefficient.

Use this period to organize your life, build new habits, or push through tasks you''ve been avoiding.

Just watch for burnout—Mars pushes hard, but your body has limits.',
 'Pick one habit or routine you want to improve, and commit to it for the next week.');

-- Jupiter in 9th house
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, house_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_jupiter_9h', 'jupiter_in_9th', '["general", "learning"]', '["house_9"]',
 'Your horizons are expanding. Great time for learning, travel, and big-picture thinking.',
 'Jupiter in your 9th house opens doors to new ideas, places, and perspectives. This is one of the best transits for education, travel, or simply expanding your worldview.

Say yes to opportunities that stretch you beyond your usual boundaries.',
 'Jupiter in your 9th house opens doors to new ideas, places, and perspectives. This is one of the best transits for education, travel, or simply expanding your worldview.

Say yes to opportunities that stretch you beyond your usual boundaries.

You''re ready for something bigger—trust that.',
 'Research one topic, place, or skill you''ve been curious about.');

-- Saturn in 10th house
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, house_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_saturn_10h', 'saturn_in_10th', '["general", "work"]', '["house_10"]',
 'Career and public image get serious now. Time to build something solid and lasting.',
 'Saturn in your 10th house brings focus, discipline, and pressure around your career and public role. This is a make-or-break period where hard work pays off, but shortcuts don''t.

Build foundations, take responsibility, and show up consistently. The results will come—but only if you do the work.',
 'Saturn in your 10th house brings focus, discipline, and pressure around your career and public role. This is a make-or-break period where hard work pays off, but shortcuts don''t.

Build foundations, take responsibility, and show up consistently. The results will come—but only if you do the work.

This transit is not easy, but it''s worth it.',
 'Identify one long-term career goal, and take one concrete step toward it today.');

-- =============================================================================
-- RU locale: Атомы по домам
-- =============================================================================

-- Солнце в 1 доме
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, house_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_sun_1h', 'sun_in_1st', '["general", "selfcare"]', '["house_1"]',
 'Твоя энергия и присутствие более заметны сейчас. Хорошее время, чтобы проявить себя.',
 'Когда Солнце проходит через твой 1-й дом, ты естественно становишься более видимым и энергичным. Это твой сезон—время сосредоточиться на себе, своих целях и том, как ты показываешь себя миру.

Используй этот период, чтобы обновить свой образ, начать новые проекты или просто быть более настойчивым в том, чего хочешь.',
 'Когда Солнце проходит через твой 1-й дом, ты естественно становишься более видимым и энергичным. Это твой сезон—время сосредоточиться на себе, своих целях и том, как ты показываешь себя миру.

Используй этот период, чтобы обновить свой образ, начать новые проекты или просто быть более настойчивым в том, чего хочешь.

Это твой личный новый год—ставь намерения и действуй.',
 'Запиши одну вещь, которую хочешь изменить в том, как ты проявляешься в мире.');

-- Венера во 2 доме
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, house_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_venus_2h', 'venus_in_2nd', '["general", "money"]', '["house_2"]',
 'Деньги и удовольствия связаны сейчас. Хорошее время для привлечения ресурсов и наслаждения тем, что есть.',
 'Венера в твоём 2-м доме фокусирует внимание на деньгах, ценностях и материальном комфорте. Это одно из лучших времён для заработка, привлечения возможностей или просто наслаждения тем, что у тебя уже есть.

Побалуй себя, договорись о повышении или пересмотри финансы с фокусом на изобилие, а не на дефицит.',
 'Венера в твоём 2-м доме фокусирует внимание на деньгах, ценностях и материальном комфорте. Это одно из лучших времён для заработка, привлечения возможностей или просто наслаждения тем, что у тебя уже есть.

Побалуй себя, договорись о повышении или пересмотри финансы с фокусом на изобилие, а не на дефицит.

Твои отношения с деньгами сейчас мягче—используй это разумно.',
 'Сделай один шаг сегодня, который увеличит твоё финансовое благополучие или удовольствие.');

-- Марс в 6 доме
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, house_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_mars_6h', 'mars_in_6th', '["general", "work", "health"]', '["house_6"]',
 'Энергия идёт в работу и здоровье сейчас. Хорошее время для задач и построения привычек.',
 'Марс в твоём 6-м доме усиливает продуктивность и дисциплину. У тебя больше энергии для работы, ежедневных рутин и улучшения здоровья—но также больше раздражения, если что-то кажется неэффективным.

Используй этот период, чтобы организовать свою жизнь, построить новые привычки или прорваться через задачи, которые откладывал.',
 'Марс в твоём 6-м доме усиливает продуктивность и дисциплину. У тебя больше энергии для работы, ежедневных рутин и улучшения здоровья—но также больше раздражения, если что-то кажется неэффективным.

Используй этот период, чтобы организовать свою жизь, построить новые привычки или прорваться через задачи, которые откладывал.

Просто следи за выгоранием—Марс толкает сильно, но у тела есть пределы.',
 'Выбери одну привычку или рутину, которую хочешь улучшить, и начни на неделю.');

-- Юпитер в 9 доме
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, house_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_jupiter_9h', 'jupiter_in_9th', '["general", "learning"]', '["house_9"]',
 'Твои горизонты расширяются. Отличное время для учёбы, путешествий и широкого взгляда.',
 'Юпитер в твоём 9-м доме открывает двери к новым идеям, местам и перспективам. Это один из лучших транзитов для образования, путешествий или просто расширения твоего мировоззрения.

Говори "да" возможностям, которые растягивают тебя за пределы обычных границ.',
 'Юпитер в твоём 9-м доме открывает двери к новым идеям, местам и перспективам. Это один из лучших транзитов для образования, путешествий или просто расширения твоего мировоззрения.

Говори "да" возможностям, которые растягивают тебя за пределы обычных границ.

Ты готов к чему-то большему—доверься этому.',
 'Изучи одну тему, место или навык, которые тебе интересны.');

-- Сатурн в 10 доме
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, house_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_saturn_10h', 'saturn_in_10th', '["general", "work"]', '["house_10"]',
 'Карьера и публичный образ становятся серьёзными сейчас. Время строить что-то прочное и долговечное.',
 'Сатурн в твоём 10-м доме приносит фокус, дисциплину и давление вокруг карьеры и публичной роли. Это период "сделать или сломаться", где упорная работа окупается, а короткие пути — нет.

Строй фундаменты, бери ответственность и появляйся последовательно. Результаты придут—но только если ты сделаешь работу.',
 'Сатурн в твоём 10-м доме приносит фокус, дисциплину и давление вокруг карьеры и публичной роли. Это период "сделать или сломаться", где упорная работа окупается, а короткие пути — нет.

Строй фундаменты, бери ответственность и появляйся последовательно. Результаты придут—но только если ты сделаешь работу.

Этот транзит не лёгкий, но он того стоит.',
 'Определи одну долгосрочную карьерную цель и сделай один конкретный шаг к ней сегодня.');

-- =============================================================================
-- ES locale: Átomos por casas
-- =============================================================================

-- Sol en casa 1
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, house_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_sun_1h', 'sun_in_1st', '["general", "selfcare"]', '["house_1"]',
 'Tu energía y presencia son más visibles ahora. Buen momento para mostrarte.',
 'Cuando el Sol pasa por tu casa 1, naturalmente te vuelves más visible y energizado. Es tu temporada—un momento para enfocarte en ti, tus metas y cómo te presentas al mundo.

Usa este período para renovar tu imagen, empezar nuevos proyectos o simplemente ser más firme sobre lo que quieres.',
 'Cuando el Sol pasa por tu casa 1, naturalmente te vuelves más visible y energizado. Es tu temporada—un momento para enfocarte en ti, tus metas y cómo te presentas al mundo.

Usa este período para renovar tu imagen, empezar nuevos proyectos o simplemente ser más firme sobre lo que quieres.

Es tu nuevo año personal—establece intenciones y actúa.',
 'Escribe una cosa que quieras cambiar sobre cómo te muestras al mundo.');

-- Venus en casa 2
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, house_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_venus_2h', 'venus_in_2nd', '["general", "money"]', '["house_2"]',
 'Dinero y placer están conectados ahora. Buen momento para atraer recursos y disfrutar lo que tienes.',
 'Venus en tu casa 2 enfoca la atención en dinero, valores y comodidad material. Es uno de los mejores momentos para ganar, atraer oportunidades o simplemente disfrutar lo que ya tienes.

Date un gusto, negocia un aumento o revisa tus finanzas con enfoque en abundancia, no escasez.',
 'Venus en tu casa 2 enfoca la atención en dinero, valores y comodidad material. Es uno de los mejores momentos para ganar, atraer oportunidades o simplemente disfrutar lo que ya tienes.

Date un gusto, negocia un aumento o revisa tus finanzas con enfoque en abundancia, no escasez.

Tu relación con el dinero es más suave ahora—úsala sabiamente.',
 'Haz un movimiento hoy que aumente tu bienestar financiero o disfrute.');

-- Marte en casa 6
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, house_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_mars_6h', 'mars_in_6th', '["general", "work", "health"]', '["house_6"]',
 'La energía va al trabajo y salud ahora. Buen momento para tareas y construir hábitos.',
 'Marte en tu casa 6 supercarga tu productividad y disciplina. Tienes más energía para trabajo, rutinas diarias y mejoras de salud—pero también más irritación si las cosas parecen ineficientes.

Usa este período para organizar tu vida, construir nuevos hábitos o avanzar en tareas que has evitado.',
 'Marte en tu casa 6 supercarga tu productividad y disciplina. Tienes más energía para trabajo, rutinas diarias y mejoras de salud—pero también más irritación si las cosas parecen ineficientes.

Usa este período para organizar tu vida, construir nuevos hábitos o avanzar en tareas que has evitado.

Solo cuida el agotamiento—Marte empuja fuerte, pero tu cuerpo tiene límites.',
 'Elige un hábito o rutina que quieras mejorar, y comprométete por una semana.');

-- Júpiter en casa 9
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, house_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_jupiter_9h', 'jupiter_in_9th', '["general", "learning"]', '["house_9"]',
 'Tus horizontes se expanden. Gran momento para aprender, viajar y pensar en grande.',
 'Júpiter en tu casa 9 abre puertas a nuevas ideas, lugares y perspectivas. Es uno de los mejores tránsitos para educación, viajes o simplemente expandir tu visión del mundo.

Di sí a oportunidades que te estiren más allá de tus límites usuales.',
 'Júpiter en tu casa 9 abre puertas a nuevas ideas, lugares y perspectivas. Es uno de los mejores tránsitos para educación, viajes o simplemente expandir tu visión del mundo.

Di sí a oportunidades que te estiren más allá de tus límites usuales.

Estás listo para algo más grande—confía en eso.',
 'Investiga un tema, lugar o habilidad que te haya interesado.');

-- Saturno en casa 10
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, house_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_saturn_10h', 'saturn_in_10th', '["general", "work"]', '["house_10"]',
 'Carrera e imagen pública se ponen serias ahora. Tiempo de construir algo sólido y duradero.',
 'Saturno en tu casa 10 trae enfoque, disciplina y presión en tu carrera y rol público. Es un período decisivo donde el trabajo duro paga, pero los atajos no.

Construye cimientos, toma responsabilidad y aparece consistentemente. Los resultados llegarán—pero solo si haces el trabajo.',
 'Saturno en tu casa 10 trae enfoque, disciplina y presión en tu carrera y rol público. Es un período decisivo donde el trabajo duro paga, pero los atajos no.

Construye cimientos, toma responsabilidad y aparece consistentemente. Los resultados llegarán—pero solo si haces el trabajo.

Este tránsito no es fácil, pero vale la pena.',
 'Identifica una meta de carrera a largo plazo y da un paso concreto hoy.');

COMMIT;
