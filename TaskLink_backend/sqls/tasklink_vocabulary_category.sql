-- 词库分类（用于管理端「更新词库」中创建/选择分类）
-- vocabulary.level 存分类名称，与本表 name 对应

DROP TABLE IF EXISTS `vocabulary_category`;
CREATE TABLE `vocabulary_category` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
