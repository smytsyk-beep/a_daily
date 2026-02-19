-- Проверка content_atoms и их persona_tags

-- Общая статистика
SELECT 
    COUNT(*) as total_atoms,
    COUNT(DISTINCT trigger) as unique_triggers,
    COUNT(DISTINCT topic_tag) as unique_topics,
    COUNT(*) FILTER (WHERE persona_tags IS NOT NULL) as with_persona_tags
FROM content_atoms;

-- Группировка по persona_tags
SELECT 
    persona_tags::text as tags,
    COUNT(*) as count,
    array_agg(DISTINCT trigger) FILTER (WHERE trigger IS NOT NULL) as example_triggers
FROM content_atoms
GROUP BY persona_tags
ORDER BY count DESC;

-- Примеры атомов с persona_tags
SELECT 
    id,
    locale,
    trigger,
    topic_tag,
    persona_tags,
    LEFT(copy_short, 50) as short_preview
FROM content_atoms
ORDER BY id
LIMIT 20;
