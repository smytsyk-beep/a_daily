-- =============================================================================
-- Seed transit atoms for EN locale
-- =============================================================================
-- 
-- This script:
-- 1. Updates existing EN transit atoms with triggers and copy_long
-- 2. Adds 15+ new transit atoms for EN locale with multiple variants
-- 3. Ensures trigger fields match RU/ES pattern
--
-- =============================================================================

BEGIN;

-- =============================================================================
-- STEP 1: Update existing EN transit atoms with triggers and copy_long
-- =============================================================================

-- EN: venus_trine_moon (find by existing pattern)
UPDATE content_atoms 
SET 
    trigger = 'venus_trine_moon',
    topic_tag = 'tr_venus_moon_harmony',
    persona_tags = '["general", "love", "selfcare"]',
    copy_short = 'Emotions and desires are moving in the same direction today. Perfect for gentle conversations, simple pleasures, and self-care.',
    copy_long = 'Today, Venus and the Moon form a harmonious aspect—one of those days when your feelings and needs don''t conflict. It''s a good time to slow down a bit, listen to yourself and to those close to you.

Focus on simple pleasures and plans without pressure: a calm walk, good food, warm but not heavy conversations. Whenever possible, avoid drama and sharp emotional reactions—the sky supports gentleness and goodwill.',
    body = 'Today, Venus and the Moon form a harmonious aspect—one of those days when your feelings and needs don''t conflict. It''s a good time to slow down a bit, listen to yourself and to those close to you.

Focus on simple pleasures and plans without pressure: a calm walk, good food, warm but not heavy conversations. Whenever possible, avoid drama and sharp emotional reactions—the sky supports gentleness and goodwill.

If there''s an important conversation or decision to make—today is a good moment: you can see both logic and emotions, and account for them without internal conflict.',
    cta = 'Write down one thing you want to do for yourself today, and just do it.'
WHERE locale = 'en' 
  AND id IN (
    SELECT id FROM content_atoms 
    WHERE locale = 'en' 
      AND (trigger = 'venus_trine_moon' OR topic_tag = 'transit_venus_trine_moon')
    LIMIT 1
  );

-- EN: mars_square_sun (find by existing pattern)
UPDATE content_atoms 
SET 
    trigger = 'mars_square_sun',
    topic_tag = 'tr_mars_sun_push',
    persona_tags = '["general", "work", "selfcare"]',
    copy_short = 'More energy, less patience. A good moment to tackle a specific task—if you move step by step and don''t burn yourself out.',
    copy_long = 'Today the sky adds both strength and internal tension. Mars square Sun highlights areas where old limitations feel too tight and you want to accelerate. This transit can be very productive if you channel it into one or two specific tasks, not into conflicts and fighting the world.

Choose a realistic goal for the day: close a pending task, organize a chaotic area of life, or finally make a decision you''ve been postponing. Act decisively, but regularly check your body: tense shoulders, jaw, or heaviness in your stomach are signals to pause and breathe.',
    body = 'Today the sky adds both strength and internal tension. Mars square Sun highlights areas where old limitations feel too tight and you want to accelerate. This transit can be very productive if you channel it into one or two specific tasks, not into conflicts and fighting the world.

Choose a realistic goal for the day: close a pending task, organize a chaotic area of life, or finally make a decision you''ve been postponing. Act decisively, but regularly check your body: tense shoulders, jaw, or heaviness in your stomach are signals to pause and breathe.

If you feel resistance from others—don''t push harder. Instead, clarify your position and give space. The transit will pass, but the burned bridges will remain.',
    cta = 'Pick one concrete task you''ve been avoiding, and close it today with full focus.'
WHERE locale = 'en' 
  AND id IN (
    SELECT id FROM content_atoms 
    WHERE locale = 'en' 
      AND (trigger = 'mars_square_sun' OR topic_tag = 'transit_mars_square_sun')
    LIMIT 1
  );

-- =============================================================================
-- STEP 2: Add new transit atoms for EN locale (15 transits, 2-3 variants each)
-- =============================================================================

-- Transit 1: Sun trine Moon (harmony of inner and outer)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_sun_moon_harmony', 'sun_trine_moon', '["general", "selfcare"]', 
 'Inner needs and outer tasks don''t clash today—they complement each other. A good day for gentle planning.',
 'Today the Sun and Moon form a harmonious aspect—one of those days when your inner needs and outer tasks don''t conflict. It''s a good time to outline plans for the coming week or just breathe out and do something for yourself.

Use this balance: plan what you''ve been putting off, or simply rest without guilt. The sky supports both action and rest—choose what you need right now.',
 'Today the Sun and Moon form a harmonious aspect—one of those days when your inner needs and outer tasks don''t conflict. It''s a good time to outline plans for the coming week or just breathe out and do something for yourself.

Use this balance: plan what you''ve been putting off, or simply rest without guilt. The sky supports both action and rest—choose what you need right now.

If there''s an important conversation or decision—today is the right moment: you see both logic and emotions, and can account for them without internal conflict.',
 'Write down one thing you want to do for yourself today, and just do it.');

-- Variant 2
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_sun_moon_harmony', 'sun_trine_moon', '["general", "work"]',
 'A day when work and personal life don''t pull in opposite directions. Use it for calm progress.',
 'Today your goals and emotional needs move in the same direction. It''s a rare day when you can advance tasks without internal resistance.

Focus on smooth, steady progress: close 2-3 tasks that have been hanging in your list, or plan something important for the coming days.',
 'Today your goals and emotional needs move in the same direction. It''s a rare day when you can advance tasks without internal resistance.

Focus on smooth, steady progress: close 2-3 tasks that have been hanging in your list, or plan something important for the coming days.

If you need to make a decision—today is a good moment: you see both the rational and emotional sides of the question.',
 'Choose one task you''ve been postponing, and calmly close it today.');

-- Transit 2: Mercury sextile Venus (easy communication)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mercury_venus_flow', 'mercury_sextile_venus', '["general", "love", "work"]',
 'Words flow easily and pleasantly today. A good moment for important conversations and agreements.',
 'Mercury and Venus form an easy, supportive aspect—today communication flows more easily than usual. It''s an excellent day for negotiations, difficult conversations, or simply to say something important to a loved one.

Use this day for dialogues you''ve been postponing: clarify relationships, agree on something important, or just be with someone in pleasant conversation.',
 'Mercury and Venus form an easy, supportive aspect—today communication flows more easily than usual. It''s an excellent day for negotiations, difficult conversations, or simply to say something important to a loved one.

Use this day for dialogues you''ve been postponing: clarify relationships, agree on something important, or just be with someone in pleasant conversation.

Words come easily today, and others are more inclined to listen and understand. If you have something to say—say it today.',
 'Text one person you''ve wanted to talk to, and set up a meeting or call.');

-- Variant 2
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mercury_venus_flow', 'mercury_sextile_venus', '["general", "money", "work"]',
 'Negotiations and agreements go smoother today. Good timing for deals and partnerships.',
 'Mercury and Venus together make it easier to find common ground. Today is favorable for any situations where you need to agree, negotiate, or present your ideas.

If you have pending negotiations or need to pitch a project—today is the day. People are more open, words are softer, and compromises are found faster.',
 'Mercury and Venus together make it easier to find common ground. Today is favorable for any situations where you need to agree, negotiate, or present your ideas.

If you have pending negotiations or need to pitch a project—today is the day. People are more open, words are softer, and compromises are found faster.

Use this window for what matters: close a deal, clarify terms, or simply have that conversation you''ve been avoiding.',
 'Send one email or message that you''ve been drafting but haven''t sent yet.');

-- Transit 3: Mars trine Jupiter (productive energy)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mars_jupiter_drive', 'mars_trine_jupiter', '["general", "work", "money"]',
 'Energy and optimism combine today. Good timing to start something new or push forward on stalled projects.',
 'Mars and Jupiter form a supportive aspect—today you have both energy and confidence. It''s one of the best transits for taking action on what you''ve been planning.

Choose 1-2 ambitious goals and move on them decisively. The sky supports bold moves, but not reckless ones—so plan your steps and go.',
 'Mars and Jupiter form a supportive aspect—today you have both energy and confidence. It''s one of the best transits for taking action on what you''ve been planning.

Choose 1-2 ambitious goals and move on them decisively. The sky supports bold moves, but not reckless ones—so plan your steps and go.

If you''ve been waiting for the right moment to launch something—this is it. Trust yourself, but stay grounded.',
 'Pick one project you''ve been planning, and take the first concrete step today.');

-- Variant 2
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mars_jupiter_drive', 'mars_trine_jupiter', '["general", "selfcare", "health"]',
 'Physical energy is high today. Great for workouts, active rest, or tackling physical tasks.',
 'Mars and Jupiter together give you extra physical and mental stamina. Today is perfect for activities that require effort: gym, sports, hiking, or simply tackling tasks you''ve been avoiding because they felt too hard.

Use this boost wisely: don''t overdo it, but don''t waste it either. Move your body, challenge yourself a bit, and enjoy the feeling of strength.',
 'Mars and Jupiter together give you extra physical and mental stamina. Today is perfect for activities that require effort: gym, sports, hiking, or simply tackling tasks you''ve been avoiding because they felt too hard.

Use this boost wisely: don''t overdo it, but don''t waste it either. Move your body, challenge yourself a bit, and enjoy the feeling of strength.

If you''ve been planning to start a new fitness routine or habit—today is a great day to begin.',
 'Do one physical activity that makes you feel strong and alive.');

-- Transit 4: Mercury square Neptune (confusion in communication)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mercury_neptune_fog', 'mercury_square_neptune', '["general", "work"]',
 'Thoughts may be fuzzy today. Double-check details, avoid important decisions if unclear.',
 'Mercury and Neptune in tense aspect can blur clarity. Today is not the best day for signing contracts, making big decisions, or having critical conversations—unless you can afford to revisit them later.

If you must deal with important matters, take extra time to check facts, ask clarifying questions, and avoid assumptions. Confusion is temporary, but hasty decisions last.',
 'Mercury and Neptune in tense aspect can blur clarity. Today is not the best day for signing contracts, making big decisions, or having critical conversations—unless you can afford to revisit them later.

If you must deal with important matters, take extra time to check facts, ask clarifying questions, and avoid assumptions. Confusion is temporary, but hasty decisions last.

Use today for creative work, rest, or anything that doesn''t require sharp precision. The fog will lift in a day or two.',
 'Postpone one decision or conversation until you have more clarity.');

-- Transit 5: Sun conjunct Mercury (mental clarity)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_sun_mercury_clarity', 'sun_conjunct_mercury', '["general", "work"]',
 'Thoughts are clear and focused today. Great for planning, writing, and important conversations.',
 'The Sun and Mercury align, bringing mental clarity and focus. Today is excellent for any work that requires clear thinking: planning, writing, strategizing, or making decisions.

If you''ve been confused about something—today you''re more likely to see it clearly. Use this window to organize your thoughts and priorities.',
 'The Sun and Mercury align, bringing mental clarity and focus. Today is excellent for any work that requires clear thinking: planning, writing, strategizing, or making decisions.

If you''ve been confused about something—today you''re more likely to see it clearly. Use this window to organize your thoughts and priorities.

Good day for important emails, proposals, or any communication where precision matters.',
 'Write down one thing you''ve been unclear about, and make a clear decision or plan about it.');

-- Variant 2
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_sun_mercury_clarity', 'sun_conjunct_mercury', '["general", "selfcare"]',
 'Your inner voice is louder and clearer today. Good time to journal or reflect on what you really want.',
 'Sun conjunct Mercury sharpens your self-awareness. Today you can hear your own thoughts more clearly, making it a good day for reflection and self-inquiry.

If you''ve been avoiding a question about yourself—today you might find the answer. Journaling, meditation, or simply quiet time can be surprisingly insightful.',
 'Sun conjunct Mercury sharpens your self-awareness. Today you can hear your own thoughts more clearly, making it a good day for reflection and self-inquiry.

If you''ve been avoiding a question about yourself—today you might find the answer. Journaling, meditation, or simply quiet time can be surprisingly insightful.

Trust what comes up—it''s likely closer to the truth than usual.',
 'Spend 10 minutes writing down what''s really on your mind, without filtering.');

-- Transit 6: Moon square Mars (emotional tension)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_moon_mars_tension', 'moon_square_mars', '["general", "selfcare"]',
 'Feelings may be sharper today. Watch for irritability and avoid reactive decisions.',
 'The Moon and Mars in tense aspect can amplify emotional reactions. You might feel more irritable, impatient, or reactive than usual. It''s temporary—but easy to act on impulse and regret it later.

If you feel a surge of anger or frustration, pause before acting. Give yourself space to cool down, and address the issue when you''re calmer.',
 'The Moon and Mars in tense aspect can amplify emotional reactions. You might feel more irritable, impatient, or reactive than usual. It''s temporary—but easy to act on impulse and regret it later.

If you feel a surge of anger or frustration, pause before acting. Give yourself space to cool down, and address the issue when you''re calmer.

Physical activity helps: go for a walk, work out, or do something hands-on to release the tension.',
 'If you feel tension building, take 5 minutes to move your body before responding.');

-- Transit 7: Venus conjunct Jupiter (joy and abundance)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_venus_jupiter_joy', 'venus_conjunct_jupiter', '["general", "love", "money"]',
 'Today feels lighter and more generous. Good for celebrations, social time, and treating yourself.',
 'Venus and Jupiter together amplify joy and abundance. Today is one of the best transits for enjoying life: good food, pleasant company, small luxuries, and generosity.

Use this day for what makes you happy: spend time with people you love, treat yourself to something nice, or simply enjoy the lighter mood.',
 'Venus and Jupiter together amplify joy and abundance. Today is one of the best transits for enjoying life: good food, pleasant company, small luxuries, and generosity.

Use this day for what makes you happy: spend time with people you love, treat yourself to something nice, or simply enjoy the lighter mood.

If you''ve been too serious lately—today is permission to lighten up and enjoy.',
 'Do one thing today that feels generous or indulgent, and enjoy it fully.');

-- Variant 2
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_venus_jupiter_joy', 'venus_conjunct_jupiter', '["general", "work", "money"]',
 'Luck and opportunity favor you today. Good timing for pitches, asks, and financial moves.',
 'Venus and Jupiter together are known as the "luck planets." Today is favorable for asking for what you want: a raise, a deal, a favor, or simply putting yourself out there.

People are more generous, open, and willing to say yes. Use this window for what matters.',
 'Venus and Jupiter together are known as the "luck planets." Today is favorable for asking for what you want: a raise, a deal, a favor, or simply putting yourself out there.

People are more generous, open, and willing to say yes. Use this window for what matters.

If you''ve been waiting for the right time to make a big ask—this is it.',
 'Make one ask you''ve been postponing: for money, opportunity, or support.');

-- Transit 8: Mercury trine Saturn (structured thinking)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mercury_saturn_structure', 'mercury_trine_saturn', '["general", "work"]',
 'Thoughts are organized and practical today. Perfect for planning, organizing, and making solid decisions.',
 'Mercury and Saturn form a supportive aspect—today your mind is clear, focused, and realistic. It''s an excellent day for tasks that require structure: planning, organizing, reviewing finances, or making long-term decisions.

Use this clarity for what matters: set up systems, make plans, or tackle tasks that require discipline.',
 'Mercury and Saturn form a supportive aspect—today your mind is clear, focused, and realistic. It''s an excellent day for tasks that require structure: planning, organizing, reviewing finances, or making long-term decisions.

Use this clarity for what matters: set up systems, make plans, or tackle tasks that require discipline.

If you''ve been avoiding something because it feels too complex—today you can break it down and handle it.',
 'Pick one complex task or project, and create a clear step-by-step plan for it.');

-- Transit 9: Mars opposite Saturn (friction and limits)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_mars_saturn_friction', 'mars_opposite_saturn', '["general", "work", "selfcare"]',
 'Effort meets resistance today. Progress may be slower—don''t force it, adjust your pace.',
 'Mars opposite Saturn brings a feeling of pushing against a wall. You want to move fast, but reality says no. This transit is frustrating, but also teaches patience and strategy.

Don''t fight the friction—work with it. Adjust your expectations, break tasks into smaller steps, and accept that today is a slow-burn day.',
 'Mars opposite Saturn brings a feeling of pushing against a wall. You want to move fast, but reality says no. This transit is frustrating, but also teaches patience and strategy.

Don''t fight the friction—work with it. Adjust your expectations, break tasks into smaller steps, and accept that today is a slow-burn day.

If something isn''t working—pause, reassess, and try a different approach. Forcing rarely helps during this transit.',
 'Identify one task where you''re meeting resistance, and try a different approach.');

-- Transit 10: Sun square Saturn (pressure and responsibility)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_sun_saturn_pressure', 'sun_square_saturn', '["general", "work"]',
 'Responsibilities feel heavier today. Focus on essentials, let go of perfectionism.',
 'The Sun and Saturn in tense aspect can make everything feel heavier and more serious. You might feel pressure, self-doubt, or the weight of responsibilities.

This is not a day to judge yourself harshly. Do what must be done, but don''t add extra weight. Progress is progress, even if it''s small.',
 'The Sun and Saturn in tense aspect can make everything feel heavier and more serious. You might feel pressure, self-doubt, or the weight of responsibilities.

This is not a day to judge yourself harshly. Do what must be done, but don''t add extra weight. Progress is progress, even if it''s small.

If you feel stuck—reach out for support, or simply give yourself permission to rest.',
 'Write down one expectation you''re holding, and decide if it''s realistic for today.');

-- Transit 11: Moon conjunct Pluto (intense emotions)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_moon_pluto_intensity', 'moon_conjunct_pluto', '["general", "selfcare"]',
 'Emotions run deep today. Powerful feelings may surface—let them, but don''t act on them immediately.',
 'The Moon and Pluto together bring emotional intensity. You might feel strong emotions, old wounds resurfacing, or a need to dig into something you''ve been avoiding.

This transit is powerful but not always comfortable. Let yourself feel, but don''t make big decisions in the heat of the moment.',
 'The Moon and Pluto together bring emotional intensity. You might feel strong emotions, old wounds resurfacing, or a need to dig into something you''ve been avoiding.

This transit is powerful but not always comfortable. Let yourself feel, but don''t make big decisions in the heat of the moment.

If something comes up—write about it, talk to someone you trust, or simply sit with it. The intensity will pass.',
 'Write down what you''re feeling today, without judgment or trying to fix it.');

-- Transit 12: Sun trine Uranus (spontaneity and breakthroughs)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_sun_uranus_breakthrough', 'sun_trine_uranus', '["general", "work"]',
 'Expect the unexpected today. Good for trying new approaches and breaking old patterns.',
 'The Sun and Uranus in harmonious aspect bring fresh energy and unexpected opportunities. Today is perfect for experimenting, trying something new, or breaking out of routine.

If you''ve been stuck in a rut—today gives you a push to try something different. Trust your instincts, take small risks, and see what happens.',
 'The Sun and Uranus in harmonious aspect bring fresh energy and unexpected opportunities. Today is perfect for experimenting, trying something new, or breaking out of routine.

If you''ve been stuck in a rut—today gives you a push to try something different. Trust your instincts, take small risks, and see what happens.

Breakthroughs often come when you least expect them—stay open.',
 'Try one new approach to an old problem today.');

-- Transit 13: Jupiter trine Saturn (sustainable growth)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_jupiter_saturn_build', 'jupiter_trine_saturn', '["general", "work", "money"]',
 'Vision meets structure today. Perfect for building something solid and long-term.',
 'Jupiter and Saturn together balance expansion and discipline. Today is one of the best transits for making real, sustainable progress on long-term goals.

If you''ve been dreaming big but lacking a plan—today you can bridge the gap. Or if you''ve been too rigid—today you can see the bigger picture.',
 'Jupiter and Saturn together balance expansion and discipline. Today is one of the best transits for making real, sustainable progress on long-term goals.

If you''ve been dreaming big but lacking a plan—today you can bridge the gap. Or if you''ve been too rigid—today you can see the bigger picture.

Use this energy to build something that will last: a project, a habit, a relationship, or a plan.',
 'Take one step today on something you want to build for the long term.');

-- Transit 14: Venus opposite Saturn (relationship reality check)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_venus_saturn_reality', 'venus_opposite_saturn', '["general", "love"]',
 'Relationships may feel more serious or heavy today. Good for honest conversations, not for idealizing.',
 'Venus opposite Saturn brings emotional sobriety. You might feel distance in relationships, notice limitations, or question what''s real versus what''s wishful thinking.

This transit is not fun, but it''s useful. It shows you where relationships need work, where you''re settling, or where you''re avoiding hard truths.',
 'Venus opposite Saturn brings emotional sobriety. You might feel distance in relationships, notice limitations, or question what''s real versus what''s wishful thinking.

This transit is not fun, but it''s useful. It shows you where relationships need work, where you''re settling, or where you''re avoiding hard truths.

If something feels off—don''t ignore it, but also don''t catastrophize. Use today to see clearly, and act later.',
 'Write down one truth about a relationship that you''ve been avoiding.');

-- Transit 15: Venus square Mars (attraction meets friction)
INSERT INTO content_atoms (locale, topic_tag, trigger, persona_tags, copy_short, copy_long, body, cta) VALUES
('en', 'tr_venus_mars_spark', 'venus_square_mars', '["general", "love"]',
 'Attraction and tension both high today. Passion is strong, but so is conflict—tread carefully.',
 'Venus and Mars in tense aspect create a charged atmosphere. There''s chemistry, desire, and intensity—but also friction, misunderstandings, and power struggles.

If you''re in a relationship, this can be passionate or combative (or both). If you''re single, be careful not to chase what''s exciting but ultimately wrong for you.',
 'Venus and Mars in tense aspect create a charged atmosphere. There''s chemistry, desire, and intensity—but also friction, misunderstandings, and power struggles.

If you''re in a relationship, this can be passionate or combative (or both). If you''re single, be careful not to chase what''s exciting but ultimately wrong for you.

Use the energy for creative projects, physical activity, or anything that channels intensity constructively.',
 'Channel one strong feeling you have today into action—creative, physical, or productive.');

COMMIT;
