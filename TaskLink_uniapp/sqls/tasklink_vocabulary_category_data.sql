-- 词库分类初始数据：与 vocabulary.level 对应，供管理端「更新词库」选择
-- 执行前请确保已创建 vocabulary_category 表（见 tasklink_vocabulary_category.sql）

INSERT INTO `vocabulary_category` (`name`) VALUES
  ('JUNIOR'),
  ('SENIOR'),
  ('CET4'),
  ('CET6'),
  ('TOEFL'),
  ('考研')
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);
