-- Auto-generated SQLite schema + data
-- Source: database/base.sql (MySQL dump)
-- Generator: scripts/convert_mysql_to_sqlite.py
PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

-- ==================== TABLES ====================
CREATE TABLE IF NOT EXISTS "analysis_logs" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "report_id" INTEGER DEFAULT NULL,
    "log_level" TEXT NOT NULL,
    "log_message" TEXT NOT NULL,
    "log_data" TEXT,
    "created_at" TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "analysis_records" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "gender" TEXT DEFAULT NULL,
    "birth_date" TEXT DEFAULT NULL,
    "birth_time" TEXT DEFAULT NULL,
    "city" TEXT DEFAULT NULL,
    "professional_chart_json" TEXT NOT NULL,
    "ai_analysis_json" TEXT NOT NULL,
    "input_json" TEXT NOT NULL,
    "created_at" TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "analysis_reports" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "report_type" TEXT NOT NULL,
    "name" TEXT DEFAULT NULL,
    "gender" TEXT DEFAULT NULL,
    "birth_date" TEXT DEFAULT NULL,
    "birth_time" TEXT DEFAULT NULL,
    "city" TEXT DEFAULT NULL,
    "question" TEXT,
    "input_data" TEXT,
    "chart_data" TEXT,
    "ai_analysis" TEXT,
    "status" TEXT DEFAULT 'completed',
    "error_message" TEXT,
    "ai_model" TEXT DEFAULT NULL,
    "token_usage" INTEGER DEFAULT 0,
    "created_at" TEXT DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "ba_gua" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "num" INTEGER NOT NULL,
    "name" TEXT NOT NULL,
    "nature" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "wuxing" TEXT NOT NULL,
    "description" TEXT
);
CREATE TABLE IF NOT EXISTS "changsheng_lookup" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "gan" TEXT NOT NULL,
    "zhi" TEXT NOT NULL,
    "stage_name" TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "city_coords" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "city_name" TEXT NOT NULL,
    "longitude" REAL NOT NULL,
    "latitude" REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS "di_zhi" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "zhi" TEXT NOT NULL,
    "wuxing" TEXT NOT NULL,
    "yinyang" TEXT NOT NULL,
    "direction" TEXT DEFAULT NULL,
    "season" TEXT DEFAULT NULL,
    "lunar_month" TEXT DEFAULT NULL,
    "hour_range" TEXT DEFAULT NULL,
    "meaning" TEXT,
    "organ" TEXT DEFAULT NULL,
    "idx" INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS "di_zhi_chong" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "zhi_pair" TEXT NOT NULL,
    "description" TEXT
);
CREATE TABLE IF NOT EXISTS "di_zhi_hai" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "zhi_pair" TEXT NOT NULL,
    "description" TEXT
);
CREATE TABLE IF NOT EXISTS "di_zhi_he" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "zhi_pair" TEXT NOT NULL,
    "hua_wuxing" TEXT NOT NULL,
    "he_name" TEXT DEFAULT NULL,
    "description" TEXT
);
CREATE TABLE IF NOT EXISTS "di_zhi_hidden_gan" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "zhi" TEXT NOT NULL,
    "hidden_gan" TEXT NOT NULL,
    "qi_type" TEXT NOT NULL,
    "qi_score" REAL NOT NULL,
    "sort_order" INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "di_zhi_san_he" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "zhi_group" TEXT NOT NULL,
    "hua_wuxing" TEXT NOT NULL,
    "description" TEXT
);
CREATE TABLE IF NOT EXISTS "di_zhi_xing" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "zhi_group" TEXT NOT NULL,
    "xing_type" TEXT DEFAULT NULL,
    "description" TEXT
);
CREATE TABLE IF NOT EXISTS "foundation_terms" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "term_type" TEXT DEFAULT NULL,
    "brief" TEXT DEFAULT NULL,
    "description" TEXT,
    "details" TEXT,
    "influences" TEXT,
    "related_terms" TEXT
);
CREATE TABLE IF NOT EXISTS "ganzhi_relation_terms" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "term_type" TEXT DEFAULT NULL,
    "brief" TEXT DEFAULT NULL,
    "description" TEXT,
    "details" TEXT,
    "influences" TEXT,
    "related_terms" TEXT
);
CREATE TABLE IF NOT EXISTS "hexagram_64" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "hexagram_id" INTEGER NOT NULL,
    "name" TEXT NOT NULL,
    "upper_num" INTEGER NOT NULL,
    "lower_num" INTEGER NOT NULL,
    "wuxing" TEXT DEFAULT NULL,
    "description" TEXT,
    "judgment" TEXT DEFAULT NULL,
    "gua_ci" TEXT
);
CREATE TABLE IF NOT EXISTS "hexagram_yao_ci" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "hexagram_id" INTEGER NOT NULL,
    "yao_name" TEXT NOT NULL,
    "yao_text" TEXT,
    "meaning" TEXT,
    "yao_order" INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS "jie_qi" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "idx" INTEGER NOT NULL,
    "name" TEXT NOT NULL,
    "angle" INTEGER NOT NULL,
    "is_major" INTEGER DEFAULT 0,
    "base_days" REAL DEFAULT NULL
);
CREATE TABLE IF NOT EXISTS "jie_qi_month_map" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "jie_qi_idx" INTEGER NOT NULL,
    "month_zhi" TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "meihua_knowledge" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "section" TEXT NOT NULL,
    "subsection" TEXT DEFAULT NULL,
    "content_key" TEXT NOT NULL,
    "content_value" TEXT
);
CREATE TABLE IF NOT EXISTS "meihua_terms" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "term_type" TEXT DEFAULT NULL,
    "brief" TEXT DEFAULT NULL,
    "description" TEXT,
    "details" TEXT,
    "influences" TEXT,
    "related_terms" TEXT
);
CREATE TABLE IF NOT EXISTS "month_gan_rules" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "year_gan_group" TEXT NOT NULL,
    "month_order" INTEGER NOT NULL,
    "month_gan" TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "nayin_wuxing" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "ganzhi_pair" TEXT NOT NULL,
    "nayin_name" TEXT NOT NULL,
    "wuxing" TEXT NOT NULL,
    "description" TEXT
);
CREATE TABLE IF NOT EXISTS "pan_records" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "user_id" INTEGER NOT NULL,
    "name" TEXT NOT NULL,
    "gender" TEXT DEFAULT NULL,
    "birth_date" TEXT DEFAULT NULL,
    "birth_time" TEXT DEFAULT NULL,
    "city" TEXT DEFAULT NULL,
    "pan_type" TEXT DEFAULT NULL,
    "result_json" TEXT NOT NULL,
    "ai_json" TEXT,
    "created_at" TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "shensha_terms" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "term_type" TEXT DEFAULT NULL,
    "brief" TEXT DEFAULT NULL,
    "description" TEXT,
    "check_method" TEXT,
    "influences" TEXT,
    "related_terms" TEXT
);
CREATE TABLE IF NOT EXISTS "shier_changsheng" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "stage" INTEGER NOT NULL,
    "meaning" TEXT,
    "characteristics" TEXT,
    "influence" TEXT
);
CREATE TABLE IF NOT EXISTS "shishen_knowledge" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "shishen_type" TEXT NOT NULL,
    "yinyang_relation" TEXT DEFAULT NULL,
    "description" TEXT,
    "meaning" TEXT,
    "positive_traits" TEXT,
    "negative_traits" TEXT,
    "career_advice" TEXT,
    "wealth_advice" TEXT,
    "love_advice" TEXT
);
CREATE TABLE IF NOT EXISTS "shishen_map" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "shishen_type" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "yang_name" TEXT DEFAULT NULL,
    "yin_name" TEXT DEFAULT NULL
);
CREATE TABLE IF NOT EXISTS "sixty_jiazi" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "idx" INTEGER NOT NULL,
    "ganzhi" TEXT NOT NULL,
    "gan" TEXT NOT NULL,
    "zhi" TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "tian_gan" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "gan" TEXT NOT NULL,
    "wuxing" TEXT NOT NULL,
    "yinyang" TEXT NOT NULL,
    "direction" TEXT DEFAULT NULL,
    "season" TEXT DEFAULT NULL,
    "meaning" TEXT,
    "organ" TEXT DEFAULT NULL,
    "body" TEXT DEFAULT NULL,
    "idx" INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS "tian_gan_he" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "gan_pair" TEXT NOT NULL,
    "hua_wuxing" TEXT NOT NULL,
    "he_name" TEXT DEFAULT NULL,
    "description" TEXT
);
CREATE TABLE IF NOT EXISTS "users" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "username" TEXT NOT NULL,
    "password_hash" TEXT NOT NULL,
    "created_at" TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "wuxing_knowledge" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "wuxing_name" TEXT NOT NULL,
    "nature" TEXT DEFAULT NULL,
    "direction" TEXT DEFAULT NULL,
    "season" TEXT DEFAULT NULL,
    "color" TEXT DEFAULT NULL,
    "organs" TEXT,
    "taste" TEXT DEFAULT NULL,
    "luck_number" INTEGER DEFAULT NULL,
    "positive_traits" TEXT,
    "negative_traits" TEXT,
    "careers" TEXT,
    "health_advice" TEXT,
    "description" TEXT,
    "characteristics" TEXT
);
CREATE TABLE IF NOT EXISTS "wuxing_relations" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "relation_type" TEXT NOT NULL,
    "relation_name" TEXT NOT NULL,
    "description" TEXT,
    "from_wuxing" TEXT NOT NULL,
    "to_wuxing" TEXT NOT NULL,
    "meaning" TEXT
);
CREATE TABLE IF NOT EXISTS "yue_ling_weight" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "zhi" TEXT NOT NULL,
    "wuxing" TEXT NOT NULL,
    "weight" REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS "yunshi_gan_analysis" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "gan" TEXT NOT NULL,
    "positive_desc" TEXT,
    "negative_desc" TEXT
);
CREATE TABLE IF NOT EXISTS "yunshi_zhi_analysis" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "zhi" TEXT NOT NULL,
    "description" TEXT
);

-- ==================== INDEXES ====================
CREATE INDEX IF NOT EXISTS "analysis_logs_idx_report_id" ON "analysis_logs" ("report_id");
CREATE INDEX IF NOT EXISTS "analysis_logs_idx_log_level" ON "analysis_logs" ("log_level");
CREATE INDEX IF NOT EXISTS "analysis_logs_idx_created_at" ON "analysis_logs" ("created_at");
CREATE INDEX IF NOT EXISTS "analysis_reports_idx_report_type" ON "analysis_reports" ("report_type");
CREATE INDEX IF NOT EXISTS "analysis_reports_idx_status" ON "analysis_reports" ("status");
CREATE INDEX IF NOT EXISTS "analysis_reports_idx_created_at" ON "analysis_reports" ("created_at");
CREATE INDEX IF NOT EXISTS "analysis_reports_idx_name" ON "analysis_reports" ("name");
CREATE UNIQUE INDEX IF NOT EXISTS "ba_gua_num" ON "ba_gua" ("num");
CREATE UNIQUE INDEX IF NOT EXISTS "changsheng_lookup_uk_gan_zhi" ON "changsheng_lookup" ("gan", "zhi");
CREATE UNIQUE INDEX IF NOT EXISTS "city_coords_city_name" ON "city_coords" ("city_name");
CREATE INDEX IF NOT EXISTS "city_coords_idx_city" ON "city_coords" ("city_name");
CREATE UNIQUE INDEX IF NOT EXISTS "di_zhi_zhi" ON "di_zhi" ("zhi");
CREATE INDEX IF NOT EXISTS "di_zhi_idx_zhi" ON "di_zhi" ("zhi");
CREATE UNIQUE INDEX IF NOT EXISTS "di_zhi_chong_zhi_pair" ON "di_zhi_chong" ("zhi_pair");
CREATE UNIQUE INDEX IF NOT EXISTS "di_zhi_hai_zhi_pair" ON "di_zhi_hai" ("zhi_pair");
CREATE UNIQUE INDEX IF NOT EXISTS "di_zhi_he_zhi_pair" ON "di_zhi_he" ("zhi_pair");
CREATE INDEX IF NOT EXISTS "di_zhi_hidden_gan_idx_zhi_hg" ON "di_zhi_hidden_gan" ("zhi");
CREATE UNIQUE INDEX IF NOT EXISTS "di_zhi_san_he_zhi_group" ON "di_zhi_san_he" ("zhi_group");
CREATE UNIQUE INDEX IF NOT EXISTS "di_zhi_xing_zhi_group" ON "di_zhi_xing" ("zhi_group");
CREATE UNIQUE INDEX IF NOT EXISTS "foundation_terms_name" ON "foundation_terms" ("name");
CREATE UNIQUE INDEX IF NOT EXISTS "ganzhi_relation_terms_name" ON "ganzhi_relation_terms" ("name");
CREATE UNIQUE INDEX IF NOT EXISTS "hexagram_64_hexagram_id" ON "hexagram_64" ("hexagram_id");
CREATE INDEX IF NOT EXISTS "hexagram_64_idx_upper_lower" ON "hexagram_64" ("upper_num", "lower_num");
CREATE INDEX IF NOT EXISTS "hexagram_yao_ci_idx_hexagram_yao" ON "hexagram_yao_ci" ("hexagram_id");
CREATE UNIQUE INDEX IF NOT EXISTS "jie_qi_idx" ON "jie_qi" ("idx");
CREATE INDEX IF NOT EXISTS "jie_qi_month_map_idx_jqmm" ON "jie_qi_month_map" ("jie_qi_idx");
CREATE UNIQUE INDEX IF NOT EXISTS "meihua_knowledge_uk_section_key" ON "meihua_knowledge" ("section", "content_key");
CREATE UNIQUE INDEX IF NOT EXISTS "meihua_terms_name" ON "meihua_terms" ("name");
CREATE UNIQUE INDEX IF NOT EXISTS "month_gan_rules_uk_yg_mo" ON "month_gan_rules" ("year_gan_group", "month_order");
CREATE UNIQUE INDEX IF NOT EXISTS "nayin_wuxing_ganzhi_pair" ON "nayin_wuxing" ("ganzhi_pair");
CREATE INDEX IF NOT EXISTS "pan_records_idx_user_id" ON "pan_records" ("user_id");
CREATE INDEX IF NOT EXISTS "pan_records_idx_created_at" ON "pan_records" ("created_at");
CREATE UNIQUE INDEX IF NOT EXISTS "shensha_terms_name" ON "shensha_terms" ("name");
CREATE UNIQUE INDEX IF NOT EXISTS "shier_changsheng_name" ON "shier_changsheng" ("name");
CREATE UNIQUE INDEX IF NOT EXISTS "shishen_knowledge_name" ON "shishen_knowledge" ("name");
CREATE INDEX IF NOT EXISTS "shishen_map_idx_ss_type" ON "shishen_map" ("shishen_type");
CREATE UNIQUE INDEX IF NOT EXISTS "sixty_jiazi_idx" ON "sixty_jiazi" ("idx");
CREATE INDEX IF NOT EXISTS "sixty_jiazi_idx_ganzhi" ON "sixty_jiazi" ("ganzhi");
CREATE UNIQUE INDEX IF NOT EXISTS "tian_gan_gan" ON "tian_gan" ("gan");
CREATE INDEX IF NOT EXISTS "tian_gan_idx_gan" ON "tian_gan" ("gan");
CREATE UNIQUE INDEX IF NOT EXISTS "tian_gan_he_gan_pair" ON "tian_gan_he" ("gan_pair");
CREATE UNIQUE INDEX IF NOT EXISTS "users_username" ON "users" ("username");
CREATE INDEX IF NOT EXISTS "users_idx_username" ON "users" ("username");
CREATE UNIQUE INDEX IF NOT EXISTS "wuxing_knowledge_wuxing_name" ON "wuxing_knowledge" ("wuxing_name");
CREATE INDEX IF NOT EXISTS "wuxing_relations_idx_relation_type" ON "wuxing_relations" ("relation_type");
CREATE UNIQUE INDEX IF NOT EXISTS "yue_ling_weight_uk_zhi_wx" ON "yue_ling_weight" ("zhi", "wuxing");
CREATE UNIQUE INDEX IF NOT EXISTS "yunshi_gan_analysis_gan" ON "yunshi_gan_analysis" ("gan");
CREATE UNIQUE INDEX IF NOT EXISTS "yunshi_zhi_analysis_zhi" ON "yunshi_zhi_analysis" ("zhi");

-- ==================== DATA ====================
INSERT INTO "analysis_logs" VALUES (1, 1, 'INFO', '测试日志', '{
    "test": true
}', '2026-06-22 15:15:30');
INSERT INTO "analysis_logs" VALUES (2, 2, 'INFO', '八字分析流程开始', '{
    "input_data": {
        "day": 15,
        "city": "北京",
        "hour": 14,
        "name": "测试命主",
        "year": 1990,
        "month": 5,
        "gender": "男",
        "minute": 30
    }
}', '2026-06-22 15:15:30');
INSERT INTO "analysis_logs" VALUES (3, 2, 'INFO', '排盘数据已准备', NULL, '2026-06-22 15:15:30');
INSERT INTO "analysis_logs" VALUES (4, 2, 'INFO', 'AI分析完成', '{
    "token_usage": 870,
    "analysis_fields": [
        "personality",
        "career",
        "marriage",
        "health",
        "suggestions"
    ]
}', '2026-06-22 15:15:55');
INSERT INTO "analysis_logs" VALUES (5, 3, 'INFO', '梅花易数分析流程开始', '{
    "method": "time",
    "question": "近期事业发展如何？"
}', '2026-06-22 15:15:55');
INSERT INTO "analysis_logs" VALUES (6, 3, 'INFO', 'AI分析完成', '{
    "token_usage": 1120,
    "analysis_fields": [
        "gua_overview",
        "situation_analysis",
        "good_omens",
        "bad_omens",
        "action_advice",
        "final_verdict"
    ]
}', '2026-06-22 15:16:31');
INSERT INTO "analysis_logs" VALUES (7, 4, 'INFO', '测试日志', '{
    "test": true
}', '2026-06-22 15:17:11');
INSERT INTO "analysis_logs" VALUES (8, 5, 'INFO', '八字分析流程开始', '{
    "input_data": {
        "day": 15,
        "city": "北京",
        "hour": 14,
        "name": "测试命主",
        "year": 1990,
        "month": 5,
        "gender": "男",
        "minute": 30
    }
}', '2026-06-22 15:17:11');
INSERT INTO "analysis_logs" VALUES (9, 5, 'INFO', '排盘数据已准备', NULL, '2026-06-22 15:17:11');
INSERT INTO "analysis_logs" VALUES (10, 5, 'INFO', 'AI分析完成', '{
    "token_usage": 1202,
    "analysis_fields": [
        "personality",
        "career",
        "marriage",
        "health",
        "suggestions"
    ]
}', '2026-06-22 15:17:31');
INSERT INTO "analysis_logs" VALUES (11, 6, 'INFO', '梅花易数分析流程开始', '{
    "method": "time",
    "question": "近期事业发展如何？"
}', '2026-06-22 15:17:31');
INSERT INTO "analysis_logs" VALUES (12, 6, 'INFO', 'AI分析完成', '{
    "token_usage": 1266,
    "analysis_fields": [
        "gua_overview",
        "situation_analysis",
        "good_omens",
        "bad_omens",
        "action_advice",
        "final_verdict"
    ]
}', '2026-06-22 15:18:15');
INSERT INTO "analysis_logs" VALUES (13, 7, 'INFO', '八字分析流程开始', '{
    "input_data": {
        "day": 22,
        "city": "北京",
        "hour": 12,
        "name": "张超超",
        "year": 2026,
        "month": 6,
        "notes": "",
        "gender": "男",
        "minute": 0,
        "age_type": "虚岁",
        "is_lunar": false,
        "latitude": 39.9042,
        "pan_type": "bazi",
        "leap_rule": "归前",
        "longitude": 116.4074,
        "hour_index": 6,
        "is_early_zi": false,
        "solar_time_mode": "自动"
    }
}', '2026-06-22 23:00:57');
INSERT INTO "analysis_logs" VALUES (14, 7, 'INFO', '排盘数据已准备', NULL, '2026-06-22 23:00:57');
INSERT INTO "analysis_logs" VALUES (15, 7, 'INFO', 'AI分析完成', '{
    "token_usage": 1233,
    "analysis_fields": [
        "personality",
        "career",
        "marriage",
        "health",
        "suggestions"
    ]
}', '2026-06-22 23:01:37');
INSERT INTO "analysis_logs" VALUES (16, 8, 'INFO', '八字分析流程开始', '{
    "input_data": {
        "day": 22,
        "city": "北京",
        "hour": 12,
        "name": "张超超",
        "year": 2026,
        "month": 6,
        "notes": "",
        "gender": "男",
        "minute": 0,
        "age_type": "虚岁",
        "is_lunar": false,
        "latitude": 39.9042,
        "pan_type": "bazi",
        "leap_rule": "归前",
        "longitude": 116.4074,
        "hour_index": 6,
        "is_early_zi": false,
        "solar_time_mode": "自动"
    }
}', '2026-06-22 23:35:09');
INSERT INTO "analysis_logs" VALUES (17, 8, 'INFO', '排盘数据已准备', NULL, '2026-06-22 23:35:09');
INSERT INTO "analysis_logs" VALUES (18, 8, 'INFO', 'AI分析完成', '{
    "token_usage": 958,
    "analysis_fields": [
        "personality",
        "career",
        "marriage",
        "health",
        "suggestions"
    ]
}', '2026-06-22 23:35:37');
INSERT INTO "analysis_logs" VALUES (19, 9, 'INFO', '八字分析流程开始', '{
    "input_data": {
        "day": 22,
        "city": "北京",
        "hour": 12,
        "name": "张超超",
        "year": 2026,
        "month": 6,
        "notes": "",
        "gender": "男",
        "minute": 0,
        "age_type": "虚岁",
        "is_lunar": false,
        "latitude": 39.9042,
        "pan_type": "ziwei",
        "leap_rule": "归前",
        "longitude": 116.4074,
        "hour_index": 6,
        "is_early_zi": false,
        "solar_time_mode": "自动"
    }
}', '2026-06-22 23:36:33');
INSERT INTO "analysis_logs" VALUES (20, 9, 'INFO', '排盘数据已准备', NULL, '2026-06-22 23:36:33');
INSERT INTO "analysis_logs" VALUES (21, 9, 'INFO', 'AI分析完成', '{
    "token_usage": 1300,
    "analysis_fields": [
        "personality",
        "career",
        "marriage",
        "health",
        "suggestions"
    ]
}', '2026-06-22 23:36:55');
INSERT INTO "analysis_logs" VALUES (22, 10, 'INFO', '八字分析流程开始', '{
    "input_data": {
        "day": 23,
        "city": "北京",
        "hour": 12,
        "name": "张超超",
        "year": 2026,
        "month": 6,
        "notes": "",
        "gender": "男",
        "minute": 0,
        "age_type": "虚岁",
        "is_lunar": false,
        "latitude": 39.9042,
        "pan_type": "bazi",
        "leap_rule": "归前",
        "longitude": 116.4074,
        "hour_index": 6,
        "is_early_zi": false,
        "solar_time_mode": "自动"
    }
}', '2026-06-23 11:12:21');
INSERT INTO "analysis_logs" VALUES (23, 10, 'INFO', '排盘数据已准备', NULL, '2026-06-23 11:12:21');
INSERT INTO "analysis_logs" VALUES (24, 10, 'INFO', 'AI分析完成', '{
    "token_usage": 1156,
    "analysis_fields": [
        "personality",
        "career",
        "marriage",
        "health",
        "suggestions"
    ]
}', '2026-06-23 11:13:05');
INSERT INTO "analysis_logs" VALUES (25, 11, 'INFO', '八字分析流程开始', '{
    "input_data": {
        "day": 23,
        "city": "北京",
        "hour": 12,
        "name": "张超超",
        "year": 2026,
        "month": 6,
        "notes": "",
        "gender": "男",
        "minute": 0,
        "age_type": "虚岁",
        "is_lunar": false,
        "latitude": 39.9042,
        "pan_type": "bazi",
        "leap_rule": "归前",
        "longitude": 116.4074,
        "hour_index": 6,
        "is_early_zi": false,
        "solar_time_mode": "自动"
    }
}', '2026-06-23 11:33:16');
INSERT INTO "analysis_logs" VALUES (26, 11, 'INFO', '排盘数据已准备', NULL, '2026-06-23 11:33:16');
INSERT INTO "analysis_logs" VALUES (27, 12, 'INFO', '八字分析流程开始', '{
    "input_data": {
        "day": 24,
        "city": "北京",
        "hour": 12,
        "name": "张超超",
        "year": 2026,
        "month": 6,
        "notes": "",
        "gender": "男",
        "minute": 0,
        "age_type": "虚岁",
        "is_lunar": false,
        "latitude": 39.9042,
        "pan_type": "bazi",
        "leap_rule": "归前",
        "longitude": 116.4074,
        "hour_index": 6,
        "is_early_zi": false,
        "solar_time_mode": "自动"
    }
}', '2026-06-24 09:06:55');
INSERT INTO "analysis_logs" VALUES (28, 12, 'INFO', '排盘数据已准备', NULL, '2026-06-24 09:06:55');
INSERT INTO "analysis_logs" VALUES (29, 13, 'INFO', '八字分析流程开始', '{
    "input_data": {
        "day": 24,
        "city": "北京",
        "hour": 12,
        "name": "张超超",
        "year": 2026,
        "month": 6,
        "notes": "",
        "gender": "男",
        "minute": 0,
        "age_type": "虚岁",
        "is_lunar": false,
        "latitude": 39.9042,
        "pan_type": "bazi",
        "leap_rule": "归前",
        "longitude": 116.4074,
        "hour_index": 6,
        "is_early_zi": false,
        "solar_time_mode": "自动"
    }
}', '2026-06-24 09:15:53');
INSERT INTO "analysis_logs" VALUES (30, 13, 'INFO', '排盘数据已准备', NULL, '2026-06-24 09:15:53');
INSERT INTO "analysis_logs" VALUES (31, 14, 'INFO', '八字分析流程开始', '{
    "input_data": {
        "day": 24,
        "city": "北京",
        "hour": 12,
        "name": "张超超",
        "year": 2026,
        "month": 6,
        "notes": "",
        "gender": "男",
        "minute": 0,
        "age_type": "虚岁",
        "is_lunar": false,
        "latitude": 39.9042,
        "pan_type": "bazi",
        "leap_rule": "归前",
        "longitude": 116.4074,
        "hour_index": 6,
        "is_early_zi": false,
        "solar_time_mode": "自动"
    }
}', '2026-06-24 09:32:10');
INSERT INTO "analysis_logs" VALUES (32, 14, 'INFO', '排盘数据已准备', NULL, '2026-06-24 09:32:10');
INSERT INTO "analysis_logs" VALUES (33, 15, 'INFO', '八字分析流程开始', '{
    "input_data": {
        "day": 24,
        "city": "北京",
        "hour": 12,
        "name": "张超超",
        "year": 2026,
        "month": 6,
        "notes": "",
        "gender": "男",
        "minute": 0,
        "age_type": "虚岁",
        "is_lunar": false,
        "latitude": 39.9042,
        "pan_type": "bazi",
        "leap_rule": "归前",
        "longitude": 116.4074,
        "hour_index": 6,
        "is_early_zi": false,
        "solar_time_mode": "自动"
    }
}', '2026-06-24 09:34:58');
INSERT INTO "analysis_logs" VALUES (34, 15, 'INFO', '排盘数据已准备', NULL, '2026-06-24 09:34:58');
INSERT INTO "analysis_logs" VALUES (35, 15, 'INFO', 'AI分析完成', '{
    "token_usage": 4053,
    "analysis_fields": [
        "personality",
        "career",
        "marriage",
        "health",
        "suggestions",
        "pattern_analysis",
        "wuxing_balance",
        "shishen_analysis"
    ]
}', '2026-06-24 09:36:46');
INSERT INTO "analysis_logs" VALUES (36, 16, 'INFO', '梅花易数分析流程开始', '{
    "method": "time",
    "question": "事业发展如何？"
}', '2026-06-24 09:41:51');
INSERT INTO "analysis_logs" VALUES (37, 16, 'INFO', 'AI分析完成', '{
    "token_usage": 1210,
    "analysis_fields": [
        "gua_overview",
        "situation_analysis",
        "good_omens",
        "bad_omens",
        "action_advice",
        "final_verdict"
    ]
}', '2026-06-24 09:42:12');
INSERT INTO "analysis_logs" VALUES (38, 17, 'INFO', '梅花易数分析流程开始', '{
    "method": "number",
    "question": "我和我老婆之间的感情如何？"
}', '2026-06-24 09:54:21');
INSERT INTO "analysis_logs" VALUES (39, 17, 'INFO', 'AI分析完成', '{
    "token_usage": 1258,
    "analysis_fields": [
        "gua_overview",
        "situation_analysis",
        "good_omens",
        "bad_omens",
        "action_advice",
        "final_verdict"
    ]
}', '2026-06-24 09:54:55');
INSERT INTO "analysis_logs" VALUES (40, 18, 'INFO', '八字分析流程开始', '{
    "input_data": {
        "day": 28,
        "city": "北京",
        "hour": 12,
        "name": "张超超",
        "year": 2026,
        "month": 6,
        "notes": "",
        "gender": "男",
        "minute": 0,
        "age_type": "虚岁",
        "is_lunar": false,
        "latitude": 39.9042,
        "pan_type": "bazi",
        "leap_rule": "归前",
        "longitude": 116.4074,
        "hour_index": 6,
        "is_early_zi": false,
        "solar_time_mode": "自动"
    }
}', '2026-06-28 17:29:48');
INSERT INTO "analysis_logs" VALUES (41, 18, 'INFO', '排盘数据已准备', NULL, '2026-06-28 17:29:48');
INSERT INTO "analysis_logs" VALUES (42, 19, 'INFO', '八字分析流程开始', '{
    "input_data": {
        "day": 28,
        "city": "北京",
        "hour": 12,
        "name": "张超超",
        "year": 2026,
        "month": 6,
        "notes": "",
        "gender": "男",
        "minute": 0,
        "age_type": "虚岁",
        "is_lunar": false,
        "latitude": 39.9042,
        "pan_type": "bazi",
        "leap_rule": "归前",
        "longitude": 116.4074,
        "hour_index": 6,
        "is_early_zi": false,
        "solar_time_mode": "自动"
    }
}', '2026-06-28 17:30:14');
INSERT INTO "analysis_logs" VALUES (43, 19, 'INFO', '排盘数据已准备', NULL, '2026-06-28 17:30:14');
INSERT INTO "analysis_logs" VALUES (44, 20, 'INFO', '梅花易数分析流程开始', '{
    "method": "time",
    "question": ""
}', '2026-06-28 17:45:23');
INSERT INTO "analysis_records" VALUES (2, '张超超', '男', '2026-06-14', '12:00', '北京', '{"user_profile": {"name": "张超超", "gender": "男", "birth_date": "2026-06-14", "birth_time": "12:00", "calendar_type": "公历", "city": "北京"}, "basic_chart": {"solar_date": "2026-6-14", "lunar_date": "2026年4月29日", "pillars": {"year": "丙午", "month": "乙巳", "day": "己酉", "hour": "庚午"}, "day_master": "己"}, "wuxing_analysis": {"summary": "水偏弱", "day_master_element": "", "strength": "", "favorable_elements": "", "unfavorable_elements": "", "distribution": {"木": {"count": 1, "elements": ["乙"], "percentage": 8.3}, "火": {"count": 5.5, "elements": ["丙", "午", "午中藏丁", "巳", "巳中藏丙", "午", "午中藏丁"], "percentage": 45.8}, "土": {"count": 2.5, "elements": ["午中藏己", "巳中藏戊", "己", "午中藏己"], "percentage": 20.8}, "金": {"count": 3.0, "elements": ["巳中藏庚", "酉", "酉中藏辛", "庚"], "percentage": 25.0}, "水": {"count": 0, "elements": [], "percentage": 0.0}}}, "shishen_analysis": {"summary": {"正财": 1, "偏印": 1, "比肩": 1, "伤官": 1}, "details": [{"pillar": "年柱", "ganzhi": "丙午", "gan": "丙", "gan_shishen": "正财", "zhi": "午", "zhi_shishens": ["丁(正官)", "己(比肩)"]}, {"pillar": "月柱", "ganzhi": "乙巳", "gan": "乙", "gan_shishen": "偏印", "zhi": "巳", "zhi_shishens": ["丙(正财)", "戊(伤官)", "庚(伤官)"]}, {"pillar": "日柱", "ganzhi": "己酉", "gan": "己", "gan_shishen": "比肩", "zhi": "酉", "zhi_shishens": ["辛(正官)"]}, {"pillar": "时柱", "ganzhi": "庚午", "gan": "庚", "gan_shishen": "伤官", "zhi": "午", "zhi_shishens": ["丁(正官)", "己(比肩)"]}]}, "mingli_analysis": {"self_seat": {"day_gan": "己", "day_zhi": "酉", "relationship": "生日", "hidden_stems": ["辛"], "description": "日主己(土)，自坐酉(金)；日支与日主关系：生日；日支藏干：辛(金)"}, "kongwang": {"year_kongwang": ["辰", "巳"], "day_kongwang": ["寅", "卯"], "affected_pillars": [{"pillar": "月柱", "ganzhi": "乙巳", "kongwang_type": "年空"}], "description": "年空：[''辰'', ''巳'']；日空：[''寅'', ''卯'']"}, "ganzhi_relations": {"gan_relations": ["丙克庚", "乙克己"], "zhi_relations": ["午刑午"]}, "hidden_stems": ["年柱地支午藏干：丁(火)、己(土)", "月柱地支巳藏干：丙(火)、戊(土)、庚(金)", "日柱地支酉藏干：辛(金)", "时柱地支午藏干：丁(火)、己(土)"], "positive_shensha": ["文昌", "天乙"], "negative_shensha": []}, "major_fortune": {"direction": "逆行", "periods": [{"period": 1, "age_range": "0-9岁", "ganzhi": "乙巳", "direction": "逆行", "description": "乙木柔韧，善于变通，主智慧、文雅、富有艺术气质；巳火热情，主活力四射，但需防急躁冲动"}, {"period": 2, "age_range": "20-29岁", "ganzhi": "甲辰", "direction": "逆行", "description": "甲木参天，蓬勃向上，主创新、开拓、积极进取；辰土藏龙，主潜力无限，但需防优柔寡断"}, {"period": 3, "age_range": "30-39岁", "ganzhi": "癸卯", "direction": "逆行", "description": "癸水柔顺，聪明伶俐，主敏感、细腻、富有想象力；卯木柔顺，主文雅艺术，但需防犹豫不决"}, {"period": 4, "age_range": "40-49岁", "ganzhi": "壬寅", "direction": "逆行", "description": "壬水奔腾，活力充沛，主智慧、灵活、适应能力强；寅木生发，主积极进取，但需防冲动鲁莽"}, {"period": 5, "age_range": "50-59岁", "ganzhi": "辛丑", "direction": "逆行", "description": "辛金清秀，才华出众，主聪慧、优雅、追求完美；丑土厚重，主稳重踏实，但需防固执保守"}, {"period": 6, "age_range": "60-69岁", "ganzhi": "庚子", "direction": "逆行", "description": "庚金锐利，果断刚毅，主决断、勇敢、事业心强；子水智慧，主思维敏捷，但需防桃花困扰"}, {"period": 7, "age_range": "70-79岁", "ganzhi": "己亥", "direction": "逆行", "description": "己土温润，包容万物，主善良、谦和、善于协调；亥水智慧，主聪明灵活，但需防散漫无章"}, {"period": 8, "age_range": "80-89岁", "ganzhi": "戊戌", "direction": "逆行", "description": "戊土厚重，稳重可靠，主踏实、守信、有责任感；戌土厚重，主稳重可靠，但需防固执己见"}]}}', '{"personality": ["稳重务实，注重实际效果", "聪明灵活，善于变通与创新", "具备艺术天赋和审美能力", "性格急躁，易因小事焦虑", "独立性强，不喜欢依赖他人"], "career": ["适合创意设计、技术研发类工作", "财运平稳，宜守不宜攻的投资策略", "30岁后事业发展加速，贵人运强", "管理能力突出，可担任领导岗位", "需注意职场人际关系维护"], "marriage": ["配偶外貌出众，性格温和体贴", "婚前感情波折较多，宜晚婚", "婚后需加强沟通，避免冷暴力", "配偶对命主事业有实质性帮助", "注意防范烂桃花干扰婚姻稳定"], "health": ["重点养护肾脏及泌尿系统", "注意心血管疾病预防", "呼吸系统较脆弱，避免吸烟", "土旺易引发脾胃消化不良", "建议坚持有氧运动调节体质"], "suggestions": ["日常多穿蓝黑色系衣物补足水元素", "办公场所摆放鱼缸增强财运", "练习书法/围棋培养沉稳心性", "定期参与公益活动化解火气", "婚配优先选择属蛇、牛、猴者"]}', '{"name": "张超超", "gender": "男", "is_lunar": false, "year": 2026, "month": 6, "day": 14, "hour": 12, "minute": 0, "hour_index": 0, "is_early_zi": false, "city": "北京", "latitude": 116.4074, "longitude": 39.9042, "solar_time_mode": "自动", "age_type": "虚岁", "leap_rule": "归前"}', '2026-06-14 09:46:41');
INSERT INTO "analysis_records" VALUES (3, '张超超', '男', '2025-06-14', '01:00', '北京', '{"user_profile": {"name": "张超超", "gender": "男", "birth_date": "2025-06-14", "birth_time": "01:00", "calendar_type": "农历", "city": "北京"}, "basic_chart": {"solar_date": "2025-7-8", "lunar_date": "2025年6月14日", "pillars": {"year": "乙巳", "month": "甲午", "day": "戊辰", "hour": "癸丑"}, "day_master": "戊"}, "wuxing_analysis": {"summary": "金偏弱", "day_master_element": "", "strength": "", "favorable_elements": "", "unfavorable_elements": "", "distribution": {"木": {"count": 2.5, "elements": ["乙", "甲", "辰中藏乙"], "percentage": 18.5}, "火": {"count": 3.0, "elements": ["巳", "巳中藏丙", "午", "午中藏丁"], "percentage": 22.2}, "土": {"count": 5.0, "elements": ["巳中藏戊", "午中藏己", "戊", "辰", "辰中藏戊", "丑", "丑中藏己"], "percentage": 37.0}, "金": {"count": 1.0, "elements": ["巳中藏庚", "丑中藏辛"], "percentage": 7.4}, "水": {"count": 2.0, "elements": ["辰中藏癸", "癸", "丑中藏癸"], "percentage": 14.8}}}, "shishen_analysis": {"summary": {"偏财": 1, "正印": 1, "劫财": 1, "": 1}, "details": [{"pillar": "年柱", "ganzhi": "乙巳", "gan": "乙", "gan_shishen": "偏财", "zhi": "巳", "zhi_shishens": ["丙(七杀)", "戊(劫财)", "庚(七杀)"]}, {"pillar": "月柱", "ganzhi": "甲午", "gan": "甲", "gan_shishen": "正印", "zhi": "午", "zhi_shishens": ["丁(食神)", "己(食神)"]}, {"pillar": "日柱", "ganzhi": "戊辰", "gan": "戊", "gan_shishen": "劫财", "zhi": "辰", "zhi_shishens": ["乙(偏财)", "戊(劫财)", "癸()"]}, {"pillar": "时柱", "ganzhi": "癸丑", "gan": "癸", "gan_shishen": "", "zhi": "丑", "zhi_shishens": ["己(食神)", "辛(偏财)", "癸()"]}]}, "mingli_analysis": {"self_seat": {"day_gan": "戊", "day_zhi": "辰", "relationship": "比和", "hidden_stems": ["戊", "乙", "癸"], "description": "日主戊(土)，自坐辰(土)；日支与日主关系：比和；日支藏干：戊(土)、乙(木)、癸(水)"}, "kongwang": {"year_kongwang": ["午", "未"], "day_kongwang": ["午", "未"], "affected_pillars": [{"pillar": "月柱", "ganzhi": "甲午", "kongwang_type": "年空"}], "description": "年空：[''午'', ''未'']；日空：[''午'', ''未'']"}, "ganzhi_relations": {"gan_relations": ["甲克戊", "乙被癸生"], "zhi_relations": ["午害丑"]}, "hidden_stems": ["年柱地支巳藏干：丙(火)、戊(土)、庚(金)", "月柱地支午藏干：丁(火)、己(土)", "日柱地支辰藏干：戊(土)、乙(木)、癸(水)", "时柱地支丑藏干：己(土)、辛(金)、癸(水)"], "positive_shensha": [], "negative_shensha": []}, "major_fortune": {"direction": "顺行", "periods": [{"period": 1, "age_range": "0-9岁", "ganzhi": "甲午", "direction": "顺行", "description": "甲木参天，蓬勃向上，主创新、开拓、积极进取；午火旺盛，主光明正大，但需防骄傲自满"}, {"period": 2, "age_range": "20-29岁", "ganzhi": "乙未", "direction": "顺行", "description": "乙木柔韧，善于变通，主智慧、文雅、富有艺术气质；未土温和，主善良包容，但需防依赖他人"}, {"period": 3, "age_range": "30-39岁", "ganzhi": "丙申", "direction": "顺行", "description": "丙火炎炎，热情洋溢，主光明、才华、社交能力强；申金锐利，主果断刚毅，但需防刻薄寡恩"}, {"period": 4, "age_range": "40-49岁", "ganzhi": "丁酉", "direction": "顺行", "description": "丁火柔和，温文尔雅，主细腻、体贴、富有同情心；酉金清秀，主才华出众，但需防孤芳自赏"}, {"period": 5, "age_range": "50-59岁", "ganzhi": "戊戌", "direction": "顺行", "description": "戊土厚重，稳重可靠，主踏实、守信、有责任感；戌土厚重，主稳重可靠，但需防固执己见"}, {"period": 6, "age_range": "60-69岁", "ganzhi": "己亥", "direction": "顺行", "description": "己土温润，包容万物，主善良、谦和、善于协调；亥水智慧，主聪明灵活，但需防散漫无章"}, {"period": 7, "age_range": "70-79岁", "ganzhi": "庚子", "direction": "顺行", "description": "庚金锐利，果断刚毅，主决断、勇敢、事业心强；子水智慧，主思维敏捷，但需防桃花困扰"}, {"period": 8, "age_range": "80-89岁", "ganzhi": "辛丑", "direction": "顺行", "description": "辛金清秀，才华出众，主聪慧、优雅、追求完美；丑土厚重，主稳重踏实，但需防固执保守"}]}}', '{"personality": ["稳重踏实，责任感强，如大地般包容", "固执坚韧，不易变通，易坚持己见", "务实理性，重视物质保障，不善浪漫表达", "内心敏感，缺乏安全感，重视家庭纽带"], "career": ["适合土木工程、建筑房产、农业矿产等土性行业", "正财稳定，偏财需谨慎，30岁后火金运助事业突破", "管理能力突出，宜担任统筹协调岗位", "避免高风险投资，金属相关行业需借助团队力量"], "marriage": ["配偶宫辰土为喜用，妻子贤惠持家", "正财癸水藏于时柱，宜晚婚（28岁后）规避桃花困扰", "需注意配偶健康，尤其肾脏泌尿系统", "日常多沟通，避免因固执引发冷战"], "health": ["土旺注意脾胃失调，饮食宜清淡规律", "火炎土燥，需预防心血管疾病及皮肤炎症", "金弱肺气不足，秋冬注意呼吸道保养", "辰丑相刑，定期检查消化系统功能"], "suggestions": ["佩戴金银首饰增强金气，办公方位首选西北方", "每日饮水2升润局，晨练宜游泳太极拳", "职业规划把握30-49岁黄金期，重点发展西南方位市场", "家中多摆放白水晶簇，每年立秋后体检重点关注肺部"]}', '{"name": "张超超", "gender": "男", "is_lunar": true, "year": 2025, "month": 6, "day": 14, "hour": 1, "minute": 0, "hour_index": 1, "is_early_zi": false, "city": "北京", "latitude": 116.4074, "longitude": 39.9042, "solar_time_mode": "自动", "age_type": "虚岁", "leap_rule": "归前"}', '2026-06-14 10:14:13');
INSERT INTO "analysis_reports" VALUES (1, 'bazi', '测试用户', '男', '1990-01-01', '00:00', '测试城市', '', '{
    "day": 1,
    "city": "测试城市",
    "hour": 0,
    "name": "测试用户",
    "year": 1990,
    "month": 1,
    "gender": "男",
    "minute": 0
}', '{
    "bazi": {
        "day": "甲子",
        "hour": "甲子",
        "year": "庚午",
        "month": "戊子",
        "rizhu": "甲"
    },
    "wuxing": {
        "土": 1,
        "木": 2,
        "水": 2,
        "火": 1,
        "金": 2
    }
}', '{
    "career": [
        "测试事业1",
        "测试事业2"
    ],
    "health": [
        "测试健康1"
    ],
    "marriage": [
        "测试婚姻1"
    ],
    "personality": [
        "测试性格1",
        "测试性格2"
    ],
    "suggestions": [
        "测试建议1",
        "测试建议2"
    ]
}', 'completed', NULL, 'deepseek-test', 100, '2026-06-22 15:15:30', '2026-06-22 15:15:30');
INSERT INTO "analysis_reports" VALUES (2, 'bazi', '测试命主', '男', '1990-05-15', '14:30', '北京', '', '{
    "day": 15,
    "city": "北京",
    "hour": 14,
    "name": "测试命主",
    "year": 1990,
    "month": 5,
    "gender": "男",
    "minute": 30
}', '{
    "bazi": {
        "day": "庚戌",
        "hour": "癸未",
        "year": "庚午",
        "month": "辛巳",
        "rizhu": "庚"
    },
    "wuxing": {
        "土": {
            "count": 2,
            "percentage": 25
        },
        "木": {
            "count": 0,
            "percentage": 0
        },
        "水": {
            "count": 1,
            "percentage": 12.5
        },
        "火": {
            "count": 2,
            "percentage": 25
        },
        "金": {
            "count": 3,
            "percentage": 37.5
        },
        "summary": "金旺，土次之，火水偏弱，缺木"
    },
    "shishen": {
        "summary": {
            "七杀": 0,
            "伤官": 0,
            "偏印": 1,
            "偏财": 1,
            "劫财": 1,
            "正印": 1,
            "正官": 1,
            "正财": 0,
            "比肩": 2,
            "食神": 1
        }
    }
}', '{
    "career": [
        "金旺火炼，官星得禄于月令，适合在体制内、大型企业或需要权威与规则的环境中发展，易得职位。",
        "财星藏于时支未土之中，为伤官生财之局，中年后（时柱主中晚年）财运渐入佳境，尤其利于凭借专业技能、口才或创意求财。",
        "比劫林立，不宜与人合伙经营，易生财务纠纷，更适合独立负责或依靠自身技艺立足。"
    ],
    "health": [
        "金过旺而木绝，需特别注意肝胆系统、筋骨（尤其是四肢）的健康，易有酸痛或损伤。",
        "火土燥而水弱，肾水、泌尿系统及血液循环方面需加留意，注意预防上火、炎症及皮肤问题。",
        "日主强旺，身体素质总体不错，但性格刚强，需防因压力大或争强好胜导致的心脑血管负荷。"
    ],
    "marriage": [
        "日柱庚戌，为魁罡日之一，且日支夫妻宫为偏印，配偶性格可能较为内向、固执，或年龄有差距，婚姻中需要更多沟通与包容。",
        "正财星不显，偏财藏于时支，感情缘分来得稍晚，或与配偶的相处模式较为独特，需用心经营方能稳定。",
        "月柱辛巳，巳中藏七杀，早年感情易有波折或竞争，需防因朋友、兄弟之事影响感情。"
    ],
    "personality": [
        "庚金日主生于巳月，火旺炼金，性格刚毅果决，有决断力，但有时显得固执己见。",
        "比肩劫财多见，为人重义气，朋友多，但竞争意识强，易因朋友或同辈之事耗费精力。",
        "日坐戌土偏印，时柱癸未伤官生财，内心细腻敏感，富有艺术或技术天赋，但思虑较多，时有孤独感。"
    ],
    "suggestions": [
        "职业发展宜向西方、西北方（金地）或南方（火地）寻求机会，以平衡命局，发挥官印相生的优势。",
        "可适当补充水、木五行元素，如从事与水、木相关的行业，或通过穿戴、居住环境调节，以疏通旺金，生助财官。",
        "修身养性，学习以柔克刚之道，遇事多思缓行，可有效化解比劫争斗与夫妻宫偏印带来的固执倾向。"
    ]
}', 'completed', NULL, 'deepseek-v3.1-250821', 870, '2026-06-22 15:15:30', '2026-06-22 15:15:55');
INSERT INTO "analysis_reports" VALUES (3, 'meihua', '', '', '2024-06-15', '', '', '近期事业发展如何？', '{
    "day": 15,
    "hour": 10,
    "year": 2024,
    "month": 6,
    "method": "time",
    "question": "近期事业发展如何？"
}', '{
    "hu": {
        "name": "天风姤",
        "description": "阴阳相遇之象"
    },
    "base": {
        "name": "乾为天",
        "gua_ci": "元亨利贞",
        "lower_name": "乾",
        "upper_name": "乾",
        "description": "纯阳之卦，刚健中正",
        "changing_yao": 3,
        "lower_nature": "天",
        "upper_nature": "天",
        "changing_yao_name": "九三",
        "changing_yao_text": "君子终日乾乾，夕惕若厉，无咎",
        "changing_yao_meaning": "勤勉努力，警惕自省"
    },
    "bian": {
        "name": "天火同人",
        "judgment": "吉",
        "description": "同心同德之象"
    },
    "overall_judgment": "吉"
}', '{
    "bad_omens": [
        "动爻''夕惕若厉''提示若放松警惕，可能面临潜在危机。",
        "变卦用克体（离火克乾金），提示后期合作中需注意意见分歧或利益分配问题。",
        "乾卦过刚易折，需防因过于强势而影响人际关系。",
        "姤卦有''女壮勿取''之诫，警示对新出现的机遇需审慎评估。",
        "三爻居位不安，暗示事业中期可能遇到瓶颈或过度劳累。"
    ],
    "good_omens": [
        "体用比和，主事业运势顺畅，个人能力可得到充分发挥。",
        "变卦同人卦辞''同人于野，亨''，预示通过广泛合作可获亨通。",
        "乾卦爻辞''终日乾乾''但''无咎''，只要勤奋谨慎，即使有挑战也能化解。",
        "互卦姤有''遇合''之义，可能遇到贵人或在关键时刻出现转机。",
        "乾为天象征领导力与开创性，适合担任主导角色或开拓新领域。"
    ],
    "gua_overview": [
        "本卦乾为天，纯阳刚健之象，象征事业正处于积极进取的阶段。",
        "动爻在第三爻，爻辞''君子终日乾乾，夕惕若厉''，提示需要持续努力并保持警惕。",
        "互卦天风姤，暗示事业发展中可能遇到新的机遇或人际变动。",
        "变卦天火同人，预示最终可能达成合作、同心协力的局面。",
        "整体卦象由纯阳之乾变为同人之合，显示事业将从个人奋斗转向团队协作。"
    ],
    "action_advice": [
        "恪守乾卦''自强不息''的精神，保持当前的努力状态，但需如爻辞所言''夕惕若厉''，每日复盘反思。",
        "积极准备迎接互卦姤预示的新机遇，主动拓展人脉，但选择合作对象时需谨慎考察。",
        "顺应变卦同人的导向，逐步从独立运作转向团队协作，注重凝聚共识。",
        "发挥乾卦领导力时，注意刚柔并济，避免独断专行，尤其变卦提示合作中需多倾听。",
        "将事业目标分解为阶段性任务，三爻位置提示当前重点在巩固基础、防范风险。"
    ],
    "final_verdict": "事业运势总体向好，正处于由个人奋斗向合作发展过渡的关键阶段。只要保持勤勉谨慎的态度，善用机遇、广结善缘，便能突破当前瓶颈，实现更广阔的发展。需特别注意合作关系的平衡与协调。",
    "situation_analysis": [
        "体用皆乾，体卦乾金为问卦者，用卦乾金为事业，体用比和，主事业根基稳固，自身能力与事业发展需求相匹配。",
        "动爻在三爻，处于下卦之顶，象征事业已取得一定基础，但面临向上突破的关键期。",
        "互卦姤（上乾下巽），用卦生互卦（乾金生巽木），显示事业发展过程中会衍生出新的机会或人际关系网络。",
        "变卦同人（上乾下离），用卦变离火（乾金变离火），火克金为用克体，提示后期需注意合作中的协调问题。",
        "从本卦到变卦，乾之三爻阳变阴，使全卦由纯阳转为阴阳相济，预示事业模式将从单打独斗转向合作共赢。"
    ]
}', 'completed', NULL, 'deepseek-v3.1-250821', 1120, '2026-06-22 15:15:55', '2026-06-22 15:16:31');
INSERT INTO "analysis_reports" VALUES (4, 'bazi', '测试用户', '男', '1990-01-01', '00:00', '测试城市', '', '{
    "day": 1,
    "city": "测试城市",
    "hour": 0,
    "name": "测试用户",
    "year": 1990,
    "month": 1,
    "gender": "男",
    "minute": 0
}', '{
    "bazi": {
        "day": "甲子",
        "hour": "甲子",
        "year": "庚午",
        "month": "戊子",
        "rizhu": "甲"
    },
    "wuxing": {
        "土": 1,
        "木": 2,
        "水": 2,
        "火": 1,
        "金": 2
    }
}', '{
    "career": [
        "测试事业1",
        "测试事业2"
    ],
    "health": [
        "测试健康1"
    ],
    "marriage": [
        "测试婚姻1"
    ],
    "personality": [
        "测试性格1",
        "测试性格2"
    ],
    "suggestions": [
        "测试建议1",
        "测试建议2"
    ]
}', 'failed', '测试错误信息', 'deepseek-test', 100, '2026-06-22 15:17:11', '2026-06-22 15:17:11');
INSERT INTO "analysis_reports" VALUES (5, 'bazi', '测试命主', '男', '1990-05-15', '14:30', '北京', '', '{
    "day": 15,
    "city": "北京",
    "hour": 14,
    "name": "测试命主",
    "year": 1990,
    "month": 5,
    "gender": "男",
    "minute": 30
}', '{
    "bazi": {
        "day": "庚戌",
        "hour": "癸未",
        "year": "庚午",
        "month": "辛巳",
        "rizhu": "庚"
    },
    "wuxing": {
        "土": {
            "count": 2,
            "percentage": 25
        },
        "木": {
            "count": 0,
            "percentage": 0
        },
        "水": {
            "count": 1,
            "percentage": 12.5
        },
        "火": {
            "count": 2,
            "percentage": 25
        },
        "金": {
            "count": 3,
            "percentage": 37.5
        },
        "summary": "金旺，土次之，火水偏弱，缺木"
    },
    "shishen": {
        "summary": {
            "七杀": 0,
            "伤官": 0,
            "偏印": 1,
            "偏财": 1,
            "劫财": 1,
            "正印": 1,
            "正官": 1,
            "正财": 0,
            "比肩": 2,
            "食神": 1
        }
    }
}', '{
    "career": [
        "金旺身强，喜火炼金成器，事业宜往火属性或需要火炼金的行业发展，如能源、电力、互联网科技、法律、军警等。",
        "月柱官印相生，且日坐偏印，适合在大型机构、国企或专业技术领域发展，易得领导赏识和职位晋升。",
        "时柱伤官生财（癸水生未中乙木财星），中年后（时柱主中晚年）财运渐佳，尤其利于凭借专业技能、口才或创意获利。",
        "比劫众多，不宜与人合伙求财，易有财务纠纷，更适合独立经营或依靠个人技术谋生。",
        "原局财星弱而藏于时支，早期财运平平，需待水木旺运，方能财源广进。"
    ],
    "health": [
        "金过旺，木气全无，需特别注意肝胆系统、筋骨（木主筋）的健康，易有肝胆功能偏弱、筋骨酸痛等问题。",
        "火气虽透但被旺金耗泄，且水弱，需防范心血管、眼睛（火主心、目）以及肾脏、泌尿系统（水主肾）的隐患。",
        "土金两旺，脾胃功能较强，但土重亦有壅塞之象，需注意饮食均衡，预防消化系统代谢不畅。",
        "全局燥气较重（火土金旺，水弱），易有皮肤干燥、便秘或体内燥热之症，宜多补充水分，食用滋阴润燥之物。",
        "比劫旺而克财（木），在健康上亦表现为易有外伤、手术或与肝胆相关的急性病症，需定期体检。"
    ],
    "marriage": [
        "日柱庚戌，日坐偏印（戌中丁火正官、戊土偏印、辛金劫财），夫妻宫坐劫财，配偶个性较强，婚姻中易有争执或财务竞争。",
        "正财星（木）不显，妻缘稍浅，需用心经营感情。未中藏有乙木正财，晚婚或与年龄差距较大者结合更为有利。",
        "比劫重重，感情路上易出现竞争者，或自身对感情投入不够专注，需防范因朋友兄弟影响夫妻关系。",
        "日主强旺，自身性格刚强，在婚姻中需多加包容，避免过于自我，以免影响感情和谐。",
        "时柱癸水伤官，对配偶的要求较高，内心情感丰富但表达方式可能不够圆融，需注意沟通技巧。"
    ],
    "personality": [
        "日主庚金生于巳月，火旺炼金，性格刚毅果决，有决断力，但有时略显固执。",
        "比肩劫财多见，为人重情重义，朋友缘佳，但易因兄弟朋友而耗财或引发竞争。",
        "时柱癸水伤官透出，内心聪慧，有艺术才华或技术天赋，但言语直接，需防口舌是非。",
        "四柱土金两旺，为人诚信稳重，但有时过于坚持己见，缺乏变通。",
        "官印相生，有责任心和管理能力，但七杀不显，魄力稍欠，关键时刻易犹豫。"
    ],
    "suggestions": [
        "职业选择上，宜向南（火地）或向东（木地）发展，从事能发挥火、木五行特性的行业最为有利。",
        "人际交往中，需谨慎处理与同辈、朋友的关系，避免经济上的深度捆绑，独立发展更佳。",
        "婚恋方面，宜选择八字中木、水较旺的伴侣，以补足自身命局所缺，达到五行调和。晚婚更利婚姻稳定。",
        "健康养生，重点养护肝胆，多食绿色蔬菜（补木），同时注意滋阴补肾（补水），保持作息规律，疏解压力。",
        "大运流年逢水、木旺的年份（如壬寅、癸卯等），是事业财运发展的良机，应积极把握。逢土金旺年则宜守不宜攻，谨慎投资。"
    ]
}', 'completed', NULL, 'deepseek-v3.1-250821', 1202, '2026-06-22 15:17:11', '2026-06-22 15:17:31');
INSERT INTO "analysis_reports" VALUES (6, 'meihua', '', '', '2024-06-15', '', '', '近期事业发展如何？', '{
    "day": 15,
    "hour": 10,
    "year": 2024,
    "month": 6,
    "method": "time",
    "question": "近期事业发展如何？"
}', '{
    "hu": {
        "name": "天风姤",
        "description": "阴阳相遇之象"
    },
    "base": {
        "name": "乾为天",
        "gua_ci": "元亨利贞",
        "lower_name": "乾",
        "upper_name": "乾",
        "description": "纯阳之卦，刚健中正",
        "changing_yao": 3,
        "lower_nature": "天",
        "upper_nature": "天",
        "changing_yao_name": "九三",
        "changing_yao_text": "君子终日乾乾，夕惕若厉，无咎",
        "changing_yao_meaning": "勤勉努力，警惕自省"
    },
    "bian": {
        "name": "天火同人",
        "judgment": "吉",
        "description": "同心同德之象"
    },
    "overall_judgment": "吉"
}', '{
    "bad_omens": [
        "乾卦过刚，若一味强进不知变通，易折损，需防刚愎自用。",
        "动爻''夕惕若厉''，提醒事业中存在隐忧，不可因表面顺利而松懈。",
        "互卦姤有''女壮勿取''之诫，对新出现的机遇需审慎辨别，防其中藏有隐患。",
        "变卦体克用（离火克乾金），虽吉但需付出较多精力，可能因合作事宜耗费心神。",
        "纯阳卦动变后引入离火，需注意事业中可能出现的竞争或''火燥''之象（如冲突、急于求成）。"
    ],
    "good_omens": [
        "乾卦''元亨利贞''，四德俱全，预示事业有开创性机遇，过程亨通。",
        "动爻''无咎''，只要保持''终日乾乾''的勤奋和''夕惕若''的谨慎，可避免过失。",
        "互卦姤为''相遇''，可能遇到关键合作伙伴或意外机会，助力发展。",
        "变卦同人''同人于野，亨''，象征通过广泛合作、凝聚人心，事业可获成功。",
        "体用生克一路相生相比，显示内外助力充沛，天时地利俱佳。"
    ],
    "gua_overview": [
        "本卦乾为天，纯阳刚健之象，象征事业正处于强健发展阶段。",
        "动爻在第三爻，爻辞''君子终日乾乾，夕惕若厉''，提示需勤奋谨慎。",
        "互卦天风姤，阴阳初遇，暗示事业发展中可能出现新的合作或机遇。",
        "变卦天火同人，同心同德之象，预示通过合作可达成目标。",
        "整体卦象由纯阳之乾，经阴阳相遇之姤，最终归于和谐同人之象，显示事业路径由自强到合作。"
    ],
    "action_advice": [
        "恪守乾卦精神：保持''天行健，君子以自强不息''的奋斗姿态，但需刚柔并济。",
        "落实三爻爻辞：白日勤奋进取（''终日乾乾''），夜晚反思警醒（''夕惕若''），每日复盘事业进展。",
        "善用互卦姤机：主动接触新的人脉与机会，但需仔细评估（姤卦提醒审慎''相遇''）。",
        "朝向变卦同人：将个人能力（乾）与团队合作（同人）结合，''同人于野''拓展事业圈子。",
        "平衡体用生克：发挥体卦乾金之刚健，但以离火之明（变卦下卦）调和，即用智慧与亲和力引领事业。"
    ],
    "final_verdict": "整体大吉，事业处于强劲上升期。卦象显示你具备成功所需的刚健与能力（乾），中期将遇助力（姤），最终可通过合作共赢达成目标（同人）。核心关键在于：既保持乾卦的奋发，又融入同人的和谐，并时刻谨记三爻''夕惕若厉''的警醒。近期事业前景光明，但需以勤慎为舟，以合作为桨，方能行稳致远。",
    "situation_analysis": [
        "体卦为乾金（下卦），用卦亦为乾金（上卦），体用比和，主事业根基稳固，自身能力与外部环境协调。",
        "动爻在三爻，居下卦之极，表示你目前处于事业的关键上升期，需加倍努力。",
        "互卦姤（上乾下巽），用卦生体卦（巽木生乾金），显示中期可能有贵人相助或新的发展思路。",
        "变卦同人（上乾下离），体卦离火克用卦乾金，但卦义以和谐为主，提示最终需以柔克刚，注重人际关系。",
        "从体用生克看：本卦比和（吉）→互卦用生体（大吉）→变卦体克用（小吉），整体趋势向好，但变卦体克用需付出心力。"
    ]
}', 'completed', NULL, 'deepseek-v3.1-250821', 1266, '2026-06-22 15:17:31', '2026-06-22 15:18:15');
INSERT INTO "analysis_reports" VALUES (7, 'bazi', '张超超', '男', '2026-06-22', '12:00', '北京', '', '{
    "day": 22,
    "city": "北京",
    "hour": 12,
    "name": "张超超",
    "year": 2026,
    "month": 6,
    "notes": "",
    "gender": "男",
    "minute": 0,
    "age_type": "虚岁",
    "is_lunar": false,
    "latitude": 39.9042,
    "pan_type": "bazi",
    "leap_rule": "归前",
    "longitude": 116.4074,
    "hour_index": 6,
    "is_early_zi": false,
    "solar_time_mode": "自动"
}', '{
    "bazi": {
        "day": "丁巳",
        "hour": "丙午",
        "year": "丙午",
        "month": "乙巳",
        "rizhu": "丁"
    },
    "wuxing": {
        "土": {
            "count": 2.0,
            "percentage": 15
        },
        "木": {
            "count": 1,
            "percentage": 7
        },
        "水": {
            "count": 0,
            "percentage": 0
        },
        "火": {
            "count": 9.0,
            "percentage": 69
        },
        "金": {
            "count": 1.0,
            "percentage": 7
        }
    }
}', '{
    "career": [
        "命局火势专旺，可入''炎上格''或''从旺格''，气势纯粹，宜从事与火、能源、文化、演艺、互联网科技等相关的行业，能充分发挥其热情与创造力。",
        "比劫为用，适合团队合作或自主创业，能在竞争激烈的环境中脱颖而出，但需注意合作中的利益分配，避免因兄弟朋友之事破财。",
        "财星辛金深藏于巳中，为''金藏火炼''，求财需经一番辛苦拼搏，中年后财运方显。不宜从事过于稳健或需要长期耐心积累的行业。",
        "官星水绝，缺乏官杀约束，不喜受人管束，在体制内或传统层级分明的企业中发展易感压抑，更适合在自由度高的平台或自己主导的事业中施展抱负。"
    ],
    "health": [
        "命局五行火旺至极，极度失衡，最需防范心脏、血液系统、心血管方面的疾病，如心悸、高血压、眼疾等。平时切忌熬夜、过度亢奋。",
        "火旺熔金，金弱受克，需注意肺部、呼吸系统及大肠的健康，易有咳嗽、皮肤干燥、便秘等问题。",
        "''火炎土燥''，脾胃（土）功能易失调，可能出现消化不良、胃火过旺、口腔溃疡等症状。饮食宜清淡，多食润燥之物。",
        "全局无水调候，肾水枯竭，代表精力消耗过大，易有阴虚火旺、失眠多梦、精力不济之象，中年后需特别注意肾脏、泌尿系统的保养。"
    ],
    "marriage": [
        "日柱丁巳，为''孤鸾煞''，且四柱比劫林立，火炎土燥，夫妻宫坐劫财，感情世界中竞争意识强，易有争夺之象，需晚婚为宜。",
        "全局不见正财妻星，仅藏偏财于地支，异性缘分不浅，但情路多波折，与伴侣相处时，需克制自身强势与急躁的性格，多些体贴与包容。",
        "火旺至极，肾水（代表感情、生殖系统）受克，需注意因忙于事业或个性过于自我而忽略家庭情感经营，导致夫妻关系疏离。",
        "时柱丙午，劫财再透，子女缘分较佳，但可能对子女较为宠溺或期望过高，需注意教育方式。"
    ],
    "personality": [
        "日主丁火生于巳月，火势炎炎，四柱地支巳午三会火局，天干透出丙乙，构成''木火通明''之象，命主性格热情奔放，精力旺盛，富有创造力与感染力。",
        "比劫重重，丙火劫财透干，性格刚强好胜，自尊心极强，不喜受人约束，行事果断，有领导才能，但易显急躁冲动，缺乏耐心。",
        "印星乙木透于月干，但木弱火焚，印星虚浮无力，表面好学聪慧，实则内心依赖直觉与冲动，思虑有时不够深远，需防固执己见。",
        "全局火旺至极，火主礼但过则燥，为人重情重义，光明磊落，但脾气火爆，言辞直接，易因一时意气与人争执，需修养心性以达中和。"
    ],
    "suggestions": [
        "此命火势冲天，性情刚烈，首要人生课题为''修心养性''。可多接触水边、北方，穿着多用黑、蓝、灰等色，佩戴水晶（黑曜石、海蓝宝）等水性饰品以调候命局。",
        "事业上宜向出生地的北方、西方或近水之地发展，从事行业可兼具''火''之热情与''金水''之理性，如IT行业的研发、文化传媒的策划等，以达五行互补。",
        "人际交往中，需刻意培养耐心与倾听的能力，尤其对待亲密关系，要学会''以柔克刚''，遇事多沟通，避免因一时口快伤人伤己。",
        "健康方面，务必建立规律作息，坚持适度的有氧运动（如游泳、慢跑），饮食多补充水分及滋阴食物（如银耳、百合），定期检查心脑血管。",
        "大运流年逢金、水之年（如申、酉、亥、子年）多为机遇期，但火旺遇水激，易有变动冲突，需稳中求进；逢木、火之年则需格外保守，防范破财与健康问题。"
    ]
}', 'completed', NULL, 'deepseek-v3.1-250821', 1233, '2026-06-22 23:00:57', '2026-06-22 23:01:37');
INSERT INTO "analysis_reports" VALUES (8, 'bazi', '张超超', '男', '2026-06-22', '12:00', '北京', '', '{
    "day": 22,
    "city": "北京",
    "hour": 12,
    "name": "张超超",
    "year": 2026,
    "month": 6,
    "notes": "",
    "gender": "男",
    "minute": 0,
    "age_type": "虚岁",
    "is_lunar": false,
    "latitude": 39.9042,
    "pan_type": "bazi",
    "leap_rule": "归前",
    "longitude": 116.4074,
    "hour_index": 6,
    "is_early_zi": false,
    "solar_time_mode": "自动"
}', '{
    "bazi": {
        "day": "丁巳",
        "hour": "丙午",
        "year": "丙午",
        "month": "乙巳",
        "rizhu": "丁"
    },
    "wuxing": {
        "土": {
            "count": 2.0,
            "percentage": 15
        },
        "木": {
            "count": 1,
            "percentage": 7
        },
        "水": {
            "count": 0,
            "percentage": 0
        },
        "火": {
            "count": 9.0,
            "percentage": 69
        },
        "金": {
            "count": 1.0,
            "percentage": 7
        }
    }
}', '{
    "career": [
        "火旺成势，宜从事与火、能源、文化、演艺、互联网、餐饮等相关的行业，能充分发挥命局优势。",
        "比劫争财，不宜与人合伙经商，易因利益分配产生纠纷，适合独立经营或技术性强的岗位。",
        "财星庚金藏于巳中，为暗财，需大运流年引动方能得财，中年后财运渐入佳境，但钱财来去较快，需注意理财。",
        "官星水绝，不适合在体制内或过于稳定的环境发展，更适合在竞争激烈、变化快的领域施展才华。"
    ],
    "health": [
        "火气过亢，需特别注意心血管系统、眼睛、血液方面的疾病，易有高血压、心悸、失眠等问题。",
        "火旺克金，金主肺、大肠，呼吸系统及肠道功能较弱，需防范呼吸道炎症、皮肤过敏等。",
        "命局燥热，体内水火失衡，平时宜多饮水，饮食清淡，避免过度熬夜及辛辣刺激食物，可适当进行游泳、静坐等滋阴活动。"
    ],
    "marriage": [
        "四柱纯阳，火炎土燥，婚姻宫坐劫财，感情路上竞争多，易出现感情争夺或配偶被他人影响的情况。",
        "妻星（财星）深藏不露，且受旺火克制，姻缘较迟，早婚易生变故，宜晚婚。配偶性格可能较为刚强或独立。",
        "夫妻相处需注意控制脾气，避免因冲动言语伤害感情，宜找性格柔和、能包容的伴侣，以调和命局之燥烈。"
    ],
    "personality": [
        "日主丁火生于巳月，地支四火成势，天干透丙乙，构成炎上专旺格局。命主性格热情奔放，精力充沛，具有强烈的表现欲和领导才能。",
        "火势过旺，性格急躁易怒，缺乏耐心，做事易冲动，有时显得固执己见，不易听取他人意见。",
        "比劫重重，为人重义气，朋友众多，但竞争意识强烈，不喜受人约束，喜欢自由自在的生活方式。",
        "印星乙木虚浮，虽聪明好学，但根基不深，易学而不精，缺乏持久钻研的精神。"
    ],
    "suggestions": [
        "性格修炼：有意识地培养耐心和包容心，学习控制情绪，遇事三思而后行，可练习书法、钓鱼等静心活动。",
        "职业发展：扬长避短，投身于能发挥热情与创造力的领域，避免陷入复杂的人际利益纠纷，注重提升专业技术的深度。",
        "人际婚姻：交友宜慎，择偶宜缓。多与命局水、土旺之人交往，以调和自身气场。婚后宜多关注配偶感受，加强沟通。",
        "健康养生：定期检查心脑血管，注重滋阴润燥，居住环境宜近水或阴凉之处，穿着多选用蓝、黑、白等色系。",
        "运势把握：逢鼠、猪（子、亥）水旺之年，运势易有波动挑战，需谨慎应对；逢牛、龙、羊、狗（丑、辰、未、戌）土旺之年，食伤泄秀，利发挥才华，运势相对顺畅。"
    ]
}', 'completed', NULL, 'deepseek-v3.1-250821', 958, '2026-06-22 23:35:09', '2026-06-22 23:35:38');
INSERT INTO "analysis_reports" VALUES (9, 'bazi', '张超超', '男', '2026-06-22', '12:00', '北京', '', '{
    "day": 22,
    "city": "北京",
    "hour": 12,
    "name": "张超超",
    "year": 2026,
    "month": 6,
    "notes": "",
    "gender": "男",
    "minute": 0,
    "age_type": "虚岁",
    "is_lunar": false,
    "latitude": 39.9042,
    "pan_type": "ziwei",
    "leap_rule": "归前",
    "longitude": 116.4074,
    "hour_index": 6,
    "is_early_zi": false,
    "solar_time_mode": "自动"
}', '{
    "bazi": {
        "day": "丁巳",
        "hour": "丙午",
        "year": "丙午",
        "month": "乙巳",
        "rizhu": "丁"
    },
    "wuxing": {
        "土": {
            "count": 2.0,
            "percentage": 15
        },
        "木": {
            "count": 1,
            "percentage": 7
        },
        "水": {
            "count": 0,
            "percentage": 0
        },
        "火": {
            "count": 9.0,
            "percentage": 69
        },
        "金": {
            "count": 1.0,
            "percentage": 7
        }
    }
}', '{
    "career": [
        "八字火旺成势，宜从事与火、能源、电力、科技、互联网、文化传播、演艺等属火行业，能发挥其热情与创造力，忌从事水利、金融等金水行业。",
        "月柱乙巳为「偏印坐劫财」，适合技术性、研究性工作，但需注意团队合作，避免因个性过强与同事发生冲突。",
        "比劫旺而无官杀（水）制衡，不宜从政或担任严格管理的职位，更适合自由职业、创业或技术领军，中年后（土金运）财运方能稳定。",
        "财星（金）微弱且藏于巳火之中，代表财运起伏大，易有意外之财但也易因朋友、投资而破财，需谨慎理财，避免投机。",
        "日坐巳火为「羊刃」，事业上有拼搏精神，但需防过度劳累引发健康问题，注意工作与休息的平衡。"
    ],
    "health": [
        "八字火炎土燥，最需水来调候，但全局无水，需特别注意心血管系统、眼睛、血液方面的疾病，易有高血压、失眠、炎症等问题。",
        "木弱火焚，肝胆功能较弱，易有肝火旺盛、头晕目眩、皮肤过敏等症状，需注意饮食清淡，避免熬夜。",
        "土燥无湿，脾胃消化系统易出问题，可能有便秘、消化不良等情况，宜多食蔬果、保持肠道湿润。",
        "金气受克，呼吸系统（肺、支气管）较弱，需防呼吸道感染、咳嗽等，避免吸烟或处于空气污染环境。",
        "火旺无制，精力消耗过大，易有虚火上升、精神亢奋后极度疲惫的循环，应注意规律作息，培养静心习惯（如冥想、阅读）。"
    ],
    "marriage": [
        "日主丁火，以庚金为正财（妻星），八字中金气微弱且藏于巳火之中，代表姻缘较晚或配偶助力不大，需主动争取感情机会。",
        "日柱丁巳为「阴差阳错日」，且日坐羊刃，婚姻易有波折，夫妻间易因性格冲突产生矛盾，需多包容沟通。",
        "比劫重重（火多），男性命局中比劫克财，需防感情竞争或配偶健康问题，婚后应注意与异性保持适当距离。",
        "配偶宫（巳火）为忌神，配偶性格可能较为强势，或家庭背景普通，需通过自身努力改善家庭关系。",
        "中年后行土金运（财星得生），婚姻关系会逐渐稳定，感情趋于和谐，宜晚婚（30岁后）更利婚姻长久。"
    ],
    "personality": [
        "日主丁火生于巳月，火势炎炎，四柱中丙午、丁巳、乙巳、丙午皆为火旺之地，形成「炎上格」或「朱雀乘风」之势，命主性格热情奔放，精力充沛，行动力强，具有领袖气质与感染力。",
        "天干透出乙木偏印，但木气微弱难以生火，反而被烈火焚烧，代表命主思维敏捷但易急躁，学习能力强但缺乏耐心，内心时有孤独感，外表开朗内心敏感。",
        "火势过旺而无水调候，性格刚烈急躁，做事易冲动，缺乏柔韧性与持久力，好胜心强，不喜受约束，有「火暴」之倾向。",
        "比劫重重（丙丁火多），为人重情义，朋友多但易因朋友破财，竞争意识强烈，不喜与人合作，喜独立行事。",
        "时柱丙午为「归禄」，晚年运势佳，但青年时期易因性格刚强而经历较多挫折，需注意修养心性。"
    ],
    "suggestions": [
        "调候为急：命局最需水来平衡，建议多接触水相关环境（如近水而居、从事水产、贸易等行业），穿戴黑色、蓝色衣物，佩戴水晶饰品（如黑曜石）以补水性。",
        "修身养性：火旺性急，需刻意培养耐心与柔韧性，可通过书法、茶道、钓鱼等静心活动平衡性格，避免冲动决策。",
        "择业方向：优先选择火属性行业（能源、文化、科技）或木火通明之业（教育、设计），避开金水行业，创业宜合伙（需选择水旺之人互补）。",
        "婚恋建议：晚婚为宜，配偶宜选择八字水旺或土金旺之人（如出生在秋冬季节者），以平衡命局火炎之势，婚后注重情绪管理。",
        "健康养生：多吃滋阴润燥食物（如银耳、百合、梨），定期检查心血管，培养午休习惯，避免夏季过度暴晒或剧烈运动，可练习深呼吸、游泳等运动。"
    ]
}', 'completed', NULL, 'deepseek-v3.1-250821', 1300, '2026-06-22 23:36:33', '2026-06-22 23:36:55');
INSERT INTO "analysis_reports" VALUES (10, 'bazi', '张超超', '男', '2026-06-23', '12:00', '北京', '', '{
    "day": 23,
    "city": "北京",
    "hour": 12,
    "name": "张超超",
    "year": 2026,
    "month": 6,
    "notes": "",
    "gender": "男",
    "minute": 0,
    "age_type": "虚岁",
    "is_lunar": false,
    "latitude": 39.9042,
    "pan_type": "bazi",
    "leap_rule": "归前",
    "longitude": 116.4074,
    "hour_index": 6,
    "is_early_zi": false,
    "solar_time_mode": "自动"
}', '{
    "bazi": {
        "day": "甲戌",
        "hour": "庚午",
        "year": "丙午",
        "month": "甲午",
        "rizhu": "甲"
    },
    "wuxing": {
        "土": {
            "count": 1.25,
            "percentage": 11
        },
        "木": {
            "count": 0.4,
            "percentage": 3
        },
        "水": {
            "count": 0.0,
            "percentage": 0
        },
        "火": {
            "count": 8.85,
            "percentage": 83
        },
        "金": {
            "count": 0.13,
            "percentage": 1
        }
    }
}', '{
    "career": [
        "命局火旺成势，伤官极旺，非常适合从事需要创意、技术、表演、演讲或与''火''相关的行业，如文化艺术、互联网科技、能源化工、餐饮娱乐等。",
        "伤官生财（火生土），但财星（土）力量较弱，且被旺火所燥，意味着虽有生财之道和赚钱点子，但钱财来得快去得也快，不易积存，需防因投资失误或过度消费而破财。",
        "时柱庚金七杀为事业星，但虚浮无根又被旺火克制，事业上易遇强劲竞争与压力，中年后（金水运来）方能真正得权柄、展抱负，早期宜积累实力，不宜强求高位。"
    ],
    "health": [
        "命局五行严重失衡，火旺至极，木枯金熔。首要防范心脏、血液系统、心血管方面的疾病，以及因上火引起的炎症、目疾、皮肤问题。",
        "甲木为肝胆，原局无水滋养，木气枯槁，需特别注意肝胆功能的保养，疏解情绪压力，避免熬夜和过量饮酒。",
        "火多土焦，脾胃消化系统也偏弱，容易有消化不良、胃火过盛等问题。时柱庚金受克，也需注意呼吸系统（肺、大肠）的健康。"
    ],
    "marriage": [
        "男命以正财为妻星，命局中戊土偏财藏于日支戌土之中，且被三午火合而化火，妻星微弱且受克严重。暗示感情路上波折较多，正缘来得晚，或与配偶缘分较浅。",
        "日支夫妻宫坐戌土偏财，又被月时两午火半合，配偶可能能力较强或有个性，但关系易受外界（朋友、环境）影响，或因命主自身专注事业、脾气急躁而产生隔阂。",
        "全局火炎土燥，无水调候，命主在感情中缺乏耐心与柔情，需注意修身养性，培养包容之心，晚婚（30岁后）更利于婚姻稳定。"
    ],
    "personality": [
        "日主甲木生于午月，火旺木焚，身弱至极。全局火势炎炎，构成''伤官泄秀''之格，命主天生聪慧，领悟力强，富有艺术才华和表现欲。",
        "但火多木燥，性格难免急躁冲动，心高气傲，不耐约束，言语直接易伤人，内心时有孤独焦虑之感。",
        "时柱庚金七杀透出，被旺火克制，形成''伤官驾杀''之势，赋予命主不畏挑战、敢于突破常规的魄力，但也伴随行事偏激、好胜心过强的倾向。",
        "地支三午自刑，内心矛盾纠结多，情绪起伏较大，常有自我较劲、自我消耗之象。"
    ],
    "suggestions": [
        "此命调候为急，首喜''水''来润局制火。日常生活中可多接触属''水''的事物，如从事北方、黑色、流动性强的工作，佩戴水晶饰品，居住近水之地，以平衡过旺的火气。",
        "修身养性至关重要。需有意识地培养耐心与定力，学习控制情绪，避免因一时冲动而决策失误或伤害人际关系。可通过书法、太极、游泳等静态或亲水活动来静心。",
        "事业上宜发挥''伤官''的创造力与专业性，深耕一技之长，成为技术或艺术领域的专家，比追求管理职权更为稳妥。财运上宜保守理财，强制储蓄，远离高风险投机。",
        "人际与婚恋方面，宜多与命局水旺（如日主为壬、癸水）或土金旺的人交往，可起到互补作用。对待感情要更加务实和包容，珍惜缘分。",
        "大运方面，早年乙未、丙申、丁酉运皆为火金旺地，运势起伏较大，压力重重，是积累和沉淀的时期。需耐心等待中年后行戊戌、己亥、庚子等水旺之运，方能真正化解原局燥热，迎来人生转机，成就事业。"
    ]
}', 'completed', NULL, 'deepseek-v3.1-250821', 1156, '2026-06-23 11:12:21', '2026-06-23 11:13:05');
INSERT INTO "analysis_reports" VALUES (11, 'bazi', '张超超', '男', '2026-06-23', '12:00', '北京', '', '{
    "day": 23,
    "city": "北京",
    "hour": 12,
    "name": "张超超",
    "year": 2026,
    "month": 6,
    "notes": "",
    "gender": "男",
    "minute": 0,
    "age_type": "虚岁",
    "is_lunar": false,
    "latitude": 39.9042,
    "pan_type": "bazi",
    "leap_rule": "归前",
    "longitude": 116.4074,
    "hour_index": 6,
    "is_early_zi": false,
    "solar_time_mode": "自动"
}', '{}', '{}', 'pending', NULL, NULL, 0, '2026-06-23 11:33:16', '2026-06-23 11:33:16');
INSERT INTO "analysis_reports" VALUES (12, 'bazi', '张超超', '男', '2026-06-24', '12:00', '北京', '', '{
    "day": 24,
    "city": "北京",
    "hour": 12,
    "name": "张超超",
    "year": 2026,
    "month": 6,
    "notes": "",
    "gender": "男",
    "minute": 0,
    "age_type": "虚岁",
    "is_lunar": false,
    "latitude": 39.9042,
    "pan_type": "bazi",
    "leap_rule": "归前",
    "longitude": 116.4074,
    "hour_index": 6,
    "is_early_zi": false,
    "solar_time_mode": "自动"
}', '{}', '{}', 'pending', NULL, NULL, 0, '2026-06-24 09:06:55', '2026-06-24 09:06:55');
INSERT INTO "analysis_reports" VALUES (13, 'bazi', '张超超', '男', '2026-06-24', '12:00', '北京', '', '{
    "day": 24,
    "city": "北京",
    "hour": 12,
    "name": "张超超",
    "year": 2026,
    "month": 6,
    "notes": "",
    "gender": "男",
    "minute": 0,
    "age_type": "虚岁",
    "is_lunar": false,
    "latitude": 39.9042,
    "pan_type": "bazi",
    "leap_rule": "归前",
    "longitude": 116.4074,
    "hour_index": 6,
    "is_early_zi": false,
    "solar_time_mode": "自动"
}', '{}', '{}', 'pending', NULL, NULL, 0, '2026-06-24 09:15:53', '2026-06-24 09:15:53');
INSERT INTO "analysis_reports" VALUES (14, 'bazi', '张超超', '男', '2026-06-24', '12:00', '北京', '', '{
    "day": 24,
    "city": "北京",
    "hour": 12,
    "name": "张超超",
    "year": 2026,
    "month": 6,
    "notes": "",
    "gender": "男",
    "minute": 0,
    "age_type": "虚岁",
    "is_lunar": false,
    "latitude": 39.9042,
    "pan_type": "bazi",
    "leap_rule": "归前",
    "longitude": 116.4074,
    "hour_index": 6,
    "is_early_zi": false,
    "solar_time_mode": "自动"
}', '{}', '{}', 'pending', NULL, NULL, 0, '2026-06-24 09:32:10', '2026-06-24 09:32:10');
INSERT INTO "analysis_reports" VALUES (15, 'bazi', '张超超', '男', '2026-06-24', '12:00', '北京', '', '{
    "day": 24,
    "city": "北京",
    "hour": 12,
    "name": "张超超",
    "year": 2026,
    "month": 6,
    "notes": "",
    "gender": "男",
    "minute": 0,
    "age_type": "虚岁",
    "is_lunar": false,
    "latitude": 39.9042,
    "pan_type": "bazi",
    "leap_rule": "归前",
    "longitude": 116.4074,
    "hour_index": 6,
    "is_early_zi": false,
    "solar_time_mode": "自动"
}', '{
    "bazi": {
        "day": "乙亥",
        "hour": "壬午",
        "year": "丙午",
        "month": "甲午",
        "rizhu": "乙"
    },
    "wuxing": {
        "土": {
            "count": 0.45,
            "percentage": 4
        },
        "木": {
            "count": 0.46,
            "percentage": 4
        },
        "水": {
            "count": 0.52,
            "percentage": 5
        },
        "火": {
            "count": 8.7,
            "percentage": 85
        },
        "金": {
            "count": 0.0,
            "percentage": 0
        }
    }
}', '{
    "career": [
        "命局火旺为食伤，代表才华、技艺、表达。命主适合从事与火、木相关的行业，如文化教育、艺术设计、互联网科技、餐饮娱乐、能源化工等需要展现才华与创造力的领域。",
        "食伤旺而无财星（土）透出转化，构成“食伤泄秀”但“秀气”难以生财。命主虽有才华，但将才华转化为实际财富的过程较为曲折，需大运流年引动财星（土）方能得利，否则易怀才不遇。",
        "年柱丙火伤官高透，月柱甲木劫财坐午火伤官。早年易有创业冲动，或尝试自由职业，但劫财坐伤官，合作求财需格外谨慎，易因合作、投资失误而破财，或为朋友、同辈花费甚多。",
        "时柱壬水正印为用，但虚浮无根。中年之后，若能沉心学习一门专业技术或考取相关资质，依靠“印”所代表的证书、名誉、稳定单位来发展，事业方能渐入佳境，获得社会认可。",
        "日支亥水正印为唯一用神，但被旺火耗泄。事业上真正的转机或贵人，可能来自于家庭内部、配偶方，或需要到一个水旺（北方）之地发展，以平衡命局过燥之势。",
        "大运若行金水之地，官印相生，则事业运势提升，可得职位、权力。若行木火土旺运，则火势更炎，需防因判断失误、口舌是非或过度消耗精力而导致事业起伏。"
    ],
    "health": [
        "命局五行严重失衡，火极旺而水木弱，金绝土燥。首要问题在于“火旺木焚”，木主肝胆、神经、筋骨。需特别注意肝胆功能，易有肝火旺盛、眼睛干涩、失眠多梦、神经衰弱等问题。",
        "水弱极受克，水主肾脏、膀胱、泌尿系统、耳朵。先天肾气不足，需防范肾虚、腰膝酸软、听力下降、泌尿系统感染或结石等症。应避免过度劳累和熬夜，极为耗损肾精。",
        "火过旺无制，亦代表心血管系统负荷重。虽然年轻时不显，但随着年龄增长，需预防高血压、心悸、心律不齐等心脑血管方面的问题，饮食宜清淡，少食辛辣燥热之物。",
        "土为财星亦代表脾胃，命局土藏于火中，被旺火烘烤。脾胃功能偏弱，易有消化不良、胃热、口腔溃疡、便秘等“上火”症状。饮食规律和调理脾胃至关重要。",
        "全局缺金，金主肺、大肠、呼吸道。肺部功能相对是短板，抵抗力可能不强，易患感冒、咳嗽、咽喉炎，或皮肤干燥敏感。需注意呼吸道的保养，远离污染环境。",
        "调候为急，日常养生应以“水”为用。多喝水，居住环境宜近水，可从事游泳等水上运动。颜色上多使用黑色、蓝色、白色（金生水），佩戴金银饰品或水晶（属水）或有助益。"
    ],
    "marriage": [
        "男命以正财为妻星，命局地支藏干中有己土偏财，但天干不透，且被旺火所生（火生土），妻星力量微弱。感情经历可能较为平淡，或正缘来得较晚，需主动把握机会。",
        "日柱乙亥，亥中藏甲木劫财与壬水正印。日支夫妻宫坐劫财，且为忌神，暗示婚姻关系中易有竞争、口角，或配偶个性较强，也可能因为经济问题、朋友介入而影响夫妻感情。",
        "全局食伤（火）过旺，食伤既代表才华，也代表对感情的要求和挑剔。命主对感情和配偶的期望值较高，注重精神交流与浪漫感受，但自身情绪波动大，易因言语直接而伤害对方。",
        "日支亥水为正印，为喜用。配偶可能性格沉稳、有学识，或家庭背景不错，能在精神上、实质上给予命主一定的支持和帮助，是命主的“贵人”之一。",
        "命局火炎土燥，水弱受克。需注意肾脏、泌尿系统健康，此亦与生殖功能相关。在子息方面，时柱子女宫壬午，水火交战，需关注子女的健康与教育，沟通上要多些耐心。",
        "婚姻的稳定关键在于大运能否补充水（印）的力量来调候命局。逢猪（亥）、鼠（子）、牛（丑）等水旺之年，感情运势相对和谐；逢蛇（巳）、马（午）、羊（未）等火土旺之年，则需多加忍让，避免冲突。"
    ],
    "personality": [
        "日主乙木，生于午月，火旺木焚，全局火势炎炎，木气被泄严重。乙木为阴柔之木，如藤萝花草，本需依附而生，但命局火过旺，导致木性焦躁。命主可能外表温和，内心却急躁不安，缺乏持久力，做事易虎头蛇尾。",
        "天干透出甲木劫财与壬水正印，甲木为兄，有帮扶之意，但坐于午火之上，自顾不暇。命主可能重情义，喜交友，但朋友助力有限，且易因朋友之事耗费心神，或受其拖累。",
        "时柱壬水正印透出，坐下午火，形成水火既济之象，但水弱火强，正印力量不足。命主内心渴望学识与精神依靠，有学习之心，但易因环境或自身定力不足而难以深入，想法多变。",
        "地支三午火自刑，且为日主乙木之食神。食神过旺为伤，命主可能思维活跃，口才不错，富有艺术或技术天赋，但易流于空想，好享受，追求精神愉悦，有时会显得任性、挑剔。",
        "日柱乙亥，亥水为日主之根，亦为正印，但被三午火围耗，亥中壬甲之力受损。命主内心存在矛盾，一方面有仁慈、传统的一面，另一方面又被旺盛的欲望（火）所驱动，情绪起伏较大。",
        "全局不见官杀（金）来制衡比劫，也无比劫（木）强根支撑。命主可能不喜受约束，规则意识相对淡薄，在团队中或缺乏权威感，行事多凭个人喜好，竞争意识不强但易有孤独感。"
    ],
    "suggestions": [
        "职业发展建议“以技立身”。充分发挥食伤旺的才华，深耕一门技术或艺术，将其做到极致，成为不可替代的专家。避免盲目创业或投机，尤其警惕与朋友合伙。",
        "方位与环境调整。事业发展与居住地宜选择北方（水地）或西方（金地，金能生水），如中国北方、沿海城市或名字带水、金偏旁的城市，有助于平衡命局过燥之气。",
        "修身养性，涵养心性。火旺之人易躁，可通过练习书法、钓鱼、茶道等静心活动，或定期进行冥想、瑜伽来平复心绪。培养“水”的智慧——沉静、包容与韧性。",
        "婚姻感情方面，降低对浪漫和完美的期待，多关注伴侣的实际付出与内在品质。选择对象时，可优先考虑八字水旺或性格沉稳包容之人，能形成互补。晚婚更利稳定。",
        "健康管理是人生重中之重。建立规律的作息，坚决不熬夜。饮食多吃黑色食物（黑豆、黑米、海带）、白色食物（银耳、百合、山药）以滋肾润肺，少吃烧烤、油炸食品。",
        "人际交往注意“慎言”。食伤旺易口无遮拦，得罪人而不自知。多听少说，三思而后言，尤其避免在公开场合批评他人或议论是非，可减少许多不必要的麻烦。",
        "抓住人生“水旺”之机。每逢猪年（亥）、鼠年（子）、牛年（丑），或大运流年遇到壬、癸、亥、子时，往往是运势转好、机遇出现的时期，应积极学习、行动，把握良机。",
        "补足五行所缺之“金”。金在命理中也代表义气、规则、果断。有意培养自己的原则性和执行力，遵守社会规范，学习金融、法律等知识，都能在无形中补益命局。"
    ],
    "wuxing_balance": [
        "五行比例严重失调。火元素占据绝对主导（年、月、时支三午，年干丙，月支午中丁己，时支午中丁己），力量超过80%，呈“炎上”之势。木（日主乙、月干甲、亥中甲）次之但无强根，水（日支亥、时干壬）微弱，土（地支藏干己土）燥，金完全缺失。此为典型的偏枯之命。",
        "生克关系：木（日主）生火（食伤），火势极旺；火生土（财），但土藏于火中不显；水（印）克火（食伤）为调候，但水弱火强，反被火耗；缺金，无法生水，也无法制木。整个命局的矛盾焦点在于“水火交战”，且水方处于绝对劣势。",
        "失衡影响：火过旺无制，焚烧万物。导致命主精力消耗过快，思虑过多而行动力不足，身体健康堪忧（对应心、小肠）。水弱受克，智慧与根基不稳，缺乏持久力和深度。缺金，则决断力、规则感、肺气皆不足。急需大运流年补充金水，以达平衡。"
    ],
    "pattern_analysis": [
        "【食伤泄秀格，然身弱不胜】乙木日主，生于午月，地支三午，天干透丙，火势冲天，为标准的食伤格。食伤代表才华、技艺，格局成立则聪明秀气。但乙木无强根（仅日支亥中甲木微根），被旺火泄身太过，构成“身弱食伤旺”，如小火苗置于洪炉之上，才华难以有效发挥，反为所累，是为“泄秀太过”。",
        "【伤官配印，用神无力】时干透出壬水正印，意图制火润局，形成“伤官配印”的贵格雏形。可惜壬水无根（坐午火被耗，亥水远隔），虚浮无力，如同杯水车薪，难以制衡全局旺火。此格局层次大打折扣，需大运强力扶助水印，方能显贵。",
        "【调候为急，金水为药】夏月乙木，火炎土燥，渴求雨露。亥水为唯一调候用神，但被众火围困，调候力量不足。命局第一用神为水（印），其次为金（官杀），金能生水，且能制木生火之源头（甲木劫财）。最忌再行木火土旺运，加重燥热。",
        "【四柱无财，藏而不露】天干地支不见财星（土）透出，仅地支午中藏有己土偏财。此为“财藏官透”之反局，意味着命主对金钱的追求并不外露，或实际财富多由技艺、才华间接获得，而非直接经商求财。财星为火所生，暗示其财富与火属性行业（科技、文化、能源）紧密相关。"
    ],
    "shishen_analysis": [
        "【食伤（火）极旺】年干丙火为伤官，月支、时支午火为食神，且三午自刑，食伤力量登峰造极。伤官主才华外露、创新叛逆、不拘小节；食神主内在才华、温和表达、享受生活。两者过旺，命主必然聪明机巧，富有艺术或技术感知力，但易骄傲、任性、言辞尖锐，不喜管束。",
        "【印星（水）弱而受制】时干壬水为正印，日支亥中壬水亦为正印。正印代表学业、长辈、贵人、稳定。印星为喜用但力量微弱，说明命主能得到一些长辈关怀或学习机会，但助力有限，学业过程多波折，需自身加倍努力。印星制食伤，也体现内心思想斗争激烈。",
        "【比劫（木）虚浮】月干甲木为劫财，日主乙木为比肩，日支亥中藏甲木劫财。比劫代表同辈、朋友、合作者。甲木坐午火被泄，乙木无根，比劫力量虚浮。意味着命主虽有人缘，但朋友对其实际帮助不大，反而可能在财务、感情上形成竞争或消耗。",
        "【财星（土）藏伏】地支午中均藏有己土偏财。偏财代表意外之财、经商才华、父亲。财星藏而不露，且为食伤所生，意味着命主的财富多来源于专业技能带来的回报，而非直接经营。与父亲缘分可能较浅，或父亲对其助力不明显。",
        "【官杀（金）全无】八字天干地支不见官杀（庚辛申酉）。官杀代表事业、权威、约束、女命之夫缘。官杀缺失，一方面说明命主不喜被管理，适合自由职业或技术岗位；另一方面也意味着在事业上缺乏明确的目标和强有力的推动力，需自我建立规则。"
    ]
}', 'completed', NULL, 'deepseek-v3.1-250821', 4053, '2026-06-24 09:34:57', '2026-06-24 09:36:46');
INSERT INTO "analysis_reports" VALUES (16, 'meihua', '', '', '2024-06-24', '', '', '事业发展如何？', '{
    "day": 24,
    "hour": 10,
    "year": 2024,
    "month": 6,
    "method": "time",
    "question": "事业发展如何？"
}', '{
    "hu": {
        "name": "天风姤",
        "description": "天下有风，姤。后以施命诰四方"
    },
    "base": {
        "name": "天火同人",
        "gua_ci": "同人于野，亨。利涉大川，利君子贞。",
        "lower_name": "离",
        "upper_name": "乾",
        "description": "二人同心，其利断金",
        "changing_yao": 3,
        "lower_nature": "火",
        "upper_nature": "天",
        "changing_yao_name": "九三",
        "changing_yao_text": "伏戎于莽，升其高陵，三岁不兴。",
        "changing_yao_meaning": "军队埋伏在草莽中，登高陵眺望，三年不能兴兵"
    },
    "bian": {
        "name": "火天大有",
        "judgment": "吉",
        "description": "火在天上，大有。君子以遏恶扬善，顺天休命"
    },
    "overall_judgment": "平"
}', '{
    "bad_omens": [
        "动爻''伏戎于莽''警示暗中竞争或阻力，需防小人作祟或资源争夺。",
        "''三岁不兴''表明短期难见显效，易生挫败感，需调整预期。",
        "互卦姤有''不期而遇''之变，突发状况可能打乱原有计划。",
        "体火克用金虽为克出，但火需持续燃烧，提示你身心消耗较大。",
        "同人卦强调''合''，若人际关系处理失当，可能反成发展瓶颈。"
    ],
    "good_omens": [
        "同人卦''利涉大川''，预示合作可跨越难关，拓展事业疆域。",
        "变卦大有直接为吉卦，终局光明，努力终得回报。",
        "体克用格局显示你对事业有主导力，可通过自身行动影响结果。",
        "姤卦''施命诰四方''，提示善用沟通与宣导能化解潜在矛盾。",
        "卦辞''利君子贞''，坚守正道与德行将为你赢得支持与机遇。"
    ],
    "gua_overview": [
        "本卦天火同人，象征志同道合、同心协力之象，事业上需注重人际关系与合作共赢。",
        "动爻在第三爻（九三），爻辞''伏戎于莽，升其高陵，三岁不兴''，提示事业发展中可能潜伏竞争或阻碍，需谨慎应对。",
        "互卦天风姤，揭示事态发展中或有突如其来的变化或邂逅，需保持警觉与灵活应变。",
        "变卦火天大有，为最终结果之象，预示若能克服困难、顺应天道，终将收获丰硕成果。",
        "体卦为离火（下卦），用卦为乾天（上卦），火生土（乾属金，火克金为耗泄，但卦象以五行生克论，此处火克金为''我克者''，体克用，主事可成但需付出努力）。"
    ],
    "action_advice": [
        "深耕合作：主动寻求志同道合的伙伴，尤其注重跨领域或上下级协作，以应''同人于野''之象。",
        "隐忍蓄力：面对''三岁不兴''阶段，宜低调积累技能与资源，避免贸然激进。",
        "察变应变：对行业风向保持敏感（姤卦启示），快速调整策略以适应新环境。",
        "扬善抑恶：秉承大有卦''遏恶扬善''精神，以诚信处事，可化竞争为共赢。",
        "平衡心火：体卦离火象征热情，但需防过度消耗，注意工作节奏与身心健康。"
    ],
    "final_verdict": "事业发展趋势呈''先平后吉''之象：短期需应对合作中的暗流与缓慢进展，但只要你坚守正道、善用团队之力，并能灵活适应变化，中长期将迈向''大有''丰收之境。关键在于以耐心孵化机遇，以光明心驾驭过程。",
    "situation_analysis": [
        "当前事业处于''同人''阶段，需依靠团队协作或外部合作方能突破，单打独斗易遇阻力。",
        "动爻''三岁不兴''暗示短期（可能数月或数年）内进展缓慢，不可急于求成，宜积蓄力量。",
        "互卦姤象''天下有风''，预示事业环境中可能出现新机遇或突发挑战，需快速响应。",
        "变卦大有''火在天上''，光明普照之象，长期看事业有蒸蒸日上之势，但必经前期磨合。",
        "体用生克中，离火（体）克乾金（用），表明你需主动付出精力以驾驭事业局面，过程稍显吃力但可控。"
    ]
}', 'completed', NULL, 'deepseek-v3.1-250821', 1210, '2026-06-24 09:41:51', '2026-06-24 09:42:12');
INSERT INTO "analysis_reports" VALUES (17, 'meihua', '', '', '', '', '', '我和我老婆之间的感情如何？', '{
    "num1": 3,
    "num2": 5,
    "method": "number",
    "question": "我和我老婆之间的感情如何？",
    "lower_num": 5,
    "upper_num": 3
}', '{
    "hu": {
        "name": "泽风大过",
        "description": "泽风大过卦，泽上风下。"
    },
    "base": {
        "name": "火风鼎",
        "gua_ci": "",
        "lower_name": "巽",
        "upper_name": "离",
        "description": "火风鼎卦，火上风下。",
        "lower_nature": "",
        "upper_nature": ""
    },
    "bian": {
        "name": "天雷无妄",
        "judgment": "平",
        "description": "天雷无妄卦，天上雷下。"
    },
    "overall_judgment": "平"
}', '{
    "bad_omens": [
        "体生用格局消耗元气，长期单向付出可能导致你产生倦怠感，如同鼎下薪火需持续添柴",
        "大过卦''泽灭木''之险，警示积累的怨气可能如泽水淹没舟船，突然爆发时易伤及根本",
        "离火克互卦兑金形成''火泽睽''的隐象，需防因财务、亲友介入等外部因素产生分歧",
        "变卦乾金克震木形成压力循环，若固执己见或强求对方改变，恐触发''无妄之灾''的意外摩擦"
    ],
    "good_omens": [
        "鼎卦''亨饪''之德，象征日常相处中仍存温情互动，共理家务或培养共同兴趣可成情感催化剂",
        "巽为长女离为中女，双阴卦相济，体现你们具备女性特有的细腻与韧性，能通过柔性方式化解矛盾",
        "变卦无妄''不利有攸往''的反面启示：若安守当下真诚相待，反得''无妄之疾，勿药有喜''的自然愈合之机",
        "体卦巽木终得变卦震木比和，预示你内在的调整意愿将逐渐获得呼应，如春风复苏草木"
    ],
    "gua_overview": [
        "本卦火风鼎（䷱），上离火下巽风，火借风势，风助火威，象征革新与稳固的平衡。鼎为烹煮之器，喻示家庭生活与情感滋养",
        "互卦泽风大过（䛐），上兑泽下巽风，泽水覆舟之象，暗示关系中存在过度或失衡的风险，需警惕压力积累",
        "变卦天雷无妄（䷘），上乾天下震雷，天道刚健而雷动不安，预示若处理得当可回归本真，反之易生意外波折",
        "体用分析：本卦下巽木（体）生上离火（用），体生用为泄气，表明你为维系感情付出较多心力；变卦中乾金克震木，提示外部压力可能影响内在和谐"
    ],
    "action_advice": [
        "借鼎卦''正位凝命''之智：定期安排不受干扰的深度交谈，如鼎器安置般创造稳定的沟通仪式",
        "化大过''独立不惧''为用：在承担家庭责任时明确边界，避免过度包揽形成隐性怨怼，学习协同分担",
        "循无妄''天命不佑''之诫：停止对完美关系的幻想，接纳彼此本性中的微小瑕疵，如天地容雷般自然相处",
        "取巽风''申命行事''之柔：以渗透式关怀替代激烈表达，如微风润物般持续传递重视而非控制",
        "用离火''明照四方''之察：共同参与文化娱乐活动（火象），以光明心性照亮可能被忽略的情感角落"
    ],
    "final_verdict": "鼎器虽稳需常涤尘垢，风火相偕贵在调薪。卦象显示你们感情如鼎足立地尚存根基，但互卦大过揭示隐性张力，变卦无妄警示妄动之险。整体吉凶参半，转机在于：化体生用的消耗为木火通明的相生，借鼎卦革新之力温和调整相处模式，则可趋近无妄卦''真实无伪''的理想状态。",
    "situation_analysis": [
        "鼎卦卦辞''元吉，亨''，初显感情基础尚存，如鼎足立地般稳定，但需注意''鼎颠趾''的爻辞警示——若根基不稳易生倾覆",
        "互卦大过''栋桡''之象，暗示长期积累的琐碎矛盾可能如房屋栋梁弯曲，表面平静下隐伏沟通不畅或责任分配不均的问题",
        "变卦无妄''其匪正有眚''，提醒避免因猜忌或强求改变引发无谓冲突，当前阶段宜守正而非妄动",
        "离火为明，巽风为入，组合显示你们对彼此有深刻了解，但火过旺则灼木，需留意情绪过热伤及包容性"
    ]
}', 'completed', NULL, 'deepseek-v3.1-250821', 1258, '2026-06-24 09:54:21', '2026-06-24 09:54:56');
INSERT INTO "analysis_reports" VALUES (18, 'bazi', '张超超', '男', '2026-06-28', '12:00', '北京', '', '{
    "day": 28,
    "city": "北京",
    "hour": 12,
    "name": "张超超",
    "year": 2026,
    "month": 6,
    "notes": "",
    "gender": "男",
    "minute": 0,
    "age_type": "虚岁",
    "is_lunar": false,
    "latitude": 39.9042,
    "pan_type": "bazi",
    "leap_rule": "归前",
    "longitude": 116.4074,
    "hour_index": 6,
    "is_early_zi": false,
    "solar_time_mode": "自动"
}', '{}', '{}', 'pending', NULL, NULL, 0, '2026-06-28 17:29:48', '2026-06-28 17:29:48');
INSERT INTO "analysis_reports" VALUES (19, 'bazi', '张超超', '男', '2026-06-28', '12:00', '北京', '', '{
    "day": 28,
    "city": "北京",
    "hour": 12,
    "name": "张超超",
    "year": 2026,
    "month": 6,
    "notes": "",
    "gender": "男",
    "minute": 0,
    "age_type": "虚岁",
    "is_lunar": false,
    "latitude": 39.9042,
    "pan_type": "bazi",
    "leap_rule": "归前",
    "longitude": 116.4074,
    "hour_index": 6,
    "is_early_zi": false,
    "solar_time_mode": "自动"
}', '{}', '{}', 'pending', NULL, NULL, 0, '2026-06-28 17:30:14', '2026-06-28 17:30:14');
INSERT INTO "analysis_reports" VALUES (20, 'meihua', '', '', '2026-06-28', '', '', '', '{
    "day": 28,
    "hour": 17,
    "year": 2026,
    "month": 6,
    "method": "time",
    "question": "",
    "time_str": ""
}', '{}', '{}', 'pending', NULL, NULL, 0, '2026-06-28 17:45:23', '2026-06-28 17:45:23');
INSERT INTO "ba_gua" VALUES (1, 1, '乾', '天', '☰', '金', '天行健，君子以自强不息');
INSERT INTO "ba_gua" VALUES (2, 2, '兑', '泽', '☱', '金', '丽泽，兑。君子以朋友讲习');
INSERT INTO "ba_gua" VALUES (3, 3, '离', '火', '☲', '火', '明两作，离。大人以继明照于四方');
INSERT INTO "ba_gua" VALUES (4, 4, '震', '雷', '☳', '木', '洊雷，震。君子以恐惧修省');
INSERT INTO "ba_gua" VALUES (5, 5, '巽', '风', '☴', '木', '随风，巽。君子以申命行事');
INSERT INTO "ba_gua" VALUES (6, 6, '坎', '水', '☵', '水', '习坎，有孚维心亨，行有尚');
INSERT INTO "ba_gua" VALUES (7, 7, '艮', '山', '☶', '土', '兼山，艮。君子以思不出其位');
INSERT INTO "ba_gua" VALUES (8, 8, '坤', '地', '☷', '土', '地势坤，君子以厚德载物');
INSERT INTO "changsheng_lookup" VALUES (1, '甲', '亥', '长生');
INSERT INTO "changsheng_lookup" VALUES (2, '甲', '子', '沐浴');
INSERT INTO "changsheng_lookup" VALUES (3, '甲', '丑', '冠带');
INSERT INTO "changsheng_lookup" VALUES (4, '甲', '寅', '临官');
INSERT INTO "changsheng_lookup" VALUES (5, '甲', '卯', '帝旺');
INSERT INTO "changsheng_lookup" VALUES (6, '甲', '辰', '衰');
INSERT INTO "changsheng_lookup" VALUES (7, '甲', '巳', '病');
INSERT INTO "changsheng_lookup" VALUES (8, '甲', '午', '死');
INSERT INTO "changsheng_lookup" VALUES (9, '甲', '未', '墓');
INSERT INTO "changsheng_lookup" VALUES (10, '甲', '申', '绝');
INSERT INTO "changsheng_lookup" VALUES (11, '甲', '酉', '胎');
INSERT INTO "changsheng_lookup" VALUES (12, '甲', '戌', '养');
INSERT INTO "changsheng_lookup" VALUES (13, '乙', '午', '长生');
INSERT INTO "changsheng_lookup" VALUES (14, '乙', '巳', '沐浴');
INSERT INTO "changsheng_lookup" VALUES (15, '乙', '辰', '冠带');
INSERT INTO "changsheng_lookup" VALUES (16, '乙', '卯', '临官');
INSERT INTO "changsheng_lookup" VALUES (17, '乙', '寅', '帝旺');
INSERT INTO "changsheng_lookup" VALUES (18, '乙', '丑', '衰');
INSERT INTO "changsheng_lookup" VALUES (19, '乙', '子', '病');
INSERT INTO "changsheng_lookup" VALUES (20, '乙', '亥', '死');
INSERT INTO "changsheng_lookup" VALUES (21, '乙', '戌', '墓');
INSERT INTO "changsheng_lookup" VALUES (22, '乙', '酉', '绝');
INSERT INTO "changsheng_lookup" VALUES (23, '乙', '申', '胎');
INSERT INTO "changsheng_lookup" VALUES (24, '乙', '未', '养');
INSERT INTO "changsheng_lookup" VALUES (25, '丙', '寅', '长生');
INSERT INTO "changsheng_lookup" VALUES (26, '丙', '卯', '沐浴');
INSERT INTO "changsheng_lookup" VALUES (27, '丙', '辰', '冠带');
INSERT INTO "changsheng_lookup" VALUES (28, '丙', '巳', '临官');
INSERT INTO "changsheng_lookup" VALUES (29, '丙', '午', '帝旺');
INSERT INTO "changsheng_lookup" VALUES (30, '丙', '未', '衰');
INSERT INTO "changsheng_lookup" VALUES (31, '丙', '申', '病');
INSERT INTO "changsheng_lookup" VALUES (32, '丙', '酉', '死');
INSERT INTO "changsheng_lookup" VALUES (33, '丙', '戌', '墓');
INSERT INTO "changsheng_lookup" VALUES (34, '丙', '亥', '绝');
INSERT INTO "changsheng_lookup" VALUES (35, '丙', '子', '胎');
INSERT INTO "changsheng_lookup" VALUES (36, '丙', '丑', '养');
INSERT INTO "changsheng_lookup" VALUES (37, '丁', '酉', '长生');
INSERT INTO "changsheng_lookup" VALUES (38, '丁', '申', '沐浴');
INSERT INTO "changsheng_lookup" VALUES (39, '丁', '未', '冠带');
INSERT INTO "changsheng_lookup" VALUES (40, '丁', '午', '临官');
INSERT INTO "changsheng_lookup" VALUES (41, '丁', '巳', '帝旺');
INSERT INTO "changsheng_lookup" VALUES (42, '丁', '辰', '衰');
INSERT INTO "changsheng_lookup" VALUES (43, '丁', '卯', '病');
INSERT INTO "changsheng_lookup" VALUES (44, '丁', '寅', '死');
INSERT INTO "changsheng_lookup" VALUES (45, '丁', '丑', '墓');
INSERT INTO "changsheng_lookup" VALUES (46, '丁', '子', '绝');
INSERT INTO "changsheng_lookup" VALUES (47, '丁', '亥', '胎');
INSERT INTO "changsheng_lookup" VALUES (48, '丁', '戌', '养');
INSERT INTO "changsheng_lookup" VALUES (49, '戊', '寅', '长生');
INSERT INTO "changsheng_lookup" VALUES (50, '戊', '卯', '沐浴');
INSERT INTO "changsheng_lookup" VALUES (51, '戊', '辰', '冠带');
INSERT INTO "changsheng_lookup" VALUES (52, '戊', '巳', '临官');
INSERT INTO "changsheng_lookup" VALUES (53, '戊', '午', '帝旺');
INSERT INTO "changsheng_lookup" VALUES (54, '戊', '未', '衰');
INSERT INTO "changsheng_lookup" VALUES (55, '戊', '申', '病');
INSERT INTO "changsheng_lookup" VALUES (56, '戊', '酉', '死');
INSERT INTO "changsheng_lookup" VALUES (57, '戊', '戌', '墓');
INSERT INTO "changsheng_lookup" VALUES (58, '戊', '亥', '绝');
INSERT INTO "changsheng_lookup" VALUES (59, '戊', '子', '胎');
INSERT INTO "changsheng_lookup" VALUES (60, '戊', '丑', '养');
INSERT INTO "changsheng_lookup" VALUES (61, '己', '酉', '长生');
INSERT INTO "changsheng_lookup" VALUES (62, '己', '申', '沐浴');
INSERT INTO "changsheng_lookup" VALUES (63, '己', '未', '冠带');
INSERT INTO "changsheng_lookup" VALUES (64, '己', '午', '临官');
INSERT INTO "changsheng_lookup" VALUES (65, '己', '巳', '帝旺');
INSERT INTO "changsheng_lookup" VALUES (66, '己', '辰', '衰');
INSERT INTO "changsheng_lookup" VALUES (67, '己', '卯', '病');
INSERT INTO "changsheng_lookup" VALUES (68, '己', '寅', '死');
INSERT INTO "changsheng_lookup" VALUES (69, '己', '丑', '墓');
INSERT INTO "changsheng_lookup" VALUES (70, '己', '子', '绝');
INSERT INTO "changsheng_lookup" VALUES (71, '己', '亥', '胎');
INSERT INTO "changsheng_lookup" VALUES (72, '己', '戌', '养');
INSERT INTO "changsheng_lookup" VALUES (73, '庚', '巳', '长生');
INSERT INTO "changsheng_lookup" VALUES (74, '庚', '午', '沐浴');
INSERT INTO "changsheng_lookup" VALUES (75, '庚', '未', '冠带');
INSERT INTO "changsheng_lookup" VALUES (76, '庚', '申', '临官');
INSERT INTO "changsheng_lookup" VALUES (77, '庚', '酉', '帝旺');
INSERT INTO "changsheng_lookup" VALUES (78, '庚', '戌', '衰');
INSERT INTO "changsheng_lookup" VALUES (79, '庚', '亥', '病');
INSERT INTO "changsheng_lookup" VALUES (80, '庚', '子', '死');
INSERT INTO "changsheng_lookup" VALUES (81, '庚', '丑', '墓');
INSERT INTO "changsheng_lookup" VALUES (82, '庚', '寅', '绝');
INSERT INTO "changsheng_lookup" VALUES (83, '庚', '卯', '胎');
INSERT INTO "changsheng_lookup" VALUES (84, '庚', '辰', '养');
INSERT INTO "changsheng_lookup" VALUES (85, '辛', '子', '长生');
INSERT INTO "changsheng_lookup" VALUES (86, '辛', '亥', '沐浴');
INSERT INTO "changsheng_lookup" VALUES (87, '辛', '戌', '冠带');
INSERT INTO "changsheng_lookup" VALUES (88, '辛', '酉', '临官');
INSERT INTO "changsheng_lookup" VALUES (89, '辛', '申', '帝旺');
INSERT INTO "changsheng_lookup" VALUES (90, '辛', '未', '衰');
INSERT INTO "changsheng_lookup" VALUES (91, '辛', '午', '病');
INSERT INTO "changsheng_lookup" VALUES (92, '辛', '巳', '死');
INSERT INTO "changsheng_lookup" VALUES (93, '辛', '辰', '墓');
INSERT INTO "changsheng_lookup" VALUES (94, '辛', '卯', '绝');
INSERT INTO "changsheng_lookup" VALUES (95, '辛', '寅', '胎');
INSERT INTO "changsheng_lookup" VALUES (96, '辛', '丑', '养');
INSERT INTO "changsheng_lookup" VALUES (97, '壬', '申', '长生');
INSERT INTO "changsheng_lookup" VALUES (98, '壬', '酉', '沐浴');
INSERT INTO "changsheng_lookup" VALUES (99, '壬', '戌', '冠带');
INSERT INTO "changsheng_lookup" VALUES (100, '壬', '亥', '临官');
INSERT INTO "changsheng_lookup" VALUES (101, '壬', '子', '帝旺');
INSERT INTO "changsheng_lookup" VALUES (102, '壬', '丑', '衰');
INSERT INTO "changsheng_lookup" VALUES (103, '壬', '寅', '病');
INSERT INTO "changsheng_lookup" VALUES (104, '壬', '卯', '死');
INSERT INTO "changsheng_lookup" VALUES (105, '壬', '辰', '墓');
INSERT INTO "changsheng_lookup" VALUES (106, '壬', '巳', '绝');
INSERT INTO "changsheng_lookup" VALUES (107, '壬', '午', '胎');
INSERT INTO "changsheng_lookup" VALUES (108, '壬', '未', '养');
INSERT INTO "changsheng_lookup" VALUES (109, '癸', '卯', '长生');
INSERT INTO "changsheng_lookup" VALUES (110, '癸', '寅', '沐浴');
INSERT INTO "changsheng_lookup" VALUES (111, '癸', '丑', '冠带');
INSERT INTO "changsheng_lookup" VALUES (112, '癸', '子', '临官');
INSERT INTO "changsheng_lookup" VALUES (113, '癸', '亥', '帝旺');
INSERT INTO "changsheng_lookup" VALUES (114, '癸', '戌', '衰');
INSERT INTO "changsheng_lookup" VALUES (115, '癸', '酉', '病');
INSERT INTO "changsheng_lookup" VALUES (116, '癸', '申', '死');
INSERT INTO "changsheng_lookup" VALUES (117, '癸', '未', '墓');
INSERT INTO "changsheng_lookup" VALUES (118, '癸', '午', '绝');
INSERT INTO "changsheng_lookup" VALUES (119, '癸', '巳', '胎');
INSERT INTO "changsheng_lookup" VALUES (120, '癸', '辰', '养');
INSERT INTO "city_coords" VALUES (1, '北京', 116.4074, 39.9042);
INSERT INTO "city_coords" VALUES (2, '上海', 121.4737, 31.2304);
INSERT INTO "city_coords" VALUES (3, '广州', 113.2644, 23.1291);
INSERT INTO "city_coords" VALUES (4, '深圳', 114.0579, 22.5431);
INSERT INTO "city_coords" VALUES (5, '杭州', 120.1552, 30.2875);
INSERT INTO "city_coords" VALUES (6, '南京', 118.7969, 32.0603);
INSERT INTO "city_coords" VALUES (7, '成都', 104.0668, 30.5728);
INSERT INTO "city_coords" VALUES (8, '武汉', 114.3055, 30.5928);
INSERT INTO "city_coords" VALUES (9, '西安', 108.948, 34.2631);
INSERT INTO "city_coords" VALUES (10, '重庆', 106.5516, 29.563);
INSERT INTO "city_coords" VALUES (11, '天津', 117.2008, 39.0842);
INSERT INTO "city_coords" VALUES (12, '苏州', 120.6293, 31.3251);
INSERT INTO "city_coords" VALUES (13, '郑州', 113.6243, 34.7466);
INSERT INTO "city_coords" VALUES (14, '长沙', 112.9388, 28.228);
INSERT INTO "city_coords" VALUES (15, '青岛', 120.3316, 36.0671);
INSERT INTO "city_coords" VALUES (16, '沈阳', 123.4328, 41.8045);
INSERT INTO "city_coords" VALUES (17, '大连', 121.6147, 38.914);
INSERT INTO "city_coords" VALUES (18, '宁波', 121.5429, 29.8753);
INSERT INTO "city_coords" VALUES (19, '无锡', 120.3199, 31.573);
INSERT INTO "city_coords" VALUES (20, '佛山', 113.1064, 23.0208);
INSERT INTO "di_zhi" VALUES (1, '子', '水', '阳', '北方', '冬季', '十一月', '23:00-01:00', '万物种子，阳气始生', '膀胱、耳', 0);
INSERT INTO "di_zhi" VALUES (2, '丑', '土', '阴', '东北方', '冬季', '十二月', '01:00-03:00', '万物纽芽，阴寒凝结', '脾、肚', 1);
INSERT INTO "di_zhi" VALUES (3, '寅', '木', '阳', '东北方', '春季', '正月', '03:00-05:00', '万物始生，阳气初发', '胆、手', 2);
INSERT INTO "di_zhi" VALUES (4, '卯', '木', '阴', '东方', '春季', '二月', '05:00-07:00', '万物茂盛，阳气盛大', '肝、指', 3);
INSERT INTO "di_zhi" VALUES (5, '辰', '土', '阳', '东南方', '春季', '三月', '07:00-09:00', '万物振奋，阳气渐盛', '胃、肩', 4);
INSERT INTO "di_zhi" VALUES (6, '巳', '火', '阴', '东南方', '夏季', '四月', '09:00-11:00', '万物已成，阳气正盛', '心、面', 5);
INSERT INTO "di_zhi" VALUES (7, '午', '火', '阳', '南方', '夏季', '五月', '11:00-13:00', '万物丰满，阳气极盛', '小肠、眼', 6);
INSERT INTO "di_zhi" VALUES (8, '未', '土', '阴', '西南方', '夏季', '六月', '13:00-15:00', '万物滋味，阴气始生', '脾、脊', 7);
INSERT INTO "di_zhi" VALUES (9, '申', '金', '阳', '西南方', '秋季', '七月', '15:00-17:00', '万物身体，阴气渐长', '大肠、经络', 8);
INSERT INTO "di_zhi" VALUES (10, '酉', '金', '阴', '西方', '秋季', '八月', '17:00-19:00', '万物成熟，阴气正盛', '肺、皮毛', 9);
INSERT INTO "di_zhi" VALUES (11, '戌', '土', '阳', '西北方', '秋季', '九月', '19:00-21:00', '万物尽灭，阳气渐衰', '胃、命门', 10);
INSERT INTO "di_zhi" VALUES (12, '亥', '水', '阴', '西北方', '冬季', '十月', '21:00-23:00', '万物收藏，阳气微弱', '肾、头', 11);
INSERT INTO "di_zhi_chong" VALUES (1, '子午', '水火相冲，主心脑血管');
INSERT INTO "di_zhi_chong" VALUES (2, '丑未', '土土相冲，主脾胃');
INSERT INTO "di_zhi_chong" VALUES (3, '寅申', '金木相冲，主道路');
INSERT INTO "di_zhi_chong" VALUES (4, '卯酉', '金木相冲，主门户');
INSERT INTO "di_zhi_chong" VALUES (5, '辰戌', '土土相冲，主墓库');
INSERT INTO "di_zhi_chong" VALUES (6, '巳亥', '水火相冲，主驿马');
INSERT INTO "di_zhi_hai" VALUES (1, '子未', '彼此损害');
INSERT INTO "di_zhi_hai" VALUES (2, '丑午', '官鬼相害');
INSERT INTO "di_zhi_hai" VALUES (3, '寅巳', '无辜受害');
INSERT INTO "di_zhi_hai" VALUES (4, '卯辰', '口舌是非');
INSERT INTO "di_zhi_hai" VALUES (5, '申亥', '竞争伤害');
INSERT INTO "di_zhi_hai" VALUES (6, '酉戌', '口舌争斗');
INSERT INTO "di_zhi_he" VALUES (1, '子丑', '土', '泥合', '主纠结，相互牵制');
INSERT INTO "di_zhi_he" VALUES (2, '寅亥', '木', '仁合', '主善良，互相生助');
INSERT INTO "di_zhi_he" VALUES (3, '卯戌', '火', '合火', '主热情，互相激荡');
INSERT INTO "di_zhi_he" VALUES (4, '辰酉', '金', '合金', '主刚毅，互相促进');
INSERT INTO "di_zhi_he" VALUES (5, '巳申', '水', '合水', '主智慧，互相滋润');
INSERT INTO "di_zhi_he" VALUES (6, '午未', '土', '合土', '主包容，互相融合');
INSERT INTO "di_zhi_hidden_gan" VALUES (1, '子', '癸', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (2, '丑', '己', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (3, '丑', '辛', '中气', 0.3, 2);
INSERT INTO "di_zhi_hidden_gan" VALUES (4, '丑', '癸', '余气', 0.1, 3);
INSERT INTO "di_zhi_hidden_gan" VALUES (5, '寅', '甲', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (6, '寅', '丙', '中气', 0.3, 2);
INSERT INTO "di_zhi_hidden_gan" VALUES (7, '寅', '戊', '余气', 0.1, 3);
INSERT INTO "di_zhi_hidden_gan" VALUES (8, '卯', '乙', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (9, '辰', '戊', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (10, '辰', '乙', '中气', 0.3, 2);
INSERT INTO "di_zhi_hidden_gan" VALUES (11, '辰', '癸', '余气', 0.1, 3);
INSERT INTO "di_zhi_hidden_gan" VALUES (12, '巳', '丙', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (13, '巳', '戊', '中气', 0.3, 2);
INSERT INTO "di_zhi_hidden_gan" VALUES (14, '巳', '庚', '余气', 0.1, 3);
INSERT INTO "di_zhi_hidden_gan" VALUES (15, '午', '丁', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (16, '午', '己', '中气', 0.3, 2);
INSERT INTO "di_zhi_hidden_gan" VALUES (17, '未', '己', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (18, '未', '丁', '中气', 0.3, 2);
INSERT INTO "di_zhi_hidden_gan" VALUES (19, '未', '乙', '余气', 0.1, 3);
INSERT INTO "di_zhi_hidden_gan" VALUES (20, '申', '庚', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (21, '申', '壬', '中气', 0.3, 2);
INSERT INTO "di_zhi_hidden_gan" VALUES (22, '申', '戊', '余气', 0.1, 3);
INSERT INTO "di_zhi_hidden_gan" VALUES (23, '酉', '辛', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (24, '戌', '戊', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (25, '戌', '辛', '中气', 0.3, 2);
INSERT INTO "di_zhi_hidden_gan" VALUES (26, '戌', '丁', '余气', 0.1, 3);
INSERT INTO "di_zhi_hidden_gan" VALUES (27, '亥', '壬', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (28, '亥', '甲', '中气', 0.3, 2);
INSERT INTO "di_zhi_hidden_gan" VALUES (29, '子', '癸', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (30, '丑', '己', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (31, '丑', '辛', '中气', 0.3, 2);
INSERT INTO "di_zhi_hidden_gan" VALUES (32, '丑', '癸', '余气', 0.1, 3);
INSERT INTO "di_zhi_hidden_gan" VALUES (33, '寅', '甲', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (34, '寅', '丙', '中气', 0.3, 2);
INSERT INTO "di_zhi_hidden_gan" VALUES (35, '寅', '戊', '余气', 0.1, 3);
INSERT INTO "di_zhi_hidden_gan" VALUES (36, '卯', '乙', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (37, '辰', '戊', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (38, '辰', '乙', '中气', 0.3, 2);
INSERT INTO "di_zhi_hidden_gan" VALUES (39, '辰', '癸', '余气', 0.1, 3);
INSERT INTO "di_zhi_hidden_gan" VALUES (40, '巳', '丙', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (41, '巳', '戊', '中气', 0.3, 2);
INSERT INTO "di_zhi_hidden_gan" VALUES (42, '巳', '庚', '余气', 0.1, 3);
INSERT INTO "di_zhi_hidden_gan" VALUES (43, '午', '丁', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (44, '午', '己', '中气', 0.3, 2);
INSERT INTO "di_zhi_hidden_gan" VALUES (45, '未', '己', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (46, '未', '丁', '中气', 0.3, 2);
INSERT INTO "di_zhi_hidden_gan" VALUES (47, '未', '乙', '余气', 0.1, 3);
INSERT INTO "di_zhi_hidden_gan" VALUES (48, '申', '庚', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (49, '申', '壬', '中气', 0.3, 2);
INSERT INTO "di_zhi_hidden_gan" VALUES (50, '申', '戊', '余气', 0.1, 3);
INSERT INTO "di_zhi_hidden_gan" VALUES (51, '酉', '辛', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (52, '戌', '戊', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (53, '戌', '辛', '中气', 0.3, 2);
INSERT INTO "di_zhi_hidden_gan" VALUES (54, '戌', '丁', '余气', 0.1, 3);
INSERT INTO "di_zhi_hidden_gan" VALUES (55, '亥', '壬', '本气', 0.6, 1);
INSERT INTO "di_zhi_hidden_gan" VALUES (56, '亥', '甲', '中气', 0.3, 2);
INSERT INTO "di_zhi_san_he" VALUES (1, '申子辰', '水', '水局，主智慧流动');
INSERT INTO "di_zhi_san_he" VALUES (2, '亥卯未', '木', '木局，主仁慈生发');
INSERT INTO "di_zhi_san_he" VALUES (3, '寅午戌', '火', '火局，主热情炎上');
INSERT INTO "di_zhi_san_he" VALUES (4, '巳酉丑', '金', '金局，主刚毅收敛');
INSERT INTO "di_zhi_xing" VALUES (1, '寅巳申', '无恩之刑', '忘恩负义，以怨报德');
INSERT INTO "di_zhi_xing" VALUES (2, '丑戌未', '恃势之刑', '仗势欺人，为富不仁');
INSERT INTO "di_zhi_xing" VALUES (3, '子卯', '无礼之刑', '以下犯上，不知礼义');
INSERT INTO "di_zhi_xing" VALUES (4, '辰午酉亥', '自刑', '自寻烦恼，自我矛盾');
INSERT INTO "hexagram_64" VALUES (1, 1, '乾为天', 1, 1, '金', '天行健，君子以自强不息', '吉', '元亨，利贞。');
INSERT INTO "hexagram_64" VALUES (2, 2, '天风姤', 1, 5, '金', '天下有风，姤。后以施命诰四方', '平', '女壮，勿用取女。');
INSERT INTO "hexagram_64" VALUES (3, 3, '天山遁', 1, 7, '金', '天下有山，遁。君子以远小人，不恶而严', '平', '亨，小利贞。');
INSERT INTO "hexagram_64" VALUES (4, 4, '天地否', 1, 8, '土', '天地不交，否。君子以俭德辟难，不可荣以禄', '凶', '否之匪人，不利君子贞，大往小来。');
INSERT INTO "hexagram_64" VALUES (5, 5, '风地观', 5, 8, '土', '风行地上，观。先王以省方观民设教', '吉', '盥而不荐，有孚颙若。');
INSERT INTO "hexagram_64" VALUES (6, 6, '山地剥', 7, 8, '土', '山附于地，剥。上以厚下安宅', '凶', '不利有攸往。');
INSERT INTO "hexagram_64" VALUES (7, 7, '火地晋', 3, 8, '火', '明出地上，晋。君子以自昭明德', '吉', '康侯用锡马蕃庶，昼日三接。');
INSERT INTO "hexagram_64" VALUES (8, 8, '火天大有', 3, 1, '火', '火在天上，大有。君子以遏恶扬善，顺天休命', '吉', '元亨。');
INSERT INTO "hexagram_64" VALUES (9, 9, '坎为水', 2, 2, '水', '习坎，有孚维心亨，行有尚', '凶', '习坎，有孚维心亨，行有尚。');
INSERT INTO "hexagram_64" VALUES (10, 10, '水泽节', 2, 6, '水', '泽上有水，节。君子以制数度，议德行', '吉', '亨，苦节不可贞。');
INSERT INTO "hexagram_64" VALUES (11, 11, '水雷屯', 2, 4, '水', '云雷屯，君子以经纶', '平', '元亨，利贞。勿用有攸往。利建侯。');
INSERT INTO "hexagram_64" VALUES (12, 12, '水火既济', 2, 3, '水', '水在火上，既济。君子以思患而豫防之', '吉', '亨，小利贞，初吉终乱。');
INSERT INTO "hexagram_64" VALUES (13, 13, '泽火革', 6, 3, '火', '泽中有火，革。君子以治历明时', '吉', '巳日乃孚，元亨，利贞，悔亡。');
INSERT INTO "hexagram_64" VALUES (14, 14, '雷火丰', 4, 3, '火', '雷电皆至，丰。君子以折狱致刑', '吉', '亨，王假之，勿忧，宜日中。');
INSERT INTO "hexagram_64" VALUES (15, 15, '地火明夷', 8, 3, '火', '明入地中，明夷。君子以莅众，用晦而明', '凶', '利艰贞。');
INSERT INTO "hexagram_64" VALUES (16, 16, '地水师', 8, 2, '水', '地中有水，师。君子以容民畜众', '平', '贞，丈人吉，无咎。');
INSERT INTO "hexagram_64" VALUES (17, 17, '艮为山', 7, 7, '土', '兼山，艮。君子以思不出其位', '平', '艮其背，不获其身，行其庭，不见其人，无咎。');
INSERT INTO "hexagram_64" VALUES (18, 18, '山火贲', 7, 3, '土', '山下有火，贲。君子以明庶政，无敢折狱', '吉', '亨，小利有攸往。');
INSERT INTO "hexagram_64" VALUES (19, 19, '山天大畜', 7, 1, '土', '天在山中，大畜。君子以多识前言往行，以畜其德', '吉', '利贞，不家食吉，利涉大川。');
INSERT INTO "hexagram_64" VALUES (20, 20, '山泽损', 7, 6, '土', '山下有泽，损。君子以惩忿窒欲', '平', '有孚，元吉，无咎，可贞，利有攸往。曷之用二簋，可用享。');
INSERT INTO "hexagram_64" VALUES (21, 21, '火泽睽', 3, 6, '火', '上火下泽，睽。君子以同而异', '平', '小事吉。');
INSERT INTO "hexagram_64" VALUES (22, 22, '天泽履', 1, 6, '金', '上天下泽，履。君子以辨上下，定民志', '吉', '履虎尾，不咥人，亨。');
INSERT INTO "hexagram_64" VALUES (23, 23, '风泽中孚', 5, 6, '金', '泽上有风，中孚。君子以议狱缓死', '吉', '豚鱼吉，利涉大川，利贞。');
INSERT INTO "hexagram_64" VALUES (24, 24, '风山渐', 5, 7, '土', '山上有木，渐。君子以居贤德善俗', '吉', '女归吉，利贞。');
INSERT INTO "hexagram_64" VALUES (25, 25, '震为雷', 4, 4, '木', '洊雷，震。君子以恐惧修省', '平', '亨，震来虩虩，笑言哑哑，震惊百里，不丧匕鬯。');
INSERT INTO "hexagram_64" VALUES (26, 26, '雷地豫', 4, 8, '土', '雷出地奋，豫。先王以作乐崇德', '吉', '利建侯行师。');
INSERT INTO "hexagram_64" VALUES (27, 27, '雷水解', 4, 2, '水', '雷雨作，解。君子以赦过宥罪', '吉', '利西南，无所往，其来复吉。有攸往，夙吉。');
INSERT INTO "hexagram_64" VALUES (28, 28, '雷风恒', 4, 5, '木', '雷风，恒。君子以立不易方', '吉', '亨，无咎，利贞，利有攸往。');
INSERT INTO "hexagram_64" VALUES (29, 29, '地风升', 8, 5, '木', '地中生木，升。君子以顺德，积小以高大', '吉', '元亨，用见大人，勿恤，南征吉。');
INSERT INTO "hexagram_64" VALUES (30, 30, '水风井', 2, 5, '木', '木上有水，井。君子以劳民劝相', '平', '改邑不改井，无丧无得，往来井井。');
INSERT INTO "hexagram_64" VALUES (31, 31, '泽风大过', 6, 5, '木', '泽灭木，大过。君子以独立不惧', '凶', '栋桡，利有攸往，亨。');
INSERT INTO "hexagram_64" VALUES (32, 32, '泽雷随', 6, 4, '木', '泽中有雷，随。君子以向晦入宴息', '吉', '元亨，利贞，无咎。');
INSERT INTO "hexagram_64" VALUES (33, 33, '巽为风', 5, 5, '木', '随风，巽。君子以申命行事', '平', '小亨，利有攸往，利见大人。');
INSERT INTO "hexagram_64" VALUES (34, 34, '风天小畜', 5, 1, '木', '风行天上，小畜。君子以懿文德', '平', '亨，密云不雨，自我西郊。');
INSERT INTO "hexagram_64" VALUES (35, 35, '风火家人', 5, 3, '木', '风自火出，家人。君子以言有物而行有恒', '吉', '利女贞。');
INSERT INTO "hexagram_64" VALUES (36, 36, '风雷益', 5, 4, '木', '风雷，益。君子以见善则迁，有过则改', '吉', '利有攸往，利涉大川。');
INSERT INTO "hexagram_64" VALUES (37, 37, '天雷无妄', 1, 4, '木', '天下雷行，物与无妄', '吉', '元亨，利贞。其匪正有眚，不利有攸往。');
INSERT INTO "hexagram_64" VALUES (38, 38, '火雷噬嗑', 3, 4, '木', '雷电，噬嗑。先王以明罚敕法', '平', '亨，利用狱。');
INSERT INTO "hexagram_64" VALUES (39, 39, '山雷颐', 7, 4, '木', '山下有雷，颐。君子以慎言语，节饮食', '吉', '贞吉，观颐，自求口实。');
INSERT INTO "hexagram_64" VALUES (40, 40, '山风蛊', 7, 5, '木', '山下有风，蛊。君子以振民育德', '平', '元亨，利涉大川。先甲三日，后甲三日。');
INSERT INTO "hexagram_64" VALUES (41, 41, '离为火', 3, 3, '火', '明两作，离。大人以继明照于四方', '吉', '利贞，亨。畜牝牛，吉。');
INSERT INTO "hexagram_64" VALUES (42, 42, '火山旅', 3, 7, '火', '山上有火，旅。君子以明慎用刑', '平', '小亨，旅贞吉。');
INSERT INTO "hexagram_64" VALUES (43, 43, '火风鼎', 3, 5, '火', '木上有火，鼎。君子以正位凝命', '吉', '元吉，亨。');
INSERT INTO "hexagram_64" VALUES (44, 44, '火水未济', 3, 2, '火', '火在水上，未济。君子以慎辨物居方', '平', '亨，小狐汔济，濡其尾，无攸利。');
INSERT INTO "hexagram_64" VALUES (45, 45, '山水蒙', 7, 2, '水', '山下出泉，蒙。君子以果行育德', '平', '亨。匪我求童蒙，童蒙求我。');
INSERT INTO "hexagram_64" VALUES (46, 46, '风水涣', 5, 2, '水', '风行水上，涣。先王以享于帝立庙', '平', '亨。王假有庙，利涉大川，利贞。');
INSERT INTO "hexagram_64" VALUES (47, 47, '天水讼', 1, 2, '水', '天与水违行，讼。君子以作事谋始', '凶', '有孚窒惕，中吉，终凶。利见大人，不利涉大川。');
INSERT INTO "hexagram_64" VALUES (48, 48, '天火同人', 1, 3, '火', '天与火，同人。君子以类族辨物', '吉', '同人于野，亨。利涉大川，利君子贞。');
INSERT INTO "hexagram_64" VALUES (49, 49, '坤为地', 8, 8, '土', '地势坤，君子以厚德载物', '吉', '元亨，利牝马之贞。君子有攸往，先迷后得主。');
INSERT INTO "hexagram_64" VALUES (50, 50, '地雷复', 8, 4, '土', '雷在地中，复。先王以至日闭关', '吉', '亨。出入无疾，朋来无咎。反复其道，七日来复。');
INSERT INTO "hexagram_64" VALUES (51, 51, '地泽临', 8, 6, '土', '泽上有地，临。君子以教思无穷', '吉', '元亨，利贞。至于八月有凶。');
INSERT INTO "hexagram_64" VALUES (52, 52, '地天泰', 8, 1, '土', '天地交，泰。后以财成天地之道', '吉', '小往大来，吉亨。');
INSERT INTO "hexagram_64" VALUES (53, 53, '雷天大壮', 4, 1, '金', '雷在天上，大壮。君子以非礼弗履', '吉', '利贞。');
INSERT INTO "hexagram_64" VALUES (54, 54, '泽天夬', 6, 1, '金', '泽上于天，夬。君子以施禄及下', '平', '扬于王庭，孚号有厉。');
INSERT INTO "hexagram_64" VALUES (55, 55, '水天需', 2, 1, '金', '云上于天，需。君子以饮食宴乐', '吉', '有孚，光亨，贞吉。利涉大川。');
INSERT INTO "hexagram_64" VALUES (56, 56, '水地比', 2, 8, '土', '地上有水，比。先王以建万国，亲诸侯', '吉', '吉。原筮元永贞，无咎。');
INSERT INTO "hexagram_64" VALUES (57, 57, '兑为泽', 6, 6, '金', '丽泽，兑。君子以朋友讲习', '吉', '亨，利贞。');
INSERT INTO "hexagram_64" VALUES (58, 58, '泽水困', 6, 2, '水', '泽无水，困。君子以致命遂志', '凶', '亨，贞，大人吉，无咎。有言不信。');
INSERT INTO "hexagram_64" VALUES (59, 59, '泽地萃', 6, 8, '土', '泽上于地，萃。君子以除戎器，戒不虞', '吉', '亨。王假有庙，利见大人。');
INSERT INTO "hexagram_64" VALUES (60, 60, '泽山咸', 6, 7, '土', '山上有泽，咸。君子以虚受人', '吉', '亨，利贞。取女吉。');
INSERT INTO "hexagram_64" VALUES (61, 61, '水山蹇', 2, 7, '土', '山上有水，蹇。君子以反身修德', '凶', '利西南，不利东北。利见大人，贞吉。');
INSERT INTO "hexagram_64" VALUES (62, 62, '地山谦', 8, 7, '土', '地中有山，谦。君子以裒多益寡，称物平施', '吉', '亨，君子有终。');
INSERT INTO "hexagram_64" VALUES (63, 63, '雷山小过', 4, 7, '土', '山上有雷，小过。君子以行过乎恭', '平', '亨，利贞，可小事，不可大事。');
INSERT INTO "hexagram_64" VALUES (64, 64, '雷泽归妹', 4, 6, '金', '泽上有雷，归妹。君子以永终知敝', '平', '征凶，无攸利。');
INSERT INTO "hexagram_yao_ci" VALUES (1, 1, '初九', '潜龙勿用。', '时机未到，阳气潜藏，宜潜伏等待，不可轻举妄动。', 1);
INSERT INTO "hexagram_yao_ci" VALUES (2, 1, '九二', '见龙在田，利见大人。', '龙出现在田野，阳气渐显，崭露头角，利于遇见贵人相助。', 2);
INSERT INTO "hexagram_yao_ci" VALUES (3, 1, '九三', '君子终日乾乾，夕惕若厉，无咎。', '君子终日勤奋努力，夜晚也要警惕自省，如临危险，如此则无灾。', 3);
INSERT INTO "hexagram_yao_ci" VALUES (4, 1, '九四', '或跃在渊，无咎。', '龙或腾跃上进，或退处在渊，审时度势，进退自如，无灾。', 4);
INSERT INTO "hexagram_yao_ci" VALUES (5, 1, '九五', '飞龙在天，利见大人。', '龙飞腾于天空，阳气极盛，大展宏图，利于遇见贵人。', 5);
INSERT INTO "hexagram_yao_ci" VALUES (6, 1, '上九', '亢龙有悔。', '龙飞得过高，过盛必衰，物极必反，应有悔恨。', 6);
INSERT INTO "hexagram_yao_ci" VALUES (7, 2, '初六', '系于金柅，贞吉。有攸往，见凶，羸豕孚蹢躅。', '系于金车，守正吉。有所往，见凶，瘦猪不安。', 1);
INSERT INTO "hexagram_yao_ci" VALUES (8, 2, '九二', '包有鱼，无咎，不利宾。', '包中有鱼，无灾，不利于待客。', 2);
INSERT INTO "hexagram_yao_ci" VALUES (9, 2, '九三', '臀无肤，其行次且，厉，无大咎。', '臀部无皮，行走困难，有危险，无大灾。', 3);
INSERT INTO "hexagram_yao_ci" VALUES (10, 2, '九四', '包无鱼，起凶。', '包中无鱼，起则凶。', 4);
INSERT INTO "hexagram_yao_ci" VALUES (11, 2, '九五', '以杞包瓜，含章，有陨自天。', '以杞柳包瓜，内含文采，有物自天而降。', 5);
INSERT INTO "hexagram_yao_ci" VALUES (12, 2, '上九', '姤其角，吝，无咎。', '相遇于角，有困难，无灾。', 6);
INSERT INTO "hexagram_yao_ci" VALUES (13, 3, '初六', '遁尾，厉，勿用有攸往。', '遁走在尾，有危险，不宜有所往。', 1);
INSERT INTO "hexagram_yao_ci" VALUES (14, 3, '六二', '执之用黄牛之革，莫之胜说。', '用黄牛皮革捆缚，不可解脱。', 2);
INSERT INTO "hexagram_yao_ci" VALUES (15, 3, '九三', '系遁，有疾厉，畜臣妾吉。', '被系不能遁，有疾危险，畜养臣妾吉。', 3);
INSERT INTO "hexagram_yao_ci" VALUES (16, 3, '九四', '好遁，君子吉，小人否。', '喜好退避，君子吉，小人不吉。', 4);
INSERT INTO "hexagram_yao_ci" VALUES (17, 3, '九五', '嘉遁，贞吉。', '美好的退避，守正吉。', 5);
INSERT INTO "hexagram_yao_ci" VALUES (18, 3, '上九', '肥遁，无不利。', '飘然退隐，无不利。', 6);
INSERT INTO "hexagram_yao_ci" VALUES (19, 4, '初六', '拔茅茹，以其汇，贞吉，亨。', '拔茅草，连类而及，守正吉，亨。', 1);
INSERT INTO "hexagram_yao_ci" VALUES (20, 4, '六二', '包承，小人吉，大人否，亨。', '包容承受，小人吉，大人不吉，亨。', 2);
INSERT INTO "hexagram_yao_ci" VALUES (21, 4, '六三', '包羞。', '包容羞辱。', 3);
INSERT INTO "hexagram_yao_ci" VALUES (22, 4, '九四', '有命无咎，畴离祉。', '有天命无灾，同类相聚得福。', 4);
INSERT INTO "hexagram_yao_ci" VALUES (23, 4, '九五', '休否，大人吉，其亡其亡，系于苞桑。', '休止否塞，大人吉，危而不忘危，系于苞桑。', 5);
INSERT INTO "hexagram_yao_ci" VALUES (24, 4, '上九', '倾否，先否后喜。', '倾覆否塞，先否后喜。', 6);
INSERT INTO "hexagram_yao_ci" VALUES (25, 5, '初六', '童观，小人无咎，君子吝。', '幼稚的观察，小人无灾，君子有困难。', 1);
INSERT INTO "hexagram_yao_ci" VALUES (26, 5, '六二', '窥观，利女贞。', '从门缝窥观，利于女子守正。', 2);
INSERT INTO "hexagram_yao_ci" VALUES (27, 5, '六三', '观我生，进退。', '观察自己的生活，决定进退。', 3);
INSERT INTO "hexagram_yao_ci" VALUES (28, 5, '六四', '观国之光，利用宾于王。', '观察国家的光辉，利于作君王的宾客。', 4);
INSERT INTO "hexagram_yao_ci" VALUES (29, 5, '九五', '观我生，君子无咎。', '观察自己的生活，君子无灾。', 5);
INSERT INTO "hexagram_yao_ci" VALUES (30, 5, '上九', '观其生，君子无咎。', '观察他人的生活，君子无灾。', 6);
INSERT INTO "hexagram_yao_ci" VALUES (31, 6, '初六', '剥床以足，蔑贞凶。', '剥落床脚，轻视守正凶。', 1);
INSERT INTO "hexagram_yao_ci" VALUES (32, 6, '六二', '剥床以辨，蔑贞凶。', '剥落床沿，轻视守正凶。', 2);
INSERT INTO "hexagram_yao_ci" VALUES (33, 6, '六三', '剥之，无咎。', '剥落它，无灾。', 3);
INSERT INTO "hexagram_yao_ci" VALUES (34, 6, '六四', '剥床以肤，凶。', '剥落床面，凶。', 4);
INSERT INTO "hexagram_yao_ci" VALUES (35, 6, '六五', '贯鱼以宫人宠，无不利。', '如贯鱼般依次得到宫人宠爱，无不利。', 5);
INSERT INTO "hexagram_yao_ci" VALUES (36, 6, '上九', '硕果不食，君子得舆，小人剥庐。', '大果实不食，君子得车，小人剥落房舍。', 6);
INSERT INTO "hexagram_yao_ci" VALUES (37, 7, '初六', '晋如，摧如，贞吉。罔孚，裕无咎。', '晋升受阻，守正吉。无人信任，宽裕无灾。', 1);
INSERT INTO "hexagram_yao_ci" VALUES (38, 7, '六二', '晋如，愁如，贞吉。受兹介福，于其王母。', '晋升忧愁，守正吉。得到大福，来自祖母。', 2);
INSERT INTO "hexagram_yao_ci" VALUES (39, 7, '六三', '众允，悔亡。', '众人信任，悔恨消除。', 3);
INSERT INTO "hexagram_yao_ci" VALUES (40, 7, '九四', '晋如鼫鼠，贞厉。', '晋升如鼫鼠，守正有危险。', 4);
INSERT INTO "hexagram_yao_ci" VALUES (41, 7, '六五', '悔亡，失得勿恤，往吉，无不利。', '悔恨消除，得失不必忧虑，前往吉，无不利。', 5);
INSERT INTO "hexagram_yao_ci" VALUES (42, 7, '上九', '晋其角，维用伐邑，厉吉，无咎，贞吝。', '晋升到角，用于征伐邑国，危险而吉，无灾，守正有困难。', 6);
INSERT INTO "hexagram_yao_ci" VALUES (43, 8, '初九', '无交害，匪咎，艰则无咎。', '没有交相侵害，非灾，艰难则无灾。', 1);
INSERT INTO "hexagram_yao_ci" VALUES (44, 8, '九二', '大车以载，有攸往，无咎。', '大车装载，有所往，无灾。', 2);
INSERT INTO "hexagram_yao_ci" VALUES (45, 8, '九三', '公用亨于天子，小人弗克。', '公侯向天子朝贡，小人不能胜任。', 3);
INSERT INTO "hexagram_yao_ci" VALUES (46, 8, '九四', '匪其彭，无咎。', '不自大，无灾。', 4);
INSERT INTO "hexagram_yao_ci" VALUES (47, 8, '六五', '厥孚交如，威如，吉。', '诚信相交，有威严，吉。', 5);
INSERT INTO "hexagram_yao_ci" VALUES (48, 8, '上九', '自天佑之，吉无不利。', '自天保佑，吉无不利。', 6);
INSERT INTO "hexagram_yao_ci" VALUES (49, 1, '初九', '潜龙勿用。', '时机未到，阳气潜藏，宜潜伏等待，不可轻举妄动。', 1);
INSERT INTO "hexagram_yao_ci" VALUES (50, 1, '九二', '见龙在田，利见大人。', '龙出现在田野，阳气渐显，崭露头角，利于遇见贵人相助。', 2);
INSERT INTO "hexagram_yao_ci" VALUES (51, 1, '九三', '君子终日乾乾，夕惕若厉，无咎。', '君子终日勤奋努力，夜晚也要警惕自省，如临危险，如此则无灾。', 3);
INSERT INTO "hexagram_yao_ci" VALUES (52, 1, '九四', '或跃在渊，无咎。', '龙或腾跃上进，或退处在渊，审时度势，进退自如，无灾。', 4);
INSERT INTO "hexagram_yao_ci" VALUES (53, 1, '九五', '飞龙在天，利见大人。', '龙飞腾于天空，阳气极盛，大展宏图，利于遇见贵人。', 5);
INSERT INTO "hexagram_yao_ci" VALUES (54, 1, '上九', '亢龙有悔。', '龙飞得过高，过盛必衰，物极必反，应有悔恨。', 6);
INSERT INTO "hexagram_yao_ci" VALUES (55, 2, '初六', '系于金柅，贞吉。有攸往，见凶，羸豕孚蹢躅。', '系于金车，守正吉。有所往，见凶，瘦猪不安。', 1);
INSERT INTO "hexagram_yao_ci" VALUES (56, 2, '九二', '包有鱼，无咎，不利宾。', '包中有鱼，无灾，不利于待客。', 2);
INSERT INTO "hexagram_yao_ci" VALUES (57, 2, '九三', '臀无肤，其行次且，厉，无大咎。', '臀部无皮，行走困难，有危险，无大灾。', 3);
INSERT INTO "hexagram_yao_ci" VALUES (58, 2, '九四', '包无鱼，起凶。', '包中无鱼，起则凶。', 4);
INSERT INTO "hexagram_yao_ci" VALUES (59, 2, '九五', '以杞包瓜，含章，有陨自天。', '以杞柳包瓜，内含文采，有物自天而降。', 5);
INSERT INTO "hexagram_yao_ci" VALUES (60, 2, '上九', '姤其角，吝，无咎。', '相遇于角，有困难，无灾。', 6);
INSERT INTO "hexagram_yao_ci" VALUES (61, 3, '初六', '遁尾，厉，勿用有攸往。', '遁走在尾，有危险，不宜有所往。', 1);
INSERT INTO "hexagram_yao_ci" VALUES (62, 3, '六二', '执之用黄牛之革，莫之胜说。', '用黄牛皮革捆缚，不可解脱。', 2);
INSERT INTO "hexagram_yao_ci" VALUES (63, 3, '九三', '系遁，有疾厉，畜臣妾吉。', '被系不能遁，有疾危险，畜养臣妾吉。', 3);
INSERT INTO "hexagram_yao_ci" VALUES (64, 3, '九四', '好遁，君子吉，小人否。', '喜好退避，君子吉，小人不吉。', 4);
INSERT INTO "hexagram_yao_ci" VALUES (65, 3, '九五', '嘉遁，贞吉。', '美好的退避，守正吉。', 5);
INSERT INTO "hexagram_yao_ci" VALUES (66, 3, '上九', '肥遁，无不利。', '飘然退隐，无不利。', 6);
INSERT INTO "hexagram_yao_ci" VALUES (67, 4, '初六', '拔茅茹，以其汇，贞吉，亨。', '拔茅草，连类而及，守正吉，亨。', 1);
INSERT INTO "hexagram_yao_ci" VALUES (68, 4, '六二', '包承，小人吉，大人否，亨。', '包容承受，小人吉，大人不吉，亨。', 2);
INSERT INTO "hexagram_yao_ci" VALUES (69, 4, '六三', '包羞。', '包容羞辱。', 3);
INSERT INTO "hexagram_yao_ci" VALUES (70, 4, '九四', '有命无咎，畴离祉。', '有天命无灾，同类相聚得福。', 4);
INSERT INTO "hexagram_yao_ci" VALUES (71, 4, '九五', '休否，大人吉，其亡其亡，系于苞桑。', '休止否塞，大人吉，危而不忘危，系于苞桑。', 5);
INSERT INTO "hexagram_yao_ci" VALUES (72, 4, '上九', '倾否，先否后喜。', '倾覆否塞，先否后喜。', 6);
INSERT INTO "hexagram_yao_ci" VALUES (73, 5, '初六', '童观，小人无咎，君子吝。', '幼稚的观察，小人无灾，君子有困难。', 1);
INSERT INTO "hexagram_yao_ci" VALUES (74, 5, '六二', '窥观，利女贞。', '从门缝窥观，利于女子守正。', 2);
INSERT INTO "hexagram_yao_ci" VALUES (75, 5, '六三', '观我生，进退。', '观察自己的生活，决定进退。', 3);
INSERT INTO "hexagram_yao_ci" VALUES (76, 5, '六四', '观国之光，利用宾于王。', '观察国家的光辉，利于作君王的宾客。', 4);
INSERT INTO "hexagram_yao_ci" VALUES (77, 5, '九五', '观我生，君子无咎。', '观察自己的生活，君子无灾。', 5);
INSERT INTO "hexagram_yao_ci" VALUES (78, 5, '上九', '观其生，君子无咎。', '观察他人的生活，君子无灾。', 6);
INSERT INTO "hexagram_yao_ci" VALUES (79, 6, '初六', '剥床以足，蔑贞凶。', '剥落床脚，轻视守正凶。', 1);
INSERT INTO "hexagram_yao_ci" VALUES (80, 6, '六二', '剥床以辨，蔑贞凶。', '剥落床沿，轻视守正凶。', 2);
INSERT INTO "hexagram_yao_ci" VALUES (81, 6, '六三', '剥之，无咎。', '剥落它，无灾。', 3);
INSERT INTO "hexagram_yao_ci" VALUES (82, 6, '六四', '剥床以肤，凶。', '剥落床面，凶。', 4);
INSERT INTO "hexagram_yao_ci" VALUES (83, 6, '六五', '贯鱼以宫人宠，无不利。', '如贯鱼般依次得到宫人宠爱，无不利。', 5);
INSERT INTO "hexagram_yao_ci" VALUES (84, 6, '上九', '硕果不食，君子得舆，小人剥庐。', '大果实不食，君子得车，小人剥落房舍。', 6);
INSERT INTO "hexagram_yao_ci" VALUES (85, 7, '初六', '晋如，摧如，贞吉。罔孚，裕无咎。', '晋升受阻，守正吉。无人信任，宽裕无灾。', 1);
INSERT INTO "hexagram_yao_ci" VALUES (86, 7, '六二', '晋如，愁如，贞吉。受兹介福，于其王母。', '晋升忧愁，守正吉。得到大福，来自祖母。', 2);
INSERT INTO "hexagram_yao_ci" VALUES (87, 7, '六三', '众允，悔亡。', '众人信任，悔恨消除。', 3);
INSERT INTO "hexagram_yao_ci" VALUES (88, 7, '九四', '晋如鼫鼠，贞厉。', '晋升如鼫鼠，守正有危险。', 4);
INSERT INTO "hexagram_yao_ci" VALUES (89, 7, '六五', '悔亡，失得勿恤，往吉，无不利。', '悔恨消除，得失不必忧虑，前往吉，无不利。', 5);
INSERT INTO "hexagram_yao_ci" VALUES (90, 7, '上九', '晋其角，维用伐邑，厉吉，无咎，贞吝。', '晋升到角，用于征伐邑国，危险而吉，无灾，守正有困难。', 6);
INSERT INTO "hexagram_yao_ci" VALUES (91, 8, '初九', '无交害，匪咎，艰则无咎。', '没有交相侵害，非灾，艰难则无灾。', 1);
INSERT INTO "hexagram_yao_ci" VALUES (92, 8, '九二', '大车以载，有攸往，无咎。', '大车装载，有所往，无灾。', 2);
INSERT INTO "hexagram_yao_ci" VALUES (93, 8, '九三', '公用亨于天子，小人弗克。', '公侯向天子朝贡，小人不能胜任。', 3);
INSERT INTO "hexagram_yao_ci" VALUES (94, 8, '九四', '匪其彭，无咎。', '不自大，无灾。', 4);
INSERT INTO "hexagram_yao_ci" VALUES (95, 8, '六五', '厥孚交如，威如，吉。', '诚信相交，有威严，吉。', 5);
INSERT INTO "hexagram_yao_ci" VALUES (96, 8, '上九', '自天佑之，吉无不利。', '自天保佑，吉无不利。', 6);
INSERT INTO "jie_qi" VALUES (1, 0, '立春', 315, 1, 3.72);
INSERT INTO "jie_qi" VALUES (2, 1, '雨水', 330, 0, 18.63);
INSERT INTO "jie_qi" VALUES (3, 2, '惊蛰', 345, 1, 43.55);
INSERT INTO "jie_qi" VALUES (4, 3, '春分', 0, 0, 58.47);
INSERT INTO "jie_qi" VALUES (5, 4, '清明', 15, 1, 73.4);
INSERT INTO "jie_qi" VALUES (6, 5, '谷雨', 30, 0, 88.28);
INSERT INTO "jie_qi" VALUES (7, 6, '立夏', 45, 1, 103.38);
INSERT INTO "jie_qi" VALUES (8, 7, '小满', 60, 0, 118.63);
INSERT INTO "jie_qi" VALUES (9, 8, '芒种', 75, 1, 134.1);
INSERT INTO "jie_qi" VALUES (10, 9, '夏至', 90, 0, 149.75);
INSERT INTO "jie_qi" VALUES (11, 10, '小暑', 105, 1, 165.43);
INSERT INTO "jie_qi" VALUES (12, 11, '大暑', 120, 0, 181.35);
INSERT INTO "jie_qi" VALUES (13, 12, '立秋', 135, 1, 197.44);
INSERT INTO "jie_qi" VALUES (14, 13, '处暑', 150, 0, 213.62);
INSERT INTO "jie_qi" VALUES (15, 14, '白露', 165, 1, 229.89);
INSERT INTO "jie_qi" VALUES (16, 15, '秋分', 180, 0, 246.26);
INSERT INTO "jie_qi" VALUES (17, 16, '寒露', 195, 1, 262.7);
INSERT INTO "jie_qi" VALUES (18, 17, '霜降', 210, 0, 279.23);
INSERT INTO "jie_qi" VALUES (19, 18, '立冬', 225, 1, 295.83);
INSERT INTO "jie_qi" VALUES (20, 19, '小雪', 240, 0, 312.51);
INSERT INTO "jie_qi" VALUES (21, 20, '大雪', 255, 1, 329.26);
INSERT INTO "jie_qi" VALUES (22, 21, '冬至', 270, 0, 346.1);
INSERT INTO "jie_qi" VALUES (23, 22, '小寒', 285, 1, 363.01);
INSERT INTO "jie_qi" VALUES (24, 23, '大寒', 300, 0, 380.0);
INSERT INTO "jie_qi_month_map" VALUES (1, 0, '寅');
INSERT INTO "jie_qi_month_map" VALUES (2, 1, '寅');
INSERT INTO "jie_qi_month_map" VALUES (3, 2, '卯');
INSERT INTO "jie_qi_month_map" VALUES (4, 3, '卯');
INSERT INTO "jie_qi_month_map" VALUES (5, 4, '辰');
INSERT INTO "jie_qi_month_map" VALUES (6, 5, '辰');
INSERT INTO "jie_qi_month_map" VALUES (7, 6, '巳');
INSERT INTO "jie_qi_month_map" VALUES (8, 7, '巳');
INSERT INTO "jie_qi_month_map" VALUES (9, 8, '午');
INSERT INTO "jie_qi_month_map" VALUES (10, 9, '午');
INSERT INTO "jie_qi_month_map" VALUES (11, 10, '未');
INSERT INTO "jie_qi_month_map" VALUES (12, 11, '未');
INSERT INTO "jie_qi_month_map" VALUES (13, 12, '申');
INSERT INTO "jie_qi_month_map" VALUES (14, 13, '申');
INSERT INTO "jie_qi_month_map" VALUES (15, 14, '酉');
INSERT INTO "jie_qi_month_map" VALUES (16, 15, '酉');
INSERT INTO "jie_qi_month_map" VALUES (17, 16, '戌');
INSERT INTO "jie_qi_month_map" VALUES (18, 17, '戌');
INSERT INTO "jie_qi_month_map" VALUES (19, 18, '亥');
INSERT INTO "jie_qi_month_map" VALUES (20, 19, '亥');
INSERT INTO "jie_qi_month_map" VALUES (21, 20, '子');
INSERT INTO "jie_qi_month_map" VALUES (22, 21, '子');
INSERT INTO "jie_qi_month_map" VALUES (23, 22, '丑');
INSERT INTO "jie_qi_month_map" VALUES (24, 23, '丑');
INSERT INTO "jie_qi_month_map" VALUES (25, 0, '寅');
INSERT INTO "jie_qi_month_map" VALUES (26, 1, '寅');
INSERT INTO "jie_qi_month_map" VALUES (27, 2, '卯');
INSERT INTO "jie_qi_month_map" VALUES (28, 3, '卯');
INSERT INTO "jie_qi_month_map" VALUES (29, 4, '辰');
INSERT INTO "jie_qi_month_map" VALUES (30, 5, '辰');
INSERT INTO "jie_qi_month_map" VALUES (31, 6, '巳');
INSERT INTO "jie_qi_month_map" VALUES (32, 7, '巳');
INSERT INTO "jie_qi_month_map" VALUES (33, 8, '午');
INSERT INTO "jie_qi_month_map" VALUES (34, 9, '午');
INSERT INTO "jie_qi_month_map" VALUES (35, 10, '未');
INSERT INTO "jie_qi_month_map" VALUES (36, 11, '未');
INSERT INTO "jie_qi_month_map" VALUES (37, 12, '申');
INSERT INTO "jie_qi_month_map" VALUES (38, 13, '申');
INSERT INTO "jie_qi_month_map" VALUES (39, 14, '酉');
INSERT INTO "jie_qi_month_map" VALUES (40, 15, '酉');
INSERT INTO "jie_qi_month_map" VALUES (41, 16, '戌');
INSERT INTO "jie_qi_month_map" VALUES (42, 17, '戌');
INSERT INTO "jie_qi_month_map" VALUES (43, 18, '亥');
INSERT INTO "jie_qi_month_map" VALUES (44, 19, '亥');
INSERT INTO "jie_qi_month_map" VALUES (45, 20, '子');
INSERT INTO "jie_qi_month_map" VALUES (46, 21, '子');
INSERT INTO "jie_qi_month_map" VALUES (47, 22, '丑');
INSERT INTO "jie_qi_month_map" VALUES (48, 23, '丑');
INSERT INTO "month_gan_rules" VALUES (1, '甲己', 0, '丙');
INSERT INTO "month_gan_rules" VALUES (2, '甲己', 1, '丁');
INSERT INTO "month_gan_rules" VALUES (3, '甲己', 2, '戊');
INSERT INTO "month_gan_rules" VALUES (4, '甲己', 3, '己');
INSERT INTO "month_gan_rules" VALUES (5, '甲己', 4, '庚');
INSERT INTO "month_gan_rules" VALUES (6, '甲己', 5, '辛');
INSERT INTO "month_gan_rules" VALUES (7, '甲己', 6, '壬');
INSERT INTO "month_gan_rules" VALUES (8, '甲己', 7, '癸');
INSERT INTO "month_gan_rules" VALUES (9, '甲己', 8, '甲');
INSERT INTO "month_gan_rules" VALUES (10, '甲己', 9, '乙');
INSERT INTO "month_gan_rules" VALUES (11, '甲己', 10, '丙');
INSERT INTO "month_gan_rules" VALUES (12, '甲己', 11, '丁');
INSERT INTO "month_gan_rules" VALUES (13, '乙庚', 0, '戊');
INSERT INTO "month_gan_rules" VALUES (14, '乙庚', 1, '己');
INSERT INTO "month_gan_rules" VALUES (15, '乙庚', 2, '庚');
INSERT INTO "month_gan_rules" VALUES (16, '乙庚', 3, '辛');
INSERT INTO "month_gan_rules" VALUES (17, '乙庚', 4, '壬');
INSERT INTO "month_gan_rules" VALUES (18, '乙庚', 5, '癸');
INSERT INTO "month_gan_rules" VALUES (19, '乙庚', 6, '甲');
INSERT INTO "month_gan_rules" VALUES (20, '乙庚', 7, '乙');
INSERT INTO "month_gan_rules" VALUES (21, '乙庚', 8, '丙');
INSERT INTO "month_gan_rules" VALUES (22, '乙庚', 9, '丁');
INSERT INTO "month_gan_rules" VALUES (23, '乙庚', 10, '戊');
INSERT INTO "month_gan_rules" VALUES (24, '乙庚', 11, '己');
INSERT INTO "month_gan_rules" VALUES (25, '丙辛', 0, '庚');
INSERT INTO "month_gan_rules" VALUES (26, '丙辛', 1, '辛');
INSERT INTO "month_gan_rules" VALUES (27, '丙辛', 2, '壬');
INSERT INTO "month_gan_rules" VALUES (28, '丙辛', 3, '癸');
INSERT INTO "month_gan_rules" VALUES (29, '丙辛', 4, '甲');
INSERT INTO "month_gan_rules" VALUES (30, '丙辛', 5, '乙');
INSERT INTO "month_gan_rules" VALUES (31, '丙辛', 6, '丙');
INSERT INTO "month_gan_rules" VALUES (32, '丙辛', 7, '丁');
INSERT INTO "month_gan_rules" VALUES (33, '丙辛', 8, '戊');
INSERT INTO "month_gan_rules" VALUES (34, '丙辛', 9, '己');
INSERT INTO "month_gan_rules" VALUES (35, '丙辛', 10, '庚');
INSERT INTO "month_gan_rules" VALUES (36, '丙辛', 11, '辛');
INSERT INTO "month_gan_rules" VALUES (37, '丁壬', 0, '壬');
INSERT INTO "month_gan_rules" VALUES (38, '丁壬', 1, '癸');
INSERT INTO "month_gan_rules" VALUES (39, '丁壬', 2, '甲');
INSERT INTO "month_gan_rules" VALUES (40, '丁壬', 3, '乙');
INSERT INTO "month_gan_rules" VALUES (41, '丁壬', 4, '丙');
INSERT INTO "month_gan_rules" VALUES (42, '丁壬', 5, '丁');
INSERT INTO "month_gan_rules" VALUES (43, '丁壬', 6, '戊');
INSERT INTO "month_gan_rules" VALUES (44, '丁壬', 7, '己');
INSERT INTO "month_gan_rules" VALUES (45, '丁壬', 8, '庚');
INSERT INTO "month_gan_rules" VALUES (46, '丁壬', 9, '辛');
INSERT INTO "month_gan_rules" VALUES (47, '丁壬', 10, '壬');
INSERT INTO "month_gan_rules" VALUES (48, '丁壬', 11, '癸');
INSERT INTO "month_gan_rules" VALUES (49, '戊癸', 0, '甲');
INSERT INTO "month_gan_rules" VALUES (50, '戊癸', 1, '乙');
INSERT INTO "month_gan_rules" VALUES (51, '戊癸', 2, '丙');
INSERT INTO "month_gan_rules" VALUES (52, '戊癸', 3, '丁');
INSERT INTO "month_gan_rules" VALUES (53, '戊癸', 4, '戊');
INSERT INTO "month_gan_rules" VALUES (54, '戊癸', 5, '己');
INSERT INTO "month_gan_rules" VALUES (55, '戊癸', 6, '庚');
INSERT INTO "month_gan_rules" VALUES (56, '戊癸', 7, '辛');
INSERT INTO "month_gan_rules" VALUES (57, '戊癸', 8, '壬');
INSERT INTO "month_gan_rules" VALUES (58, '戊癸', 9, '癸');
INSERT INTO "month_gan_rules" VALUES (59, '戊癸', 10, '甲');
INSERT INTO "month_gan_rules" VALUES (60, '戊癸', 11, '乙');
INSERT INTO "nayin_wuxing" VALUES (1, '甲子', '海中金', '金', NULL);
INSERT INTO "nayin_wuxing" VALUES (2, '乙丑', '海中金', '金', NULL);
INSERT INTO "nayin_wuxing" VALUES (3, '丙寅', '炉中火', '火', NULL);
INSERT INTO "nayin_wuxing" VALUES (4, '丁卯', '炉中火', '火', NULL);
INSERT INTO "nayin_wuxing" VALUES (5, '戊辰', '大林木', '木', NULL);
INSERT INTO "nayin_wuxing" VALUES (6, '己巳', '大林木', '木', NULL);
INSERT INTO "nayin_wuxing" VALUES (7, '庚午', '路旁土', '土', NULL);
INSERT INTO "nayin_wuxing" VALUES (8, '辛未', '路旁土', '土', NULL);
INSERT INTO "nayin_wuxing" VALUES (9, '壬申', '剑锋金', '金', NULL);
INSERT INTO "nayin_wuxing" VALUES (10, '癸酉', '剑锋金', '金', NULL);
INSERT INTO "nayin_wuxing" VALUES (11, '甲戌', '山头火', '火', NULL);
INSERT INTO "nayin_wuxing" VALUES (12, '乙亥', '山头火', '火', NULL);
INSERT INTO "nayin_wuxing" VALUES (13, '丙子', '涧下水', '水', NULL);
INSERT INTO "nayin_wuxing" VALUES (14, '丁丑', '涧下水', '水', NULL);
INSERT INTO "nayin_wuxing" VALUES (15, '戊寅', '城头土', '土', NULL);
INSERT INTO "nayin_wuxing" VALUES (16, '己卯', '城头土', '土', NULL);
INSERT INTO "nayin_wuxing" VALUES (17, '庚辰', '白蜡金', '金', NULL);
INSERT INTO "nayin_wuxing" VALUES (18, '辛巳', '白蜡金', '金', NULL);
INSERT INTO "nayin_wuxing" VALUES (19, '壬午', '杨柳木', '木', NULL);
INSERT INTO "nayin_wuxing" VALUES (20, '癸未', '杨柳木', '木', NULL);
INSERT INTO "nayin_wuxing" VALUES (21, '甲申', '泉中水', '水', NULL);
INSERT INTO "nayin_wuxing" VALUES (22, '乙酉', '泉中水', '水', NULL);
INSERT INTO "nayin_wuxing" VALUES (23, '丙戌', '屋上土', '土', NULL);
INSERT INTO "nayin_wuxing" VALUES (24, '丁亥', '屋上土', '土', NULL);
INSERT INTO "nayin_wuxing" VALUES (25, '戊子', '霹雳火', '火', NULL);
INSERT INTO "nayin_wuxing" VALUES (26, '己丑', '霹雳火', '火', NULL);
INSERT INTO "nayin_wuxing" VALUES (27, '庚寅', '松柏木', '木', NULL);
INSERT INTO "nayin_wuxing" VALUES (28, '辛卯', '松柏木', '木', NULL);
INSERT INTO "nayin_wuxing" VALUES (29, '壬辰', '长流水', '水', NULL);
INSERT INTO "nayin_wuxing" VALUES (30, '癸巳', '长流水', '水', NULL);
INSERT INTO "nayin_wuxing" VALUES (31, '甲午', '沙中金', '金', NULL);
INSERT INTO "nayin_wuxing" VALUES (32, '乙未', '沙中金', '金', NULL);
INSERT INTO "nayin_wuxing" VALUES (33, '丙申', '山下火', '火', NULL);
INSERT INTO "nayin_wuxing" VALUES (34, '丁酉', '山下火', '火', NULL);
INSERT INTO "nayin_wuxing" VALUES (35, '戊戌', '平地木', '木', NULL);
INSERT INTO "nayin_wuxing" VALUES (36, '己亥', '平地木', '木', NULL);
INSERT INTO "nayin_wuxing" VALUES (37, '庚子', '壁上土', '土', NULL);
INSERT INTO "nayin_wuxing" VALUES (38, '辛丑', '壁上土', '土', NULL);
INSERT INTO "nayin_wuxing" VALUES (39, '壬寅', '金箔金', '金', NULL);
INSERT INTO "nayin_wuxing" VALUES (40, '癸卯', '金箔金', '金', NULL);
INSERT INTO "nayin_wuxing" VALUES (41, '甲辰', '覆灯火', '火', NULL);
INSERT INTO "nayin_wuxing" VALUES (42, '乙巳', '覆灯火', '火', NULL);
INSERT INTO "nayin_wuxing" VALUES (43, '丙午', '天河水', '水', NULL);
INSERT INTO "nayin_wuxing" VALUES (44, '丁未', '天河水', '水', NULL);
INSERT INTO "nayin_wuxing" VALUES (45, '戊申', '大驿土', '土', NULL);
INSERT INTO "nayin_wuxing" VALUES (46, '己酉', '大驿土', '土', NULL);
INSERT INTO "nayin_wuxing" VALUES (47, '庚戌', '钗钏金', '金', NULL);
INSERT INTO "nayin_wuxing" VALUES (48, '辛亥', '钗钏金', '金', NULL);
INSERT INTO "nayin_wuxing" VALUES (49, '壬子', '桑柘木', '木', NULL);
INSERT INTO "nayin_wuxing" VALUES (50, '癸丑', '桑柘木', '木', NULL);
INSERT INTO "nayin_wuxing" VALUES (51, '甲寅', '大溪水', '水', NULL);
INSERT INTO "nayin_wuxing" VALUES (52, '乙卯', '大溪水', '水', NULL);
INSERT INTO "nayin_wuxing" VALUES (53, '丙辰', '沙中土', '土', NULL);
INSERT INTO "nayin_wuxing" VALUES (54, '丁巳', '沙中土', '土', NULL);
INSERT INTO "nayin_wuxing" VALUES (55, '戊午', '天上火', '火', NULL);
INSERT INTO "nayin_wuxing" VALUES (56, '己未', '天上火', '火', NULL);
INSERT INTO "nayin_wuxing" VALUES (57, '庚申', '石榴木', '木', NULL);
INSERT INTO "nayin_wuxing" VALUES (58, '辛酉', '石榴木', '木', NULL);
INSERT INTO "nayin_wuxing" VALUES (59, '壬戌', '大海水', '水', NULL);
INSERT INTO "nayin_wuxing" VALUES (60, '癸亥', '大海水', '水', NULL);
INSERT INTO "shensha_terms" VALUES (1, '天德', '神煞', 'positive', '天德贵人，主吉祥、逢凶化吉', '天德贵人是四柱神煞中最吉祥的神煞之一。天德者，谓合天德之正气，主人慈祥和蔼，聪明正直，一生少病灾，遇难呈祥，逢凶化吉。命中有天德贵人者，多为善良之人，容易得到他人帮助，一生平安顺遂。', '{"type": "gan", "conditions": {"丙": ["寅"], "丁": ["亥"], "戊": ["寅"], "己": ["申"], "庚": ["亥"], "辛": ["巳"], "壬": ["寅"], "癸": ["申"]}, "locations": ["月柱"]}', '[
    "健康",
    "贵人运",
    "平安"
]', '[
    "月德",
    "天乙贵人"
]');
INSERT INTO "shensha_terms" VALUES (2, '月德', '神煞', 'positive', '月德贵人，主仁慈、聪明、福寿', '月德贵人与天德贵人并称"二德"，同为吉祥神煞。月德者，谓合月德之正气，主人仁慈敦厚，聪明好学，福寿双全，一生平安。命中有月德贵人者，性情温和，乐于助人，容易得到长辈和上级的提携。', '{"type": "gan", "conditions": {"丙": ["甲"], "丁": ["壬"], "戊": ["丙"], "己": ["甲"], "庚": ["戊"], "辛": ["丙"], "壬": ["庚"], "癸": ["戊"]}, "locations": ["月柱"]}', '[
    "贵人运",
    "健康",
    "福寿"
]', '[
    "天德"
]');
INSERT INTO "shensha_terms" VALUES (3, '文昌', '神煞', 'positive', '文昌星，主学业、才华、聪明过人', '文昌星主学业、文章、才华。命中有文昌星者，聪明伶俐，记忆力强，学习能力出众，容易在学业上取得优异成绩，适合从事学术研究、教育、文化艺术等工作。文昌星入命，主其人多才多艺，富有创造力。', '{"type": "gan", "conditions": {"甲": ["巳"], "乙": ["午"], "丙": ["申"], "丁": ["酉"], "戊": ["申"], "己": ["酉"], "庚": ["亥"], "辛": ["子"], "壬": ["寅"], "癸": ["卯"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}', '[
    "学业",
    "才华",
    "聪明"
]', '[
    "学堂",
    "词馆"
]');
INSERT INTO "shensha_terms" VALUES (4, '桃花', '神煞', 'neutral', '桃花星，主人缘、异性缘、社交能力强', '桃花星主异性缘、人际关系、社交能力。命中有桃花星者，相貌俊秀，气质高雅，善于交际，异性缘旺盛。桃花星也主艺术才华，适合从事演艺、娱乐、公关等行业。但桃花过旺也可能带来感情困扰，需注意把握分寸。', '{"type": "zhi", "conditions": {"子": ["卯"], "午": ["酉"], "卯": ["子"], "酉": ["午"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}', '[
    "桃花",
    "人缘",
    "社交"
]', '[
    "红艳"
]');
INSERT INTO "shensha_terms" VALUES (5, '驿马', '神煞', 'neutral', '驿马星，主变动、旅行、迁移', '驿马星主变动、旅行、迁移、外出。命中有驿马星者，一生多动少静，喜欢旅行和探索，适合从事需要经常出差或外出的工作，如销售、物流、旅游等行业。驿马星也主机遇，往往在变动中获得发展机会。', '{"type": "zhi", "conditions": {"申": ["寅"], "寅": ["申"], "巳": ["亥"], "亥": ["巳"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}', '[
    "变动",
    "旅行",
    "迁移"
]', '[
    "华盖"
]');
INSERT INTO "shensha_terms" VALUES (6, '华盖', '神煞', 'neutral', '华盖星，主艺术、才华、孤独', '华盖星主艺术、才华、宗教、哲学。命中有华盖星者，富有艺术天赋，对传统文化、宗教哲学有浓厚兴趣，容易在这些领域取得成就。但华盖星也主孤独，其人往往性格内向，喜欢独处，有时会显得孤僻不合群。', '{"type": "zhi", "conditions": {"寅": ["戌"], "戌": ["寅"], "辰": ["丑"], "丑": ["辰"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}', '[
    "艺术",
    "才华",
    "孤独"
]', '[
    "驿马"
]');
INSERT INTO "shensha_terms" VALUES (7, '将星', '神煞', 'positive', '将星，主权威、领导力、事业有成', '将星主权威、领导力、组织能力。命中有将星者，具有领导才能，善于组织和指挥他人，容易成为团队中的核心人物或领导者。将星入命，主其人在事业上容易取得成就，适合从事管理、军事、政治等工作。', '{"type": "zhi", "conditions": {"子": ["午"], "午": ["子"], "卯": ["酉"], "酉": ["卯"]}, "locations": ["月柱", "时柱"]}', '[
    "权威",
    "领导力",
    "事业"
]', '[
    "紫微"
]');
INSERT INTO "shensha_terms" VALUES (8, '天乙', '神煞', 'positive', '天乙贵人，主贵人相助、逢凶化吉', '天乙贵人是四柱神煞中最重要的贵人星。天乙者，乃天上之神，在紫微垣、阊阖门外，与太乙并列，事天皇大帝，下游三辰，家在己丑斗牛之次，出乎己未井鬼之舍，执玉衡较量天人之事，名曰天乙也。命中有天乙贵人者，一生多得贵人相助，逢凶化吉，遇难呈祥。', '{"type": "gan", "conditions": {"甲": ["丑", "未"], "乙": ["子", "申"], "丙": ["亥", "酉"], "丁": ["亥", "酉"], "戊": ["丑", "未"], "己": ["子", "申"], "庚": ["寅", "午"], "辛": ["寅", "午"], "壬": ["巳", "卯"], "癸": ["巳", "卯"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}', '[
    "贵人运",
    "吉祥",
    "帮助"
]', '[
    "天德",
    "月德"
]');
INSERT INTO "shensha_terms" VALUES (9, '劫煞', '神煞', 'negative', '劫煞，主是非、争斗、意外之灾', '劫煞主是非、争斗、抢劫、意外之灾。命中有劫煞者，性格刚烈，容易冲动，好勇斗狠，容易与人发生争执和冲突。劫煞也主财物损失，需注意防范盗窃、抢劫等意外事件。但劫煞也主勇敢果断，若能善用其力，也可在竞争中取得优势。', '{"type": "zhi", "conditions": {"申": ["巳"], "巳": ["申"], "寅": ["亥"], "亥": ["寅"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}', '[
    "是非",
    "争斗",
    "意外"
]', '[
    "亡神"
]');
INSERT INTO "shensha_terms" VALUES (10, '亡神', '神煞', 'negative', '亡神，主官非、病灾、精神困扰', '亡神主官非、病灾、精神困扰。命中有亡神者，容易遇到官司诉讼，身体方面容易有慢性疾病，精神上容易焦虑不安。亡神也主阴谋、暗害，需注意防范小人陷害。但亡神也主聪明才智，若能修身养性，也可将其转化为智慧之力。', '{"type": "zhi", "conditions": {"寅": ["巳"], "巳": ["申"], "申": ["亥"], "亥": ["寅"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}', '[
    "官非",
    "病灾",
    "精神困扰"
]', '[
    "劫煞"
]');
INSERT INTO "shensha_terms" VALUES (11, '孤辰', '神煞', 'negative', '孤辰，主孤独、寡合、婚姻不顺', '孤辰主孤独、寡合、婚姻不顺。命中有孤辰者，性格孤僻，不善于与人交往，朋友稀少，婚姻方面容易晚婚或婚姻不顺。孤辰也主内心空虚，容易感到孤独寂寞。但孤辰也主独立自强，其人往往能够独自完成事业，不需要依赖他人。', '{"type": "zhi", "conditions": {"寅": ["巳"], "巳": ["申"], "申": ["亥"], "亥": ["寅"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}', '[
    "孤独",
    "寡合",
    "婚姻不顺"
]', '[
    "寡宿"
]');
INSERT INTO "shensha_terms" VALUES (12, '寡宿', '神煞', 'negative', '寡宿，主孤独、守寡、人际关系淡薄', '寡宿主孤独、守寡、人际关系淡薄。命中有寡宿者，女性容易守寡或婚姻不幸，男性则容易孤独终老。寡宿也主人际关系淡薄，朋友不多，社交圈子狭窄。但寡宿也主清净无为，其人往往能够专注于自己的事业，不受外界干扰。', '{"type": "zhi", "conditions": {"辰": ["丑"], "丑": ["辰"], "戌": ["未"], "未": ["戌"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}', '[
    "孤独",
    "守寡",
    "人际关系淡薄"
]', '[
    "孤辰"
]');
INSERT INTO "shensha_terms" VALUES (13, '福星', '神煞', 'positive', '福星贵人，主福禄、长寿、吉祥', '福星贵人主福禄、长寿、吉祥。命中有福星贵人者，一生福气深厚，衣食无忧，寿命较长。福星贵人也主善良仁慈，乐于助人，容易得到他人的尊敬和爱戴。', '{"type": "gan", "conditions": {"甲": ["子"], "乙": ["丑"], "丙": ["寅"], "丁": ["卯"], "戊": ["辰"], "己": ["巳"], "庚": ["午"], "辛": ["未"], "壬": ["申"], "癸": ["酉"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}', '[
    "福禄",
    "长寿",
    "吉祥"
]', '[
    "金舆"
]');
INSERT INTO "shensha_terms" VALUES (14, '金舆', '神煞', 'positive', '金舆贵人，主财富、地位、车房', '金舆贵人主财富、地位、车房。命中有金舆贵人者，容易拥有车辆、房产等资产，财运较好，社会地位较高。金舆贵人也主出行便利，一生出行多有车辆代步。', '{"type": "gan", "conditions": {"甲": ["辰"], "乙": ["巳"], "丙": ["午"], "丁": ["未"], "戊": ["申"], "己": ["酉"], "庚": ["戌"], "辛": ["亥"], "壬": ["子"], "癸": ["丑"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}', '[
    "财富",
    "地位",
    "车房"
]', '[
    "福星"
]');
INSERT INTO "shensha_terms" VALUES (15, '学堂', '神煞', 'positive', '学堂星，主学业、教育、知识', '学堂星主学业、教育、知识。命中有学堂星者，学习能力强，学业成绩优异，适合从事教育、学术研究等工作。学堂星也主智慧，其人往往聪明好学，知识渊博。', '{"type": "gan", "conditions": {"甲": ["亥"], "乙": ["戌"], "丙": ["寅"], "丁": ["卯"], "戊": ["巳"], "己": ["午"], "庚": ["申"], "辛": ["酉"], "壬": ["子"], "癸": ["丑"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}', '[
    "学业",
    "教育",
    "知识"
]', '[
    "文昌",
    "词馆"
]');
INSERT INTO "shensha_terms" VALUES (16, '词馆', '神煞', 'positive', '词馆星，主文辞、才华、写作', '词馆星主文辞、才华、写作。命中有词馆星者，善于文辞表达，写作能力强，适合从事文学创作、新闻媒体、文案策划等工作。词馆星也主口才，其人往往能言善辩，表达能力出众。', '{"type": "gan", "conditions": {"甲": ["寅"], "乙": ["卯"], "丙": ["巳"], "丁": ["午"], "戊": ["申"], "己": ["酉"], "庚": ["亥"], "辛": ["子"], "壬": ["辰"], "癸": ["丑"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}', '[
    "文辞",
    "才华",
    "写作"
]', '[
    "文昌",
    "学堂"
]');
INSERT INTO "shensha_terms" VALUES (17, '太极贵人', '神煞', 'positive', '太极贵人，主智慧、神秘、悟性', '太极贵人主智慧、神秘、悟性。命中有太极贵人者，对哲学、宗教、神秘学等有浓厚兴趣，悟性较高，容易理解深奥的道理。太极贵人也主创造力，其人往往能够提出独特的见解和想法。', '{"type": "gan", "conditions": {"甲": ["子"], "乙": ["午"], "丙": ["卯"], "丁": ["酉"], "戊": ["辰"], "己": ["戌"], "庚": ["巳"], "辛": ["亥"], "壬": ["寅"], "癸": ["申"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}', '[
    "智慧",
    "神秘",
    "悟性"
]', '[
    "华盖"
]');
INSERT INTO "shensha_terms" VALUES (18, '天医', '神煞', 'positive', '天医星，主健康、医药、治愈', '天医星主健康、医药、治愈。命中有天医星者，对医学、养生等有浓厚兴趣，适合从事医疗、养生、保健等行业。天医星也主身体健康，其人往往较少生病，即使生病也容易痊愈。', '{"type": "gan", "conditions": {"甲": ["卯"], "乙": ["寅"], "丙": ["子"], "丁": ["亥"], "戊": ["丑"], "己": ["子"], "庚": ["酉"], "辛": ["申"], "壬": ["午"], "癸": ["巳"]}, "locations": ["月柱", "时柱"]}', '[
    "健康",
    "医药",
    "治愈"
]', '[
    "华盖"
]');
INSERT INTO "shensha_terms" VALUES (19, '红艳', '神煞', 'neutral', '红艳煞，主桃花、感情、魅力', '红艳煞主桃花、感情、魅力。命中有红艳煞者，相貌出众，气质迷人，异性缘非常旺盛。红艳煞也主感情丰富，其人往往容易陷入感情纠葛，需注意把握感情分寸。', '{"type": "gan", "conditions": {"甲": ["午"], "乙": ["巳"], "丙": ["寅"], "丁": ["卯"], "戊": ["辰"], "己": ["丑"], "庚": ["子"], "辛": ["亥"], "壬": ["戌"], "癸": ["酉"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}', '[
    "桃花",
    "感情",
    "魅力"
]', '[
    "桃花"
]');
INSERT INTO "shensha_terms" VALUES (20, '勾绞', '神煞', 'negative', '勾绞煞，主是非、纠缠、牵连', '勾绞煞主是非、纠缠、牵连。命中有勾绞煞者，容易卷入他人的是非纠纷中，即使与自己无关也可能被牵连。勾绞煞也主人际关系复杂，容易与人发生矛盾和冲突。', '{"type": "zhi", "conditions": {"子": ["卯"], "卯": ["子"], "丑": ["辰"], "辰": ["丑"], "寅": ["巳"], "巳": ["寅"], "卯": ["午"], "午": ["卯"], "辰": ["未"], "未": ["辰"], "巳": ["申"], "申": ["巳"], "午": ["酉"], "酉": ["午"], "未": ["戌"], "戌": ["未"], "申": ["亥"], "亥": ["申"], "酉": ["子"], "子": ["酉"], "戌": ["丑"], "丑": ["戌"], "亥": ["寅"], "寅": ["亥"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}', '[
    "是非",
    "纠缠",
    "牵连"
]', '[
    "绞煞"
]');
INSERT INTO "shensha_terms" VALUES (21, '绞煞', '神煞', 'negative', '绞煞，主纠缠、束缚、困扰', '绞煞主纠缠、束缚、困扰。命中有绞煞者，容易被事情或人际关系所束缚，难以摆脱困扰。绞煞也主精神压力，其人往往感到身心疲惫，难以放松。', '{"type": "zhi", "conditions": {"子": ["酉"], "酉": ["子"], "丑": ["戌"], "戌": ["丑"], "寅": ["亥"], "亥": ["寅"], "卯": ["子"], "子": ["卯"], "辰": ["丑"], "丑": ["辰"], "巳": ["寅"], "寅": ["巳"], "午": ["卯"], "卯": ["午"], "未": ["辰"], "辰": ["未"], "申": ["巳"], "巳": ["申"], "酉": ["午"], "午": ["酉"], "戌": ["未"], "未": ["戌"], "亥": ["申"], "申": ["亥"]}, "locations": ["年柱", "月柱", "日柱", "时柱"]}', '[
    "纠缠",
    "束缚",
    "困扰"
]', '[
    "勾绞"
]');
INSERT INTO "shier_changsheng" VALUES (1, '长生', 1, '万物出生、生长的阶段，象征新生、希望、起点', '[
    "生机勃勃",
    "充满希望",
    "新的开始",
    "发展潜力大"
]', '运势上升，有利于学习、创业、恋爱等新事物的开始');
INSERT INTO "shier_changsheng" VALUES (2, '沐浴', 2, '万物初生后沐浴清洁，象征洗礼、净化、诱惑', '[
    "清洗净化",
    "桃花旺盛",
    "易受诱惑",
    "需要谨慎"
]', '桃花运旺，但需警惕感情波折，注意洁身自好');
INSERT INTO "shier_changsheng" VALUES (3, '冠带', 3, '万物渐长，穿衣戴冠，象征成长、礼仪、成年', '[
    "逐渐成熟",
    "注重形象",
    "社交活跃",
    "事业起步"
]', '运势稳步上升，适合发展事业、建立人际关系');
INSERT INTO "shier_changsheng" VALUES (4, '临官', 4, '万物长成，可以出仕做官，象征事业、官位、成就', '[
    "事业有成",
    "官位亨通",
    "财运亨通",
    "地位提升"
]', '事业运势最好的阶段，利于升职加薪、创业发展');
INSERT INTO "shier_changsheng" VALUES (5, '帝旺', 5, '万物极盛，如帝王般强盛，象征巅峰、鼎盛、极盛', '[
    "鼎盛时期",
    "如日中天",
    "功成名就",
    "物极必反"
]', '运势达到顶峰，但需注意盛极而衰，保持谦虚谨慎');
INSERT INTO "shier_changsheng" VALUES (6, '衰', 6, '万物由盛转衰，象征衰退、减弱、走下坡', '[
    "运势渐衰",
    "精力减退",
    "保守为宜",
    "不宜冒进"
]', '运势开始下降，宜守不宜攻，注意养生保健');
INSERT INTO "shier_changsheng" VALUES (7, '病', 7, '万物生病，象征疾病、困苦、不顺', '[
    "身体欠安",
    "诸事不顺",
    "困难重重",
    "需要休养"
]', '运势不佳，容易生病或遇到困难，宜静养修身');
INSERT INTO "shier_changsheng" VALUES (8, '死', 8, '万物死亡，象征终结、消亡、低谷', '[
    "运势低谷",
    "诸事不成",
    "死气沉沉",
    "需要转变"
]', '运势最差的阶段，但物极必反，黑暗中孕育希望');
INSERT INTO "shier_changsheng" VALUES (9, '墓', 9, '万物入墓收藏，象征收藏、入库、结束', '[
    "收藏入库",
    "尘埃落定",
    "安定平稳",
    "适合总结"
]', '运势趋于平稳，适合总结经验、积蓄力量');
INSERT INTO "shier_changsheng" VALUES (10, '绝', 10, '万物气绝，象征断绝、灭绝、最低点', '[
    "运势低谷",
    "孤立无援",
    "断绝关系",
    "重新开始"
]', '运势极低，但绝处逢生，是新循环的开始');
INSERT INTO "shier_changsheng" VALUES (11, '胎', 11, '万物受胎孕育，象征孕育、萌芽、计划', '[
    "孕育新生命",
    "计划酝酿",
    "充满期待",
    "打基础"
]', '运势开始回升，适合规划未来、打基础、学习充电');
INSERT INTO "shier_changsheng" VALUES (12, '养', 12, '万物养育成长，象征养育、培养、准备', '[
    "蓄势待发",
    "养精蓄锐",
    "稳步成长",
    "准备充分"
]', '运势继续上升，适合学习成长、积蓄力量，等待时机');
INSERT INTO "shishen_knowledge" VALUES (1, '比肩', '同我', '同阴阳', '与日主五行相同、阴阳相同的天干或地支藏干', '代表兄弟、朋友、同事、竞争者、自我意识', '[
    "独立自主",
    "意志坚定",
    "自尊自信",
    "行动力强",
    "善于合作"
]', '[
    "固执己见",
    "争强好胜",
    "容易冲动",
    "缺乏耐心",
    "孤独自负"
]', '适合独立创业、自由职业、合伙经营', '能守财，但也容易因朋友兄弟而破财', '感情中较为自我，容易与伴侣产生争执');
INSERT INTO "shishen_knowledge" VALUES (2, '劫财', '同我', '异阴阳', '与日主五行相同、阴阳不同的天干或地支藏干', '代表异性朋友、兄弟姐妹、竞争者、破财星', '[
    "热情开朗",
    "善于交际",
    "行动力强",
    "敢于冒险",
    "仗义疏财"
]', '[
    "冲动好斗",
    "花钱大手",
    "容易受骗",
    "嫉妒心强",
    "口舌是非"
]', '适合销售、公关、娱乐等需要交际的行业', '财运起伏大，容易大起大落', '异性缘好，但感情容易有竞争');
INSERT INTO "shishen_knowledge" VALUES (3, '食神', '我生', '同阴阳', '日主所生、与日主阴阳相同的天干或地支藏干', '代表子女、才华、福气、口福、艺术天赋', '[
    "聪明智慧",
    "才华横溢",
    "乐观开朗",
    "品味高雅",
    "福德深厚"
]', '[
    "过于享乐",
    "懒散拖延",
    "清高孤傲",
    "不切实际",
    "容易发胖"
]', '适合艺术、设计、美食、教育、文化等行业', '财运稳定，衣食无忧', '感情浪漫，追求精神层面的契合');
INSERT INTO "shishen_knowledge" VALUES (4, '伤官', '我生', '异阴阳', '日主所生、与日主阴阳不同的天干或地支藏干', '代表才华、创造力、口才、叛逆', '[
    "才华出众",
    "思维敏捷",
    "口才极佳",
    "创造力强",
    "敢作敢当"
]', '[
    "叛逆不羁",
    "心高气傲",
    "口舌是非",
    "容易得罪人",
    "感情波折"
]', '适合创意、表演、销售、法律、传媒等行业', '财运起伏大，靠才华赚钱', '感情丰富，但容易有波折');
INSERT INTO "shishen_knowledge" VALUES (5, '偏财', '我克', '异阴阳', '日主所克、与日主阴阳不同的天干或地支藏干', '代表偏财运、意外之财、父亲、情妇、生意', '[
    "财运亨通",
    "善于理财",
    "慷慨大方",
    "商业头脑",
    "人缘极好"
]', '[
    "花钱大手",
    "投机心理",
    "感情不专",
    "容易被骗",
    "虚荣浮华"
]', '适合经商、投资、金融、销售等行业', '偏财旺，容易有意外收入', '异性缘佳，感情经历丰富');
INSERT INTO "shishen_knowledge" VALUES (6, '正财', '我克', '同阴阳', '日主所克、与日主阴阳相同的天干或地支藏干', '代表正财运、稳定收入、妻子、财产、务实', '[
    "踏实肯干",
    "勤俭节约",
    "财运稳定",
    "顾家负责",
    "诚实守信"
]', '[
    "过于节俭",
    "固执保守",
    "缺乏浪漫",
    "容易斤斤计较",
    "劳碌命"
]', '适合稳定工作、财务管理、实业经营', '正财运好，收入稳定', '感情稳定，重视家庭');
INSERT INTO "shishen_knowledge" VALUES (7, '正官', '克我', '异阴阳', '克制日主、与日主阴阳不同的天干或地支藏干', '代表官职、地位、丈夫、规矩、约束力', '[
    "正直守信",
    "责任感强",
    "领导能力",
    "规矩自律",
    "名声好"
]', '[
    "过于刻板",
    "压抑自我",
    "胆小怕事",
    "压力山大",
    "墨守成规"
]', '适合公务员、管理层、法律、军警等职业', '财运稳定，靠职位收入', '女命正官为夫，感情稳定');
INSERT INTO "shishen_knowledge" VALUES (8, '七杀', '克我', '同阴阳', '克制日主、与日主阴阳相同的天干或地支藏干', '代表偏官、权力、小人、压力、冲劲', '[
    "有魄力",
    "决断力强",
    "不服输",
    "执行力强",
    "敢闯敢拼"
]', '[
    "脾气暴躁",
    "好勇斗狠",
    "压力过大",
    "容易招小人",
    "叛逆反抗"
]', '适合军警、创业、竞争激烈的行业', '财运起伏大，风险与机遇并存', '感情有挑战，需要磨合');
INSERT INTO "shishen_knowledge" VALUES (9, '正印', '生我', '异阴阳', '生助日主、与日主阴阳不同的天干或地支藏干', '代表母亲、长辈、学问、名誉、贵人', '[
    "学识渊博",
    "心地善良",
    "贵人相助",
    "名声好",
    "有福气"
]', '[
    "依赖心强",
    "缺乏主见",
    "好逸恶劳",
    "空想多实干少",
    "过于清高"
]', '适合教育、学术研究、文化、出版等行业', '财运平稳，靠知识技能赚钱', '感情温和，注重精神交流');
INSERT INTO "shishen_knowledge" VALUES (10, '偏印', '生我', '同阴阳', '生助日主、与日主阴阳相同的天干或地支藏干', '代表继母、偏门学问、玄学、孤独、枭神', '[
    "思维独特",
    "悟性极高",
    "偏才多能",
    "直觉敏锐",
    "适合研究"
]', '[
    "性格孤僻",
    "多疑善变",
    "容易钻牛角尖",
    "离群索居",
    "不利于子女"
]', '适合玄学、心理学、科研、技术研发等', '财运偏门，靠特殊技能赚钱', '感情平淡，追求精神层面');
INSERT INTO "shishen_map" VALUES (1, '生我', '印星', '偏印', '正印');
INSERT INTO "shishen_map" VALUES (2, '我生', '食伤', '伤官', '食神');
INSERT INTO "shishen_map" VALUES (3, '克我', '官杀', '七杀', '正官');
INSERT INTO "shishen_map" VALUES (4, '我克', '财星', '偏财', '正财');
INSERT INTO "shishen_map" VALUES (5, '同我', '比劫', '比肩', '劫财');
INSERT INTO "shishen_map" VALUES (6, '生我', '印星', '偏印', '正印');
INSERT INTO "shishen_map" VALUES (7, '我生', '食伤', '伤官', '食神');
INSERT INTO "shishen_map" VALUES (8, '克我', '官杀', '七杀', '正官');
INSERT INTO "shishen_map" VALUES (9, '我克', '财星', '偏财', '正财');
INSERT INTO "shishen_map" VALUES (10, '同我', '比劫', '比肩', '劫财');
INSERT INTO "sixty_jiazi" VALUES (1, 0, '甲子', '甲', '子');
INSERT INTO "sixty_jiazi" VALUES (2, 1, '乙丑', '乙', '丑');
INSERT INTO "sixty_jiazi" VALUES (3, 2, '丙寅', '丙', '寅');
INSERT INTO "sixty_jiazi" VALUES (4, 3, '丁卯', '丁', '卯');
INSERT INTO "sixty_jiazi" VALUES (5, 4, '戊辰', '戊', '辰');
INSERT INTO "sixty_jiazi" VALUES (6, 5, '己巳', '己', '巳');
INSERT INTO "sixty_jiazi" VALUES (7, 6, '庚午', '庚', '午');
INSERT INTO "sixty_jiazi" VALUES (8, 7, '辛未', '辛', '未');
INSERT INTO "sixty_jiazi" VALUES (9, 8, '壬申', '壬', '申');
INSERT INTO "sixty_jiazi" VALUES (10, 9, '癸酉', '癸', '酉');
INSERT INTO "sixty_jiazi" VALUES (11, 10, '甲戌', '甲', '戌');
INSERT INTO "sixty_jiazi" VALUES (12, 11, '乙亥', '乙', '亥');
INSERT INTO "sixty_jiazi" VALUES (13, 12, '丙子', '丙', '子');
INSERT INTO "sixty_jiazi" VALUES (14, 13, '丁丑', '丁', '丑');
INSERT INTO "sixty_jiazi" VALUES (15, 14, '戊寅', '戊', '寅');
INSERT INTO "sixty_jiazi" VALUES (16, 15, '己卯', '己', '卯');
INSERT INTO "sixty_jiazi" VALUES (17, 16, '庚辰', '庚', '辰');
INSERT INTO "sixty_jiazi" VALUES (18, 17, '辛巳', '辛', '巳');
INSERT INTO "sixty_jiazi" VALUES (19, 18, '壬午', '壬', '午');
INSERT INTO "sixty_jiazi" VALUES (20, 19, '癸未', '癸', '未');
INSERT INTO "sixty_jiazi" VALUES (21, 20, '甲申', '甲', '申');
INSERT INTO "sixty_jiazi" VALUES (22, 21, '乙酉', '乙', '酉');
INSERT INTO "sixty_jiazi" VALUES (23, 22, '丙戌', '丙', '戌');
INSERT INTO "sixty_jiazi" VALUES (24, 23, '丁亥', '丁', '亥');
INSERT INTO "sixty_jiazi" VALUES (25, 24, '戊子', '戊', '子');
INSERT INTO "sixty_jiazi" VALUES (26, 25, '己丑', '己', '丑');
INSERT INTO "sixty_jiazi" VALUES (27, 26, '庚寅', '庚', '寅');
INSERT INTO "sixty_jiazi" VALUES (28, 27, '辛卯', '辛', '卯');
INSERT INTO "sixty_jiazi" VALUES (29, 28, '壬辰', '壬', '辰');
INSERT INTO "sixty_jiazi" VALUES (30, 29, '癸巳', '癸', '巳');
INSERT INTO "sixty_jiazi" VALUES (31, 30, '甲午', '甲', '午');
INSERT INTO "sixty_jiazi" VALUES (32, 31, '乙未', '乙', '未');
INSERT INTO "sixty_jiazi" VALUES (33, 32, '丙申', '丙', '申');
INSERT INTO "sixty_jiazi" VALUES (34, 33, '丁酉', '丁', '酉');
INSERT INTO "sixty_jiazi" VALUES (35, 34, '戊戌', '戊', '戌');
INSERT INTO "sixty_jiazi" VALUES (36, 35, '己亥', '己', '亥');
INSERT INTO "sixty_jiazi" VALUES (37, 36, '庚子', '庚', '子');
INSERT INTO "sixty_jiazi" VALUES (38, 37, '辛丑', '辛', '丑');
INSERT INTO "sixty_jiazi" VALUES (39, 38, '壬寅', '壬', '寅');
INSERT INTO "sixty_jiazi" VALUES (40, 39, '癸卯', '癸', '卯');
INSERT INTO "sixty_jiazi" VALUES (41, 40, '甲辰', '甲', '辰');
INSERT INTO "sixty_jiazi" VALUES (42, 41, '乙巳', '乙', '巳');
INSERT INTO "sixty_jiazi" VALUES (43, 42, '丙午', '丙', '午');
INSERT INTO "sixty_jiazi" VALUES (44, 43, '丁未', '丁', '未');
INSERT INTO "sixty_jiazi" VALUES (45, 44, '戊申', '戊', '申');
INSERT INTO "sixty_jiazi" VALUES (46, 45, '己酉', '己', '酉');
INSERT INTO "sixty_jiazi" VALUES (47, 46, '庚戌', '庚', '戌');
INSERT INTO "sixty_jiazi" VALUES (48, 47, '辛亥', '辛', '亥');
INSERT INTO "sixty_jiazi" VALUES (49, 48, '壬子', '壬', '子');
INSERT INTO "sixty_jiazi" VALUES (50, 49, '癸丑', '癸', '丑');
INSERT INTO "sixty_jiazi" VALUES (51, 50, '甲寅', '甲', '寅');
INSERT INTO "sixty_jiazi" VALUES (52, 51, '乙卯', '乙', '卯');
INSERT INTO "sixty_jiazi" VALUES (53, 52, '丙辰', '丙', '辰');
INSERT INTO "sixty_jiazi" VALUES (54, 53, '丁巳', '丁', '巳');
INSERT INTO "sixty_jiazi" VALUES (55, 54, '戊午', '戊', '午');
INSERT INTO "sixty_jiazi" VALUES (56, 55, '己未', '己', '未');
INSERT INTO "sixty_jiazi" VALUES (57, 56, '庚申', '庚', '申');
INSERT INTO "sixty_jiazi" VALUES (58, 57, '辛酉', '辛', '酉');
INSERT INTO "sixty_jiazi" VALUES (59, 58, '壬戌', '壬', '戌');
INSERT INTO "sixty_jiazi" VALUES (60, 59, '癸亥', '癸', '亥');
INSERT INTO "tian_gan" VALUES (1, '甲', '木', '阳', '东方', '春季', '万物破土而出，开始生长', '胆', '头、头发', 0);
INSERT INTO "tian_gan" VALUES (2, '乙', '木', '阴', '东方', '春季', '万物初生，枝叶柔软', '肝', '肩、颈', 1);
INSERT INTO "tian_gan" VALUES (3, '丙', '火', '阳', '南方', '夏季', '万物光明茂盛，气势恢宏', '小肠', '额、肩', 2);
INSERT INTO "tian_gan" VALUES (4, '丁', '火', '阴', '南方', '夏季', '万物成长，欣欣向荣', '心', '胸、舌', 3);
INSERT INTO "tian_gan" VALUES (5, '戊', '土', '阳', '中央', '长夏', '万物茂盛，阳土厚重', '胃', '胁、鼻', 4);
INSERT INTO "tian_gan" VALUES (6, '己', '土', '阴', '中央', '长夏', '万物蕴藏，阴土柔和', '脾', '腹、口', 5);
INSERT INTO "tian_gan" VALUES (7, '庚', '金', '阳', '西方', '秋季', '万物收敛，阳金刚健', '大肠', '筋、爪', 6);
INSERT INTO "tian_gan" VALUES (8, '辛', '金', '阴', '西方', '秋季', '万物成熟，阴金温润', '肺', '胸、肺', 7);
INSERT INTO "tian_gan" VALUES (9, '壬', '水', '阳', '北方', '冬季', '万物潜藏，阳水奔腾', '膀胱', '胫、足', 8);
INSERT INTO "tian_gan" VALUES (10, '癸', '水', '阴', '北方', '冬季', '万物闭藏，阴水滋润', '肾', '足、发', 9);
INSERT INTO "tian_gan_he" VALUES (1, '甲己', '土', '中正之合', '主诚信稳重，以仁合义');
INSERT INTO "tian_gan_he" VALUES (2, '乙庚', '金', '仁义之合', '主刚柔并济，以义合仁');
INSERT INTO "tian_gan_he" VALUES (3, '丙辛', '水', '威制之合', '主威严果决，以威制众');
INSERT INTO "tian_gan_he" VALUES (4, '丁壬', '木', '淫昵之合', '主感情丰富，以情合意');
INSERT INTO "tian_gan_he" VALUES (5, '戊癸', '火', '无情之合', '主老少相配，无情中有情');
INSERT INTO "wuxing_knowledge" VALUES (1, '木', '木曰曲直', '东方', '春季', '绿色、青色', '[
    "肝",
    "胆"
]', '酸', 3, '[
    "积极向上",
    "富有创造力",
    "善于创新",
    "有进取心",
    "正直善良",
    "乐观开朗"
]', '[
    "固执己见",
    "过于冲动",
    "缺乏耐心",
    "容易情绪化",
    "优柔寡断"
]', '[
    "创意设计",
    "艺术文化",
    "教育培训",
    "林业农业",
    "木材加工",
    "出版传媒"
]', '注意肝胆保养，少熬夜，多运动，保持心情舒畅', '木主生发，代表生命力和成长力。木旺之人性格开朗、有创造力，但需注意避免过于冲动。', '[
    "生长",
    "生发",
    "条达",
    "舒畅",
    "仁慈"
]');
INSERT INTO "wuxing_knowledge" VALUES (2, '火', '火曰炎上', '南方', '夏季', '红色、紫色', '[
    "心",
    "小肠"
]', '苦', 2, '[
    "热情洋溢",
    "乐观开朗",
    "富有感染力",
    "社交能力强",
    "充满活力",
    "敢作敢当"
]', '[
    "急躁冲动",
    "缺乏冷静",
    "过于张扬",
    "容易骄傲",
    "缺乏耐心"
]', '[
    "销售营销",
    "演艺娱乐",
    "公共关系",
    "能源电力",
    "餐饮酒店",
    "互联网"
]', '注意心脏和血压保养，避免过度劳累，保持心态平和', '火主炎上，代表热情和活力。火旺之人性格开朗、善于交际，但需注意控制情绪，避免急躁。', '[
    "温热",
    "上升",
    "光明",
    "热烈",
    "急躁"
]');
INSERT INTO "wuxing_knowledge" VALUES (3, '土', '土爰稼穑', '中央', '长夏', '黄色、棕色', '[
    "脾",
    "胃"
]', '甘', 5, '[
    "稳重可靠",
    "诚实守信",
    "有责任感",
    "踏实肯干",
    "包容大度",
    "务实节俭"
]', '[
    "过于保守",
    "缺乏变通",
    "固执僵化",
    "反应迟钝",
    "容易犹豫"
]', '[
    "金融银行",
    "房地产",
    "建筑工程",
    "企业管理",
    "农业生产",
    "仓储物流"
]', '注意脾胃保养，饮食规律，避免暴饮暴食，适当运动', '土主稼穑，代表包容和承载。土旺之人性格稳重、值得信赖，但需注意避免过于保守，学会灵活变通。', '[
    "生化",
    "承载",
    "受纳",
    "稳重",
    "包容"
]');
INSERT INTO "wuxing_knowledge" VALUES (4, '金', '金曰从革', '西方', '秋季', '白色、金色', '[
    "肺",
    "大肠"
]', '辛', 4, '[
    "果断刚毅",
    "追求完美",
    "有决断力",
    "精明干练",
    "公正无私",
    "重情重义"
]', '[
    "刻薄寡恩",
    "刚愎自用",
    "过于挑剔",
    "缺乏变通",
    "容易悲伤"
]', '[
    "法律司法",
    "金融投资",
    "金属机械",
    "汽车制造",
    "珠宝首饰",
    "军警保安"
]', '注意肺部和呼吸道保养，多喝水，保持空气清新，避免悲伤过度', '金主从革，代表决断和变革。金旺之人性格刚毅、做事果断，但需注意人际关系，避免过于苛刻。', '[
    "清净",
    "肃杀",
    "收敛",
    "决断",
    "刚毅"
]');
INSERT INTO "wuxing_knowledge" VALUES (5, '水', '水曰润下', '北方', '冬季', '蓝色、黑色', '[
    "肾",
    "膀胱"
]', '咸', 1, '[
    "聪明灵活",
    "思维敏捷",
    "适应力强",
    "富有智慧",
    "善于变通",
    "足智多谋"
]', '[
    "散漫无章",
    "缺乏定力",
    "优柔寡断",
    "过于敏感",
    "容易多疑"
]', '[
    "商贸物流",
    "旅游服务",
    "科技研发",
    "水产养殖",
    "交通运输",
    "咨询策划"
]', '注意肾脏和泌尿系统保养，避免过度劳累，注意保暖', '水主润下，代表智慧和灵活。水旺之人聪明机智、善于变通，但需注意保持专注，避免过于散漫。', '[
    "寒凉",
    "向下",
    "滋润",
    "智慧",
    "灵活"
]');
INSERT INTO "wuxing_relations" VALUES (1, 'sheng', '五行相生', '木生火，火生土，土生金，金生水，水生木', '木', '火', '木燃而生火，木为火之母，火为木之子');
INSERT INTO "wuxing_relations" VALUES (2, 'sheng', '五行相生', '', '火', '土', '火焚万物而生土，火为土之母，土为火之子');
INSERT INTO "wuxing_relations" VALUES (3, 'sheng', '五行相生', '', '土', '金', '土中藏金，土为金之母，金为土之子');
INSERT INTO "wuxing_relations" VALUES (4, 'sheng', '五行相生', '', '金', '水', '金销熔生水，金为水之母，水为金之子');
INSERT INTO "wuxing_relations" VALUES (5, 'sheng', '五行相生', '', '水', '木', '水滋润生木，水为木之母，木为水之子');
INSERT INTO "wuxing_relations" VALUES (6, 'ke', '五行相克', '木克土，土克水，水克火，火克金，金克木', '木', '土', '木植根于土中，吸收土中养分，故土被木所克');
INSERT INTO "wuxing_relations" VALUES (7, 'ke', '五行相克', '', '土', '水', '土能阻挡水流，故土能克水');
INSERT INTO "wuxing_relations" VALUES (8, 'ke', '五行相克', '', '水', '火', '水能灭火，故水能克火');
INSERT INTO "wuxing_relations" VALUES (9, 'ke', '五行相克', '', '火', '金', '火能熔金，故火能克金');
INSERT INTO "wuxing_relations" VALUES (10, 'ke', '五行相克', '', '金', '木', '金属制成的刀具能砍伐树木，故金能克木');
INSERT INTO "wuxing_relations" VALUES (11, 'multiplication', '五行相乘', '乘，即乘虚侵袭之意。相乘即相克太过', '木', '土', '木气太过，乘土之虚而克之');
INSERT INTO "wuxing_relations" VALUES (12, 'multiplication', '五行相乘', '', '土', '水', '土气太过，乘水之虚而克之');
INSERT INTO "wuxing_relations" VALUES (13, 'multiplication', '五行相乘', '', '水', '火', '水气太过，乘火之虚而克之');
INSERT INTO "wuxing_relations" VALUES (14, 'multiplication', '五行相乘', '', '火', '金', '火气太过，乘金之虚而克之');
INSERT INTO "wuxing_relations" VALUES (15, 'multiplication', '五行相乘', '', '金', '木', '金气太过，乘木之虚而克之');
INSERT INTO "wuxing_relations" VALUES (16, 'insult', '五行相侮', '侮，即持强凌弱之意。相侮即反克', '木', '金', '木气太过，反侮金（木旺反侮金）');
INSERT INTO "wuxing_relations" VALUES (17, 'insult', '五行相侮', '', '金', '火', '金气太过，反侮火（金旺反侮火）');
INSERT INTO "wuxing_relations" VALUES (18, 'insult', '五行相侮', '', '火', '水', '火气太过，反侮水（火旺反侮水）');
INSERT INTO "wuxing_relations" VALUES (19, 'insult', '五行相侮', '', '水', '土', '水气太过，反侮土（水旺反侮土）');
INSERT INTO "wuxing_relations" VALUES (20, 'insult', '五行相侮', '', '土', '木', '土气太过，反侮木（土旺反侮木）');
INSERT INTO "wuxing_relations" VALUES (21, 'sheng', '五行相生', '木生火，火生土，土生金，金生水，水生木', '木', '火', '木燃而生火，木为火之母，火为木之子');
INSERT INTO "wuxing_relations" VALUES (22, 'sheng', '五行相生', '', '火', '土', '火焚万物而生土，火为土之母，土为火之子');
INSERT INTO "wuxing_relations" VALUES (23, 'sheng', '五行相生', '', '土', '金', '土中藏金，土为金之母，金为土之子');
INSERT INTO "wuxing_relations" VALUES (24, 'sheng', '五行相生', '', '金', '水', '金销熔生水，金为水之母，水为金之子');
INSERT INTO "wuxing_relations" VALUES (25, 'sheng', '五行相生', '', '水', '木', '水滋润生木，水为木之母，木为水之子');
INSERT INTO "wuxing_relations" VALUES (26, 'ke', '五行相克', '木克土，土克水，水克火，火克金，金克木', '木', '土', '木植根于土中，吸收土中养分，故土被木所克');
INSERT INTO "wuxing_relations" VALUES (27, 'ke', '五行相克', '', '土', '水', '土能阻挡水流，故土能克水');
INSERT INTO "wuxing_relations" VALUES (28, 'ke', '五行相克', '', '水', '火', '水能灭火，故水能克火');
INSERT INTO "wuxing_relations" VALUES (29, 'ke', '五行相克', '', '火', '金', '火能熔金，故火能克金');
INSERT INTO "wuxing_relations" VALUES (30, 'ke', '五行相克', '', '金', '木', '金属制成的刀具能砍伐树木，故金能克木');
INSERT INTO "wuxing_relations" VALUES (31, 'multiplication', '五行相乘', '乘，即乘虚侵袭之意。相乘即相克太过', '木', '土', '木气太过，乘土之虚而克之');
INSERT INTO "wuxing_relations" VALUES (32, 'multiplication', '五行相乘', '', '土', '水', '土气太过，乘水之虚而克之');
INSERT INTO "wuxing_relations" VALUES (33, 'multiplication', '五行相乘', '', '水', '火', '水气太过，乘火之虚而克之');
INSERT INTO "wuxing_relations" VALUES (34, 'multiplication', '五行相乘', '', '火', '金', '火气太过，乘金之虚而克之');
INSERT INTO "wuxing_relations" VALUES (35, 'multiplication', '五行相乘', '', '金', '木', '金气太过，乘木之虚而克之');
INSERT INTO "wuxing_relations" VALUES (36, 'insult', '五行相侮', '侮，即持强凌弱之意。相侮即反克', '木', '金', '木气太过，反侮金（木旺反侮金）');
INSERT INTO "wuxing_relations" VALUES (37, 'insult', '五行相侮', '', '金', '火', '金气太过，反侮火（金旺反侮火）');
INSERT INTO "wuxing_relations" VALUES (38, 'insult', '五行相侮', '', '火', '水', '火气太过，反侮水（火旺反侮水）');
INSERT INTO "wuxing_relations" VALUES (39, 'insult', '五行相侮', '', '水', '土', '水气太过，反侮土（水旺反侮土）');
INSERT INTO "wuxing_relations" VALUES (40, 'insult', '五行相侮', '', '土', '木', '土气太过，反侮木（土旺反侮木）');
INSERT INTO "yue_ling_weight" VALUES (1, '寅', '木', 1.5);
INSERT INTO "yue_ling_weight" VALUES (2, '寅', '火', 0.5);
INSERT INTO "yue_ling_weight" VALUES (3, '寅', '土', 0.3);
INSERT INTO "yue_ling_weight" VALUES (4, '寅', '金', 0.2);
INSERT INTO "yue_ling_weight" VALUES (5, '寅', '水', 0.3);
INSERT INTO "yue_ling_weight" VALUES (6, '卯', '木', 1.5);
INSERT INTO "yue_ling_weight" VALUES (7, '卯', '火', 0.6);
INSERT INTO "yue_ling_weight" VALUES (8, '卯', '土', 0.2);
INSERT INTO "yue_ling_weight" VALUES (9, '卯', '金', 0.1);
INSERT INTO "yue_ling_weight" VALUES (10, '卯', '水', 0.3);
INSERT INTO "yue_ling_weight" VALUES (11, '辰', '土', 1.0);
INSERT INTO "yue_ling_weight" VALUES (12, '辰', '木', 0.4);
INSERT INTO "yue_ling_weight" VALUES (13, '辰', '水', 0.3);
INSERT INTO "yue_ling_weight" VALUES (14, '辰', '火', 0.2);
INSERT INTO "yue_ling_weight" VALUES (15, '辰', '金', 0.3);
INSERT INTO "yue_ling_weight" VALUES (16, '巳', '火', 1.5);
INSERT INTO "yue_ling_weight" VALUES (17, '巳', '土', 0.4);
INSERT INTO "yue_ling_weight" VALUES (18, '巳', '金', 0.2);
INSERT INTO "yue_ling_weight" VALUES (19, '巳', '木', 0.3);
INSERT INTO "yue_ling_weight" VALUES (20, '巳', '水', 0.2);
INSERT INTO "yue_ling_weight" VALUES (21, '午', '火', 1.5);
INSERT INTO "yue_ling_weight" VALUES (22, '午', '土', 0.5);
INSERT INTO "yue_ling_weight" VALUES (23, '午', '金', 0.1);
INSERT INTO "yue_ling_weight" VALUES (24, '午', '木', 0.2);
INSERT INTO "yue_ling_weight" VALUES (25, '午', '水', 0.2);
INSERT INTO "yue_ling_weight" VALUES (26, '未', '土', 1.0);
INSERT INTO "yue_ling_weight" VALUES (27, '未', '火', 0.4);
INSERT INTO "yue_ling_weight" VALUES (28, '未', '木', 0.3);
INSERT INTO "yue_ling_weight" VALUES (29, '未', '水', 0.2);
INSERT INTO "yue_ling_weight" VALUES (30, '未', '金', 0.3);
INSERT INTO "yue_ling_weight" VALUES (31, '申', '金', 1.5);
INSERT INTO "yue_ling_weight" VALUES (32, '申', '水', 0.5);
INSERT INTO "yue_ling_weight" VALUES (33, '申', '土', 0.3);
INSERT INTO "yue_ling_weight" VALUES (34, '申', '木', 0.2);
INSERT INTO "yue_ling_weight" VALUES (35, '申', '火', 0.2);
INSERT INTO "yue_ling_weight" VALUES (36, '酉', '金', 1.5);
INSERT INTO "yue_ling_weight" VALUES (37, '酉', '土', 0.4);
INSERT INTO "yue_ling_weight" VALUES (38, '酉', '水', 0.3);
INSERT INTO "yue_ling_weight" VALUES (39, '酉', '木', 0.1);
INSERT INTO "yue_ling_weight" VALUES (40, '酉', '火', 0.2);
INSERT INTO "yue_ling_weight" VALUES (41, '戌', '土', 1.0);
INSERT INTO "yue_ling_weight" VALUES (42, '戌', '金', 0.4);
INSERT INTO "yue_ling_weight" VALUES (43, '戌', '火', 0.3);
INSERT INTO "yue_ling_weight" VALUES (44, '戌', '木', 0.2);
INSERT INTO "yue_ling_weight" VALUES (45, '戌', '水', 0.2);
INSERT INTO "yue_ling_weight" VALUES (46, '亥', '水', 1.5);
INSERT INTO "yue_ling_weight" VALUES (47, '亥', '木', 0.5);
INSERT INTO "yue_ling_weight" VALUES (48, '亥', '火', 0.2);
INSERT INTO "yue_ling_weight" VALUES (49, '亥', '土', 0.3);
INSERT INTO "yue_ling_weight" VALUES (50, '亥', '金', 0.3);
INSERT INTO "yue_ling_weight" VALUES (51, '子', '水', 1.5);
INSERT INTO "yue_ling_weight" VALUES (52, '子', '金', 0.4);
INSERT INTO "yue_ling_weight" VALUES (53, '子', '火', 0.1);
INSERT INTO "yue_ling_weight" VALUES (54, '子', '木', 0.3);
INSERT INTO "yue_ling_weight" VALUES (55, '子', '土', 0.3);
INSERT INTO "yue_ling_weight" VALUES (56, '丑', '土', 1.0);
INSERT INTO "yue_ling_weight" VALUES (57, '丑', '水', 0.4);
INSERT INTO "yue_ling_weight" VALUES (58, '丑', '金', 0.3);
INSERT INTO "yue_ling_weight" VALUES (59, '丑', '火', 0.2);
INSERT INTO "yue_ling_weight" VALUES (60, '丑', '木', 0.2);
INSERT INTO "yunshi_gan_analysis" VALUES (1, '甲', '甲木参天，蓬勃向上，主创新、开拓、积极进取', '过旺则固执、冲动，需注意人际关系');
INSERT INTO "yunshi_gan_analysis" VALUES (2, '乙', '乙木柔韧，善于变通，主智慧、文雅、富有艺术气质', '过弱则意志不坚，容易随波逐流');
INSERT INTO "yunshi_gan_analysis" VALUES (3, '丙', '丙火炎炎，热情洋溢，主光明、才华、社交能力强', '过旺则急躁、冲动，需控制情绪');
INSERT INTO "yunshi_gan_analysis" VALUES (4, '丁', '丁火柔和，温文尔雅，主细腻、体贴、富有同情心', '过弱则缺乏主见，容易犹豫不决');
INSERT INTO "yunshi_gan_analysis" VALUES (5, '戊', '戊土厚重，稳重可靠，主诚信、务实、有担当', '过旺则保守、固执，缺乏灵活性');
INSERT INTO "yunshi_gan_analysis" VALUES (6, '己', '己土湿润，包容滋养，主善良、忍耐、有包容心', '过弱则缺乏自信，容易受人影响');
INSERT INTO "yunshi_gan_analysis" VALUES (7, '庚', '庚金刚健，果断决断，主正义、刚强、有魄力', '过旺则刚愎自用，容易得罪人');
INSERT INTO "yunshi_gan_analysis" VALUES (8, '辛', '辛金温润，细腻精致，主精致、敏锐、追求完美', '过弱则优柔寡断，缺乏决断力');
INSERT INTO "yunshi_gan_analysis" VALUES (9, '壬', '壬水浩荡，聪明灵活，主智慧、变通、足智多谋', '过旺则放纵不羁，缺乏定力');
INSERT INTO "yunshi_gan_analysis" VALUES (10, '癸', '癸水柔细，智慧深沉，主细腻、直觉、深谋远虑', '过弱则多疑敏感，缺乏安全感');
INSERT INTO "yunshi_zhi_analysis" VALUES (1, '子', '子水智慧，主思维敏捷，但需防桃花困扰');
INSERT INTO "yunshi_zhi_analysis" VALUES (2, '丑', '丑土厚重，主稳重踏实，但需防固执保守');
INSERT INTO "yunshi_zhi_analysis" VALUES (3, '寅', '寅木生发，主积极进取，但需防冲动鲁莽');
INSERT INTO "yunshi_zhi_analysis" VALUES (4, '卯', '卯木柔顺，主文雅艺术，但需防犹豫不决');
INSERT INTO "yunshi_zhi_analysis" VALUES (5, '辰', '辰土藏龙，主潜力无限，但需防优柔寡断');
INSERT INTO "yunshi_zhi_analysis" VALUES (6, '巳', '巳火热情，主活力四射，但需防急躁冲动');
INSERT INTO "yunshi_zhi_analysis" VALUES (7, '午', '午火旺盛，主光明正大，但需防骄傲自满');
INSERT INTO "yunshi_zhi_analysis" VALUES (8, '未', '未土温和，主善良包容，但需防依赖他人');
INSERT INTO "yunshi_zhi_analysis" VALUES (9, '申', '申金锐利，主果断刚毅，但需防刻薄寡恩');
INSERT INTO "yunshi_zhi_analysis" VALUES (10, '酉', '酉金清秀，主才华出众，但需防孤芳自赏');
INSERT INTO "yunshi_zhi_analysis" VALUES (11, '戌', '戌土厚重，主稳重可靠，但需防固执己见');
INSERT INTO "yunshi_zhi_analysis" VALUES (12, '亥', '亥水智慧，主聪明灵活，但需防散漫无章');

COMMIT;
