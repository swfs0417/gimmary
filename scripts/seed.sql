-- =============================================================
-- 테스트 데이터 시드 SQL
-- 비밀번호: pass1234 (argon2id)
-- 실행: mysql -u <user> -p <db> < scripts/seed.sql
-- =============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ── 기존 데이터 초기화 ─────────────────────────────────────────
DELETE FROM group_missions;
DELETE FROM group_members;
DELETE FROM missions;
DELETE FROM `groups`;
DELETE FROM team_members;
DELETE FROM teams;
DELETE FROM users;

-- ── 유저 ─────────────────────────────────────────────────────
INSERT INTO users (login_id, username, password_hash, gender, student_id, hakbun, mbti) VALUES
  ('admin1', '어드민1', '$argon2id$v=19$m=65536,t=3,p=4$R73GywS99HE+wAtxDu0irQ$xqw7PrJDH6MqR6JwiM2hz+h6/PCtzDhc/6rjvnIgVws', 'male',   '2021001', 21, 'INTJ'),
  ('user1',  '참여자1', '$argon2id$v=19$m=65536,t=3,p=4$R73GywS99HE+wAtxDu0irQ$xqw7PrJDH6MqR6JwiM2hz+h6/PCtzDhc/6rjvnIgVws', 'female', '2021002', 21, 'ENFP'),
  ('user2',  '참여자2', '$argon2id$v=19$m=65536,t=3,p=4$R73GywS99HE+wAtxDu0irQ$xqw7PrJDH6MqR6JwiM2hz+h6/PCtzDhc/6rjvnIgVws', 'male',   '2021003', 21, 'ISFJ'),
  ('user3',  '참여자3', '$argon2id$v=19$m=65536,t=3,p=4$R73GywS99HE+wAtxDu0irQ$xqw7PrJDH6MqR6JwiM2hz+h6/PCtzDhc/6rjvnIgVws', 'female', '2022001', 22, 'ENTP'),
  ('user4',  '참여자4', '$argon2id$v=19$m=65536,t=3,p=4$R73GywS99HE+wAtxDu0irQ$xqw7PrJDH6MqR6JwiM2hz+h6/PCtzDhc/6rjvnIgVws', 'male',   '2022002', 22, 'INFP'),
  ('user5',  '참여자5', '$argon2id$v=19$m=65536,t=3,p=4$R73GywS99HE+wAtxDu0irQ$xqw7PrJDH6MqR6JwiM2hz+h6/PCtzDhc/6rjvnIgVws', 'female', '2022003', 22, 'ESTJ');

-- ── 팀 ───────────────────────────────────────────────────────
INSERT INTO teams (name, admin_id, auth_code, created_at) VALUES
  ('테스트팀A', 1, 'TEST01', NOW());

-- ── 팀 멤버 ──────────────────────────────────────────────────
INSERT INTO team_members (team_id, user_id, role) VALUES
  (1, 1, 'admin'),
  (1, 2, 'participant'),
  (1, 3, 'participant'),
  (1, 4, 'participant'),
  (1, 5, 'participant'),
  (1, 6, 'participant');

-- ── 그룹 ─────────────────────────────────────────────────────
INSERT INTO `groups` (team_id, name, leader_id, created_at) VALUES
  (1, '1조', 2, NOW()),
  (1, '2조', 4, NOW());

-- ── 그룹 멤버 ────────────────────────────────────────────────
INSERT INTO group_members (group_id, user_id, joined_at) VALUES
  (1, 2, NOW()),
  (1, 3, NOW()),
  (2, 4, NOW()),
  (2, 5, NOW()),
  (2, 6, NOW());

-- ── 미션 (팀 레벨) ────────────────────────────────────────────
INSERT INTO missions (team_id, title, description, points, created_at) VALUES
  (1, '점심 같이 먹기', '팀원들과 함께 점심 식사를 하세요.', 10, NOW()),
  (1, '팀 사진 찍기',   '단체 사진을 찍어서 공유하세요.',   20, NOW());

-- ── 그룹 미션 (그룹별 달성 상태) ──────────────────────────────
INSERT INTO group_missions (mission_id, group_id, status) VALUES
  (1, 1, 'pending'),
  (1, 2, 'pending'),
  (2, 1, 'pending'),
  (2, 2, 'pending');

SET FOREIGN_KEY_CHECKS = 1;
