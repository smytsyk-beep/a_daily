-- =============================================================================
-- Add orb-based variations for transit atoms
-- =============================================================================
--
-- This script adds content atoms that vary based on orb strength:
-- - Exact (0-1°): Most intense, precise timing
-- - Applying (1-3°): Building up, anticipation
-- - Separating (1-3°): Fading, integration
-- - Wide (3-5°): Background influence
--
-- This adds nuance to how transits are described based on their actual strength.
--
-- =============================================================================

BEGIN;

-- =============================================================================
-- EN locale: Orb-based variations
-- =============================================================================

-- Mars square Sun - exact orb (most intense)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mars_sun_push_exact', 'mars_square_sun_exact', '["general", "work"]',
 'Tension peaks today. This is the exact moment of Mars-Sun friction—move decisively or step back.',
 'Today Mars and Sun form an exact square—the peak of this transit. Energy is high, patience is low, and everything feels urgent. This is the day to either channel it into focused action or consciously step back to avoid conflicts.

Choose one clear goal and give it everything, or take space and let the intensity pass without acting on it.',
 'Today Mars and Sun form an exact square—the peak of this transit. Energy is high, patience is low, and everything feels urgent. This is the day to either channel it into focused action or consciously step back to avoid conflicts.

Choose one clear goal and give it everything, or take space and let the intensity pass without acting on it.

If you feel resistance—pause. The exact transit magnifies both productive power and destructive impulses.',
 'Decide now: act with full focus on one thing, or consciously rest until tomorrow.');

-- Venus trine Moon - applying (building up)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_venus_moon_harmony_applying', 'venus_trine_moon_applying', '["general", "love"]',
 'Emotional warmth is building. A gentle day that will get even better tomorrow.',
 'Venus and Moon are moving toward a harmonious aspect—not quite exact yet, but you can already feel the softening. This is the build-up phase: emotional ease is increasing, and connections feel lighter.

Use today to set the stage for something you want to bloom: reach out, plan something nice, or simply enjoy the gentle mood.',
 'Venus and Moon are moving toward a harmonious aspect—not quite exact yet, but you can already feel the softening. This is the build-up phase: emotional ease is increasing, and connections feel lighter.

Use today to set the stage for something you want to bloom: reach out, plan something nice, or simply enjoy the gentle mood.

The best is still ahead—but today is already better than yesterday.',
 'Reach out to someone you care about, or plan something you''ll enjoy in the next few days.');

-- Mercury square Neptune - separating (fading)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mercury_neptune_fog_separating', 'mercury_square_neptune_separating', '["general", "work"]',
 'Mental fog is clearing. The confusion is fading—today you start seeing more clearly.',
 'The Mercury-Neptune square is separating—the worst of the fog has passed, and clarity is gradually returning. You might still feel a bit fuzzy, but decisions are easier now than they were yesterday.

Use today to review anything you postponed during the fog, and start moving forward again.',
 'The Mercury-Neptune square is separating—the worst of the fog has passed, and clarity is gradually returning. You might still feel a bit fuzzy, but decisions are easier now than they were yesterday.

Use today to review anything you postponed during the fog, and start moving forward again.

Trust your mind more today—it''s coming back online.',
 'Revisit one decision or task you put on hold, and move it forward.');

-- Jupiter trine Saturn - wide orb (background support)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_jupiter_saturn_build_wide', 'jupiter_trine_saturn_wide', '["general", "work"]',
 'Slow, steady progress is supported in the background. No fireworks, just solid building.',
 'Jupiter and Saturn are in a wide harmonious aspect—this isn''t a day of dramatic breakthroughs, but there''s a quiet, steady energy supporting your long-term goals.

Use this period for consistent, unglamorous work: the kind that doesn''t look impressive but adds up over time.',
 'Jupiter and Saturn are in a wide harmonious aspect—this isn''t a day of dramatic breakthroughs, but there''s a quiet, steady energy supporting your long-term goals.

Use this period for consistent, unglamorous work: the kind that doesn''t look impressive but adds up over time.

Think foundation, not fireworks.',
 'Do one small, boring task today that supports your long-term goals.');

-- =============================================================================
-- RU locale: Вариации по орбу
-- =============================================================================

-- Марс квадрат Солнце - точный орб (максимальная интенсивность)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_mars_sun_push_exact', 'mars_square_sun_exact', '["general", "work"]',
 'Напряжение на пике сегодня. Это точный момент квадратуры Марс-Солнце—действуй решительно или отойди в сторону.',
 'Сегодня Марс и Солнце образуют точную квадратуру—пик этого транзита. Энергии много, терпения мало, и всё кажется срочным. Это день, чтобы либо направить энергию в сфокусированное действие, либо сознательно отступить, чтобы избежать конфликтов.

Выбери одну чёткую цель и вложи в неё всё, или возьми паузу и дай интенсивности пройти, не действуя на неё.',
 'Сегодня Марс и Солнце образуют точную квадратуру—пик этого транзита. Энергии много, терпения мало, и всё кажется срочным. Это день, чтобы либо направить энергию в сфокусированное действие, либо сознательно отступить, чтобы избежать конфликтов.

Выбери одну чёткую цель и вложи в неё всё, или возьми паузу и дай интенсивности пройти, не действуя на неё.

Если чувствуешь сопротивление—остановись. Точный транзит усиливает и продуктивную силу, и разрушительные импульсы.',
 'Реши сейчас: действуй с полным фокусом на одну вещь, или сознательно отдохни до завтра.');

-- Венера трин Луна - сближающийся орб (нарастает)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_venus_moon_harmony_applying', 'venus_trine_moon_applying', '["general", "love"]',
 'Эмоциональное тепло нарастает. Мягкий день, который завтра станет ещё лучше.',
 'Венера и Луна движутся к гармоничному аспекту—ещё не совсем точно, но ты уже можешь почувствовать смягчение. Это фаза нарастания: эмоциональная лёгкость усиливается, и связи кажутся светлее.

Используй сегодня, чтобы подготовить почву для того, что хочешь, чтобы расцвело: протяни руку, запланируй что-то приятное или просто наслаждайся мягким настроением.',
 'Венера и Луна движутся к гармоничному аспекту—ещё не совсем точно, но ты уже можешь почувствовать смягчение. Это фаза нарастания: эмоциональная лёгкость усиливается, и связи кажутся светлее.

Используй сегодня, чтобы подготовить почву для того, что хочешь, чтобы расцвело: протяни руку, запланируй что-то приятное или просто наслаждайся мягким настроением.

Лучшее ещё впереди—но сегодня уже лучше, чем вчера.',
 'Выйди на связь с тем, кто тебе дорог, или запланируй что-то, чем насладишься в ближайшие дни.');

-- Меркурий квадрат Нептун - расходящийся орб (угасает)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_mercury_neptune_fog_separating', 'mercury_square_neptune_separating', '["general", "work"]',
 'Ментальный туман рассеивается. Путаница уходит—сегодня ты начинаешь видеть яснее.',
 'Квадратура Меркурий-Нептун расходится—худшее прошло, и ясность постепенно возвращается. Ты всё ещё можешь чувствовать лёгкую нечёткость, но решения даются легче, чем вчера.

Используй сегодня, чтобы пересмотреть всё, что откладывал во время тумана, и начать двигаться вперёд снова.',
 'Квадратура Меркурий-Нептун расходится—худшее прошло, и ясность постепенно возвращается. Ты всё ещё можешь чувствовать лёгкую нечёткость, но решения даются легче, чем вчера.

Используй сегодня, чтобы пересмотреть всё, что откладывал во время тумана, и начать двигаться вперёд снова.

Доверяй своему уму больше сегодня—он возвращается в строй.',
 'Вернись к одному решению или задаче, которые отложил, и двигай их вперёд.');

-- Юпитер трин Сатурн - широкий орб (фоновая поддержка)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('ru', 'tr_jupiter_saturn_build_wide', 'jupiter_trine_saturn_wide', '["general", "work"]',
 'Медленный, устойчивый прогресс поддерживается на фоне. Никакого фейерверка, просто надёжное строительство.',
 'Юпитер и Сатурн в широком гармоничном аспекте—это не день драматических прорывов, но есть тихая, устойчивая энергия, поддерживающая твои долгосрочные цели.

Используй этот период для последовательной, негламурной работы: той, которая не выглядит впечатляюще, но складывается со временем.',
 'Юпитер и Сатурн в широком гармоничном аспекте—это не день драматических прорывов, но есть тихая, устойчивая энергия, поддерживающая твои долгосрочные цели.

Используй этот период для последовательной, негламурной работы: той, которая не выглядит впечатляюще, но складывается со временем.

Думай о фундаменте, а не о фейерверках.',
 'Сделай одну маленькую, скучную задачу сегодня, которая поддерживает твои долгосрочные цели.');

-- =============================================================================
-- ES locale: Variaciones por orbe
-- =============================================================================

-- Marte cuadratura Sol - orbe exacto (máxima intensidad)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_mars_sun_push_exact', 'mars_square_sun_exact', '["general", "work"]',
 'La tensión está en su pico hoy. Es el momento exacto de la cuadratura Marte-Sol—actúa con decisión o retírate.',
 'Hoy Marte y el Sol forman una cuadratura exacta—el pico de este tránsito. La energía es alta, la paciencia baja, y todo parece urgente. Es el día para canalizar la energía en acción enfocada o conscientemente retroceder para evitar conflictos.

Elige un objetivo claro y dale todo, o toma espacio y deja que la intensidad pase sin actuar sobre ella.',
 'Hoy Marte y el Sol forman una cuadratura exacta—el pico de este tránsito. La energía es alta, la paciencia baja, y todo parece urgente. Es el día para canalizar la energía en acción enfocada o conscientemente retroceder para evitar conflictos.

Elige un objetivo claro y dale todo, o toma espacio y deja que la intensidad pase sin actuar sobre ella.

Si sientes resistencia—pausa. El tránsito exacto magnifica tanto el poder productivo como los impulsos destructivos.',
 'Decide ahora: actúa con enfoque total en una cosa, o descansa conscientemente hasta mañana.');

-- Venus trígono Luna - orbe aplicándose (construyendo)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_venus_moon_harmony_applying', 'venus_trine_moon_applying', '["general", "love"]',
 'La calidez emocional está creciendo. Un día suave que mejorará aún más mañana.',
 'Venus y la Luna se mueven hacia un aspecto armonioso—todavía no es exacto, pero ya puedes sentir el suavizamiento. Esta es la fase de construcción: la facilidad emocional aumenta y las conexiones se sienten más ligeras.

Usa hoy para preparar el terreno para algo que quieres que florezca: comunícate, planea algo bonito o simplemente disfruta del ambiente suave.',
 'Venus y la Luna se mueven hacia un aspecto armonioso—todavía no es exacto, pero ya puedes sentir el suavizamiento. Esta es la fase de construcción: la facilidad emocional aumenta y las conexiones se sienten más ligeras.

Usa hoy para preparar el terreno para algo que quieres que florezca: comunícate, planea algo bonito o simplemente disfruta del ambiente suave.

Lo mejor está por venir—pero hoy ya es mejor que ayer.',
 'Contacta a alguien que te importa, o planea algo que disfrutarás en los próximos días.');

-- Mercurio cuadratura Neptuno - orbe separándose (desvaneciendo)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_mercury_neptune_fog_separating', 'mercury_square_neptune_separating', '["general", "work"]',
 'La niebla mental se está despejando. La confusión se desvanece—hoy empiezas a ver más claro.',
 'La cuadratura Mercurio-Neptuno se está separando—lo peor de la niebla ha pasado y la claridad está regresando gradualmente. Todavía puedes sentirte un poco borroso, pero las decisiones son más fáciles ahora que ayer.

Usa hoy para revisar cualquier cosa que pospusiste durante la niebla, y comienza a avanzar de nuevo.',
 'La cuadratura Mercurio-Neptuno se está separando—lo peor de la niebla ha pasado y la claridad está regresando gradualmente. Todavía puedes sentirte un poco borroso, pero las decisiones son más fáciles ahora que ayer.

Usa hoy para revisar cualquier cosa que pospusiste durante la niebla, y comienza a avanzar de nuevo.

Confía más en tu mente hoy—está volviendo a funcionar.',
 'Revisa una decisión o tarea que dejaste pendiente, y avanza con ella.');

-- Júpiter trígono Saturno - orbe amplio (apoyo de fondo)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('es', 'tr_jupiter_saturn_build_wide', 'jupiter_trine_saturn_wide', '["general", "work"]',
 'El progreso lento y constante tiene apoyo de fondo. Sin fuegos artificiales, solo construcción sólida.',
 'Júpiter y Saturno están en un aspecto armonioso amplio—este no es un día de avances dramáticos, pero hay una energía tranquila y constante apoyando tus metas a largo plazo.

Usa este período para trabajo consistente y sin glamour: el tipo que no se ve impresionante pero se acumula con el tiempo.',
 'Júpiter y Saturno están en un aspecto armonioso amplio—este no es un día de avances dramáticos, pero hay una energía tranquila y constante apoyando tus metas a largo plazo.

Usa este período para trabajo consistente y sin glamour: el tipo que no se ve impresionante pero se acumula con el tiempo.

Piensa en cimientos, no en fuegos artificiales.',
 'Haz una tarea pequeña y aburrida hoy que apoye tus metas a largo plazo.');

COMMIT;
