-- =============================================================================
-- Seed transit atoms for RU and ES locales
-- =============================================================================
-- 
-- This script:
-- 1. Removes test atoms (ml_test_tag) from RU locale
-- 2. Updates existing RU and ES transit atoms with copy_long
-- 3. Adds 15 new transit atoms for RU locale
-- 4. Adds 15 new transit atoms for ES locale
--
-- =============================================================================

BEGIN;

-- =============================================================================
-- STEP 1: Clean up test atoms from RU locale
-- =============================================================================

DELETE FROM content_atoms 
WHERE locale = 'ru' 
  AND topic_tag = 'ml_test_tag';

-- =============================================================================
-- STEP 2: Update existing transit atoms with copy_long
-- =============================================================================

-- RU: venus_trine_moon (ID=447)
UPDATE content_atoms 
SET copy_long = 'Сегодня эмоциональный фон мягче обычного. Венера и Луна образуют поддерживающий аспект, поэтому чувства и потребности легче согласовать между собой. Это хороший день, чтобы немного замедлиться, прислушаться к себе и к близким.

Сделай ставку на простые удовольствия и планы без лишнего давления: спокойная прогулка, вкусная еда, тёплые, но не тяжёлые разговоры. По возможности избегай драм и резких эмоциональных реакций — небесная картинка поддерживает именно мягкость и доброжелательность.'
WHERE id = 447;

-- RU: mars_square_sun (ID=450)
UPDATE content_atoms 
SET copy_long = 'Сегодня небо добавляет и силы, и внутреннего напряжения. Квадратура Марса и Солнца подсвечивает те сферы, где старые ограничения уже тесны и хочется резко ускориться. Транзит может быть очень продуктивным, если направить его в одно-две конкретные задачи, а не в перепалки и борьбу с миром.

Выбери реалистичную цель дня: закрыть зависшую задачу, навести порядок в хаотичном участке жизни или наконец принять решение, которое откладывалось. Действуй решительно, но регулярно проверяй тело: зажатые плечи, челюсть или тяжесть в животе — сигнал сделать паузу и выдохнуть.'
WHERE id = 450;

-- ES: venus_trine_moon (ID=448)
UPDATE content_atoms 
SET copy_long = 'Hoy el ambiente emocional es más suave de lo habitual. Venus y la Luna forman un aspecto de apoyo, facilitando que sentimientos y necesidades fluyan juntos. Es un buen día para ir más despacio, escucharte a ti y a los que te rodean.

Apuesta por placeres simples y planes sin presión: un paseo tranquilo, buena comida, conversaciones cálidas pero ligeras. Evita dramas y reacciones emocionales intensas; el cielo apoya la suavidad y el buen rollo.'
WHERE id = 448;

-- ES: mars_square_sun (ID=451)
UPDATE content_atoms 
SET copy_long = 'Hoy el cielo añade energía y tensión interna. La cuadratura de Marte y el Sol resalta áreas donde las limitaciones antiguas ya no funcionan y quieres acelerar. Este tránsito puede ser muy productivo si lo canalizas en una o dos tareas concretas, no en conflictos.

Elige un objetivo realista: cerrar algo pendiente, ordenar un área caótica o tomar una decisión postergada. Actúa con decisión, pero revisa tu cuerpo: hombros tensos, mandíbula apretada o peso en el abdomen son señales para pausar y respirar.'
WHERE id = 451;

-- =============================================================================
-- STEP 3: Add new transit atoms for RU locale (15 transits, 2-3 variants each)
-- =============================================================================

-- Транзит 1: Sun trine Moon (Солнце трин Луна) - гармония внутреннего и внешнего
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_sun_moon_harmony', 'sun_trine_moon', '["general", "selfcare"]', 
 'Внутренние потребности и внешние задачи сегодня не спорят, а дополняют друг друга. Хороший день для мягкого планирования.',
 'Сегодня Солнце и Луна образуют гармоничный аспект — один из тех дней, когда твои внутренние потребности и внешние задачи не конфликтуют. Это хорошее время, чтобы наметить планы на ближайшую неделю или просто выдохнуть и сделать что-то для себя.

Воспользуйся этим балансом: запланируй то, что давно откладывал, или просто отдохни без чувства вины. Небо поддерживает и действие, и покой — выбирай то, что тебе нужно прямо сейчас.',
 'Сегодня Солнце и Луна образуют гармоничный аспект — один из тех дней, когда твои внутренние потребности и внешние задачи не конфликтуют. Это хорошее время, чтобы наметить планы на ближайшую неделю или просто выдохнуть и сделать что-то для себя.

Воспользуйся этим балансом: запланируй то, что давно откладывал, или просто отдохни без чувства вины. Небо поддерживает и действие, и покой — выбирай то, что тебе нужно прямо сейчас.

Если есть важный разговор или решение — сегодня подходящий момент: ты видишь и логику, и эмоции, и можешь их учесть без внутреннего конфликта.',
 'Запиши одну вещь, которую ты хочешь сделать для себя сегодня, и просто сделай её.');

-- Вариант 2
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_sun_moon_harmony', 'sun_trine_moon', '["general", "work"]',
 'День, когда работа и личная жизнь не тянут в разные стороны. Используй это для спокойного прогресса.',
 'Сегодня твои цели и эмоциональные потребности двигаются в одном направлении. Это редкий день, когда можно продвигаться по задачам без внутреннего сопротивления.

Сделай ставку на плавный, устойчивый прогресс: закрой 2-3 задачи, которые давно висят в списке, или запланируй что-то важное на ближайшие дни.',
 'Сегодня твои цели и эмоциональные потребности двигаются в одном направлении. Это редкий день, когда можно продвигаться по задачам без внутреннего сопротивления.

Сделай ставку на плавный, устойчивый прогресс: закрой 2-3 задачи, которые давно висят в списке, или запланируй что-то важное на ближайшие дни.

Если нужно принять решение — сегодня хороший момент: ты видишь и рациональную, и эмоциональную сторону вопроса.',
 'Выбери одну задачу, которую откладывал, и спокойно закрой её сегодня.');

-- Транзит 2: Mercury sextile Venus (Меркурий секстиль Венера) - лёгкое общение
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_mercury_venus_flow', 'mercury_sextile_venus', '["general", "love", "work"]',
 'Слова сегодня текут легко и приятно. Хороший момент для важных разговоров и договорённостей.',
 'Меркурий и Венера образуют лёгкий, поддерживающий аспект — сегодня общение идёт проще, чем обычно. Это отличный день для переговоров, сложных разговоров или просто для того, чтобы сказать что-то важное близкому человеку.

Используй этот день для диалогов, которые откладывал: прояснить отношения, договориться о чём-то важном или просто побыть с кем-то в приятной беседе.',
 'Меркурий и Венера образуют лёгкий, поддерживающий аспект — сегодня общение идёт проще, чем обычно. Это отличный день для переговоров, сложных разговоров или просто для того, чтобы сказать что-то важное близкому человеку.

Используй этот день для диалогов, которые откладывал: прояснить отношения, договориться о чём-то важном или просто побыть с кем-то в приятной беседе.

Слова сегодня находятся легко, и другие люди более склонны слушать и понимать. Если есть что сказать — говори сегодня.',
 'Напиши одному человеку, с которым давно хотел поговорить, и назначь встречу или созвон.');

-- Вариант 2
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_mercury_venus_flow', 'mercury_sextile_venus', '["general", "creativity"]',
 'Творческие идеи и слова сегодня находят друг друга без усилий. Время для креатива и общения.',
 'Сегодня Меркурий и Венера поддерживают лёгкость в общении и творческом выражении. Если ты пишешь, рисуешь, придумываешь — сегодня идеи будут приходить легче, чем обычно.

Посвяти хотя бы полчаса творчеству или просто запиши идеи, которые приходят в голову. Этот день хорош для черновиков, набросков и свободного потока мыслей.',
 'Сегодня Меркурий и Венера поддерживают лёгкость в общении и творческом выражении. Если ты пишешь, рисуешь, придумываешь — сегодня идеи будут приходить легче, чем обычно.

Посвяти хотя бы полчаса творчеству или просто запиши идеи, которые приходят в голову. Этот день хорош для черновиков, набросков и свободного потока мыслей.

Даже если ты не считаешь себя творческим человеком — попробуй записать мысли, зарисовать что-то или просто поиграть с идеями. Сегодня это будет даваться легко.',
 'Возьми блокнот или откройти заметки и запиши 3-5 идей, которые крутятся в голове.');

-- Транзит 3: Mars trine Jupiter (Марс трин Юпитер) - уверенное действие
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_mars_jupiter_action', 'mars_trine_jupiter', '["general", "work", "money"]',
 'Сегодня действие встречается с возможностями. Хороший день для смелых, но реалистичных шагов.',
 'Марс и Юпитер образуют поддерживающий аспект — твоя энергия встречается с возможностями и оптимизмом. Это один из лучших дней для того, чтобы сделать что-то, что давно откладывал из-за страха или неуверенности.

Выбери одно важное дело и двигайся смело, но с расчётом. Сегодня небо поддерживает уверенное действие, но не безрассудство.',
 'Марс и Юпитер образуют поддерживающий аспект — твоя энергия встречается с возможностями и оптимизмом. Это один из лучших дней для того, чтобы сделать что-то, что давно откладывал из-за страха или неуверенности.

Выбери одно важное дело и двигайся смело, но с расчётом. Сегодня небо поддерживает уверенное действие, но не безрассудство.

Если есть проект, переговоры или решение, которое требует смелости — сегодня подходящий момент. Ты чувствуешь себя увереннее, и другие это видят.',
 'Сделай один смелый шаг в проекте или цели, которую откладывал.');

-- Транзит 4: Venus square Mars (Венера квадрат Марс) - напряжение в желаниях
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_venus_mars_tension', 'venus_square_mars', '["general", "love", "selfcare"]',
 'Желания и действия сегодня могут тянуть в разные стороны. Не спеши, проверь, чего ты действительно хочешь.',
 'Венера и Марс сегодня в напряжённом аспекте — твои желания и действия могут не совпадать. Это день, когда легко сделать что-то импульсивно, а потом пожалеть.

Перед важными решениями сделай паузу: чего ты хочешь на самом деле? Если чувствуешь раздражение или нетерпение — это сигнал замедлиться.',
 'Венера и Марс сегодня в напряжённом аспекте — твои желания и действия могут не совпадать. Это день, когда легко сделать что-то импульсивно, а потом пожалеть.

Перед важными решениями сделай паузу: чего ты хочешь на самом деле? Если чувствуешь раздражение или нетерпение — это сигнал замедлиться.

В отношениях избегай резких слов и ультиматумов. Если что-то напрягает — лучше отложить разговор на день-два, чем говорить сгоряча.',
 'Если чувствуешь раздражение — сделай три глубоких вдоха, прежде чем действовать или говорить.');

-- Транзит 5: Mercury square Neptune (Меркурий квадрат Нептун) - туман в мышлении
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_mercury_neptune_fog', 'mercury_square_neptune', '["general", "work"]',
 'Мышление сегодня может быть туманным. Не подписывай важных документов и перепроверяй детали.',
 'Меркурий и Нептун сегодня в сложном аспекте — мышление может быть менее чётким, чем обычно. Это день, когда легко что-то упустить, не расслышать или неправильно понять.

Перепроверяй важные детали, откладывай подписание контрактов и не принимай крупных решений. Если что-то кажется неясным — так и есть, лучше уточнить позже.',
 'Меркурий и Нептун сегодня в сложном аспекте — мышление может быть менее чётким, чем обычно. Это день, когда легко что-то упустить, не расслышать или неправильно понять.

Перепроверяй важные детали, откладывай подписание контрактов и не принимай крупных решений. Если что-то кажется неясным — так и есть, лучше уточнить позже.

Зато сегодня хорош для творчества, мечтаний и визуализации. Если не нужна точность — позволь себе плыть по течению идей.',
 'Перепроверь одну важную деталь в работе или договорённости, чтобы не упустить ошибку.');

-- Транзит 6: Sun square Saturn (Солнце квадрат Сатурн) - столкновение с ограничениями
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_sun_saturn_limits', 'sun_square_saturn', '["general", "work"]',
 'Сегодня могут проявиться ограничения и сопротивление. Не бейся о стену — лучше переформулируй задачу.',
 'Солнце и Сатурн сегодня в напряжённом аспекте — день может ощущаться тяжелее обычного. Это время, когда проявляются реальные ограничения: времени, ресурсов, энергии.

Вместо того чтобы биться о стену, посмотри на задачу под другим углом: может, есть другой путь? Сегодня не день для героических прорывов, а день для реалистичных шагов.',
 'Солнце и Сатурн сегодня в напряжённом аспекте — день может ощущаться тяжелее обычного. Это время, когда проявляются реальные ограничения: времени, ресурсов, энергии.

Вместо того чтобы биться о стену, посмотри на задачу под другим углом: может, есть другой путь? Сегодня не день для героических прорывов, а день для реалистичных шагов.

Если чувствуешь давление или критику (внешнюю или внутреннюю) — это часть транзита. Не принимай это слишком близко к сердцу, просто делай то, что можешь, шаг за шагом.',
 'Выбери одну маленькую задачу, которую точно можешь закрыть сегодня, и просто сделай её.');

-- Транзит 7: Venus conjunct Jupiter (Венера соединение Юпитер) - щедрость и радость
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_venus_jupiter_joy', 'venus_conjunct_jupiter', '["general", "love", "money"]',
 'Один из самых лёгких и радостных дней. Сегодня хорошо дарить, получать и наслаждаться.',
 'Венера и Юпитер сегодня вместе — это один из самых приятных и щедрых дней в году. Сегодня хочется и можно больше: больше радости, больше связи, больше удовольствия.

Позволь себе что-то хорошее: встретиться с близкими, купить то, что давно хотел, или просто побыть в моменте и насладиться им.',
 'Венера и Юпитер сегодня вместе — это один из самых приятных и щедрых дней в году. Сегодня хочется и можно больше: больше радости, больше связи, больше удовольствия.

Позволь себе что-то хорошее: встретиться с близкими, купить то, что давно хотел, или просто побыть в моменте и насладиться им.

Единственный риск сегодня — переборщить. Если покупаешь что-то дорогое или принимаешь важное решение — убедись, что это не импульс, а настоящее желание.',
 'Сделай сегодня что-то приятное для себя или для близкого человека.');

-- Транзит 8: Moon conjunct Pluto (Луна соединение Плутон) - глубокие эмоции
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_moon_pluto_depth', 'moon_conjunct_pluto', '["general", "selfcare"]',
 'Эмоции сегодня могут быть глубже и интенсивнее, чем обычно. Дай себе пространство их прожить.',
 'Луна и Плутон сегодня вместе — эмоции могут быть более интенсивными и глубокими. Это день, когда всплывают старые чувства или темы, которые ты обычно не замечаешь.

Не пытайся всё контролировать или подавлять. Просто позволь себе почувствовать то, что есть, и дай этому место.',
 'Луна и Плутон сегодня вместе — эмоции могут быть более интенсивными и глубокими. Это день, когда всплывают старые чувства или темы, которые ты обычно не замечаешь.

Не пытайся всё контролировать или подавлять. Просто позволь себе почувствовать то, что есть, и дай этому место.

Если всплывает что-то сложное — это не проблема, это информация. Запиши, что чувствуешь, или поговори с кем-то, кому доверяешь.',
 'Запиши в блокнот или заметки, что ты чувствуешь прямо сейчас, без анализа и оценки.');

-- Транзит 9: Mercury trine Saturn (Меркурий трин Сатурн) - структурное мышление
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_mercury_saturn_structure', 'mercury_trine_saturn', '["general", "work"]',
 'Мышление сегодня чёткое и структурное. Хороший день для планирования и организации.',
 'Меркурий и Сатурн образуют поддерживающий аспект — сегодня ты можешь думать чётко, последовательно и видеть долгосрочные последствия. Это один из лучших дней для планирования, написания важных документов или просто для того, чтобы разложить по полочкам что-то сложное.

Используй этот день для задач, которые требуют концентрации и точности.',
 'Меркурий и Сатурн образуют поддерживающий аспект — сегодня ты можешь думать чётко, последовательно и видеть долгосрочные последствия. Это один из лучших дней для планирования, написания важных документов или просто для того, чтобы разложить по полочкам что-то сложное.

Используй этот день для задач, которые требуют концентрации и точности.

Если давно хотел навести порядок в проектах, финансах или планах — сегодня идеальный момент. Твой ум работает как хорошо настроенный инструмент.',
 'Выдели час на планирование: что ты хочешь закрыть на этой неделе и в следующем месяце?');

-- Транзит 10: Sun trine Uranus (Солнце трин Уран) - свобода и новизна
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_sun_uranus_freedom', 'sun_trine_uranus', '["general", "creativity"]',
 'Сегодня тянет на новизну и свободу. Хороший день для экспериментов и неожиданных идей.',
 'Солнце и Уран образуют поддерживающий аспект — сегодня ты можешь почувствовать тягу к новизне, свободе и экспериментам. Это день, когда можно попробовать что-то новое без страха ошибиться.

Позволь себе отойти от привычного сценария: выбери другой маршрут, попробуй новый подход к задаче или просто сделай что-то спонтанное.',
 'Солнце и Уран образуют поддерживающий аспект — сегодня ты можешь почувствовать тягу к новизне, свободе и экспериментам. Это день, когда можно попробовать что-то новое без страха ошибиться.

Позволь себе отойти от привычного сценария: выбери другой маршрут, попробуй новый подход к задаче или просто сделай что-то спонтанное.

Если давно хотел изменить что-то в рутине или попробовать новое — сегодня хороший момент для первого шага.',
 'Сделай сегодня одну вещь, которую обычно не делаешь: другой маршрут, новое место, необычная задача.');

-- Транзит 11: Venus opposite Saturn (Венера оппозиция Сатурн) - серьёзность в отношениях
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_venus_saturn_serious', 'venus_opposite_saturn', '["general", "love"]',
 'Сегодня в отношениях могут проявиться серьёзные темы или дистанция. Не спеши с выводами.',
 'Венера и Сатурн сегодня в оппозиции — это может быть день, когда в отношениях всплывают серьёзные темы: обязательства, границы, реальность вместо романтики. Это не плохо, но может ощущаться тяжелее, чем обычно.

Если чувствуешь холодность или дистанцию — не паникуй. Это временное напряжение, которое может помочь увидеть реальную картину.',
 'Венера и Сатурн сегодня в оппозиции — это может быть день, когда в отношениях всплывают серьёзные темы: обязательства, границы, реальность вместо романтики. Это не плохо, но может ощущаться тяжелее, чем обычно.

Если чувствуешь холодность или дистанцию — не паникуй. Это временное напряжение, которое может помочь увидеть реальную картину.

Не принимай сегодня крупных решений в отношениях. Просто замечай, что происходит, и дай себе время подумать.',
 'Если чувствуешь напряжение в отношениях — запиши, что именно тебя беспокоит, прежде чем говорить об этом.');

-- Транзит 12: Mars opposite Saturn (Марс оппозиция Сатурн) - столкновение действия и ограничения
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_mars_saturn_block', 'mars_opposite_saturn', '["general", "work"]',
 'Энергия встречается с препятствиями. Не дави — ищи обходные пути или подожди день-два.',
 'Марс и Сатурн сегодня в оппозиции — твоя энергия может столкнуться с реальными препятствиями или сопротивлением. Это день, когда хочется действовать, но что-то (или кто-то) блокирует движение.

Не дави напролом. Вместо этого посмотри: может, есть другой путь? Или может, это сигнал сделать паузу и подумать, прежде чем двигаться дальше?',
 'Марс и Сатурн сегодня в оппозиции — твоя энергия может столкнуться с реальными препятствиями или сопротивлением. Это день, когда хочется действовать, но что-то (или кто-то) блокирует движение.

Не дави напролом. Вместо этого посмотри: может, есть другой путь? Или может, это сигнал сделать паузу и подумать, прежде чем двигаться дальше?

Если чувствуешь фрустрацию — это нормально. Просто не превращай её в конфликт. Дай себе физическую разрядку: прогулка, тренировка, уборка — что угодно, что задействует тело.',
 'Если чувствуешь застой — переключись на физическую активность: прогулку, зарядку, уборку.');

-- Транзит 13: Sun conjunct Mercury (Солнце соединение Меркурий) - ясность мышления
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_sun_mercury_clarity', 'sun_conjunct_mercury', '["general", "work"]',
 'Мышление сегодня особенно ясное и быстрое. Хороший день для важных разговоров и решений.',
 'Солнце и Меркурий сегодня вместе — это один из лучших дней для ясного мышления, важных разговоров и принятия решений. Ты видишь суть вещей без лишнего тумана и можешь чётко выразить свои мысли.

Используй этот день для всего, что требует коммуникации: переговоры, презентации, сложные объяснения.',
 'Солнце и Меркурий сегодня вместе — это один из лучших дней для ясного мышления, важных разговоров и принятия решений. Ты видишь суть вещей без лишнего тумана и можешь чётко выразить свои мысли.

Используй этот день для всего, что требует коммуникации: переговоры, презентации, сложные объяснения.

Если есть решение, которое откладывал — сегодня хороший момент, чтобы его принять. Твой ум работает чётко, и ты можешь доверять своей логике.',
 'Прими одно решение, которое откладывал, пока ум ясен.');

-- Транзит 14: Moon square Mars (Луна квадрат Марс) - эмоциональная импульсивность
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_moon_mars_impulse', 'moon_square_mars', '["general", "selfcare"]',
 'Эмоции могут быстро перейти в действие. Перед важными шагами сделай паузу.',
 'Луна и Марс сегодня в напряжённом аспекте — эмоции могут быстро переходить в действие или слова. Это день, когда легко сказать или сделать что-то сгоряча, а потом пожалеть.

Перед важными шагами сделай паузу: это реакция или осознанный выбор?',
 'Луна и Марс сегодня в напряжённом аспекте — эмоции могут быстро переходить в действие или слова. Это день, когда легко сказать или сделать что-то сгоряча, а потом пожалеть.

Перед важными шагами сделай паузу: это реакция или осознанный выбор?

Если чувствуешь раздражение или нетерпение — это часть транзита. Дай себе физическую разрядку вместо того, чтобы вымещать это на других.',
 'Перед тем как ответить на что-то раздражающее, посчитай до десяти и сделай три глубоких вдоха.');

-- Транзит 15: Jupiter trine Saturn (Юпитер трин Сатурн) - реалистичный рост
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_jupiter_saturn_growth', 'jupiter_trine_saturn', '["general", "work", "money"]',
 'Возможности встречаются со структурой. Хороший день для долгосрочного планирования и реалистичных целей.',
 'Юпитер и Сатурн образуют поддерживающий аспект — сегодня твои амбиции и реальность не конфликтуют, а дополняют друг друга. Это редкий день, когда можно мечтать и одновременно видеть, как это реализовать.

Используй этот день для долгосрочного планирования: какую цель ты хочешь достичь через год? Какие шаги для этого нужны?',
 'Юпитер и Сатурн образуют поддерживающий аспект — сегодня твои амбиции и реальность не конфликтуют, а дополняют друг друга. Это редкий день, когда можно мечтать и одновременно видеть, как это реализовать.

Используй этот день для долгосрочного планирования: какую цель ты хочешь достичь через год? Какие шаги для этого нужны?

Если есть проект или идея, которую хочешь развить — сегодня отличный момент, чтобы наметить реальный план действий.',
 'Выбери одну большую цель на год и запиши три первых шага к ней.');

-- =============================================================================
-- STEP 4: Add new transit atoms for ES locale (15 transits, 2 variants each)
-- =============================================================================

-- Tránsito 1: Sun trine Moon
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_sun_moon_harmony', 'sun_trine_moon', '["general", "selfcare"]',
 'Las necesidades internas y tareas externas hoy fluyen juntas. Buen día para planificar con calma.',
 'Hoy el Sol y la Luna forman un aspecto armónico: un día donde tus necesidades internas y tareas externas no luchan. Es buen momento para planificar la próxima semana o simplemente hacer algo para ti.

Aprovecha este equilibrio: planifica lo que has postergado o descansa sin culpa. El cielo apoya tanto la acción como el descanso.',
 'Hoy el Sol y la Luna forman un aspecto armónico: un día donde tus necesidades internas y tareas externas no luchan. Es buen momento para planificar la próxima semana o simplemente hacer algo para ti.

Aprovecha este equilibrio: planifica lo que has postergado o descansa sin culpa. El cielo apoya tanto la acción como el descanso.

Si hay una conversación o decisión importante, hoy es el momento: ves tanto la lógica como las emociones y puedes considerarlas sin conflicto interno.',
 'Anota una cosa que quieras hacer por ti hoy y hazla.');

-- Variante 2
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_sun_moon_harmony', 'sun_trine_moon', '["general", "work"]',
 'Trabajo y vida personal no tiran en direcciones opuestas. Úsalo para avanzar tranquilo.',
 'Hoy tus metas y necesidades emocionales van en la misma dirección. Es un día raro donde puedes avanzar sin resistencia interna.

Apuesta por progreso constante: cierra 2-3 tareas pendientes o planifica algo importante para los próximos días.',
 'Hoy tus metas y necesidades emocionales van en la misma dirección. Es un día raro donde puedes avanzar sin resistencia interna.

Apuesta por progreso constante: cierra 2-3 tareas pendientes o planifica algo importante para los próximos días.

Si necesitas tomar una decisión, hoy es buen momento: ves el lado racional y emocional.',
 'Elige una tarea que has postergado y ciérrala hoy con calma.');

-- Tránsito 2: Mercury sextile Venus
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_mercury_venus_flow', 'mercury_sextile_venus', '["general", "love", "work"]',
 'Las palabras fluyen fácil y agradable hoy. Buen momento para conversaciones importantes.',
 'Mercurio y Venus forman un aspecto suave: hoy la comunicación es más fácil que de costumbre. Es excelente para negociaciones, charlas difíciles o decir algo importante a alguien cercano.

Usa este día para diálogos postergados: aclarar una relación, acordar algo importante o simplemente estar en buena conversación.',
 'Mercurio y Venus forman un aspecto suave: hoy la comunicación es más fácil que de costumbre. Es excelente para negociaciones, charlas difíciles o decir algo importante a alguien cercano.

Usa este día para diálogos postergados: aclarar una relación, acordar algo importante o simplemente estar en buena conversación.

Las palabras vienen fácil hoy y otros están más dispuestos a escuchar y entender. Si hay algo que decir, dilo hoy.',
 'Escribe a una persona con quien querías hablar y agenda una llamada o encuentro.');

-- Tránsito 3: Mars trine Jupiter
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_mars_jupiter_action', 'mars_trine_jupiter', '["general", "work", "money"]',
 'Hoy la acción se encuentra con oportunidades. Buen día para pasos audaces pero realistas.',
 'Marte y Júpiter forman un aspecto de apoyo: tu energía se encuentra con oportunidades y optimismo. Es uno de los mejores días para hacer algo que has postergado por miedo o inseguridad.

Elige una tarea importante y muévete con confianza, pero con cálculo. El cielo apoya acción decidida, no temeridad.',
 'Marte y Júpiter forman un aspecto de apoyo: tu energía se encuentra con oportunidades y optimismo. Es uno de los mejores días para hacer algo que has postergado por miedo o inseguridad.

Elige una tarea importante y muévete con confianza, pero con cálculo. El cielo apoya acción decidida, no temeridad.

Si hay un proyecto, negociación o decisión que requiere valentía, hoy es el momento. Te sientes más seguro y otros lo ven.',
 'Da un paso audaz en un proyecto o meta que has postergado.');

-- Tránsito 4: Venus square Mars
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_venus_mars_tension', 'venus_square_mars', '["general", "love", "selfcare"]',
 'Deseos y acciones hoy pueden tirar en direcciones distintas. No te apresures, revisa qué quieres de verdad.',
 'Venus y Marte hoy en aspecto tenso: tus deseos y acciones pueden no coincidir. Es un día donde es fácil hacer algo impulsivo y luego arrepentirse.

Antes de decisiones importantes haz una pausa: ¿qué quieres realmente? Si sientes irritación o impaciencia, es señal de ir más despacio.',
 'Venus y Marte hoy en aspecto tenso: tus deseos y acciones pueden no coincidir. Es un día donde es fácil hacer algo impulsivo y luego arrepentirse.

Antes de decisiones importantes haz una pausa: ¿qué quieres realmente? Si sientes irritación o impaciencia, es señal de ir más despacio.

En relaciones evita palabras bruscas y ultimátums. Si algo te molesta, mejor pospón la conversación uno o dos días que hablar en caliente.',
 'Si sientes irritación, toma tres respiraciones profundas antes de actuar o hablar.');

-- Tránsito 5: Mercury square Neptune
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_mercury_neptune_fog', 'mercury_square_neptune', '["general", "work"]',
 'El pensamiento puede estar nublado hoy. No firmes documentos importantes y revisa detalles.',
 'Mercurio y Neptuno hoy en aspecto difícil: el pensamiento puede ser menos claro que de costumbre. Es un día donde es fácil pasar algo por alto, no escuchar bien o malentender.

Revisa detalles importantes, pospón firmar contratos y no tomes decisiones grandes. Si algo parece poco claro, lo es; mejor aclarar después.',
 'Mercurio y Neptuno hoy en aspecto difícil: el pensamiento puede ser menos claro que de costumbre. Es un día donde es fácil pasar algo por alto, no escuchar bien o malentender.

Revisa detalles importantes, pospón firmar contratos y no tomes decisiones grandes. Si algo parece poco claro, lo es; mejor aclarar después.

En cambio, hoy es bueno para creatividad, soñar y visualizar. Si no necesitas precisión, déjate fluir con las ideas.',
 'Revisa un detalle importante en trabajo o acuerdos para no perder un error.');

-- Tránsito 6: Sun square Saturn
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_sun_saturn_limits', 'sun_square_saturn', '["general", "work"]',
 'Hoy pueden aparecer limitaciones y resistencia. No luches contra la pared: reformula la tarea.',
 'El Sol y Saturno hoy en aspecto tenso: el día puede sentirse más pesado que de costumbre. Es momento donde aparecen limitaciones reales: de tiempo, recursos, energía.

En vez de luchar contra la pared, mira la tarea desde otro ángulo: ¿hay otro camino? Hoy no es día para avances heroicos, sino para pasos realistas.',
 'El Sol y Saturno hoy en aspecto tenso: el día puede sentirse más pesado que de costumbre. Es momento donde aparecen limitaciones reales: de tiempo, recursos, energía.

En vez de luchar contra la pared, mira la tarea desde otro ángulo: ¿hay otro camino? Hoy no es día para avances heroicos, sino para pasos realistas.

Si sientes presión o crítica (externa o interna), es parte del tránsito. No lo tomes muy a pecho, solo haz lo que puedas, paso a paso.',
 'Elige una tarea pequeña que puedas cerrar hoy con seguridad y hazla.');

-- Tránsito 7: Venus conjunct Jupiter
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_venus_jupiter_joy', 'venus_conjunct_jupiter', '["general", "love", "money"]',
 'Uno de los días más ligeros y alegres. Hoy es bueno dar, recibir y disfrutar.',
 'Venus y Júpiter hoy juntos: es uno de los días más agradables y generosos del año. Hoy quieres y puedes más: más alegría, más conexión, más placer.

Permítete algo bueno: reunirte con cercanos, comprar algo que querías o simplemente estar en el momento y disfrutarlo.',
 'Venus y Júpiter hoy juntos: es uno de los días más agradables y generosos del año. Hoy quieres y puedes más: más alegría, más conexión, más placer.

Permítete algo bueno: reunirte con cercanos, comprar algo que querías o simplemente estar en el momento y disfrutarlo.

El único riesgo hoy es excederse. Si compras algo caro o tomas una decisión importante, asegúrate de que no es impulso sino deseo real.',
 'Haz algo agradable hoy para ti o para alguien cercano.');

-- Tránsito 8: Moon conjunct Pluto
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_moon_pluto_depth', 'moon_conjunct_pluto', '["general", "selfcare"]',
 'Las emociones hoy pueden ser más profundas e intensas que de costumbre. Date espacio para vivirlas.',
 'La Luna y Plutón hoy juntos: las emociones pueden ser más intensas y profundas. Es un día donde surgen sentimientos viejos o temas que normalmente no notas.

No intentes controlar o reprimir todo. Solo permítete sentir lo que hay y dale espacio.',
 'La Luna y Plutón hoy juntos: las emociones pueden ser más intensas y profundas. Es un día donde surgen sentimientos viejos o temas que normalmente no notas.

No intentes controlar o reprimir todo. Solo permítete sentir lo que hay y dale espacio.

Si surge algo difícil, no es un problema, es información. Anota lo que sientes o habla con alguien de confianza.',
 'Anota en tu libreta o notas lo que sientes ahora mismo, sin analizar ni juzgar.');

-- Tránsito 9: Mercury trine Saturn
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_mercury_saturn_structure', 'mercury_trine_saturn', '["general", "work"]',
 'El pensamiento hoy es claro y estructurado. Buen día para planificar y organizar.',
 'Mercurio y Saturno forman un aspecto de apoyo: hoy puedes pensar con claridad, secuencia y ver consecuencias a largo plazo. Es uno de los mejores días para planificar, escribir documentos importantes o simplemente ordenar algo complejo.

Usa este día para tareas que requieren concentración y precisión.',
 'Mercurio y Saturno forman un aspecto de apoyo: hoy puedes pensar con claridad, secuencia y ver consecuencias a largo plazo. Es uno de los mejores días para planificar, escribir documentos importantes o simplemente ordenar algo complejo.

Usa este día para tareas que requieren concentración y precisión.

Si querías ordenar proyectos, finanzas o planes, hoy es el momento ideal. Tu mente trabaja como una herramienta bien ajustada.',
 'Dedica una hora a planificar: ¿qué quieres cerrar esta semana y el próximo mes?');

-- Tránsito 10: Sun trine Uranus
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_sun_uranus_freedom', 'sun_trine_uranus', '["general", "creativity"]',
 'Hoy te atrae lo nuevo y la libertad. Buen día para experimentos e ideas inesperadas.',
 'El Sol y Urano forman un aspecto de apoyo: hoy puedes sentir atracción por lo nuevo, la libertad y los experimentos. Es un día donde puedes probar algo nuevo sin miedo a equivocarte.

Permítete salir del guion habitual: elige otra ruta, prueba un nuevo enfoque en una tarea o simplemente haz algo espontáneo.',
 'El Sol y Urano forman un aspecto de apoyo: hoy puedes sentir atracción por lo nuevo, la libertad y los experimentos. Es un día donde puedes probar algo nuevo sin miedo a equivocarte.

Permítete salir del guion habitual: elige otra ruta, prueba un nuevo enfoque en una tarea o simplemente haz algo espontáneo.

Si querías cambiar algo en tu rutina o probar algo nuevo, hoy es buen momento para el primer paso.',
 'Haz una cosa hoy que normalmente no haces: otra ruta, nuevo lugar, tarea inusual.');

-- Tránsito 11: Venus opposite Saturn
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_venus_saturn_serious', 'venus_opposite_saturn', '["general", "love"]',
 'Hoy pueden surgir temas serios o distancia en relaciones. No te apresures con conclusiones.',
 'Venus y Saturno hoy en oposición: puede ser un día donde en relaciones surgen temas serios: compromisos, límites, realidad en vez de romance. No es malo, pero puede sentirse más pesado.

Si sientes frialdad o distancia, no entres en pánico. Es tensión temporal que puede ayudar a ver el panorama real.',
 'Venus y Saturno hoy en oposición: puede ser un día donde en relaciones surgen temas serios: compromisos, límites, realidad en vez de romance. No es malo, pero puede sentirse más pesado.

Si sientes frialdad o distancia, no entres en pánico. Es tensión temporal que puede ayudar a ver el panorama real.

No tomes decisiones grandes en relaciones hoy. Solo nota lo que pasa y date tiempo para pensar.',
 'Si sientes tensión en relaciones, anota qué te preocupa exactamente antes de hablarlo.');

-- Tránsito 12: Mars opposite Saturn
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_mars_saturn_block', 'mars_opposite_saturn', '["general", "work"]',
 'La energía se encuentra con obstáculos. No presiones: busca caminos alternativos o espera un par de días.',
 'Marte y Saturno hoy en oposición: tu energía puede encontrarse con obstáculos reales o resistencia. Es un día donde quieres actuar, pero algo (o alguien) bloquea el movimiento.

No presiones a la fuerza. En vez de eso mira: ¿hay otro camino? ¿O es señal de pausar y pensar antes de seguir?',
 'Marte y Saturno hoy en oposición: tu energía puede encontrarse con obstáculos reales o resistencia. Es un día donde quieres actuar, pero algo (o alguien) bloquea el movimiento.

No presiones a la fuerza. En vez de eso mira: ¿hay otro camino? ¿O es señal de pausar y pensar antes de seguir?

Si sientes frustración, es normal. Solo no la conviertas en conflicto. Date descarga física: caminar, entrenar, limpiar; cualquier cosa que use el cuerpo.',
 'Si sientes estancamiento, cambia a actividad física: caminar, ejercicio, limpieza.');

-- Tránsito 13: Sun conjunct Mercury
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_sun_mercury_clarity', 'sun_conjunct_mercury', '["general", "work"]',
 'El pensamiento hoy es especialmente claro y rápido. Buen día para conversaciones y decisiones importantes.',
 'El Sol y Mercurio hoy juntos: es uno de los mejores días para pensamiento claro, conversaciones importantes y tomar decisiones. Ves la esencia de las cosas sin niebla y puedes expresar tus ideas con claridad.

Usa este día para todo lo que requiere comunicación: negociaciones, presentaciones, explicaciones complejas.',
 'El Sol y Mercurio hoy juntos: es uno de los mejores días para pensamiento claro, conversaciones importantes y tomar decisiones. Ves la esencia de las cosas sin niebla y puedes expresar tus ideas con claridad.

Usa este día para todo lo que requiere comunicación: negociaciones, presentaciones, explicaciones complejas.

Si hay una decisión que has postergado, hoy es buen momento para tomarla. Tu mente trabaja con claridad y puedes confiar en tu lógica.',
 'Toma una decisión que has postergado mientras tu mente está clara.');

-- Tránsito 14: Moon square Mars
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_moon_mars_impulse', 'moon_square_mars', '["general", "selfcare"]',
 'Las emociones pueden pasar rápido a la acción. Antes de pasos importantes haz una pausa.',
 'La Luna y Marte hoy en aspecto tenso: las emociones pueden pasar rápido a acción o palabras. Es un día donde es fácil decir o hacer algo en caliente y luego arrepentirse.

Antes de pasos importantes haz una pausa: ¿es reacción o elección consciente?',
 'La Luna y Marte hoy en aspecto tenso: las emociones pueden pasar rápido a acción o palabras. Es un día donde es fácil decir o hacer algo en caliente y luego arrepentirse.

Antes de pasos importantes haz una pausa: ¿es reacción o elección consciente?

Si sientes irritación o impaciencia, es parte del tránsito. Date descarga física en vez de desquitarte con otros.',
 'Antes de responder a algo irritante, cuenta hasta diez y toma tres respiraciones profundas.');

-- Tránsito 15: Jupiter trine Saturn
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_jupiter_saturn_growth', 'jupiter_trine_saturn', '["general", "work", "money"]',
 'Las oportunidades se encuentran con la estructura. Buen día para planificación a largo plazo y metas realistas.',
 'Júpiter y Saturno forman un aspecto de apoyo: hoy tus ambiciones y la realidad no luchan, se complementan. Es un día raro donde puedes soñar y a la vez ver cómo realizarlo.

Usa este día para planificación a largo plazo: ¿qué meta quieres lograr en un año? ¿Qué pasos se necesitan?',
 'Júpiter y Saturno forman un aspecto de apoyo: hoy tus ambiciones y la realidad no luchan, se complementan. Es un día raro donde puedes soñar y a la vez ver cómo realizarlo.

Usa este día para planificación a largo plazo: ¿qué meta quieres lograr en un año? ¿Qué pasos se necesitan?

Si hay un proyecto o idea que quieres desarrollar, hoy es excelente para trazar un plan real de acción.',
 'Elige una meta grande para el año y anota tres primeros pasos hacia ella.');

COMMIT;
